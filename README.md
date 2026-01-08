# Linux Health Checks

[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)](https://github.com/0xgruber/linux-health-checks/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/)
[![Debian](https://img.shields.io/badge/Debian-12%20%7C%2013-red.svg)](https://www.debian.org/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04%20%7C%2024.04-orange.svg)](https://ubuntu.com/)
[![Rocky](https://img.shields.io/badge/Rocky-9%20%7C%2010-green.svg)](https://rockylinux.org/)
[![openSUSE](https://img.shields.io/badge/openSUSE-Leap%20%7C%20Tumbleweed-brightgreen.svg)](https://www.opensuse.org/)
[![Tests](https://img.shields.io/badge/tests-8%2F8%20passing-success.svg)](test_results/DISTRO_TEST_REPORT.md)

Comprehensive cross-distribution health and security audit script for Linux servers. The script performs 35+ distinct checks across security, system health, storage, packages, networking, and iSCSI, ranks findings by severity (Critical/High/Medium/Low/Info), and produces exportable reports with optional GPG encryption and email delivery.

**Author:** Aaron Gruber <aaron@gizmobear.io>  
**Version:** 1.3.0 ([Semantic Versioning](https://semver.org/))  
**License:** MIT  
**Repository:** https://github.com/0xgruber/linux-health-checks

## Key Features

### Configuration

Customize the script without modifying code using an external configuration file.

**Quick Start:**
```bash
# Copy example config
cp health_check.cfg.example health_check.cfg

# Edit your settings
nano health_check.cfg

# Config file is git-ignored, won't be overwritten on updates
```

**Configuration Priority:**
1. **Environment variables** (highest priority) - temporary overrides
2. **Config file** (`health_check.cfg`) - persistent settings
3. **Hardcoded defaults** (fallback)

**Available Settings:**
- **Output**: Report directory and filename
- **Email**: SMTP delivery settings (enabled, from, to, subject)
- **SMTP**: Server connection details (server, port, TLS, credentials)
- **GPG**: Encryption options (encrypt, recipient, delete_unencrypted)
- **Thresholds**: System health warning/critical levels (filesystem, memory, load)
- **Version Check**: GitHub update notifications (enabled, timeout)

See [`health_check.cfg.example`](health_check.cfg.example) for complete documentation with examples.

**Security Note:**
```bash
# Protect config if it contains credentials
chmod 600 health_check.cfg
```

**Example Environment Variable Override:**
```bash
# Override filesystem warning threshold for one-time check
FILESYSTEM_WARNING=75 sudo ./linux_health_check.py

# Override multiple values
OUTPUT_DIR=/var/log/health FILESYSTEM_WARNING=70 sudo ./linux_health_check.py
```

### Cross-Distribution Support

**Officially Supported ✅** (Tested in Docker containers):
- **Debian:** 12 (Bookworm), 13 (Trixie)
- **Ubuntu:** 22.04 LTS (Jammy), 24.04 LTS (Noble)
- **Rocky Linux:** 9, 10
- **openSUSE:** Leap 15, Tumbleweed

**Experimental ⚠️** (Not officially tested):
- **Arch Linux:** May work but use at your own risk. Not tested or officially supported.

**Auto-detection features:**
- Package managers: `dnf`/`yum`, `apt`, `zypper`, `pacman`
- Firewalls: firewalld, ufw, iptables
- Security frameworks: SELinux, AppArmor
- Distribution-specific log paths and configurations

> See [test_results/DISTRO_TEST_REPORT.md](test_results/DISTRO_TEST_REPORT.md) for detailed test results across all supported distributions.

### Security Auditing (8 checks)
- SELinux/AppArmor enforcement status
- SSH authentication analysis:
  - **HIGH severity**: Password authentication enabled
  - **MEDIUM severity**: RSA/DSA keys in use (weak algorithms)
  - **LOW severity**: ed25519 or ECDSA keys (strong key-based auth)
  - **INFO**: SSH service disabled (good)
- SSH root login configuration (PermitRootLogin)
- Wheel group membership (should be empty per policy)
- Login shell users (only `locadmin` allowed per policy)
- Sudoers permissions (NOEXEC restrictions)
- Password aging policy (PASS_MAX_DAYS ≤ 90)
- Failed login attempt monitoring

### System State & Health (7 checks)
- System uptime (informational)
- Load average vs CPU count with high-load detection
- Memory usage percentage with critical thresholds (>85%, >95%)
- Zombie process detection
- Failed systemd services
- Disk I/O errors from dmesg
- CPU temperature monitoring (warns >70°C, critical >80°C)

### Storage & Filesystem (3 checks)
- Filesystem usage (85% threshold, 98% for `/mnt/backup`)
- Inode usage (85% threshold)
- Filesystem errors in kernel logs

### Package & Update Compliance (3 checks)
- Security updates pending (distro-aware)
- Orphaned/extra packages (allows `veeamdeployment`, `veeamtransport`)
- Kernel version updates available

### Networking Diagnostics (6 checks)
- Firewall status (firewalld/ufw/iptables)
- Listening ports (warns on SSH port 22)
- NTP synchronization status
- Network interface statistics
- Ethernet errors/drops via ethtool
- DNS resolution tests

### iSCSI Coverage (7 checks)
- iscsid service status (active/enabled)
- Active iSCSI sessions
- Target connectivity/configuration
- lsscsi device enumeration
- dmesg iSCSI error patterns
- journalctl iSCSI logs (last hour)
- System log connection/authentication errors

### Reporting & Export
- Primary log: `/root/health_report.txt` (or `/tmp/health_report.txt` for non-root)
- Export formats: Markdown (default), JSON, XML, plain text
- Ranked issue summary table by severity
- Detailed issue sections with descriptions and remediation context
- GPG encryption support for sensitive reports
- SMTP email delivery with attachments

## Installation

### From GitHub Releases

Download the latest release:

```bash
# Download the latest version
wget https://github.com/0xgruber/linux-health-checks/releases/latest/download/linux_health_check.py

# Make executable
chmod +x linux_health_check.py

# Optional: Download and customize config file
wget https://github.com/0xgruber/linux-health-checks/releases/latest/download/health_check.cfg.example
cp health_check.cfg.example health_check.cfg
nano health_check.cfg  # Customize output directory, email, thresholds, etc.

# Run the script
sudo ./linux_health_check.py
```

> **Note:** Configuration file is optional. The script works with sensible defaults. Create `health_check.cfg` only if you need to customize output directory, email delivery, or system thresholds. See [Configuration](#configuration) section for details.

### From Source

```bash
# Clone the repository
git clone https://github.com/0xgruber/linux-health-checks.git
cd linux-health-checks

# Make executable
chmod +x linux_health_check.py

# Optional: Set up configuration file
cp health_check.cfg.example health_check.cfg
nano health_check.cfg  # Customize output directory, email, thresholds, etc.

# Run the script
sudo ./linux_health_check.py
```

> **Note:** Configuration file is optional. The script works with sensible defaults. Create `health_check.cfg` only if you need to customize output directory, email delivery, or system thresholds. See [Configuration](#configuration) section for details.


### Usage Examples

**Basic execution** (requires root for full coverage):
```bash
sudo ./linux_health_check.py
```

**As non-root** (limited visibility, writes to /tmp):
```bash
./linux_health_check.py
```

**Choose output format** (default: markdown):
```bash
# JSON format (machine-readable)
EXPORT_FORMAT=json sudo ./linux_health_check.py

# XML format (enterprise systems)
EXPORT_FORMAT=xml sudo ./linux_health_check.py

# Plain text format (simple parsing)
EXPORT_FORMAT=text sudo ./linux_health_check.py
```

**Override configuration temporarily**:
```bash
# Override filesystem warning threshold for one-time check
FILESYSTEM_WARNING=75 sudo ./linux_health_check.py

# Override multiple values
OUTPUT_DIR=/var/log/health FILESYSTEM_WARNING=70 sudo ./linux_health_check.py
```

### Versioning

This project follows **[Semantic Versioning 2.0.0](https://semver.org/)** (SemVer).

**Format:** `MAJOR.MINOR.PATCH` (e.g., `1.0.0`)

- **MAJOR** version (X.0.0): Breaking changes, incompatible API changes
- **MINOR** version (1.X.0): New features, backward-compatible functionality
- **PATCH** version (1.0.X): Bug fixes, security patches, documentation updates

**Current Version:** 1.1.0

View all releases and changelog: https://github.com/0xgruber/linux-health-checks/releases

### Automated Update Checking

The script automatically checks for newer versions by querying the GitHub Releases API. If a newer version is available, an **INFO-level notification** is included in the health check report with upgrade instructions.

**Features:**
- Checks GitHub Releases API on every execution
- 3-second timeout (prevents hanging on slow networks)
- Silent failure (network errors don't break health checks)
- INFO-level severity (non-intrusive notification)
- Manual upgrade only (no auto-update functionality)

**Configuration:**

Disable version checking:
```bash
DISABLE_VERSION_CHECK=1 sudo ./linux_health_check.py
```

Custom API timeout (default: 3 seconds):
```bash
VERSION_CHECK_TIMEOUT=5 sudo ./linux_health_check.py
```

**Rate Limits:**  
GitHub API allows 60 requests/hour for unauthenticated requests. If you run the script more frequently than this, consider disabling version checks with `DISABLE_VERSION_CHECK=1`.

**Security:**
- Uses HTTPS with certificate validation
- No credentials required (public API)
- No auto-update (manual download and verification required)
- All errors fail silently and are logged at DEBUG level only

## Requirements

### Python Environment
- Python 3.6 or higher
- Standard library only - no pip dependencies required
- Modules used: `os`, `re`, `subprocess`, `sys`, `logging`, `pathlib`, `json`, `xml.etree.ElementTree`, `datetime`, `collections`, `typing`, `smtplib`, `email`, `urllib.request`, `urllib.error`

### System Utilities
The script gracefully handles missing commands but coverage is maximized with:

**Core utilities** (nearly universal):
- `systemctl`, `hostname`, `uptime`, `whoami`, `date`, `free`, `df`, `ps`, `uname`, `grep`, `which`, `getent`, `nproc`

**Networking**:
- `ip`, `ss`, `nslookup`, `ethtool` (optional)

**Package managers** (distro-specific):
- RHEL/Rocky/CentOS: `dnf` or `yum`
- Debian/Ubuntu: `apt` or `apt-get`
- SUSE: `zypper`
- Arch: `pacman`

**Security frameworks**:
- SELinux: `getenforce`
- AppArmor: `aa-status`

**Firewalls**:
- `firewall-cmd` (firewalld)
- `ufw` (Ubuntu/Debian)
- `iptables`

**iSCSI**:
- `iscsiadm`, `lsscsi` (optional)

**Monitoring** (optional but recommended):
- `sensors` (lm-sensors package)
- `journalctl`
- `dmesg`
- `lastb`

**Optional for encryption/email**:
- `gnupg` / `gpg` command
- SMTP relay accessible from host

## Configuration

Edit the constants at the top of `linux_health_check.py` (lines 20-40) before running:

> **Note:** Future releases will support external configuration files. See [IMPROVEMENTS.md](IMPROVEMENTS.md) for planned enhancements.

### Output Directory
```python
OUTPUT_DIR = "/root" if os.geteuid() == 0 else "/tmp"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "health_report.txt")
```
- Root users: Files written to `/root/`
- Non-root users: Files written to `/tmp/`
- Execution log: `health_report.txt` (diagnostic logging)
- Health report: `health_report_{hostname}.{ext}` (primary output, format based on EXPORT_FORMAT)

### Email Configuration
```python
EMAIL_ENABLED = True                      # Set False to disable email
EMAIL_TO = "admin@example.com"            # Recipient address
EMAIL_FROM = "root@localhost"             # Sender address
EMAIL_SUBJECT = "Linux Health Check Report"
SMTP_SERVER = "localhost"                 # SMTP server hostname/IP
SMTP_PORT = 25                            # Common ports: 25, 587, 465
SMTP_USER = None                          # Username (or None)
SMTP_PASSWORD = None                      # Password (or None)
SMTP_USE_TLS = False                      # True for STARTTLS
```

### GPG Encryption
```python
GPG_ENABLED = True                        # Set False to disable
GPG_RECIPIENT = None                      # Email, fingerprint, or key ID
GPG_KEYRING = None                        # Optional keyring path
```
**Important**: Set `GPG_RECIPIENT` to a valid key identifier. Script uses `--trust-model always` to avoid interactive prompts.

### Policy Thresholds

Hard-coded policy expectations (modify in source if your standards differ):

- **SSH**: 
  - INFO if disabled (good)
  - HIGH if password authentication enabled
  - MEDIUM if using RSA/DSA keys
  - LOW if using ed25519/ECDSA keys (acceptable)
  - Root login should be forbidden
- **Users**: Only `locadmin` should have login shell (UID ≥ 1000, excluding 65534)
- **Wheel group**: Should be empty
- **Sudoers**: `locadmin` limited to NOEXEC for `/usr/sbin/reboot` and `/usr/sbin/shutdown`
- **Password aging**: `PASS_MAX_DAYS` ≤ 90 days
- **Filesystems**: ≤85% usage (except `/mnt/backup` ≤98%)
- **Inodes**: ≤85% usage
- **Memory**: Warn >85%, critical >95%
- **System load**: Warn >1.5×CPUs, critical >2×CPUs
- **CPU temp**: Warn >70°C, critical >80°C
- **Orphaned packages**: Only `veeamdeployment` and `veeamtransport` allowed

## Output Artifacts

### Execution Log (Diagnostic)
- **Location**: `/root/health_report.txt` (root) or `/tmp/health_report.txt` (non-root)
- **Format**: Plain text Python logging output (INFO, WARNING, ERROR messages)
- **Contains**: Timestamped execution trace of all checks performed
- **Purpose**: Debugging and audit trail of script execution

### Health Check Report (Primary Output)
Automatically generated in the format specified by `EXPORT_FORMAT` environment variable (default: markdown):

- **Markdown** (default): `health_report_{hostname}.md`
  - Formatted tables, severity emoji (🔴🟠🟡🔵ℹ️), code blocks
  - GitHub-compatible markdown
  - Best for human readability and documentation
  
- **JSON**: `health_report_{hostname}.json`
  - Machine-readable structured data
  - Includes metadata (hostname, distro, timestamp, OS info)
  - Array of issues with severity/category/details/timestamp
  - Best for automation and integrations
  
- **XML**: `health_report_{hostname}.xml`
  - XML tree with metadata and issues elements
  - Schema: `<health_check_report><metadata>...<issues>...`
  - Best for enterprise systems and legacy integrations
  
- **Plain Text**: `health_report_{hostname}.txt`
  - Formatted report without markdown syntax
  - Suitable for email body or terminal viewing
  - Best for simple text processing

**Usage:**
```bash
# Default (Markdown)
./linux_health_check.py

# JSON output
EXPORT_FORMAT=json ./linux_health_check.py

# XML output
EXPORT_FORMAT=xml ./linux_health_check.py

# Plain text output
EXPORT_FORMAT=text ./linux_health_check.py
```

### GPG Encrypted Files
When `GPG_ENABLED=True` and `GPG_RECIPIENT` is set:
- Creates `.gpg` extension file (ASCII armored)
- Uses `--trust-model always` to avoid prompts
- Original plaintext report is deleted if `delete_unencrypted=true` (recommended for security)
- **⚠️ Breaking change in v1.3.0**: Log file (`health_report.txt`) is now also deleted when `delete_unencrypted=true`
  - **Before v1.3.0**: Only the markdown report was deleted
  - **After v1.3.0**: Both the markdown report AND the log file are deleted
  - **Why**: Prevents plain text vulnerability data from persisting on disk
  - **Impact**: If you need to keep the log file, set `delete_unencrypted=false` in your configuration

### Email Attachments
Email delivery includes:
- Report file (Markdown by default)
- Encrypted `.gpg` file (if GPG enabled)
- Email body contains summary metadata

## Automation with Cron

The script is designed for unattended execution via cron. Email/export happens automatically when configured.

### Example Crontab Entries

**Nightly at 2 AM** (recommended for most use cases):
```cron
0 2 * * * root /usr/bin/python3 /root/linux_health_check.py >/var/log/linux_health_check.log 2>&1
```

**Daily at 6 AM with explicit path**:
```cron
0 6 * * * root cd /home/aaron/code/linux-health-checks && /usr/bin/python3 ./linux_health_check.py >/var/log/linux_health_check_cron.log 2>&1
```

**Weekly on Sunday at midnight**:
```cron
0 0 * * 0 root /usr/bin/python3 /root/linux_health_check.py
```

### Cron Environment Considerations

1. **Use absolute paths** - Cron has minimal PATH
2. **Specify Python 3** - Use `/usr/bin/python3` not just `python`
3. **Redirect output** - Capture stdout/stderr to log file
4. **GPG agent** - May need `--batch` GPG options for non-interactive
5. **SMTP access** - Ensure cron user can reach SMTP server
6. **File permissions** - Script needs write access to `OUTPUT_DIR`

### Testing Cron Setup
```bash
# Test as root with cron-like environment
sudo su -c '/usr/bin/python3 /root/linux_health_check.py' -
```

### Monitoring Cron Execution
```bash
# Check if cron job ran
grep "linux_health_check" /var/log/cron

# Review execution log
tail -f /var/log/linux_health_check.log

# Check for email delivery
mailq  # or check mail logs
```

## Troubleshooting

### Missing Commands
**Symptom**: Warnings like "WARNING: command not available"  
**Solution**: Install the missing package for your distribution:

```bash
# RHEL/Rocky/CentOS
sudo dnf install ethtool lm_sensors iscsi-initiator-utils lsscsi

# Debian/Ubuntu
sudo apt install ethtool lm-sensors open-iscsi lsscsi iproute2

# SUSE
sudo zypper install ethtool sensors iscsi-initiator-utils lsscsi

# Arch
sudo pacman -S ethtool lm_sensors open-iscsi lsscsi
```

### Email Delivery Failures
**Symptom**: "SMTP error sending email" or "Connection refused"

**Common causes**:
1. **SMTP server unreachable** - Check `SMTP_SERVER` and `SMTP_PORT`
2. **Authentication required** - Set `SMTP_USER` and `SMTP_PASSWORD`
3. **TLS required** - Set `SMTP_USE_TLS = True` (usually port 587)
4. **Firewall blocking** - Check local firewall and network ACLs
5. **Relay restrictions** - SMTP server may reject unauthenticated relay

**Testing**:
```bash
# Test SMTP connectivity
telnet smtp.example.com 25
# or for TLS
openssl s_client -connect smtp.example.com:587 -starttls smtp
```

### GPG Encryption Issues
**Symptom**: "GPG encryption failed" or "key not found"

**Solutions**:
```bash
# List available keys
gpg --list-keys

# Import recipient public key
gpg --import recipient_pubkey.asc

# Verify key ID/email matches GPG_RECIPIENT
gpg --list-keys recipient@example.com

# Test encryption manually
echo "test" | gpg --encrypt --armor --recipient recipient@example.com

# If using custom keyring
gpg --keyring /path/to/keyring.gpg --list-keys
```

**Common issues**:
- `GPG_RECIPIENT` doesn't match any key (check email/fingerprint/key ID)
- Key is expired or revoked
- Missing public key on system
- GPG agent requires passphrase (use `--batch` or agent pre-authorization)

### Permission Errors
**Symptom**: Cannot write to `/root/health_report.txt`

**Causes**:
- Running as non-root (script falls back to `/tmp`)
- SELinux/AppArmor denials (check `ausearch` or `aa-status`)
- Filesystem full or read-only

**Solutions**:
```bash
# Run as root
sudo ./linux_health_check.py

# Check SELinux denials
sudo ausearch -m avc -ts recent

# Check disk space
df -h /root
```

### False Positives
**Symptom**: Script reports issues that don't apply to your environment

**Solution**: Edit policy thresholds in the script source code:

- SSH policy (lines 670-717): Modify if SSH should be enabled
- Wheel group (lines 719-734): Adjust if wheel membership is required
- Filesystem thresholds (lines 1066-1122): Change 85%/98% limits
- Orphaned packages (lines 1293-1338): Add allowed packages to whitelist
- Sudoers (lines 755-800): Modify NOEXEC expectations

### Incomplete Results
**Symptom**: Missing checks or "WARNING: package manager not detected"

**Causes**:
- Unsupported distribution
- Missing system utilities
- Running as non-root (limited access to logs, configs)

**Solutions**:
1. Run as root: `sudo ./linux_health_check.py`
2. Install missing utilities (see "Missing Commands" above)
3. Review `/tmp/health_report.txt` for specific warnings
4. For unsupported distros, manually set `OS_INFO` variables in source

### Email Not Sending
**Symptom**: Script completes but no email received

**Checklist**:
1. Is `EMAIL_ENABLED = True`?
2. Is `EMAIL_TO` correct recipient address?
3. Check SMTP logs on mail server
4. Check spam/junk folder
5. Verify GPG encryption didn't fail (check for `.gpg` file in OUTPUT_DIR)
6. Look for errors in script output or `/var/log/linux_health_check.log`

## Contributing

We welcome contributions! See [IMPROVEMENTS.md](IMPROVEMENTS.md) for a list of planned enhancements.

### Testing

The project includes a comprehensive test suite that validates all features across 8 supported distributions.

#### Running Tests Locally

```bash
# Run comprehensive test suite (all 8 distributions)
./test_suite.sh

# Expected runtime: ~15 minutes
# Requires: Docker installed and running
```

#### Test Coverage

The test suite validates:
- ✅ **8 distributions**: Debian 12/13, Ubuntu 22.04/24.04, Rocky Linux 9.7/10.1, openSUSE Leap 15/Tumbleweed
- ✅ **8 tests per distribution**: Syntax, dependencies, health checks, exports, version checking, exit codes
- ✅ **All features**: Health checks (35+), version checking, export formats, configuration
- ✅ **Python compatibility**: 3.6.15 - 3.13.5

#### Continuous Integration

Tests run automatically on every pull request via GitHub Actions:
- ✅ All tests must pass before merge
- ✅ Auto-merge on success (no manual approval needed)
- ❌ GitHub Issue created automatically on failure
- 📊 Test results posted as PR comments
- 📦 Test artifacts retained for 30 days

**See [TEST_REPORT.md](TEST_REPORT.md) for detailed test results and methodology.**

### How to Contribute

1. **Fork the repository** on GitHub
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** with clear, descriptive commits
4. **Test locally**: Run `./test_suite.sh` to validate changes
5. **Submit a pull request** with a detailed description

GitHub Actions will automatically test your PR on all 8 distributions.

### Development Guidelines

- Maintain Python 3.6+ compatibility
- No external pip dependencies (stdlib only)
- Follow existing code style and patterns
- **Run test suite** before submitting PRs: `./test_suite.sh`
- Update documentation (README.md, comments)
- Consider cross-distribution compatibility
- Tests must pass on all 8 distributions

### Reporting Issues

Found a bug or have a feature request?

1. Check existing issues: https://github.com/0xgruber/linux-health-checks/issues
2. Create a new issue with:
   - Clear description of the problem/request
   - Steps to reproduce (for bugs)
   - Your distribution and version
   - Relevant log output or error messages

## Releases

This project uses [Semantic Versioning](https://semver.org/) for releases. View all releases at:
https://github.com/0xgruber/linux-health-checks/releases

Each release includes:
- Standalone script file (`linux_health_check.py`)
- Source code archives (tar.gz, zip)
- SHA256 checksums
- Detailed changelog with all changes

**Release Process:** See [CONTRIBUTING.md](CONTRIBUTING.md) for version bumping guidelines.

## Future Enhancements

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for planned features including:
- Configuration file support
- Custom check plugins
- Historical tracking and trending
- Web dashboard
- Compliance profiles (CIS, STIG, PCI-DSS)
- Container security checks
- And many more...

## License
MIT License - See repository for details.

