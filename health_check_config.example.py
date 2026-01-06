"""
Linux Health Check Configuration File - Example

Copy this file to 'health_check_config.py' in the same directory as the
linux_health_check.py script and customize the values below.

The health_check_config.py file is git-ignored so your settings won't be
overwritten when you update the script.

Configuration Priority:
1. Environment variables (highest priority)
2. This config file (health_check_config.py)
3. Hardcoded defaults in the script (lowest priority)

Security Note:
If this file contains sensitive information (SMTP passwords, etc.),
restrict file permissions: chmod 600 health_check_config.py
"""

# ============================================================================
# OUTPUT CONFIGURATION
# ============================================================================

# Directory where reports will be saved
# Default: "/root" if running as root, otherwise "/tmp"
# OUTPUT_DIR = "/var/log/health-checks"

# Output filename (will be combined with OUTPUT_DIR)
# Default: "health_report.txt"
# OUTPUT_FILE = None  # Set to None to use default location

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================

# Enable/disable email reporting
# Set to True to send reports via email
EMAIL_ENABLED = False

# Email addresses
# Set these if EMAIL_ENABLED is True
EMAIL_TO = None  # Example: "admin@example.com"
EMAIL_FROM = None  # Example: "health-check@example.com"

# Email subject line
# Use {hostname} placeholder to include the hostname
EMAIL_SUBJECT = "Linux Health Check Report - {hostname}"

# ============================================================================
# SMTP CONFIGURATION
# ============================================================================

# SMTP server settings (required if EMAIL_ENABLED is True)
SMTP_SERVER = None  # Example: "smtp.gmail.com"
SMTP_PORT = 587  # Common ports: 587 (TLS), 465 (SSL), 25 (unencrypted)
SMTP_USE_TLS = True  # Use TLS/STARTTLS for secure connection

# SMTP authentication (if required by your server)
SMTP_USERNAME = None  # Example: "your-email@gmail.com"
SMTP_PASSWORD = None  # Example: "your-app-password"

# Security Warning: Store SMTP_PASSWORD securely!
# Consider using environment variables instead:
#   export SMTP_PASSWORD="your-password"
# Or use application-specific passwords (Gmail, etc.)

# ============================================================================
# GPG ENCRYPTION CONFIGURATION
# ============================================================================

# Enable/disable GPG encryption for reports
# Requires gpg command to be available
GPG_ENABLED = False

# GPG recipient email/key ID
# Reports will be encrypted for this recipient
GPG_RECIPIENT = None  # Example: "admin@example.com"

# Note: The GPG recipient's public key must be imported:
#   gpg --import recipient-public-key.asc
#   gpg --trust-model always --encrypt ...

# ============================================================================
# POLICY THRESHOLDS - FILESYSTEM
# ============================================================================

# Filesystem usage thresholds (percentage: 0-100)
# WARNING: Triggers when usage exceeds this percentage
FILESYSTEM_WARNING_THRESHOLD = 85

# CRITICAL: Triggers when usage exceeds this percentage
FILESYSTEM_CRITICAL_THRESHOLD = 98

# ============================================================================
# POLICY THRESHOLDS - MEMORY
# ============================================================================

# Memory usage thresholds (percentage: 0-100)
MEMORY_WARNING_THRESHOLD = 85
MEMORY_CRITICAL_THRESHOLD = 95

# ============================================================================
# POLICY THRESHOLDS - LOAD AVERAGE
# ============================================================================

# Load average thresholds (multiplier of CPU count)
# WARNING: Triggers when load > (CPU_COUNT * multiplier)
# Example: 0.7 means 70% of CPU capacity
LOAD_WARNING_MULTIPLIER = 0.7

# CRITICAL: Triggers when load >= (CPU_COUNT * multiplier)
# Example: 1.0 means 100% of CPU capacity (fully loaded)
LOAD_CRITICAL_MULTIPLIER = 1.0

# ============================================================================
# VERSION CHECKING CONFIGURATION
# ============================================================================

# GitHub repository for version checking
# Format: "owner/repo-name"
GITHUB_REPO = "0xgruber/linux-health-checks"

# Timeout for version check HTTP requests (seconds)
# Set to lower value to avoid delays on network issues
VERSION_CHECK_TIMEOUT = 3

# Disable version checking entirely
# Set to "1" to skip version checks (can also use environment variable)
# DISABLE_VERSION_CHECK = "0"

# ============================================================================
# ADVANCED CONFIGURATION
# ============================================================================

# Enable verbose logging for debugging
# VERBOSE_LOGGING = False

# Custom log format
# LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# ============================================================================
# ENVIRONMENT VARIABLE OVERRIDES
# ============================================================================

# All configuration values can be overridden via environment variables.
# Environment variables take precedence over this config file.
#
# Examples:
#   export OUTPUT_DIR="/custom/path"
#   export EMAIL_ENABLED="True"
#   export SMTP_PASSWORD="secret-password"
#   export FILESYSTEM_WARNING_THRESHOLD="90"
#   export VERSION_CHECK_TIMEOUT="5"
#   export DISABLE_VERSION_CHECK="1"
#
# Boolean values: Use "True", "true", "1", "yes" for True
#                 Use "False", "false", "0", "no" for False
#
# Integer values: Use numeric strings "85", "90", etc.

# ============================================================================
# QUICK START EXAMPLES
# ============================================================================

# Example 1: Enable email reporting with Gmail
# EMAIL_ENABLED = True
# EMAIL_TO = "admin@example.com"
# EMAIL_FROM = "healthcheck@gmail.com"
# SMTP_SERVER = "smtp.gmail.com"
# SMTP_PORT = 587
# SMTP_USE_TLS = True
# SMTP_USERNAME = "healthcheck@gmail.com"
# SMTP_PASSWORD = "your-app-specific-password"  # Create at google.com/accounts

# Example 2: Enable GPG encryption
# GPG_ENABLED = True
# GPG_RECIPIENT = "admin@example.com"
# First import the public key: gpg --import admin-pubkey.asc

# Example 3: Adjust filesystem thresholds for larger disks
# FILESYSTEM_WARNING_THRESHOLD = 90
# FILESYSTEM_CRITICAL_THRESHOLD = 95

# Example 4: Custom output directory
# OUTPUT_DIR = "/var/log/health-checks"

# Example 5: Faster version check timeout
# VERSION_CHECK_TIMEOUT = 1

# ============================================================================
# MIGRATION FROM SCRIPT EDITS
# ============================================================================

# If you previously edited the script directly:
# 1. Copy this file to 'health_check_config.py'
# 2. Copy your custom values from the script's CONFIGURATION section
# 3. Test: Run the script and verify configuration is loaded
# 4. Update script: Pull latest version without losing your config
