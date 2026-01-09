# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.0] - 2026-01-08

### Fixed
- **CRITICAL SECURITY FIX**: Unencrypted log file (`health_report.txt`) is now deleted when `delete_unencrypted=true` in GPG configuration
  - **Issue**: Plain text log file containing vulnerability data was left on disk even with `delete_unencrypted=true`
  - **Impact**: Sensitive security findings were exposed in plain text, creating a security vulnerability
  - **Resolution**: Log file is now properly deleted after email delivery when GPG cleanup is enabled
  - **Breaking Change**: Users with `delete_unencrypted=true` will lose the log file after execution
    - If you need to preserve the log file for debugging, set `delete_unencrypted=false` in your configuration
  - **Location**: `linux_health_check.py:2199-2206`

### Changed
- GPG `delete_unencrypted` flag now properly respected for markdown reports
  - **Previous behavior**: Markdown report was always deleted after encryption (unconditional)
  - **New behavior**: Markdown report only deleted if `delete_unencrypted=true`
  - **Location**: `linux_health_check.py:2007-2009`
- Enhanced error handling for log file deletion with try/except block

### Security
- Prevents plain text vulnerability data from persisting on disk when GPG encryption is enabled
- Honors user's security intent when `delete_unencrypted=true` is configured
- Improves compliance with data protection regulations

## [1.2.3] - 2026-01-08

### Fixed
- Synchronized version references across all files (README.md, linux_health_check.py)
- Version badge and version field in README.md updated from 1.2.0 → 1.2.3

## [1.2.2] - 2026-01-08

### Fixed
- Removed `openspec/` directory from release archives
- Modified release workflow to exclude internal development documentation
- Archives now only contain user-facing files

## [1.2.1] - 2026-01-08

### Fixed
- Made test suite version-agnostic to prevent future CI/CD failures on version bumps
- Updated `test_suite.sh` to use regex patterns instead of hardcoded version numbers
- Added missing `health_check.cfg.example` to release assets

## [1.1.0] - 2026-01-06

### Added
- **Automated version checking** - Queries GitHub Releases API to detect newer versions
  - INFO-level notification when update is available
  - Includes wget download command and changelog link
  - 3-second timeout prevents hanging on slow networks
  - Silent failure on network errors (doesn't break health checks)
  - Can be disabled with `DISABLE_VERSION_CHECK=1` environment variable
  - Configurable timeout via `VERSION_CHECK_TIMEOUT` (default: 3 seconds)
- **New environment variables**:
  - `DISABLE_VERSION_CHECK` - Set to `1` to opt out of version checking
  - `VERSION_CHECK_TIMEOUT` - API request timeout in seconds

### Security
- Version check uses HTTPS with certificate validation
- No auto-update functionality (manual upgrade required for security)
- Rate limit: 60 requests/hour (GitHub API unauthenticated limit)
- All version check errors fail silently (logged at DEBUG level only)

### Changed
- Bumped version number from `1.0.0` to `1.1.0` (continuing to follow Semantic Versioning)
- Script now displays version `1.1.0` instead of `1.0.0`

## [1.0.0] - 2026-01-06

### Added

#### Core Features
- **35+ automated health and security checks** across 6 categories
- **Zero-dependency design** - Uses only Python 3.6+ standard library
- **Multi-format export** - Markdown (default), JSON, XML, plain text
- **GPG encryption support** - Protect sensitive health reports
- **SMTP email delivery** - Send reports via email with attachments
- **Ranked severity system** - Critical, High, Medium, Low, Info classifications

#### Security Auditing (8 checks)
- **Enhanced SSH authentication analysis** - Distinguishes between authentication methods:
  - HIGH severity: Password authentication enabled (security risk)
  - MEDIUM severity: RSA/DSA keys detected (weak key algorithms)
  - LOW severity: ed25519/ECDSA keys (strong key-based authentication)
  - INFO: SSH service disabled (acceptable state)
- SELinux/AppArmor enforcement status monitoring
- SSH root login configuration analysis (PermitRootLogin)
- Wheel group membership auditing (policy: should be empty)
- Login shell user validation (policy: only `locadmin` allowed)
- Sudoers permissions check (NOEXEC restrictions)
- Password aging policy compliance (PASS_MAX_DAYS ≤ 90)
- Failed login attempt monitoring

#### System Health Checks (7 checks)
- System uptime reporting (informational)
- Load average analysis with CPU-aware thresholds
- Memory usage monitoring (alerts >85%, critical >95%)
- Zombie process detection
- Failed systemd service detection
- Disk I/O error scanning via dmesg
- CPU temperature monitoring (warn >70°C, critical >80°C)

#### Storage & Filesystem (3 checks)
- Filesystem usage monitoring (85% threshold, 98% for `/mnt/backup`)
- Inode usage tracking (85% threshold)
- Filesystem error detection in kernel logs

#### Package Management (3 checks)
- Security update detection (distribution-aware: apt/dnf/zypper)
- Orphaned package identification (allows `veeamdeployment`, `veeamtransport`)
- Kernel version update availability

#### Networking Diagnostics (6 checks)
- Firewall status monitoring (firewalld/ufw/iptables)
- Listening port analysis (warns on SSH port 22 exposure)
- NTP synchronization status
- Network interface statistics
- Ethernet error/drop detection via ethtool
- DNS resolution testing

#### iSCSI Coverage (7 checks)
- iscsid service status monitoring (active/enabled state)
- Active iSCSI session enumeration
- Target connectivity and configuration validation
- lsscsi device enumeration
- dmesg iSCSI error pattern detection
- journalctl iSCSI log analysis (last hour)
- System log connection/authentication error scanning

#### Distribution Support
- **8 officially supported distributions** with comprehensive testing:
  - Debian 12 (Bookworm)
  - Debian 13 (Trixie)
  - Ubuntu 22.04 LTS (Jammy Jellyfish)
  - Ubuntu 24.04 LTS (Noble Numbat)
  - Rocky Linux 9
  - Rocky Linux 10 (Red Quartz - released June 2025)
  - openSUSE Leap 15
  - openSUSE Tumbleweed
- Auto-detection of package managers: `apt`, `dnf`, `yum`, `zypper`, `pacman`
- Auto-detection of firewalls: firewalld, ufw, iptables
- Auto-detection of security frameworks: SELinux, AppArmor
- Distribution-specific log paths and configuration handling

#### Testing Infrastructure
- **Comprehensive Docker-based test suite** (`test_all_distros.sh`)
- Automated multi-distribution testing across all 8 supported platforms
- JSON output validation and severity counting
- Test report generation with detailed results
- Graceful container cleanup and error handling

#### Documentation
- Comprehensive README with installation and usage instructions
- 9 professional badges (version, license, Python, distributions, test status)
- Detailed test reports for all supported distributions
- Troubleshooting guide for common issues
- Future enhancements roadmap (IMPROVEMENTS.md)

### Changed
- **Migrated to Semantic Versioning** from date-based versioning (YYYY.MM.DD → MAJOR.MINOR.PATCH)
- Clarified distinction between execution log (`health_report.txt`) and health report (`health_report_{hostname}.md`)
- Marked Arch Linux as **Experimental** (not officially tested or supported)

### Fixed
- Documentation confusion about execution log vs health check report filenames
- Rocky Linux 10 support (Docker image naming: `rockylinux/rockylinux:10`)

### Development
- GitHub Actions workflow for automated releases on version tags
- Semantic versioning validation in CI/CD pipeline
- Release artifact generation (script, archives, checksums)
- Automated changelog generation from git history

### Notes

This is the **first stable release** (1.0.0) of the Linux Health Check script, marking it as production-ready.

**Migration from v2026.01.05:**
- Previous release used date-based versioning (YYYY.MM.DD)
- All features from v2026.01.05 are included and unchanged
- Only versioning strategy has changed (no functional changes)

**Test Status:**
- All 8 officially supported distributions: ✅ PASSING
- Total automated checks: 35+
- Severity levels tested: Critical, High, Medium, Low, Info
- Export formats tested: Markdown, JSON, XML, text

**Known Limitations:**
- Arch Linux marked as experimental (not officially tested)
- Some checks require specific tools (e.g., smartctl for SMART status)
- SELinux checks limited to policy enforcement status (no deep analysis)

[Unreleased]: https://github.com/0xgruber/linux-health-checks/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/0xgruber/linux-health-checks/releases/tag/v1.3.0
[1.2.3]: https://github.com/0xgruber/linux-health-checks/releases/tag/v1.2.3
[1.2.2]: https://github.com/0xgruber/linux-health-checks/releases/tag/v1.2.2
[1.2.1]: https://github.com/0xgruber/linux-health-checks/releases/tag/v1.2.1
[1.1.0]: https://github.com/0xgruber/linux-health-checks/releases/tag/v1.1.0
[1.0.0]: https://github.com/0xgruber/linux-health-checks/releases/tag/v1.0.0
