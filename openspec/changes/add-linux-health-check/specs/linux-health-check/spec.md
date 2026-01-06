# Linux Health Check Specification

## ADDED Requirements

### Requirement: Cross-Distribution Detection
The system SHALL automatically detect the Linux distribution and adapt to distribution-specific tooling including package managers (dnf, yum, apt, zypper, pacman), security frameworks (SELinux, AppArmor), firewalls (firewalld, ufw, iptables), and log file paths.

#### Scenario: Rocky Linux detection
- **WHEN** script runs on Rocky Linux 8.9
- **THEN** system detects `distro_id="rocky"`, `package_manager="dnf"`, `security_framework="selinux"`, `firewall="firewalld"`, `log_file="/var/log/messages"`

#### Scenario: Ubuntu detection
- **WHEN** script runs on Ubuntu 22.04
- **THEN** system detects `distro_id="ubuntu"`, `package_manager="apt"`, `security_framework="apparmor"`, `firewall="ufw"`, `log_file="/var/log/syslog"`

### Requirement: Security Framework Validation
The system SHALL validate that mandatory access control frameworks (SELinux or AppArmor) are enabled and enforcing. For SELinux, status must be "Enforcing". For AppArmor, profiles must be loaded and in enforce mode.

#### Scenario: SELinux enforcing passes
- **WHEN** `getenforce` returns "Enforcing"
- **THEN** check reports PASS with Info severity

#### Scenario: SELinux permissive fails
- **WHEN** `getenforce` returns "Permissive"
- **THEN** check reports FAIL and adds High severity issue with message "SELinux is not enforcing"

#### Scenario: AppArmor complain mode warning
- **WHEN** `aa-status` shows profiles in complain mode
- **THEN** check adds Medium severity issue with message "Some AppArmor profiles are in complain mode"

### Requirement: SSH Service Hardening
The system SHALL verify that the SSH service (sshd) is disabled and inactive, and that root login via SSH is prohibited (PermitRootLogin=no).

#### Scenario: SSH properly disabled
- **WHEN** `systemctl is-enabled sshd` returns "disabled" AND `systemctl is-active sshd` returns "inactive"
- **THEN** check reports PASS

#### Scenario: SSH enabled but inactive
- **WHEN** `systemctl is-enabled sshd` returns "enabled" AND `systemctl is-active sshd` returns "inactive"
- **THEN** check adds Medium severity issue "SSH service is enabled but not active"

#### Scenario: SSH active
- **WHEN** `systemctl is-active sshd` returns "active"
- **THEN** check adds High severity issue "SSH service is active"

#### Scenario: Root login enabled
- **WHEN** `/etc/ssh/sshd_config` contains `PermitRootLogin yes`
- **THEN** check adds Critical severity issue "SSH root login is enabled"

### Requirement: User Access Control
The system SHALL validate that only approved users have login shells (UID >= 1000, excluding 65534), that the wheel group contains no members, and that sudoers permissions follow NOEXEC restrictions for locadmin.

#### Scenario: Only locadmin has login shell
- **WHEN** parsing `/etc/passwd` shows only "locadmin" with bash/sh shell and UID >= 1000
- **THEN** check reports PASS

#### Scenario: Unauthorized user with login shell
- **WHEN** parsing `/etc/passwd` shows "alice" with bash shell and UID 1001
- **THEN** check adds High severity issue "Unexpected users with login shells: alice"

#### Scenario: Wheel group empty
- **WHEN** `getent group wheel` returns no members in field 4
- **THEN** check reports PASS

#### Scenario: Wheel group has members
- **WHEN** `getent group wheel` returns "wheel:x:10:alice,bob"
- **THEN** check adds High severity issue "Wheel group contains users: alice,bob"

### Requirement: System Health Monitoring
The system SHALL monitor system load relative to CPU count, memory usage percentage, zombie processes, failed systemd services, disk I/O errors, and CPU temperature with appropriate severity thresholds.

#### Scenario: Normal system load
- **WHEN** 1-minute load average is 2.5 AND CPU count is 4
- **THEN** check reports normal (load < 1.5×CPUs)

#### Scenario: High system load
- **WHEN** 1-minute load average is 7.0 AND CPU count is 4
- **THEN** check adds Medium severity issue "High system load: 7.0 (CPUs: 4)"

#### Scenario: Critical system load
- **WHEN** 1-minute load average is 9.0 AND CPU count is 4
- **THEN** check adds High severity issue "Very high system load: 9.0 (CPUs: 4)"

#### Scenario: High memory usage
- **WHEN** memory usage is 87% (between 85% and 95%)
- **THEN** check adds High severity issue "High memory usage"

#### Scenario: Critical memory usage
- **WHEN** memory usage is 96%
- **THEN** check adds Critical severity issue "Critical memory usage"

#### Scenario: Zombie processes detected
- **WHEN** `ps -eo stat` shows 3 processes with state "Z"
- **THEN** check adds Medium severity issue "Found 3 zombie process(es)"

#### Scenario: Failed systemd service
- **WHEN** `systemctl --failed` shows "httpd.service" failed
- **THEN** check adds High severity issue with list of failed services

### Requirement: Storage Capacity Monitoring
The system SHALL monitor filesystem usage (85% threshold, 98% for /mnt/backup), inode usage (85% threshold), and filesystem errors in kernel logs.

#### Scenario: Filesystem within threshold
- **WHEN** `/home` is at 72% usage
- **THEN** check reports within threshold

#### Scenario: Filesystem over threshold
- **WHEN** `/var` is at 89% usage
- **THEN** check adds High severity issue "Filesystem /var is over threshold: 89%"

#### Scenario: Filesystem critical
- **WHEN** `/opt` is at 97% usage
- **THEN** check adds Critical severity issue "Filesystem /opt is over threshold: 97%"

#### Scenario: Backup filesystem special threshold
- **WHEN** `/mnt/backup` is at 97% usage
- **THEN** check reports within threshold (98% limit for backup)

#### Scenario: Inode exhaustion warning
- **WHEN** `/var/log` has 89% inode usage
- **THEN** check adds High severity issue "Inode usage for /var/log is 89%"

### Requirement: Package Update Compliance
The system SHALL detect pending security updates, orphaned packages (with whitelist for veeamdeployment and veeamtransport), and available kernel updates using distribution-specific package managers.

#### Scenario: Security updates available (dnf)
- **WHEN** `dnf updateinfo list security` shows 5 security updates
- **THEN** check adds High severity issue "5 security update(s) available" with update list

#### Scenario: No security updates (apt)
- **WHEN** `apt list --upgradable` shows no packages with "security" keyword
- **THEN** check reports PASS

#### Scenario: Orphaned package allowed
- **WHEN** `dnf repoquery --extras` returns "veeamdeployment"
- **THEN** check reports PASS (whitelisted package)

#### Scenario: Unauthorized orphaned package
- **WHEN** `dnf repoquery --extras` returns "custom-app"
- **THEN** check adds Medium severity issue "Found 1 unauthorized orphaned package(s): custom-app"

### Requirement: Networking Diagnostics
The system SHALL validate firewall status, enumerate listening ports with policy checks, verify NTP synchronization, collect interface statistics, detect network errors via ethtool, and test DNS resolution.

#### Scenario: firewalld active
- **WHEN** `systemctl is-active firewalld` returns "active"
- **THEN** check reports PASS

#### Scenario: firewalld inactive
- **WHEN** `systemctl is-active firewalld` returns "inactive"
- **THEN** check adds High severity issue "firewalld is not active"

#### Scenario: SSH port listening detected
- **WHEN** `ss -tulpn` shows port 22 in LISTEN state
- **THEN** check adds Medium severity issue "SSH port (22) is listening"

#### Scenario: NTP synchronized
- **WHEN** `timedatectl status` shows "System clock synchronized: yes"
- **THEN** check reports PASS

#### Scenario: NTP not synchronized
- **WHEN** `timedatectl status` shows "System clock synchronized: no"
- **THEN** check adds Medium severity issue "System clock is not synchronized"

#### Scenario: High network errors
- **WHEN** `ethtool -S eth0` shows total errors > 1000
- **THEN** check adds Medium severity issue "High network error count on eth0"

### Requirement: iSCSI Connectivity Monitoring
The system SHALL validate iscsid service status, enumerate active iSCSI sessions, verify target configuration, scan for iSCSI devices via lsscsi, and analyze kernel/journal logs for iSCSI errors.

#### Scenario: iscsid service active and enabled
- **WHEN** `systemctl is-active iscsid` returns "active" AND `systemctl is-enabled iscsid` returns "enabled"
- **THEN** check reports both conditions PASS

#### Scenario: iscsid service inactive
- **WHEN** `systemctl is-active iscsid` returns "inactive"
- **THEN** check adds Critical severity issue "iscsid service is not active"

#### Scenario: Active iSCSI sessions found
- **WHEN** `iscsiadm -m session` shows 2 active sessions
- **THEN** check logs "Found 2 iSCSI session(s)"

#### Scenario: No active iSCSI sessions
- **WHEN** `iscsiadm -m session` returns "No active sessions"
- **THEN** check adds Medium severity issue "No active iSCSI sessions found"

#### Scenario: iSCSI errors in dmesg
- **WHEN** `dmesg` contains "iscsi: connection error" or "iscsi: timeout"
- **THEN** check adds High severity issue "Found N iSCSI error(s) in dmesg" with error lines

### Requirement: Severity-Ranked Reporting
The system SHALL accumulate all findings with severity levels (Critical, High, Medium, Low, Info), display a summary table by severity count, and present detailed issues sorted by severity priority.

#### Scenario: Multiple issues with ranking
- **WHEN** checks detect 1 Critical, 3 High, 2 Medium issues
- **THEN** summary table shows counts and detailed report lists Critical first, then High, then Medium

#### Scenario: No issues detected
- **WHEN** all checks pass with no issues added
- **THEN** system displays "No Issues Found" and "System health check passed!"

### Requirement: Multi-Format Export
The system SHALL export reports in Markdown (with emoji/tables), JSON (structured data with metadata), XML (health_check_report schema), and plain text formats with timestamped filenames.

#### Scenario: Markdown export with issues
- **WHEN** auto-export runs with 2 High severity issues
- **THEN** Markdown file created at `OUTPUT_DIR/health_report_export_YYYYMMDD_HHMMSS.md` containing severity table with emoji and issue details in code blocks

#### Scenario: JSON export structure
- **WHEN** JSON export runs
- **THEN** output contains `report_metadata` (hostname, distro, timestamp, total_issues), `issues` array, and `summary` object with severity counts

#### Scenario: XML export schema
- **WHEN** XML export runs
- **THEN** output contains `<health_check_report><metadata><issues>` structure with proper XML declaration

### Requirement: GPG Encryption Support
The system SHALL encrypt export files using GPG with configurable recipient, keyring, and trust model when GPG_ENABLED is True.

#### Scenario: Successful encryption
- **WHEN** `GPG_ENABLED=True`, `GPG_RECIPIENT="admin@example.com"`, and key exists
- **THEN** system creates `.gpg` armored file using `gpg --encrypt --armor --recipient admin@example.com --trust-model always`

#### Scenario: Missing GPG recipient
- **WHEN** `GPG_ENABLED=True` but `GPG_RECIPIENT=None`
- **THEN** system logs "WARNING: GPG encryption enabled but no recipient specified" and skips encryption

#### Scenario: GPG key not found
- **WHEN** `GPG_RECIPIENT="unknown@example.com"` and key doesn't exist
- **THEN** encryption fails with stderr logged and returns None

### Requirement: SMTP Email Delivery
The system SHALL send email reports with attachments (plain or encrypted) via configurable SMTP server with TLS support and authentication when EMAIL_ENABLED is True.

#### Scenario: Successful email with TLS
- **WHEN** `EMAIL_ENABLED=True`, `SMTP_USE_TLS=True`, and credentials valid
- **THEN** system connects via STARTTLS, authenticates, sends email with Markdown attachment

#### Scenario: Email disabled
- **WHEN** `EMAIL_ENABLED=False`
- **THEN** system skips email delivery without error

#### Scenario: Email with encrypted attachment
- **WHEN** both GPG and email enabled and encryption succeeds
- **THEN** email body notes "The report is GPG encrypted for security" and attaches `.gpg` file

### Requirement: Cron Automation Support
The system SHALL execute non-interactively without prompts, handle missing utilities gracefully, and complete all checks/exports/email automatically for unattended cron execution.

#### Scenario: Non-interactive execution
- **WHEN** script runs via cron (no TTY)
- **THEN** auto_export_and_email() executes without user input and completes successfully

#### Scenario: Missing utility graceful degradation
- **WHEN** `sensors` command not found
- **THEN** CPU temperature check logs "Temperature sensors not available" and continues to next check

#### Scenario: Non-root cron execution
- **WHEN** cron runs as non-root user
- **THEN** OUTPUT_DIR falls back to `/tmp` and script completes with limited visibility warnings

### Requirement: Configurable Policy Thresholds
The system SHALL use configurable constants for output directory, email settings, GPG settings, and hard-coded policy expectations (SSH state, user/group rules, filesystem/memory/load thresholds).

#### Scenario: Custom output directory
- **WHEN** `OUTPUT_DIR="/var/log/health"` configured
- **THEN** primary log written to `/var/log/health/health_report.txt`

#### Scenario: Custom SMTP port
- **WHEN** `SMTP_PORT=587` and `SMTP_USE_TLS=True` configured
- **THEN** system connects to SMTP server on port 587 with STARTTLS

#### Scenario: Custom filesystem threshold
- **WHEN** source modified to use 90% instead of 85%
- **THEN** filesystems at 87% usage report PASS instead of FAIL
