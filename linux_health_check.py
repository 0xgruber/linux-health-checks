#!/usr/bin/env python3
"""
Linux Health Check Script
Author: System Administrator
Description: Comprehensive health and security audit for Linux systems
License: MIT
"""

__version__ = "1.2.1"

import os
import sys
import subprocess
import logging
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import re
import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import urllib.request
import urllib.error
import configparser
import stat

# ============================================================================
# CONFIGURATION
# ============================================================================
#
# You can customize these settings by creating a health_check.cfg file
# in the same directory as this script. See health_check.cfg.example
# for a template with all available options.
#
# The script will load settings from health_check.cfg if it exists,
# otherwise it will use the defaults below.
#
# Configuration priority: Environment Variables > Config File > Defaults
# ============================================================================

# Try to load user configuration
_config = None
_has_config = False

try:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    _config_file = os.path.join(_script_dir, "health_check.cfg")

    if os.path.exists(_config_file):
        # Check file permissions for security
        _file_stat = os.stat(_config_file)
        if _file_stat.st_mode & (
            stat.S_IRGRP | stat.S_IROTH | stat.S_IWGRP | stat.S_IWOTH
        ):
            print("⚠️  WARNING: Config file is readable or writable by others")
            print("   Consider: chmod 600 health_check.cfg")

        # Load config file
        _config = configparser.ConfigParser()
        _config.read(_config_file)
        print(f"✓ Loaded configuration from: {_config_file}")
        _has_config = True
    else:
        print("ℹ️  No config file found, using defaults")
        print(f"   Create {_config_file} to customize settings")
        _has_config = False
except Exception as _e:
    print(f"⚠️  WARNING: Error loading config: {_e}")
    print("   Using default configuration")
    _has_config = False


def _cfg(section, key, default, value_type=str):
    """
    Get config value from environment, config file, or default.

    Priority: Environment Variable > Config File > Default

    Args:
        section: INI section name (e.g., 'output', 'email', 'smtp')
        key: Configuration key name (e.g., 'output_dir', 'enabled')
        default: Default value if not found in env or config
        value_type: Expected type (str, int, float, bool)

    Returns:
        Configuration value with proper type
    """
    # Priority 1: Environment variable (uppercase key name)
    env_key = key.upper()
    env_val = os.getenv(env_key)
    if env_val is not None:
        try:
            if value_type is bool:
                return env_val.lower() in ("true", "1", "yes", "on")
            elif value_type is int:
                return int(env_val)
            elif value_type is float:
                return float(env_val)
            else:
                return env_val
        except (ValueError, TypeError):
            pass  # Fall through to config file or default

    # Priority 2: Config file
    if _has_config and _config and _config.has_option(section, key):
        try:
            if value_type is bool:
                return _config.getboolean(section, key)
            elif value_type is int:
                return _config.getint(section, key)
            elif value_type is float:
                return _config.getfloat(section, key)
            else:
                return _config.get(section, key)
        except (ValueError, TypeError, configparser.Error):
            pass  # Fall through to default

    # Priority 3: Default value
    return default


# Configuration values (with config file support)
OUTPUT_DIR = str(_cfg("output", "output_dir", "/root" if os.geteuid() == 0 else "/tmp"))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "health_report.txt")

# Email Configuration
EMAIL_ENABLED = bool(_cfg("email", "enabled", False, bool))
EMAIL_TO = str(_cfg("email", "to", "root@localhost"))
EMAIL_FROM = str(_cfg("email", "from", "root@localhost"))
EMAIL_SUBJECT = str(_cfg("email", "subject", "Linux Health Check Report - {hostname}"))

# SMTP Configuration
SMTP_SERVER = str(_cfg("smtp", "server", "localhost"))
SMTP_PORT = int(_cfg("smtp", "port", 25, int))
SMTP_USE_TLS = bool(_cfg("smtp", "use_tls", False, bool))
SMTP_USERNAME = str(_cfg("smtp", "username", ""))
SMTP_PASSWORD = str(_cfg("smtp", "password", ""))

# GPG Configuration
GPG_ENABLED = bool(_cfg("gpg", "encrypt", False, bool))
GPG_RECIPIENT = str(_cfg("gpg", "recipient", "root@localhost"))
GPG_DELETE_UNENCRYPTED = bool(_cfg("gpg", "delete_unencrypted", False, bool))

# Policy Thresholds
FILESYSTEM_WARNING_THRESHOLD = int(_cfg("thresholds", "filesystem_warning", 80, int))
FILESYSTEM_CRITICAL_THRESHOLD = int(_cfg("thresholds", "filesystem_critical", 90, int))
MEMORY_WARNING_THRESHOLD = int(_cfg("thresholds", "memory_warning", 80, int))
MEMORY_CRITICAL_THRESHOLD = int(_cfg("thresholds", "memory_critical", 90, int))
LOAD_WARNING_MULTIPLIER = (
    float(int(_cfg("thresholds", "load_warning", 200, int))) / 100.0
)
LOAD_CRITICAL_MULTIPLIER = (
    float(int(_cfg("thresholds", "load_critical", 300, int))) / 100.0
)

# Version Checking Configuration
GITHUB_REPO = str(_cfg("version_check", "github_repo", "0xgruber/linux-health-checks"))
VERSION_CHECK_ENABLED = bool(_cfg("version_check", "enabled", True, bool))
VERSION_CHECK_TIMEOUT = int(_cfg("version_check", "timeout", 5, int))

# ============================================================================
# GLOBAL STATE
# ============================================================================

issues = []
OS_INFO = {}
HOSTNAME = socket.gethostname()

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(OUTPUT_FILE, mode="w"),
    ],
)
logger = logging.getLogger(__name__)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def run_command(cmd, check=False, timeout=30):
    """
    Execute a shell command safely without shell=True.
    Returns (returncode, stdout, stderr).
    """
    try:
        if isinstance(cmd, str):
            cmd = cmd.split()
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.warning(f"Command timed out: {' '.join(cmd)}")
        return -1, "", "Command timed out"
    except FileNotFoundError:
        logger.warning(f"Command not found: {cmd[0]}")
        return -1, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        logger.warning(f"Command failed: {e}")
        return -1, "", str(e)


def command_exists(cmd):
    """Check if a command exists in PATH."""
    rc, _, _ = run_command(["which", cmd])
    return rc == 0


def grep_output(text, pattern):
    """Python implementation of grep - returns matching lines."""
    lines = text.split("\n")
    return [line for line in lines if re.search(pattern, line)]


def grep_count(text, pattern):
    """Count matching lines."""
    return len(grep_output(text, pattern))


def head_lines(text, n=10):
    """Return first n lines."""
    return "\n".join(text.split("\n")[:n])


def tail_lines(text, n=10):
    """Return last n lines."""
    lines = text.split("\n")
    return "\n".join(lines[-n:] if len(lines) >= n else lines)


def add_issue(severity, category, description, details=None):
    """Add an issue to the global issues list."""
    issue = {
        "severity": severity,
        "category": category,
        "description": description,
        "details": details,
        "timestamp": datetime.now().isoformat(),
    }
    issues.append(issue)

    severity_emoji = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🔵",
        "INFO": "ℹ️",
    }

    logger.warning(
        f"{severity_emoji.get(severity, '')} [{severity}] {category}: {description}"
    )
    if details:
        logger.info(f"  Details: {details}")


# ============================================================================
# VERSION CHECKING
# ============================================================================


def parse_semantic_version(version_string):
    """
    Parse semantic version string into tuple of integers.

    Args:
        version_string: Version in format "X.Y.Z" or "vX.Y.Z"

    Returns:
        Tuple of (major, minor, patch) or None if invalid

    Examples:
        >>> parse_semantic_version("1.2.3")
        (1, 2, 3)
        >>> parse_semantic_version("v1.2.3")
        (1, 2, 3)
        >>> parse_semantic_version("invalid")
        None
    """
    try:
        # Strip 'v' prefix if present
        version = version_string.lstrip("v")

        # Split on '.' and convert to integers
        parts = version.split(".")

        # Must have exactly 3 parts (MAJOR.MINOR.PATCH)
        if len(parts) != 3:
            return None

        major, minor, patch = [int(p) for p in parts]

        # Validate non-negative
        if major < 0 or minor < 0 or patch < 0:
            return None

        return (major, minor, patch)

    except (ValueError, AttributeError):
        return None


def compare_versions(current, latest):
    """
    Compare two semantic version tuples.

    Args:
        current: Current version tuple (major, minor, patch)
        latest: Latest version tuple (major, minor, patch)

    Returns:
        -1 if current < latest (update available)
         0 if current == latest (up to date)
         1 if current > latest (dev version)

    Examples:
        >>> compare_versions((1, 0, 0), (1, 1, 0))
        -1
        >>> compare_versions((1, 1, 0), (1, 1, 0))
        0
        >>> compare_versions((1, 2, 0), (1, 1, 0))
        1
    """
    # Python tuple comparison handles semantic versioning naturally
    if current < latest:
        return -1
    elif current == latest:
        return 0
    else:
        return 1


def check_github_releases():
    """
    Query GitHub Releases API for latest version.

    Returns:
        Tuple of (version, release_url, changelog_url) on success
        Tuple of (None, None, None) on failure

    Environment Variables:
        DISABLE_VERSION_CHECK: Set to "1" to skip check
        VERSION_CHECK_TIMEOUT: Timeout in seconds (default: 3)
    """
    # Check if version checking is disabled
    if os.getenv("DISABLE_VERSION_CHECK", "0") == "1":
        logger.debug("Version check disabled via DISABLE_VERSION_CHECK")
        return None, None, None

    # Build API URL
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

    # Get timeout from configuration
    timeout = VERSION_CHECK_TIMEOUT

    try:
        # Create request with User-Agent header
        headers = {
            "User-Agent": f"linux-health-check/{__version__}",
            "Accept": "application/vnd.github.v3+json",
        }
        request = urllib.request.Request(api_url, headers=headers)

        # Fetch with timeout
        logger.debug(f"Fetching latest release from: {api_url}")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))

        # Parse response
        tag_name = data.get("tag_name", "")
        version = tag_name.lstrip("v")  # Remove 'v' prefix
        release_url = data.get("html_url", "")
        changelog_url = release_url  # Same as release URL

        logger.debug(f"Latest version: {version}")
        return version, release_url, changelog_url

    except urllib.error.HTTPError as e:
        # HTTP errors (404, 403, etc.)
        logger.debug(f"GitHub API HTTP error: {e.code} {e.reason}")
        return None, None, None

    except urllib.error.URLError as e:
        # Network errors (no connection, DNS failure, etc.)
        logger.debug(f"GitHub API network error: {e.reason}")
        return None, None, None

    except json.JSONDecodeError as e:
        # Invalid JSON response
        logger.debug(f"GitHub API JSON parse error: {e}")
        return None, None, None

    except Exception as e:
        # Catch-all for any other errors
        logger.debug(f"GitHub API unexpected error: {e}")
        return None, None, None


def check_version_update():
    """
    Check for script updates and add notification issue if available.

    This function queries the GitHub Releases API to check if a newer version
    is available. If found, it adds an INFO-level issue with upgrade instructions.
    All errors fail silently and do not interrupt health checks.
    """
    # Query GitHub API for latest release
    latest_version_str, release_url, changelog_url = check_github_releases()

    # If check failed or disabled, return without adding issue
    if not latest_version_str:
        logger.debug("Version check skipped or failed")
        return

    # Parse versions
    current_version = parse_semantic_version(__version__)
    latest_version = parse_semantic_version(latest_version_str)

    # Handle parsing errors
    if not current_version or not latest_version:
        logger.debug("Failed to parse version strings")
        return

    # Compare versions
    comparison = compare_versions(current_version, latest_version)

    if comparison < 0:
        # Update available
        logger.info(
            f"New version available: {latest_version_str} (current: {__version__})"
        )

        # Build download URL
        download_url = f"https://github.com/{GITHUB_REPO}/releases/download/v{latest_version_str}/linux_health_check.py"

        # Format issue details
        details = (
            f"A newer version of this script is available.\n"
            f"\n"
            f"Upgrade instructions:\n"
            f"  wget {download_url}\n"
            f"  chmod +x linux_health_check.py\n"
            f"\n"
            f"Changelog: {changelog_url}"
        )

        # Add INFO-level issue
        add_issue(
            severity="INFO",
            category="Version Update",
            description=f"New version available: {latest_version_str} (current: {__version__})",
            details=details,
        )

    elif comparison == 0:
        # Up to date
        logger.debug(f"Script is up to date (version {__version__})")

    else:
        # Running dev/future version
        logger.debug(
            f"Running dev/future version {__version__} (latest: {latest_version_str})"
        )


# ============================================================================
# OS DETECTION
# ============================================================================


def detect_os():
    """Detect OS distribution, package manager, firewall, and security framework."""
    global OS_INFO

    logger.info("Detecting OS configuration...")

    OS_INFO = {
        "distribution": "Unknown",
        "version": "Unknown",
        "package_manager": None,
        "firewall": None,
        "security_framework": None,
    }

    # Detect distribution
    if os.path.exists("/etc/os-release"):
        rc, stdout, _ = run_command(["cat", "/etc/os-release"])
        if rc == 0:
            for line in stdout.split("\n"):
                if line.startswith("ID="):
                    OS_INFO["distribution"] = line.split("=")[1].strip('"')
                elif line.startswith("VERSION_ID="):
                    OS_INFO["version"] = line.split("=")[1].strip('"')

    # Detect package manager
    if command_exists("rpm"):
        OS_INFO["package_manager"] = "rpm"
    elif command_exists("dpkg"):
        OS_INFO["package_manager"] = "dpkg"
    elif command_exists("pacman"):
        OS_INFO["package_manager"] = "pacman"

    # Detect firewall
    if command_exists("firewall-cmd"):
        OS_INFO["firewall"] = "firewalld"
    elif command_exists("ufw"):
        OS_INFO["firewall"] = "ufw"
    elif command_exists("iptables"):
        OS_INFO["firewall"] = "iptables"

    # Detect security framework
    if os.path.exists("/sys/fs/selinux"):
        OS_INFO["security_framework"] = "selinux"
    elif os.path.exists("/sys/kernel/security/apparmor"):
        OS_INFO["security_framework"] = "apparmor"

    logger.info(f"OS Detection: {OS_INFO}")
    return OS_INFO


# ============================================================================
# SECURITY CHECKS
# ============================================================================


def check_ssh_status():
    """Check SSH service status and authentication configuration."""
    logger.info("Checking SSH status and authentication methods...")

    # Check if SSH is running
    rc, stdout, _ = run_command(["systemctl", "is-active", "sshd"])
    if rc != 0 or "active" not in stdout.lower():
        add_issue(
            "INFO", "Security", "SSH service is not running", "Good: SSH is disabled"
        )
        return

    # SSH is running - now check authentication configuration
    sshd_config = "/etc/ssh/sshd_config"
    if not os.path.exists(sshd_config):
        add_issue(
            "MEDIUM",
            "Security",
            "SSH is running but sshd_config not found",
            "Cannot verify SSH authentication settings",
        )
        return

    try:
        with open(sshd_config, "r") as f:
            config_content = f.read()

        # Check password authentication
        password_auth_enabled = True
        password_lines = grep_output(config_content, r"^\s*PasswordAuthentication")
        for line in reversed(password_lines):
            if not line.strip().startswith("#"):
                if "no" in line.lower():
                    password_auth_enabled = False
                break

        # Check pubkey authentication
        pubkey_auth_enabled = True  # Default is yes
        pubkey_lines = grep_output(config_content, r"^\s*PubkeyAuthentication")
        for line in reversed(pubkey_lines):
            if not line.strip().startswith("#"):
                if "no" in line.lower():
                    pubkey_auth_enabled = False
                break

        # If password auth is enabled (and pubkey might be disabled)
        if password_auth_enabled:
            add_issue(
                "HIGH",
                "Security",
                "SSH is running with password authentication enabled",
                "Password authentication should be disabled. Use key-based authentication with ed25519 or better",
            )
            return

        # Password auth disabled, check key types
        if pubkey_auth_enabled:
            # Check for allowed key types and host keys
            weak_keys_found = []
            strong_keys_found = []

            # Check HostKey directives for key types in use
            hostkey_lines = grep_output(config_content, r"^\s*HostKey\s+")
            for line in hostkey_lines:
                if not line.strip().startswith("#"):
                    if "rsa" in line.lower() or "dsa" in line.lower():
                        weak_keys_found.append(line.strip())
                    elif "ed25519" in line.lower() or "ecdsa" in line.lower():
                        strong_keys_found.append(line.strip())

            # Check PubkeyAcceptedKeyTypes or PubkeyAcceptedAlgorithms (newer OpenSSH)
            accepted_key_lines = grep_output(
                config_content, r"^\s*PubkeyAccepted(KeyTypes|Algorithms)"
            )
            weak_algo_allowed = False
            for line in accepted_key_lines:
                if not line.strip().startswith("#"):
                    if "rsa" in line.lower() or "dsa" in line.lower():
                        weak_algo_allowed = True

            # Check authorized_keys for actual key types (check common locations)
            auth_keys_paths = [
                "/root/.ssh/authorized_keys",
                "/home/*/.ssh/authorized_keys",
            ]

            rsa_keys_in_use = False
            ed25519_keys_in_use = False

            for pattern in auth_keys_paths:
                import glob

                for auth_file in glob.glob(pattern):
                    try:
                        with open(auth_file, "r") as f:
                            auth_content = f.read()
                            if "ssh-rsa" in auth_content or "ssh-dss" in auth_content:
                                rsa_keys_in_use = True
                            if "ssh-ed25519" in auth_content:
                                ed25519_keys_in_use = True
                    except (PermissionError, IOError):
                        pass

            # Determine severity based on findings
            if rsa_keys_in_use or weak_keys_found or weak_algo_allowed:
                add_issue(
                    "MEDIUM",
                    "Security",
                    "SSH is using weak key algorithms (RSA or older)",
                    f"SSH accepts RSA/DSA keys. Upgrade to ed25519 keys. Weak keys: {', '.join(weak_keys_found) if weak_keys_found else 'RSA keys in authorized_keys'}",
                )
            elif ed25519_keys_in_use or strong_keys_found:
                add_issue(
                    "LOW",
                    "Security",
                    "SSH is running with strong key-based authentication",
                    "SSH uses ed25519 or ECDSA keys - acceptable configuration",
                )
            else:
                # Can't determine key types
                add_issue(
                    "LOW",
                    "Security",
                    "SSH is running with pubkey authentication",
                    "Password auth disabled, but cannot verify key types. Ensure ed25519 keys are used.",
                )
        else:
            # Pubkey disabled and password disabled = problematic
            add_issue(
                "HIGH",
                "Security",
                "SSH is running but all authentication methods disabled",
                "Both password and pubkey authentication are disabled",
            )

    except PermissionError:
        add_issue(
            "MEDIUM",
            "Security",
            "SSH is running but cannot read sshd_config",
            "Permission denied - run as root to verify SSH configuration",
        )


def check_wheel_group():
    """Check if wheel/sudo group has members."""
    logger.info("Checking wheel/sudo group membership...")

    # Try wheel first (RHEL/CentOS), then sudo (Debian/Ubuntu)
    for group in ["wheel", "sudo"]:
        rc, stdout, _ = run_command(["getent", "group", group])
        if rc == 0:
            members = stdout.split(":")[-1].strip()
            if not members:
                add_issue(
                    "CRITICAL",
                    "Security",
                    f"Group '{group}' has no members",
                    "No users can use sudo - administrative access may be blocked",
                )
            else:
                add_issue("INFO", "Security", f"Group '{group}' members: {members}")
            return

    add_issue(
        "MEDIUM",
        "Security",
        "Neither wheel nor sudo group found",
        "Cannot verify administrative access",
    )


def check_firewall():
    """Check if firewall is enabled and configured."""
    logger.info("Checking firewall status...")

    if OS_INFO["firewall"] == "firewalld":
        rc, stdout, _ = run_command(["firewall-cmd", "--state"])
        if rc != 0 or "running" not in stdout.lower():
            add_issue(
                "HIGH",
                "Security",
                "firewalld is not running",
                "Firewall should be enabled for network security",
            )
        else:
            add_issue("INFO", "Security", "firewalld is running and active")

    elif OS_INFO["firewall"] == "ufw":
        rc, stdout, _ = run_command(["ufw", "status"])
        if rc != 0 or "inactive" in stdout.lower():
            add_issue(
                "HIGH",
                "Security",
                "ufw is not active",
                "Firewall should be enabled for network security",
            )
        else:
            add_issue("INFO", "Security", "ufw is active")

    elif OS_INFO["firewall"] == "iptables":
        rc, stdout, _ = run_command(["iptables", "-L", "-n"])
        if rc == 0:
            rule_count = len(stdout.split("\n"))
            if rule_count < 10:
                add_issue(
                    "MEDIUM",
                    "Security",
                    "iptables has minimal rules",
                    f"Only {rule_count} lines of iptables output",
                )
            else:
                add_issue(
                    "INFO", "Security", f"iptables is configured ({rule_count} lines)"
                )
    else:
        add_issue(
            "HIGH",
            "Security",
            "No firewall detected",
            "No recognized firewall (firewalld, ufw, iptables) found",
        )


def check_selinux_apparmor():
    """Check SELinux or AppArmor status."""
    logger.info("Checking mandatory access control (SELinux/AppArmor)...")

    if OS_INFO["security_framework"] == "selinux":
        rc, stdout, _ = run_command(["getenforce"])
        if rc == 0:
            status = stdout.strip()
            if status == "Enforcing":
                add_issue(
                    "INFO",
                    "Security",
                    "SELinux is in Enforcing mode",
                    "Good security posture",
                )
            elif status == "Permissive":
                add_issue(
                    "MEDIUM",
                    "Security",
                    "SELinux is in Permissive mode",
                    "SELinux should be in Enforcing mode for production",
                )
            else:
                add_issue(
                    "HIGH",
                    "Security",
                    "SELinux is Disabled",
                    "SELinux should be enabled and enforcing",
                )

    elif OS_INFO["security_framework"] == "apparmor":
        rc, stdout, _ = run_command(["aa-status"])
        if rc == 0:
            if "apparmor module is loaded" in stdout.lower():
                add_issue("INFO", "Security", "AppArmor is active and loaded")
            else:
                add_issue("MEDIUM", "Security", "AppArmor status unclear", stdout[:200])
        else:
            add_issue("MEDIUM", "Security", "Cannot determine AppArmor status")
    else:
        add_issue(
            "MEDIUM",
            "Security",
            "No MAC framework detected",
            "Neither SELinux nor AppArmor found",
        )


def check_failed_logins():
    """Check for failed login attempts."""
    logger.info("Checking for failed login attempts...")

    if not os.path.exists("/var/log/secure") and not os.path.exists(
        "/var/log/auth.log"
    ):
        add_issue(
            "LOW",
            "Security",
            "Cannot check failed logins",
            "Neither /var/log/secure nor /var/log/auth.log exists",
        )
        return

    log_file = (
        "/var/log/secure" if os.path.exists("/var/log/secure") else "/var/log/auth.log"
    )

    try:
        with open(log_file, "r") as f:
            content = f.read()
            failed_count = grep_count(content, r"Failed password")

            if failed_count > 100:
                add_issue(
                    "HIGH",
                    "Security",
                    f"{failed_count} failed login attempts detected",
                    f"Check {log_file} for details",
                )
            elif failed_count > 20:
                add_issue(
                    "MEDIUM",
                    "Security",
                    f"{failed_count} failed login attempts detected",
                    f"Check {log_file} for details",
                )
            elif failed_count > 0:
                add_issue(
                    "LOW", "Security", f"{failed_count} failed login attempts detected"
                )
            else:
                add_issue("INFO", "Security", "No failed login attempts detected")
    except PermissionError:
        add_issue(
            "LOW",
            "Security",
            f"Cannot read {log_file}",
            "Permission denied - run as root",
        )


def check_open_ports():
    """Check for listening network ports."""
    logger.info("Checking open ports...")

    rc, stdout, _ = run_command(["ss", "-tuln"])
    if rc != 0:
        rc, stdout, _ = run_command(["netstat", "-tuln"])

    if rc == 0:
        listening_lines = grep_output(stdout, r"LISTEN")
        port_count = len(listening_lines)

        if port_count > 20:
            add_issue(
                "MEDIUM",
                "Security",
                f"{port_count} listening ports detected",
                "Review open ports for unnecessary services",
            )
        else:
            add_issue("INFO", "Security", f"{port_count} listening ports detected")

        # Check for common insecure ports
        dangerous_ports = {
            "23": "Telnet",
            "21": "FTP",
            "69": "TFTP",
            "513": "rlogin",
            "514": "rsh",
        }

        for port, service in dangerous_ports.items():
            if any(f":{port} " in line for line in listening_lines):
                add_issue(
                    "CRITICAL",
                    "Security",
                    f"Insecure service {service} listening on port {port}",
                    f"Port {port} should not be exposed",
                )
    else:
        add_issue(
            "LOW",
            "Security",
            "Cannot check open ports",
            "Neither ss nor netstat available",
        )


def check_root_login():
    """Check if root can login via SSH."""
    logger.info("Checking SSH root login configuration...")

    sshd_config = "/etc/ssh/sshd_config"
    if not os.path.exists(sshd_config):
        add_issue(
            "LOW", "Security", "Cannot find sshd_config", "SSH may not be installed"
        )
        return

    try:
        with open(sshd_config, "r") as f:
            content = f.read()

        permit_root_lines = grep_output(content, r"^\s*PermitRootLogin")

        if not permit_root_lines:
            add_issue(
                "MEDIUM",
                "Security",
                "PermitRootLogin not explicitly set in sshd_config",
                "Default may allow root login",
            )
        else:
            # Get the last uncommented line
            for line in reversed(permit_root_lines):
                if not line.strip().startswith("#"):
                    if "no" in line.lower():
                        add_issue(
                            "INFO",
                            "Security",
                            "Root SSH login is disabled",
                            "Good security practice",
                        )
                    else:
                        add_issue(
                            "HIGH",
                            "Security",
                            "Root SSH login is enabled",
                            "PermitRootLogin should be set to 'no'",
                        )
                    break
    except PermissionError:
        add_issue("LOW", "Security", f"Cannot read {sshd_config}", "Permission denied")


def check_password_policy():
    """Check password aging and policy settings."""
    logger.info("Checking password policy...")

    login_defs = "/etc/login.defs"
    if os.path.exists(login_defs):
        try:
            with open(login_defs, "r") as f:
                content = f.read()

            pass_max_days = grep_output(content, r"^\s*PASS_MAX_DAYS")
            pass_min_days = grep_output(content, r"^\s*PASS_MIN_DAYS")
            pass_min_len = grep_output(content, r"^\s*PASS_MIN_LEN")

            if not pass_max_days or any("99999" in line for line in pass_max_days):
                add_issue(
                    "MEDIUM",
                    "Security",
                    "Password expiration not enforced",
                    "PASS_MAX_DAYS should be set to reasonable value (e.g., 90)",
                )
            else:
                add_issue(
                    "INFO",
                    "Security",
                    f"Password policy configured: {pass_max_days[0].strip()}",
                )

        except PermissionError:
            add_issue(
                "LOW", "Security", f"Cannot read {login_defs}", "Permission denied"
            )
    else:
        add_issue(
            "LOW", "Security", "Cannot check password policy", f"{login_defs} not found"
        )


# ============================================================================
# SYSTEM HEALTH CHECKS
# ============================================================================


def check_uptime():
    """Check system uptime."""
    logger.info("Checking system uptime...")

    rc, stdout, _ = run_command(["uptime", "-p"])
    if rc == 0:
        add_issue("INFO", "System Health", f"System uptime: {stdout.strip()}")
    else:
        rc, stdout, _ = run_command(["uptime"])
        if rc == 0:
            add_issue("INFO", "System Health", f"Uptime: {stdout.strip()}")


def check_load_average():
    """Check system load average."""
    logger.info("Checking load average...")

    try:
        with open("/proc/loadavg", "r") as f:
            loadavg = f.read().strip().split()
            load_1min = float(loadavg[0])
            load_5min = float(loadavg[1])
            load_15min = float(loadavg[2])

        # Get CPU count
        cpu_count = os.cpu_count() or 1

        load_per_cpu = load_1min / cpu_count

        if load_per_cpu > LOAD_CRITICAL_MULTIPLIER:
            add_issue(
                "CRITICAL",
                "System Health",
                f"Load average critically high: {load_1min} ({load_per_cpu:.2f} per CPU)",
                f"CPU count: {cpu_count}, 1/5/15 min: {load_1min}/{load_5min}/{load_15min}",
            )
        elif load_per_cpu > LOAD_WARNING_MULTIPLIER:
            add_issue(
                "HIGH",
                "System Health",
                f"Load average high: {load_1min} ({load_per_cpu:.2f} per CPU)",
                f"CPU count: {cpu_count}, 1/5/15 min: {load_1min}/{load_5min}/{load_15min}",
            )
        else:
            add_issue(
                "INFO",
                "System Health",
                f"Load average normal: {load_1min} ({load_per_cpu:.2f} per CPU)",
                f"CPU count: {cpu_count}, 1/5/15 min: {load_1min}/{load_5min}/{load_15min}",
            )
    except Exception as e:
        add_issue("LOW", "System Health", "Cannot check load average", str(e))


def check_memory_usage():
    """Check memory usage."""
    logger.info("Checking memory usage...")

    rc, stdout, _ = run_command(["free", "-m"])
    if rc == 0:
        lines = stdout.split("\n")
        if len(lines) >= 2:
            mem_line = lines[1].split()
            if len(mem_line) >= 3:
                total = int(mem_line[1])
                used = int(mem_line[2])
                percent = (used / total) * 100

                if percent > MEMORY_CRITICAL_THRESHOLD:
                    add_issue(
                        "CRITICAL",
                        "System Health",
                        f"Memory usage critically high: {percent:.1f}% ({used}MB/{total}MB)",
                        "Consider adding more RAM or reducing memory usage",
                    )
                elif percent > MEMORY_WARNING_THRESHOLD:
                    add_issue(
                        "HIGH",
                        "System Health",
                        f"Memory usage high: {percent:.1f}% ({used}MB/{total}MB)",
                    )
                else:
                    add_issue(
                        "INFO",
                        "System Health",
                        f"Memory usage normal: {percent:.1f}% ({used}MB/{total}MB)",
                    )
                return

    add_issue(
        "LOW", "System Health", "Cannot check memory usage", "free command failed"
    )


def check_cpu_info():
    """Report CPU information."""
    logger.info("Checking CPU information...")

    if os.path.exists("/proc/cpuinfo"):
        try:
            with open("/proc/cpuinfo", "r") as f:
                content = f.read()

            cpu_count = grep_count(content, r"^processor")
            model_lines = grep_output(content, r"model name")

            if model_lines:
                model = model_lines[0].split(":")[1].strip()
                add_issue("INFO", "System Health", f"CPU: {cpu_count} cores, {model}")
            else:
                add_issue("INFO", "System Health", f"CPU: {cpu_count} cores")
        except Exception as e:
            add_issue("LOW", "System Health", "Cannot read CPU info", str(e))


def check_zombie_processes():
    """Check for zombie processes."""
    logger.info("Checking for zombie processes...")

    rc, stdout, _ = run_command(["ps", "aux"])
    if rc == 0:
        zombie_count = grep_count(stdout, r"<defunct>")

        if zombie_count > 10:
            add_issue(
                "HIGH",
                "System Health",
                f"{zombie_count} zombie processes detected",
                "Large number of zombies may indicate application issues",
            )
        elif zombie_count > 0:
            add_issue(
                "MEDIUM", "System Health", f"{zombie_count} zombie processes detected"
            )
        else:
            add_issue("INFO", "System Health", "No zombie processes detected")
    else:
        add_issue("LOW", "System Health", "Cannot check for zombie processes")


def check_systemd_failed():
    """Check for failed systemd services."""
    logger.info("Checking for failed systemd services...")

    rc, stdout, _ = run_command(["systemctl", "list-units", "--failed", "--no-pager"])
    if rc == 0:
        failed_lines = grep_output(stdout, r"●.*failed")
        failed_count = len(failed_lines)

        if failed_count > 5:
            add_issue(
                "HIGH",
                "System Health",
                f"{failed_count} systemd services failed",
                "Multiple service failures detected",
            )
        elif failed_count > 0:
            add_issue(
                "MEDIUM",
                "System Health",
                f"{failed_count} systemd service(s) failed",
                "\n".join(failed_lines[:5]),
            )
        else:
            add_issue("INFO", "System Health", "No failed systemd services")
    else:
        add_issue(
            "LOW",
            "System Health",
            "Cannot check systemd services",
            "systemctl may not be available",
        )


def check_dmesg_errors():
    """Check kernel ring buffer for errors."""
    logger.info("Checking dmesg for errors...")

    rc, stdout, _ = run_command(["dmesg", "-l", "err,crit,alert,emerg"])
    if rc == 0:
        if stdout.strip():
            error_lines = len(stdout.split("\n"))
            if error_lines > 50:
                add_issue(
                    "HIGH",
                    "System Health",
                    f"{error_lines} kernel errors in dmesg",
                    head_lines(stdout, 10),
                )
            elif error_lines > 10:
                add_issue(
                    "MEDIUM",
                    "System Health",
                    f"{error_lines} kernel errors in dmesg",
                    head_lines(stdout, 5),
                )
            else:
                add_issue(
                    "LOW", "System Health", f"{error_lines} kernel error(s) in dmesg"
                )
        else:
            add_issue("INFO", "System Health", "No critical kernel errors in dmesg")
    else:
        add_issue(
            "LOW",
            "System Health",
            "Cannot check dmesg",
            "Permission denied or not available",
        )


# ============================================================================
# STORAGE CHECKS
# ============================================================================


def check_filesystem_usage():
    """Check filesystem usage."""
    logger.info("Checking filesystem usage...")

    rc, stdout, _ = run_command(["df", "-h"])
    if rc == 0:
        lines = stdout.split("\n")[1:]  # Skip header

        for line in lines:
            if not line.strip():
                continue

            parts = line.split()
            if len(parts) >= 6:
                filesystem = parts[0]
                use_percent_str = parts[4].rstrip("%")
                mountpoint = parts[5]

                # Skip pseudo filesystems
                if filesystem in ["tmpfs", "devtmpfs", "none", "udev"]:
                    continue

                try:
                    use_percent = int(use_percent_str)

                    if use_percent >= FILESYSTEM_CRITICAL_THRESHOLD:
                        add_issue(
                            "CRITICAL",
                            "Storage",
                            f"Filesystem {mountpoint} critically full: {use_percent}%",
                            f"{filesystem} mounted at {mountpoint}",
                        )
                    elif use_percent >= FILESYSTEM_WARNING_THRESHOLD:
                        add_issue(
                            "HIGH",
                            "Storage",
                            f"Filesystem {mountpoint} filling up: {use_percent}%",
                            f"{filesystem} mounted at {mountpoint}",
                        )
                    elif use_percent >= 75:
                        add_issue(
                            "MEDIUM",
                            "Storage",
                            f"Filesystem {mountpoint} at {use_percent}%",
                            f"{filesystem} mounted at {mountpoint}",
                        )
                except ValueError:
                    continue
    else:
        add_issue(
            "LOW", "Storage", "Cannot check filesystem usage", "df command failed"
        )


def check_inode_usage():
    """Check inode usage."""
    logger.info("Checking inode usage...")

    rc, stdout, _ = run_command(["df", "-i"])
    if rc == 0:
        lines = stdout.split("\n")[1:]  # Skip header

        for line in lines:
            if not line.strip():
                continue

            parts = line.split()
            if len(parts) >= 6:
                filesystem = parts[0]
                use_percent_str = parts[4].rstrip("%")
                mountpoint = parts[5]

                # Skip pseudo filesystems
                if filesystem in ["tmpfs", "devtmpfs", "none", "udev"]:
                    continue

                try:
                    use_percent = int(use_percent_str)

                    if use_percent >= 90:
                        add_issue(
                            "CRITICAL",
                            "Storage",
                            f"Inodes critically low on {mountpoint}: {use_percent}%",
                            f"{filesystem} mounted at {mountpoint}",
                        )
                    elif use_percent >= 80:
                        add_issue(
                            "HIGH",
                            "Storage",
                            f"Inodes running low on {mountpoint}: {use_percent}%",
                            f"{filesystem} mounted at {mountpoint}",
                        )
                except (ValueError, IndexError):
                    continue
    else:
        add_issue("LOW", "Storage", "Cannot check inode usage", "df -i command failed")


def check_disk_smart():
    """Check SMART status of disks."""
    logger.info("Checking disk SMART status...")

    if not command_exists("smartctl"):
        add_issue(
            "LOW",
            "Storage",
            "smartctl not available",
            "Install smartmontools to check disk health",
        )
        return

    # Find block devices
    rc, stdout, _ = run_command(["lsblk", "-d", "-n", "-o", "NAME"])
    if rc != 0:
        add_issue("LOW", "Storage", "Cannot list block devices", "lsblk command failed")
        return

    devices = [
        f"/dev/{line.strip()}"
        for line in stdout.split("\n")
        if line.strip() and not line.startswith("loop")
    ]

    for device in devices[:5]:  # Check first 5 devices
        rc, stdout, _ = run_command(["smartctl", "-H", device])
        if rc == 0:
            if "PASSED" in stdout:
                add_issue("INFO", "Storage", f"SMART status OK for {device}")
            elif "FAILED" in stdout:
                add_issue(
                    "CRITICAL",
                    "Storage",
                    f"SMART status FAILED for {device}",
                    "Disk may be failing - backup data immediately",
                )
        # Don't report if smartctl fails (device may not support SMART)


# ============================================================================
# PACKAGE & UPDATE CHECKS
# ============================================================================


def check_package_updates():
    """Check for available package updates."""
    logger.info("Checking for package updates...")

    if OS_INFO["package_manager"] == "rpm":
        # RHEL/CentOS/Rocky
        rc, stdout, _ = run_command(["yum", "check-update"], timeout=60)
        if rc == 100:  # yum returns 100 when updates are available
            update_count = len(
                [
                    l
                    for l in stdout.split("\n")
                    if l.strip()
                    and not l.startswith("Loaded")
                    and not l.startswith("Security")
                ]
            )
            add_issue(
                "MEDIUM",
                "Updates",
                f"Package updates available (approx. {update_count})",
                "Run 'yum update' to apply updates",
            )
        elif rc == 0:
            add_issue("INFO", "Updates", "All packages up to date")

    elif OS_INFO["package_manager"] == "dpkg":
        # Debian/Ubuntu
        # Update package list first
        run_command(["apt-get", "update"], timeout=120)

        rc, stdout, _ = run_command(["apt", "list", "--upgradable"], timeout=60)
        if rc == 0:
            update_lines = grep_output(stdout, r"upgradable")
            if len(update_lines) > 10:
                add_issue(
                    "MEDIUM",
                    "Updates",
                    f"{len(update_lines)} package updates available",
                    "Run 'apt upgrade' to apply updates",
                )
            elif len(update_lines) > 0:
                add_issue(
                    "LOW", "Updates", f"{len(update_lines)} package update(s) available"
                )
            else:
                add_issue("INFO", "Updates", "All packages up to date")

    else:
        add_issue(
            "LOW",
            "Updates",
            "Cannot check for updates",
            f"Package manager '{OS_INFO['package_manager']}' not supported for update checks",
        )


def check_kernel_version():
    """Check kernel version and if reboot is required."""
    logger.info("Checking kernel version...")

    rc, running_kernel, _ = run_command(["uname", "-r"])
    if rc == 0:
        running_kernel = running_kernel.strip()
        add_issue("INFO", "Updates", f"Running kernel: {running_kernel}")

        # Check if reboot required (various methods)
        if os.path.exists("/var/run/reboot-required"):
            add_issue(
                "HIGH",
                "Updates",
                "System reboot required",
                "New kernel or critical updates installed",
            )

        # Check if running kernel matches installed kernel
        if OS_INFO["package_manager"] == "rpm":
            rc, stdout, _ = run_command(["rpm", "-q", "kernel"])
            if rc == 0:
                installed_kernels = stdout.strip().split("\n")
                latest_kernel = installed_kernels[-1].replace("kernel-", "")
                if running_kernel not in latest_kernel:
                    add_issue(
                        "MEDIUM",
                        "Updates",
                        "Running kernel is not the latest installed",
                        f"Running: {running_kernel}, Latest: {latest_kernel}",
                    )


def check_security_updates():
    """Check for security updates."""
    logger.info("Checking for security updates...")

    if OS_INFO["package_manager"] == "rpm":
        rc, stdout, _ = run_command(
            ["yum", "updateinfo", "list", "security"], timeout=60
        )
        if rc == 0:
            security_lines = [l for l in stdout.split("\n") if "security" in l.lower()]
            if len(security_lines) > 10:
                add_issue(
                    "HIGH",
                    "Updates",
                    f"{len(security_lines)} security updates available",
                    "Apply security updates immediately",
                )
            elif len(security_lines) > 0:
                add_issue(
                    "MEDIUM",
                    "Updates",
                    f"{len(security_lines)} security update(s) available",
                )
            else:
                add_issue("INFO", "Updates", "No security updates pending")


# ============================================================================
# NETWORKING CHECKS
# ============================================================================


def check_network_interfaces():
    """Check network interface status."""
    logger.info("Checking network interfaces...")

    rc, stdout, _ = run_command(["ip", "link", "show"])
    if rc == 0:
        interfaces = grep_output(stdout, r"^\d+:")
        up_count = grep_count(stdout, r"state UP")
        down_count = grep_count(stdout, r"state DOWN")

        add_issue(
            "INFO",
            "Networking",
            f"Network interfaces: {len(interfaces)} total, {up_count} up, {down_count} down",
        )

        # Check for interfaces in down state (excluding loopback)
        for line in interfaces:
            if "state DOWN" in line and "lo:" not in line:
                iface_name = line.split(":")[1].strip()
                add_issue("LOW", "Networking", f"Interface {iface_name} is DOWN")
    else:
        add_issue(
            "LOW", "Networking", "Cannot check network interfaces", "ip command failed"
        )


def check_dns_resolution():
    """Check DNS resolution."""
    logger.info("Checking DNS resolution...")

    test_hosts = ["google.com", "1.1.1.1"]

    for host in test_hosts:
        rc, stdout, _ = run_command(["nslookup", host])
        if rc == 0 and "answer" in stdout.lower():
            add_issue("INFO", "Networking", f"DNS resolution working (tested {host})")
            return

    add_issue(
        "HIGH",
        "Networking",
        "DNS resolution may be failing",
        "Could not resolve test hosts",
    )


def check_default_gateway():
    """Check default gateway configuration."""
    logger.info("Checking default gateway...")

    rc, stdout, _ = run_command(["ip", "route", "show", "default"])
    if rc == 0 and stdout.strip():
        gateway = stdout.split()[2] if len(stdout.split()) >= 3 else "unknown"
        add_issue("INFO", "Networking", f"Default gateway: {gateway}")

        # Try to ping gateway
        rc, _, _ = run_command(["ping", "-c", "1", "-W", "2", gateway])
        if rc == 0:
            add_issue("INFO", "Networking", f"Gateway {gateway} is reachable")
        else:
            add_issue(
                "MEDIUM",
                "Networking",
                f"Gateway {gateway} is not reachable",
                "Network connectivity may be impaired",
            )
    else:
        add_issue(
            "HIGH",
            "Networking",
            "No default gateway configured",
            "System cannot reach external networks",
        )


def check_listening_services():
    """Check listening network services."""
    logger.info("Checking listening services...")

    rc, stdout, _ = run_command(["ss", "-tulpn"])
    if rc != 0:
        rc, stdout, _ = run_command(["netstat", "-tulpn"])

    if rc == 0:
        listening = grep_output(stdout, r"LISTEN")

        services = {}
        for line in listening:
            parts = line.split()
            if len(parts) >= 5:
                port_info = parts[4]
                if ":" in port_info:
                    port = port_info.split(":")[-1]
                    services[port] = services.get(port, 0) + 1

        add_issue("INFO", "Networking", f"Listening on {len(services)} unique port(s)")


def check_network_errors():
    """Check network interface error counters."""
    logger.info("Checking network interface errors...")

    rc, stdout, _ = run_command(["ip", "-s", "link"])
    if rc == 0:
        error_lines = grep_output(stdout, r"errors:")

        high_error_count = 0
        for line in error_lines:
            parts = line.split()
            if len(parts) >= 2:
                try:
                    errors = int(parts[1])
                    if errors > 1000:
                        high_error_count += 1
                except (ValueError, IndexError):
                    continue

        if high_error_count > 0:
            add_issue(
                "MEDIUM",
                "Networking",
                f"{high_error_count} interface(s) with high error counts",
                "Check 'ip -s link' for details",
            )
        else:
            add_issue("INFO", "Networking", "Network error counters are low")


def check_connectivity():
    """Check external connectivity."""
    logger.info("Checking external connectivity...")

    test_hosts = ["8.8.8.8", "1.1.1.1"]

    for host in test_hosts:
        rc, _, _ = run_command(["ping", "-c", "2", "-W", "3", host])
        if rc == 0:
            add_issue(
                "INFO", "Networking", f"External connectivity OK (reached {host})"
            )
            return

    add_issue(
        "HIGH",
        "Networking",
        "Cannot reach external hosts",
        "Internet connectivity may be down",
    )


# ============================================================================
# iSCSI CHECKS
# ============================================================================


def check_iscsi_service():
    """Check if iSCSI initiator service is running."""
    logger.info("Checking iSCSI service...")

    services = ["iscsid", "iscsi"]

    for service in services:
        rc, stdout, _ = run_command(["systemctl", "is-active", service])
        if rc == 0 and "active" in stdout:
            add_issue("INFO", "iSCSI", f"iSCSI service '{service}' is active")
            return

    add_issue(
        "LOW",
        "iSCSI",
        "iSCSI service not running",
        "If iSCSI storage is used, ensure iscsid service is active",
    )


def check_iscsi_sessions():
    """Check active iSCSI sessions."""
    logger.info("Checking iSCSI sessions...")

    if not command_exists("iscsiadm"):
        add_issue(
            "LOW",
            "iSCSI",
            "iscsiadm not available",
            "iSCSI tools not installed or not in PATH",
        )
        return

    rc, stdout, _ = run_command(["iscsiadm", "-m", "session"])
    if rc == 0 and stdout.strip():
        session_count = len(stdout.strip().split("\n"))
        add_issue("INFO", "iSCSI", f"{session_count} active iSCSI session(s)")
    elif rc == 0:
        add_issue("INFO", "iSCSI", "No active iSCSI sessions")
    else:
        add_issue(
            "LOW",
            "iSCSI",
            "Cannot check iSCSI sessions",
            "No sessions or permission denied",
        )


def check_iscsi_multipath():
    """Check multipath status for iSCSI."""
    logger.info("Checking multipath status...")

    if not command_exists("multipath"):
        add_issue(
            "LOW",
            "iSCSI",
            "multipath command not available",
            "Install multipath-tools if using multipath iSCSI",
        )
        return

    rc, stdout, _ = run_command(["multipath", "-ll"])
    if rc == 0 and stdout.strip():
        # Check for failed paths
        if "failed" in stdout.lower() or "faulty" in stdout.lower():
            add_issue(
                "HIGH",
                "iSCSI",
                "Multipath has failed/faulty paths",
                "Check 'multipath -ll' for details",
            )
        else:
            path_count = grep_count(stdout, r"status=active")
            add_issue(
                "INFO", "iSCSI", f"Multipath configured with {path_count} active paths"
            )
    else:
        add_issue("LOW", "iSCSI", "No multipath devices or not configured")


def check_iscsi_targets():
    """Check configured iSCSI targets."""
    logger.info("Checking iSCSI target configuration...")

    if not command_exists("iscsiadm"):
        return

    rc, stdout, _ = run_command(["iscsiadm", "-m", "node"])
    if rc == 0 and stdout.strip():
        target_count = len(stdout.strip().split("\n"))
        add_issue("INFO", "iSCSI", f"{target_count} iSCSI target(s) configured")
    elif rc == 0:
        add_issue("INFO", "iSCSI", "No iSCSI targets configured")


def check_iscsi_performance():
    """Check iSCSI disk performance metrics."""
    logger.info("Checking iSCSI disk I/O...")

    rc, stdout, _ = run_command(["iostat", "-x", "1", "2"])
    if rc == 0:
        # Look for high await times or utilization
        lines = stdout.split("\n")
        device_lines = [l for l in lines if l.startswith("sd") or l.startswith("dm-")]

        high_util_devices = []
        for line in device_lines:
            parts = line.split()
            if len(parts) >= 12:
                try:
                    util = float(parts[-1])
                    if util > 90:
                        device = parts[0]
                        high_util_devices.append(f"{device} ({util}%)")
                except (ValueError, IndexError):
                    continue

        if high_util_devices:
            add_issue(
                "MEDIUM",
                "iSCSI",
                "High disk utilization detected",
                f"Devices: {', '.join(high_util_devices)}",
            )
        else:
            add_issue("INFO", "iSCSI", "Disk I/O utilization normal")
    else:
        add_issue(
            "LOW",
            "iSCSI",
            "Cannot check I/O statistics",
            "iostat not available - install sysstat package",
        )


def check_iscsi_timeouts():
    """Check iSCSI timeout settings."""
    logger.info("Checking iSCSI timeout configuration...")

    timeout_file = "/sys/module/iscsi_tcp/parameters/timeout"
    if os.path.exists(timeout_file):
        try:
            with open(timeout_file, "r") as f:
                timeout = f.read().strip()
                add_issue("INFO", "iSCSI", f"iSCSI TCP timeout: {timeout} seconds")
        except Exception:
            pass


def check_iscsi_errors():
    """Check system logs for iSCSI errors."""
    logger.info("Checking for iSCSI errors in logs...")

    rc, stdout, _ = run_command(
        ["journalctl", "-u", "iscsid", "-p", "err", "-n", "50", "--no-pager"]
    )
    if rc == 0:
        if stdout.strip():
            error_count = len(stdout.strip().split("\n"))
            add_issue(
                "MEDIUM",
                "iSCSI",
                f"{error_count} iSCSI error(s) in recent logs",
                head_lines(stdout, 5),
            )
        else:
            add_issue("INFO", "iSCSI", "No recent iSCSI errors in logs")


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================


def export_markdown():
    """Export issues in Markdown format."""
    logger.info("Generating Markdown report...")

    report = f"# Linux Health Check Report\n\n"
    report += f"**Hostname:** {HOSTNAME}\n\n"
    report += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report += f"**OS:** {OS_INFO.get('distribution', 'Unknown')} {OS_INFO.get('version', '')}\n\n"
    report += "---\n\n"

    # Summary by severity
    severity_counts = {}
    for issue in issues:
        sev = issue["severity"]
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    report += "## Summary\n\n"
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        count = severity_counts.get(sev, 0)
        report += f"- **{sev}:** {count}\n"
    report += f"\n**Total Issues:** {len(issues)}\n\n"
    report += "---\n\n"

    # Issues by category
    categories = {}
    for issue in issues:
        cat = issue["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(issue)

    for category in sorted(categories.keys()):
        report += f"## {category}\n\n"

        for issue in categories[category]:
            severity_emoji = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "🔵",
                "INFO": "ℹ️",
            }

            emoji = severity_emoji.get(issue["severity"], "")
            report += f"### {emoji} [{issue['severity']}] {issue['description']}\n\n"

            if issue["details"]:
                report += f"```\n{issue['details']}\n```\n\n"

    return report


def export_json():
    """Export issues in JSON format."""
    logger.info("Generating JSON report...")

    report = {
        "hostname": HOSTNAME,
        "timestamp": datetime.now().isoformat(),
        "os_info": OS_INFO,
        "summary": {},
        "issues": issues,
    }

    # Calculate summary
    for issue in issues:
        sev = issue["severity"]
        report["summary"][sev] = report["summary"].get(sev, 0) + 1

    return json.dumps(report, indent=2)


def export_xml():
    """Export issues in XML format."""
    logger.info("Generating XML report...")

    root = ET.Element("health_check_report")

    # Metadata
    meta = ET.SubElement(root, "metadata")
    ET.SubElement(meta, "hostname").text = HOSTNAME
    ET.SubElement(meta, "timestamp").text = datetime.now().isoformat()
    ET.SubElement(meta, "distribution").text = OS_INFO.get("distribution", "Unknown")
    ET.SubElement(meta, "version").text = OS_INFO.get("version", "Unknown")

    # Summary
    summary = ET.SubElement(root, "summary")
    severity_counts = {}
    for issue in issues:
        sev = issue["severity"]
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    for sev, count in severity_counts.items():
        sev_elem = ET.SubElement(summary, "severity", level=sev)
        sev_elem.text = str(count)

    # Issues
    issues_elem = ET.SubElement(root, "issues")
    for issue in issues:
        issue_elem = ET.SubElement(issues_elem, "issue")
        ET.SubElement(issue_elem, "severity").text = issue["severity"]
        ET.SubElement(issue_elem, "category").text = issue["category"]
        ET.SubElement(issue_elem, "description").text = issue["description"]
        ET.SubElement(issue_elem, "timestamp").text = issue["timestamp"]
        if issue["details"]:
            ET.SubElement(issue_elem, "details").text = str(issue["details"])

    return ET.tostring(root, encoding="unicode", method="xml")


def export_text():
    """Export issues in plain text format."""
    logger.info("Generating plain text report...")

    report = "=" * 80 + "\n"
    report += "Linux Health Check Report\n"
    report += "=" * 80 + "\n\n"
    report += f"Hostname: {HOSTNAME}\n"
    report += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += (
        f"OS: {OS_INFO.get('distribution', 'Unknown')} {OS_INFO.get('version', '')}\n"
    )
    report += "\n" + "-" * 80 + "\n"
    report += "SUMMARY\n"
    report += "-" * 80 + "\n\n"

    severity_counts = {}
    for issue in issues:
        sev = issue["severity"]
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        count = severity_counts.get(sev, 0)
        report += f"{sev:12} {count}\n"
    report += f"\nTotal Issues: {len(issues)}\n\n"

    report += "=" * 80 + "\n"
    report += "ISSUES\n"
    report += "=" * 80 + "\n\n"

    categories = {}
    for issue in issues:
        cat = issue["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(issue)

    for category in sorted(categories.keys()):
        report += f"\n{category}\n"
        report += "-" * len(category) + "\n\n"

        for issue in categories[category]:
            report += f"[{issue['severity']}] {issue['description']}\n"
            if issue["details"]:
                report += f"  Details: {issue['details']}\n"
            report += "\n"

    return report


# ============================================================================
# ENCRYPTION & EMAIL
# ============================================================================


def encrypt_file_gpg(file_path):
    """Encrypt file with GPG."""
    if not GPG_ENABLED or not GPG_RECIPIENT:
        return file_path

    if not command_exists("gpg"):
        logger.warning("GPG encryption requested but gpg command not found")
        return file_path

    logger.info(f"Encrypting {file_path} with GPG...")

    encrypted_path = file_path + ".gpg"
    rc, stdout, stderr = run_command(
        [
            "gpg",
            "--encrypt",
            "--recipient",
            GPG_RECIPIENT,
            "--trust-model",
            "always",
            "--output",
            encrypted_path,
            file_path,
        ]
    )

    if rc == 0:
        logger.info(f"File encrypted successfully: {encrypted_path}")
        # Remove unencrypted file
        os.remove(file_path)
        return encrypted_path
    else:
        logger.error(f"GPG encryption failed: {stderr}")
        return file_path


def send_email_report(report_file):
    """Send report via email using SMTP."""
    if not EMAIL_ENABLED or not all([EMAIL_TO, EMAIL_FROM, SMTP_SERVER]):
        return

    logger.info(f"Sending email report to {EMAIL_TO}...")

    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM if EMAIL_FROM else "health-check@localhost"
        msg["To"] = EMAIL_TO if EMAIL_TO else "admin@localhost"
        msg["Subject"] = (
            EMAIL_SUBJECT.format(hostname=HOSTNAME)
            if EMAIL_SUBJECT
            else f"Health Check Report - {HOSTNAME}"
        )

        # Email body
        body = f"Health check report for {HOSTNAME} is attached.\n\n"
        body += f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        # Add summary
        severity_counts = {}
        for issue in issues:
            sev = issue["severity"]
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        body += "\nSummary:\n"
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            count = severity_counts.get(sev, 0)
            body += f"  {sev}: {count}\n"

        msg.attach(MIMEText(body, "plain"))

        # Attach report file
        with open(report_file, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(report_file)}",
            )
            msg.attach(part)

        # Send email
        smtp_host = SMTP_SERVER if SMTP_SERVER else "localhost"
        if SMTP_USE_TLS:
            server = smtplib.SMTP(smtp_host, SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP(smtp_host, SMTP_PORT)

        if SMTP_USERNAME and SMTP_PASSWORD:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)

        server.send_message(msg)
        server.quit()

        logger.info("Email sent successfully")

    except Exception as e:
        logger.error(f"Failed to send email: {e}")


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("Linux Health Check Starting")
    logger.info("=" * 80)
    logger.info(f"Hostname: {HOSTNAME}")
    logger.info(f"Run as: {'root' if os.geteuid() == 0 else 'non-root user'}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info("")

    # Detect OS
    detect_os()
    logger.info("")

    # Check for script updates
    logger.info("Checking for script updates...")
    check_version_update()
    logger.info("")

    # Security Checks
    logger.info("Running Security Checks...")
    check_ssh_status()
    check_wheel_group()
    check_firewall()
    check_selinux_apparmor()
    check_failed_logins()
    check_open_ports()
    check_root_login()
    check_password_policy()
    logger.info("")

    # System Health Checks
    logger.info("Running System Health Checks...")
    check_uptime()
    check_load_average()
    check_memory_usage()
    check_cpu_info()
    check_zombie_processes()
    check_systemd_failed()
    check_dmesg_errors()
    logger.info("")

    # Storage Checks
    logger.info("Running Storage Checks...")
    check_filesystem_usage()
    check_inode_usage()
    check_disk_smart()
    logger.info("")

    # Package & Update Checks
    logger.info("Running Package & Update Checks...")
    check_package_updates()
    check_kernel_version()
    check_security_updates()
    logger.info("")

    # Networking Checks
    logger.info("Running Networking Checks...")
    check_network_interfaces()
    check_dns_resolution()
    check_default_gateway()
    check_listening_services()
    check_network_errors()
    check_connectivity()
    logger.info("")

    # iSCSI Checks
    logger.info("Running iSCSI Checks...")
    check_iscsi_service()
    check_iscsi_sessions()
    check_iscsi_multipath()
    check_iscsi_targets()
    check_iscsi_performance()
    check_iscsi_timeouts()
    check_iscsi_errors()
    logger.info("")

    # Generate reports
    logger.info("=" * 80)
    logger.info("Generating Reports")
    logger.info("=" * 80)

    # Export in requested format (default: markdown)
    export_format = os.getenv("EXPORT_FORMAT", "markdown").lower()

    if export_format == "json":
        report_content = export_json()
        report_file = os.path.join(OUTPUT_DIR, f"health_report_{HOSTNAME}.json")
    elif export_format == "xml":
        report_content = export_xml()
        report_file = os.path.join(OUTPUT_DIR, f"health_report_{HOSTNAME}.xml")
    elif export_format == "text":
        report_content = export_text()
        report_file = os.path.join(OUTPUT_DIR, f"health_report_{HOSTNAME}.txt")
    else:  # markdown (default)
        report_content = export_markdown()
        report_file = os.path.join(OUTPUT_DIR, f"health_report_{HOSTNAME}.md")

    # Write report
    with open(report_file, "w") as f:
        f.write(report_content)

    logger.info(f"Report saved to: {report_file}")

    # Encrypt if configured
    if GPG_ENABLED:
        report_file = encrypt_file_gpg(report_file)

    # Send email if configured
    if EMAIL_ENABLED:
        send_email_report(report_file)

    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("Health Check Complete")
    logger.info("=" * 80)

    severity_counts = {}
    for issue in issues:
        sev = issue["severity"]
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    logger.info("\nSummary:")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        count = severity_counts.get(sev, 0)
        logger.info(f"  {sev:12} {count}")
    logger.info(f"\n  Total Issues: {len(issues)}")
    logger.info(f"\nReport: {report_file}")
    logger.info("")

    # Exit code based on severity
    if severity_counts.get("CRITICAL", 0) > 0:
        sys.exit(2)
    elif severity_counts.get("HIGH", 0) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nHealth check interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
