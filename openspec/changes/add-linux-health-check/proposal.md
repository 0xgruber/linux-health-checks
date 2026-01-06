# Change: Add Linux Health Check System

## Why

Operations teams need automated, cross-distribution health and security auditing for Linux servers. Manual inspections are time-consuming, inconsistent across distributions, and don't provide severity-ranked findings or automated reporting workflows. A single Python script that detects distribution specifics, validates security posture, checks system health, and produces exportable reports (with optional encryption/email) addresses this gap for both interactive use and cron automation.

## What Changes

- Add comprehensive Linux health check script (`linux_health_check.py`) with 35+ distinct checks
- Implement cross-distribution support (RHEL/Rocky/CentOS, Debian/Ubuntu, SUSE, Arch) with automatic detection
- Add security auditing (8 checks): SELinux/AppArmor, SSH hardening, user/group policies, password aging, failed logins
- Add system health monitoring (7 checks): uptime, load, memory, zombie processes, failed services, disk I/O, CPU temperature
- Add storage checks (3 checks): filesystem usage, inode usage, filesystem errors
- Add package compliance (3 checks): security updates, orphaned packages, kernel updates
- Add networking diagnostics (6 checks): firewall, listening ports, NTP, interface stats, ethtool, DNS
- Add iSCSI coverage (7 checks): service status, sessions, targets, device enumeration, kernel/journal logs
- Implement severity ranking system (Critical/High/Medium/Low/Info)
- Add multi-format export: Markdown, JSON, XML, plain text
- Add GPG encryption support for sensitive reports
- Add SMTP email delivery with attachments
- Add comprehensive documentation (README.md) and project context (openspec/project.md)

## Impact

- **Affected specs**: `linux-health-check` (new capability)
- **Affected code**: 
  - New file: `linux_health_check.py` (~2500 lines)
  - Documentation: `README.md`, `openspec/project.md`
- **Dependencies**: Python 3.6+ stdlib only; optional GPG and SMTP relay
- **Breaking changes**: None (new capability)
- **Migration path**: N/A (new system)

## Success Criteria

- Script runs successfully on RHEL/Rocky/CentOS, Debian/Ubuntu, SUSE, and Arch distributions
- All 35+ checks execute and produce PASS/FAIL results with appropriate severity
- Export generates valid Markdown, JSON, XML, and text formats
- GPG encryption produces valid armored files when configured
- Email delivery successfully sends reports via SMTP when configured
- Cron automation executes without interactive prompts
- Documentation covers installation, configuration, usage, automation, and troubleshooting
