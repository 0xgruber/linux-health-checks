# Project Context

## Purpose
Linux Health Checks delivers a single Python utility (`linux_health_check.py`) that performs an end-to-end health and security audit across common Linux distributions. It inspects OS configuration, authentication controls, package/update status, storage capacity, networking posture, and iSCSI connectivity, ranks issues by severity, and exports/email reports for operators or automated cron jobs.

## Tech Stack
- Python 3.8+ using only the standard library (logging, subprocess, json, xml, email, etc.)
- Native Linux tooling (`systemctl`, `ip`, `ss`, `df`, `grep`, `dnf|yum|apt|zypper|pacman`, `ethtool`, `iscsiadm`, `journalctl`, `nslookup`, `sensors`, etc.)
- Optional GPG (`gnupg`) for report encryption and SMTP relay for outbound email delivery

## Project Conventions

### Code Style
- Follow Python conventions (PEP 8-ish) with descriptive function names such as `check_security_framework` or `check_filesystem_usage`.
- Centralized logging via `log(...)` writes to both stdout and `/root/health_report.txt` (or `/tmp` for non-root).
- Severity labels (`Critical`, `High`, `Medium`, `Low`, `Info`) control ranking and output sections.
- Configuration constants live at the top of the script for easy environment overrides (email, GPG, thresholds).

### Architecture Patterns
- Modular procedural design: each subsystem (security, system health, storage, packages, networking, iSCSI) has its own `check_*` function.
- Shared helpers (`run_command`, `run_and_filter`, `grep_output`, etc.) replace shell pipelines and enforce safe command execution.
- Results accumulate in a global `issues` list which drives reporting/export logic.
- Automated export pipeline writes Markdown and optional JSON/XML/Text artifacts, then optionally encrypts and emails them.

### Testing Strategy
- Primary validation is via running the script on representative hosts (different distros, root vs non-root) and reviewing the generated log/report.
- Each check logs PASS/FAIL and adds severity-tagged issues that can be inspected to confirm rule accuracy.
- Cron-based runs capture regressions by comparing historical exports; no formal unit tests yet.

### Git Workflow
- Keep changes focused (e.g., new check, config tweak, or README/docs update) and describe the reason in commit messages.
- Default branch reflects the runnable script; feature branches may be used for larger rewrites before merging.
- Avoid rewriting history; prefer additive commits that preserve previous audit behavior for traceability.

## Domain Context
- Targets enterprise Linux servers that must meet strict security baselines (e.g., SSH disabled, SELinux/AppArmor enforcing, empty `wheel` group).
- Operators rely on severity-ranked findings and auto-emailed, optionally GPG-encrypted reports for compliance evidence.
- Storage and iSCSI checks focus on ensuring backup mounts and block devices remain healthy.

## Important Constraints
- Script must run without third-party Python dependencies (standard library only) and degrade gracefully when OS utilities are missing.
- Must support multiple distributions by auto-detecting package managers, firewalls, and log paths.
- Intended to run as root for maximum visibility but must not crash when executed as non-root.
- Email/GPG behavior should be configurable to avoid leaking sensitive reports.

## External Dependencies
- SMTP relay reachable from the host for sending reports (`EMAIL_*` + `SMTP_*` settings).
- GPG key material (if `GPG_ENABLED`) to encrypt report exports.
- OS-level utilities listed in the README; absence reduces coverage but should not abort execution.
