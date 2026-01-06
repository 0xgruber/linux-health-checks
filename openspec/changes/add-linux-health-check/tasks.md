# Implementation Tasks

## 1. Core Script Development
- [x] 1.1 Create Python script with logging infrastructure
- [x] 1.2 Implement OS detection (distribution, package manager, firewall, security framework)
- [x] 1.3 Implement safe command execution helpers (no shell=True)
- [x] 1.4 Implement Python replacements for shell pipelines (grep, head, tail, count)
- [x] 1.5 Add issue tracking system with severity levels

## 2. Security Checks
- [x] 2.1 Implement SELinux/AppArmor enforcement validation
- [x] 2.2 Implement SSH service status check (disabled/inactive)
- [x] 2.3 Implement SSH root login configuration check
- [x] 2.4 Implement wheel group membership validation
- [x] 2.5 Implement login shell user enumeration
- [x] 2.6 Implement sudoers permissions validation
- [x] 2.7 Implement password aging policy check
- [x] 2.8 Implement failed login attempts monitoring

## 3. System Health Checks
- [x] 3.1 Implement system uptime reporting
- [x] 3.2 Implement load average monitoring with CPU-relative thresholds
- [x] 3.3 Implement memory usage percentage calculation
- [x] 3.4 Implement zombie process detection
- [x] 3.5 Implement failed systemd services detection
- [x] 3.6 Implement disk I/O error scanning (dmesg)
- [x] 3.7 Implement CPU temperature monitoring (sensors)

## 4. Storage Checks
- [x] 4.1 Implement filesystem usage validation (85% threshold, 98% for /mnt/backup)
- [x] 4.2 Implement inode usage validation (85% threshold)
- [x] 4.3 Implement filesystem error detection (kernel logs)

## 5. Package & Update Compliance
- [x] 5.1 Implement security update detection (dnf/yum/apt/zypper/pacman)
- [x] 5.2 Implement orphaned package detection with whitelist
- [x] 5.3 Implement kernel version update detection

## 6. Networking Diagnostics
- [x] 6.1 Implement firewall status check (firewalld/ufw/iptables)
- [x] 6.2 Implement listening port enumeration with policy validation
- [x] 6.3 Implement NTP synchronization status check
- [x] 6.4 Implement network interface statistics collection
- [x] 6.5 Implement ethtool error/drop detection
- [x] 6.6 Implement DNS resolution testing

## 7. iSCSI Coverage
- [x] 7.1 Implement iscsid service status check
- [x] 7.2 Implement iSCSI session enumeration
- [x] 7.3 Implement iSCSI target connectivity validation
- [x] 7.4 Implement lsscsi device enumeration
- [x] 7.5 Implement dmesg iSCSI error pattern detection
- [x] 7.6 Implement journalctl iSCSI log analysis
- [x] 7.7 Implement system log connection error detection

## 8. Reporting & Export
- [x] 8.1 Implement severity-ranked issue summary display
- [x] 8.2 Implement Markdown export format
- [x] 8.3 Implement JSON export format
- [x] 8.4 Implement XML export format
- [x] 8.5 Implement plain text export format
- [x] 8.6 Implement timestamped file naming

## 9. Encryption & Email
- [x] 9.1 Implement GPG encryption with configurable recipient
- [x] 9.2 Implement SMTP email delivery with TLS support
- [x] 9.3 Implement email attachment handling (plain and encrypted)
- [x] 9.4 Implement automatic export and email workflow

## 10. Configuration & Automation
- [x] 10.1 Add configurable output directory (root vs /tmp)
- [x] 10.2 Add configurable email settings (SMTP, credentials, TLS)
- [x] 10.3 Add configurable GPG settings (recipient, keyring)
- [x] 10.4 Implement non-interactive execution for cron compatibility
- [x] 10.5 Add proper error handling and graceful degradation

## 11. Documentation
- [x] 11.1 Create comprehensive README.md with installation instructions
- [x] 11.2 Document all configuration parameters with examples
- [x] 11.3 Document all 35+ checks with thresholds
- [x] 11.4 Document output artifact formats and locations
- [x] 11.5 Document cron automation setup with examples
- [x] 11.6 Create troubleshooting guide for common issues
- [x] 11.7 Update openspec/project.md with project context
- [x] 11.8 Create OpenSpec proposal documentation

## 12. Testing & Validation
- [ ] 12.1 Test on RHEL/Rocky/CentOS 8+ with dnf
- [ ] 12.2 Test on Debian/Ubuntu with apt
- [ ] 12.3 Test on SUSE with zypper
- [ ] 12.4 Test on Arch with pacman
- [ ] 12.5 Test root vs non-root execution scenarios
- [ ] 12.6 Test GPG encryption with various key formats
- [ ] 12.7 Test SMTP delivery with TLS and without
- [ ] 12.8 Test cron execution in non-interactive environment
- [ ] 12.9 Validate all export formats parse correctly
- [ ] 12.10 Test graceful degradation with missing utilities
