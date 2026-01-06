# Linux Health Checks

Comprehensive cross-distribution health and security audit script for Linux servers. The script performs 35+ distinct checks across security, system health, storage, packages, networking, and iSCSI, ranks findings by severity (Critical/High/Medium/Low/Info), and produces exportable reports with optional GPG encryption and email delivery.

**Author:** Aaron Gruber <aaron@gizmobear.io>  
**Version:** 2026.01.05 (Date-based versioning: YYYY.MM.DD)  
**License:** MIT  
**Repository:** https://github.com/0xgruber/linux-health-checks

## Key Features

### Cross-Distribution Support
Automatically detects and adapts to:
- **RHEL/Rocky/CentOS** - Uses `dnf`/`yum`, firewalld, SELinux
- **Debian/Ubuntu** - Uses `apt`, ufw/iptables, AppArmor  
- **SUSE** - Uses `zypper`
- **Arch** - Uses `pacman`
- Auto-detection of package managers, firewalls (firewalld/ufw/iptables), security frameworks (SELinux/AppArmor), and distribution-specific log paths

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

# Run the script
sudo ./linux_health_check.py
```

### From Source

```bash
# Clone the repository
git clone https://github.com/0xgruber/linux-health-checks.git
cd linux-health-checks

# Make executable
chmod +x linux_health_check.py

# Run the script
sudo ./linux_health_check.py
```

### Release Versioning

This project uses **date-based versioning** in the format `YYYY.MM.DD` (e.g., `2026.01.05`). 

- New releases are automatically created via GitHub Actions
- Each release includes the script, archives (tar.gz, zip), and checksums
- View all releases: https://github.com/0xgruber/linux-health-checks/releases

## Requirements

### Python Environment
- Python 3.8 or higher
- Standard library only - no pip dependencies required
- Modules used: `os`, `re`, `subprocess`, `sys`, `logging`, `pathlib`, `json`, `xml.etree.ElementTree`, `datetime`, `collections`, `typing`, `smtplib`, `email`

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
OUTPUT = f"{OUTPUT_DIR}/health_report.txt"
```
- Root users: logs to `/root/health_report.txt`
- Non-root users: logs to `/tmp/health_report.txt`

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

## Installation & Usage

### Installation
```bash
# Create directory structure
mkdir -p ~/code/linux-health-checks
cd ~/code/linux-health-checks

# Copy script from Downloads (adjust path if different)
cp ~/Downloads/linux_health_check.py .

# Make executable
chmod +x linux_health_check.py

# Edit configuration constants at top of file
nano linux_health_check.py  # or vim, vi, etc.
```

### Running the Script

**Interactive run** (requires root for full coverage):
```bash
sudo ./linux_health_check.py
```

**As non-root** (limited visibility, logs to /tmp):
```bash
./linux_health_check.py
```

### What Happens During Execution

1. **OS Detection** - Identifies distribution, package manager, firewall, security framework
2. **Security Checks** - Validates hardening configurations
3. **System Health** - Monitors load, memory, processes, services
4. **Storage** - Checks filesystem and inode usage
5. **Package Updates** - Scans for security updates and orphans
6. **Networking** - Tests firewall, ports, NTP, DNS, interface stats
7. **iSCSI** - Verifies service, sessions, targets, logs
8. **Issue Summary** - Displays table of findings by severity
9. **Auto-Export** - Creates timestamped Markdown report in `OUTPUT_DIR`
10. **Email** - Optionally encrypts and sends report (if configured)

### Example Output

Console/log output shows:
```
## OS Detection
Distribution: Rocky Linux 8.9 (Green Obsidian)
Package Manager: dnf
Security Framework: selinux
Firewall: firewalld

## SELinux Status
Desired state: Enforcing
Current state: Enforcing
PASS: SELinux is enforcing.

## SSH Service Status
Desired state: Disabled, Inactive
Enabled: disabled
Active: inactive
PASS: SSH is disabled and inactive.
...
```

Issue summary table at end:
```
| Severity | Count |
|----------|-------|
| 🔴 **Critical** | 2 |
| 🟠 **High** | 5 |
| 🟡 **Medium** | 3 |
```

## Output Artifacts

### Primary Log
- **Location**: `/root/health_report.txt` (root) or `/tmp/health_report.txt` (non-root)
- **Format**: Plain text with markdown-style headers
- **Contains**: All check output, PASS/FAIL status, issue details

### Exported Reports
Automatic export creates timestamped files in `OUTPUT_DIR`:

- **Markdown**: `health_report_export_YYYYMMDD_HHMMSS.md` (default)
  - Formatted tables, severity emoji, code blocks
  - GitHub-compatible markdown
  
- **JSON**: `health_report_export_YYYYMMDD_HHMMSS.json`
  - Machine-readable structured data
  - Includes metadata (hostname, distro, timestamp)
  - Array of issues with severity/category/details
  
- **XML**: `health_report_export_YYYYMMDD_HHMMSS.xml`
  - XML tree with metadata and issues elements
  - Schema: `<health_check_report><metadata>...<issues>...`
  
- **Plain Text**: `health_report_export_YYYYMMDD_HHMMSS.txt`
  - Formatted report without markdown syntax
  - Suitable for email body or terminal viewing

### GPG Encrypted Files
When `GPG_ENABLED=True` and `GPG_RECIPIENT` is set:
- Creates `.gpg` extension file (ASCII armored)
- Uses `--trust-model always` to avoid prompts
- Original plaintext file is retained

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

### How to Contribute

1. **Fork the repository** on GitHub
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** with clear, descriptive commits
4. **Test thoroughly** on multiple distributions if possible
5. **Submit a pull request** with a detailed description

### Development Guidelines

- Maintain Python 3.8+ compatibility
- No external pip dependencies (stdlib only)
- Follow existing code style and patterns
- Add tests for new functionality when possible
- Update documentation (README.md, comments)
- Consider cross-distribution compatibility

### Reporting Issues

Found a bug or have a feature request?

1. Check existing issues: https://github.com/0xgruber/linux-health-checks/issues
2. Create a new issue with:
   - Clear description of the problem/request
   - Steps to reproduce (for bugs)
   - Your distribution and version
   - Relevant log output or error messages

## Releases

This project uses automated date-based releases (YYYY.MM.DD format). View all releases at:
https://github.com/0xgruber/linux-health-checks/releases

Each release includes:
- Standalone script file
- Source code archives (tar.gz, zip)
- SHA256 checksums
- Release notes with changes

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

