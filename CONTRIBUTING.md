# Contributing to Linux Health Checks

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Table of Contents
- [Pull Request Conventions](#pull-request-conventions)
- [Versioning Strategy](#versioning-strategy)
- [Release Process](#release-process)
- [Development Workflow](#development-workflow)
- [Testing Requirements](#testing-requirements)
- [Code Style](#code-style)

---

## Pull Request Conventions

### Chore PRs (Skip Heavy Tests)

If your change only updates documentation, fixes typos, or performs other non-functional chores, please prefix your pull request title with `chore:` (case-insensitive). Pull requests with titles starting with `chore:` will skip the repository's heavy CI jobs, while still running a lightweight validation check required by branch protection.

**Examples:**
- `chore: fix typo in README`
- `chore: update CONTRIBUTING guide`
- `Chore: formatting cleanup`

**Note:** This convention helps preserve CI resources while maintaining branch protection requirements. Non-chore PRs will run the full test suite across all supported distributions.

---

## Versioning Strategy

This project follows **[Semantic Versioning 2.0.0](https://semver.org/)** (SemVer).

### Version Format

```
MAJOR.MINOR.PATCH
```

**Examples:** `1.0.0`, `1.2.3`, `2.0.0`

### When to Bump Version Numbers

#### MAJOR Version (X.0.0) - Breaking Changes
Increment when making incompatible changes that break backward compatibility:

- **CLI interface changes** - Removing or renaming command-line arguments
- **Output format changes** - Breaking changes to Markdown/JSON/XML structure
- **Configuration file format** - Incompatible config changes (when implemented)
- **Dropping distribution support** - Removing officially supported distributions
- **Python version requirement increase** - Requiring newer Python (e.g., 3.8 → 3.10)
- **Check behavior changes** - Modifying check logic in incompatible ways

**Example:** Removing the `-o`/`--output` flag or changing JSON output structure

#### MINOR Version (1.X.0) - New Features (Backward-Compatible)
Increment when adding new functionality that doesn't break existing usage:

- **New health checks** - Adding new security/system/network checks
- **New distribution support** - Adding new tested Linux distributions
- **New export formats** - Adding new output formats (e.g., CSV, HTML)
- **New CLI options** - Adding new command-line flags (backward-compatible)
- **Configuration features** - New config file support (backward-compatible)
- **Performance improvements** - Significant speed improvements
- **Feature enhancements** - Expanding existing check capabilities

**Example:** Adding a new SSH key strength check or supporting Fedora

#### PATCH Version (1.0.X) - Bug Fixes & Maintenance
Increment for backward-compatible bug fixes and minor updates:

- **Bug fixes** - Fixing broken checks or incorrect logic
- **Security patches** - Fixing security vulnerabilities
- **Documentation updates** - README, comments, docstrings
- **Error handling improvements** - Better error messages
- **Typo corrections** - Fixing spelling/grammar
- **Dependency updates** - Updating library versions (if any added)
- **Test improvements** - Enhancing test coverage
- **Refactoring** - Internal code improvements (no behavior change)

**Example:** Fixing a false positive in the memory usage check

---

## Release Process

### Overview

Releases are **tag-driven** and **semi-automated**:
1. Developer manually updates version and changelog
2. Developer creates and pushes git tag
3. GitHub Actions automatically builds and publishes release

### Step-by-Step Release Process

#### 1. Determine Next Version Number

Based on changes since last release:
```bash
# View commits since last release
git log v1.0.0..HEAD --oneline

# Analyze changes and decide: MAJOR.MINOR.PATCH?
```

**Decision tree:**
- Breaking changes? → Bump MAJOR
- New features? → Bump MINOR  
- Only bug fixes? → Bump PATCH

**Example:** If current version is `1.2.3`:
- Breaking change: → `2.0.0`
- New feature: → `1.3.0`
- Bug fix: → `1.2.4`

#### 2. Update Version in Code

**File:** `linux_health_check.py`

Update the `__version__` constant (line ~9):

```python
__version__ = "1.3.0"  # Update this line
```

#### 3. Update CHANGELOG.md

Move items from `[Unreleased]` to new version section:

```markdown
## [Unreleased]

## [1.3.0] - 2026-01-15

### Added
- New AppArmor profile violation check
- Support for Fedora 40

### Fixed
- False positive in zombie process detection

[Unreleased]: https://github.com/0xgruber/linux-health-checks/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/0xgruber/linux-health-checks/releases/tag/v1.3.0
[1.2.3]: https://github.com/0xgruber/linux-health-checks/releases/tag/v1.2.3
```

#### 4. Commit Version Bump

```bash
# Stage changes
git add linux_health_check.py CHANGELOG.md

# Commit with conventional message
git commit -m "chore: bump version to 1.3.0"
```

#### 5. Create Git Tag

Create **annotated tag** with release notes:

```bash
git tag -a v1.3.0 -m "Release 1.3.0

New Features:
- AppArmor profile violation detection
- Fedora 40 support

Bug Fixes:
- Fixed zombie process false positives

See CHANGELOG.md for full details."
```

**Tag naming convention:** `v{MAJOR}.{MINOR}.{PATCH}` (e.g., `v1.3.0`)

#### 6. Push to GitHub

```bash
# Push commit
git push origin main

# Push tag (this triggers GitHub Actions)
git push origin v1.3.0
```

#### 7. Verify Automated Release

GitHub Actions will automatically:
1. ✅ Extract version from tag
2. ✅ Verify `__version__` matches tag (warns if mismatch)
3. ✅ Run linting checks
4. ✅ Generate release archives (tar.gz, zip)
5. ✅ Calculate SHA256 checksums
6. ✅ Create GitHub release with artifacts
7. ✅ Mark as "Latest Release"

**Monitor:** https://github.com/0xgruber/linux-health-checks/actions

**Verify:** https://github.com/0xgruber/linux-health-checks/releases

#### 8. Announce Release (Optional)

- Update project documentation if needed
- Announce in relevant channels
- Update deployment scripts/documentation

---

## Development Workflow

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/0xgruber/linux-health-checks.git
cd linux-health-checks

# Verify Python version
python3 --version  # Should be 3.8+

# Run script locally
sudo ./linux_health_check.py

# Run tests
python3 test_health_check.py
./test_all_distros.sh  # Requires Docker
```

### Branch Strategy

- **main** - Stable, production-ready code
- **feature/** - New features (e.g., `feature/apparmor-check`)
- **fix/** - Bug fixes (e.g., `fix/memory-false-positive`)

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring (no behavior change)
- `chore:` - Maintenance tasks (version bumps, dependencies)

**Examples:**
```bash
git commit -m "feat: add AppArmor profile violation check"
git commit -m "fix: correct memory usage calculation for containers"
git commit -m "docs: update README with Fedora support"
git commit -m "chore: bump version to 1.3.0"
```

---

## Testing Requirements

### Before Submitting Pull Request

1. **Run unit tests:**
   ```bash
   python3 test_health_check.py
   ```

2. **Test on multiple distributions:**
   ```bash
   ./test_all_distros.sh
   ```

3. **Verify export formats:**
   ```bash
   EXPORT_FORMAT=json ./linux_health_check.py
   EXPORT_FORMAT=xml ./linux_health_check.py
   EXPORT_FORMAT=txt ./linux_health_check.py
   ```

4. **Check for Python errors:**
   ```bash
   python3 -m py_compile linux_health_check.py
   ```

### Test Coverage Guidelines

New checks should include:
- ✅ Error handling for missing tools/files
- ✅ Distribution-specific logic (if applicable)
- ✅ Proper severity classification
- ✅ Clear issue descriptions and context
- ✅ Unit test in `test_health_check.py`

---

## Code Style

### Python Style Guidelines

- **PEP 8** compliance (mostly)
- **Type hints** encouraged but not required
- **Docstrings** for functions and classes
- **Comments** for complex logic
- **Standard library only** - no external dependencies

### Code Organization

```python
# 1. Shebang and docstring
#!/usr/bin/env python3
"""Module docstring"""

__version__ = "1.0.0"

# 2. Imports (grouped: stdlib, third-party, local)
import os
import sys

# 3. Constants
OUTPUT_DIR = "/root"

# 4. Helper functions
def helper_function():
    pass

# 5. Check functions
def check_ssh():
    pass

# 6. Main execution
if __name__ == "__main__":
    main()
```

### Check Function Template

```python
def check_example():
    """
    Brief description of what this check does.
    
    Returns:
        list: Issues found (dicts with severity, description, etc.)
    """
    issues = []
    
    try:
        # Check logic here
        if condition:
            issues.append({
                "severity": "HIGH",
                "description": "Issue found",
                "context": "Additional details"
            })
    except Exception as e:
        log_error(f"Check failed: {e}")
    
    return issues
```

---

## Questions?

- **Issues:** https://github.com/0xgruber/linux-health-checks/issues
- **Discussions:** https://github.com/0xgruber/linux-health-checks/discussions
- **Email:** aaron@gizmobear.io

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
