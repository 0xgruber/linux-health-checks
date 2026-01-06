# Tasks for add-version-check-notification

## Overview
Implementation tasks for Feature #6: Automated Update Checking. This change adds version checking that queries GitHub Releases API to detect newer versions and includes upgrade notifications in health reports.

**Target Version**: 1.1.0 (MINOR release)

---

## Phase 1: Version Comparison Logic ⏳

### Task 1.1: Implement `parse_semantic_version()` function
- [ ] Create function to parse version strings (e.g., "1.2.3" or "v1.2.3")
- [ ] Strip 'v' prefix if present
- [ ] Split on '.' and convert to tuple of integers
- [ ] Handle invalid formats gracefully (return None or raise ValueError)
- [ ] Add docstring with examples

**Acceptance Criteria**:
- Parses "1.2.3" → (1, 2, 3)
- Parses "v1.2.3" → (1, 2, 3)
- Handles "2.0.0" → (2, 0, 0)
- Returns None or raises error for invalid input

### Task 1.2: Implement `compare_versions()` function
- [ ] Create function to compare two version tuples
- [ ] Return -1 if current < latest (update available)
- [ ] Return 0 if current == latest (up to date)
- [ ] Return 1 if current > latest (dev/future version)
- [ ] Use Python tuple comparison for MAJOR.MINOR.PATCH

**Acceptance Criteria**:
- compare_versions((1, 0, 0), (1, 1, 0)) → -1
- compare_versions((1, 1, 0), (1, 1, 0)) → 0
- compare_versions((1, 2, 0), (1, 1, 0)) → 1

### Task 1.3: Add unit tests for version comparison
- [ ] Test parse_semantic_version with valid inputs
- [ ] Test parse_semantic_version with invalid inputs
- [ ] Test compare_versions with various version combinations
- [ ] Test edge cases (0.0.0, large version numbers)
- [ ] Document test cases in comments

**Acceptance Criteria**:
- All tests pass
- Edge cases covered
- 100% code coverage for these functions

---

## Phase 2: GitHub API Integration 🔌

### Task 2.1: Implement `check_github_releases()` function
- [ ] Create function to fetch latest release from GitHub API
- [ ] Use `urllib.request.Request` (stdlib only, no requests library)
- [ ] Set User-Agent header to 'linux-health-check/VERSION'
- [ ] Return tuple: (latest_version, release_url, changelog_url)
- [ ] Return (None, None, None) on any error

**Acceptance Criteria**:
- Successfully fetches from: https://api.github.com/repos/0xgruber/linux-health-checks/releases/latest
- Parses JSON response correctly
- Returns version string without 'v' prefix
- Returns valid URLs

### Task 2.2: Implement timeout handling
- [ ] Add VERSION_CHECK_TIMEOUT constant (default: 3 seconds)
- [ ] Read from environment variable: VERSION_CHECK_TIMEOUT
- [ ] Pass timeout parameter to urllib.request.urlopen()
- [ ] Log timeout errors at debug level

**Acceptance Criteria**:
- Request times out after 3 seconds by default
- Timeout is configurable via environment variable
- No error messages shown to user on timeout

### Task 2.3: Handle API errors gracefully
- [ ] Catch URLError (network failures)
- [ ] Catch HTTPError (404, 403, etc.)
- [ ] Catch JSONDecodeError (invalid response)
- [ ] Log all errors at debug level only
- [ ] Return (None, None, None) for all error cases

**Acceptance Criteria**:
- Network disconnected → silent failure, no error shown
- Invalid JSON → silent failure, no error shown
- HTTP 403/404 → silent failure, no error shown
- Health checks continue normally on API failure

### Task 2.4: Handle rate limiting
- [ ] Detect HTTP 403 with rate limit headers
- [ ] Log warning about rate limiting at debug level
- [ ] Document rate limits in README (60 req/hour unauthenticated)
- [ ] Suggest disabling checks if rate limited frequently

**Acceptance Criteria**:
- Rate limit errors logged but not shown to user
- README documents rate limits
- DISABLE_VERSION_CHECK mentioned as workaround

### Task 2.5: Test with real GitHub API
- [ ] Manual test: fetch latest release
- [ ] Verify response parsing
- [ ] Test with network disconnected (simulate failure)
- [ ] Test with invalid repository (simulate 404)
- [ ] Verify timeout works correctly

**Acceptance Criteria**:
- Successfully fetches v1.0.0 (or latest)
- All error cases handled gracefully
- No crashes or exceptions propagated

---

## Phase 3: Report Integration 📋

### Task 3.1: Create `check_version_update()` function
- [ ] Call check_github_releases() to get latest version
- [ ] Compare with current __version__ using version comparison logic
- [ ] Return empty list if no update available
- [ ] Return empty list if check failed (silent failure)
- [ ] Return issue dict if newer version found

**Acceptance Criteria**:
- Returns [] when up to date
- Returns [] when check fails
- Returns [issue] when update available

### Task 3.2: Format INFO-level issue notification
- [ ] Set severity to "INFO"
- [ ] Description: "New version available: X.Y.Z (current: A.B.C)"
- [ ] Context includes:
  - Brief explanation
  - wget command to download new version
  - Link to changelog/release notes
- [ ] Follow existing issue format conventions

**Acceptance Criteria**:
```python
{
    "severity": "INFO",
    "description": "New version available: 1.1.0 (current: 1.0.0)",
    "context": "A newer version of this script is available\n"
               "Upgrade: wget https://github.com/.../releases/download/v1.1.0/linux_health_check.py\n"
               "Changelog: https://github.com/.../releases/tag/v1.1.0"
}
```

### Task 3.3: Add to check execution flow
- [ ] Find appropriate location in main execution (after initialization)
- [ ] Call check_version_update() and extend issues list
- [ ] Add logging: "Checking for script updates..." (INFO level)
- [ ] Ensure it runs before other checks (shows at top of report)

**Location**: Around line 900-1000 in linux_health_check.py

**Acceptance Criteria**:
- Version check runs automatically on every execution
- Appears near top of health check report
- Does not delay other checks significantly

### Task 3.4: Test in Markdown export format
- [ ] Run script with newer version mocked
- [ ] Verify INFO issue appears in Markdown report
- [ ] Verify formatting is correct
- [ ] Verify links are clickable

**Acceptance Criteria**:
- Shows as INFO-level issue in Markdown
- Upgrade instructions clearly visible
- Links formatted correctly

### Task 3.5: Test in JSON export format
- [ ] Run with EXPORT_FORMAT=json
- [ ] Verify issue appears in JSON output
- [ ] Verify JSON structure matches other issues
- [ ] Verify all fields present (severity, description, context)

**Acceptance Criteria**:
- Valid JSON output
- Issue includes all required fields
- Can be parsed by external tools

### Task 3.6: Test in XML export format
- [ ] Run with EXPORT_FORMAT=xml
- [ ] Verify issue appears in XML output
- [ ] Verify XML is valid and well-formed
- [ ] Verify special characters are escaped properly

**Acceptance Criteria**:
- Valid XML output
- Issue properly formatted
- URLs don't break XML structure

### Task 3.7: Test in text export format
- [ ] Run with EXPORT_FORMAT=text
- [ ] Verify issue appears in plain text report
- [ ] Verify formatting is readable
- [ ] Verify line wrapping is appropriate

**Acceptance Criteria**:
- Readable plain text output
- Upgrade instructions clear
- URLs on separate lines

---

## Phase 4: Configuration & Safety ⚙️

### Task 4.1: Add DISABLE_VERSION_CHECK environment variable
- [ ] Check for DISABLE_VERSION_CHECK=1 in check_github_releases()
- [ ] Return (None, None, None) immediately if set
- [ ] Document in README usage section
- [ ] Add to help text or configuration section

**Acceptance Criteria**:
- DISABLE_VERSION_CHECK=1 → no API call made
- DISABLE_VERSION_CHECK=0 → API call proceeds normally
- Documented in README

### Task 4.2: Add configuration constants
- [ ] Add VERSION_CHECK_TIMEOUT constant (default: 3)
- [ ] Add GITHUB_REPO constant ('0xgruber/linux-health-checks')
- [ ] Add constants near top of file with other configuration
- [ ] Document constants in comments

**Acceptance Criteria**:
```python
# Version checking configuration
VERSION_CHECK_TIMEOUT = int(os.getenv('VERSION_CHECK_TIMEOUT', '3'))
GITHUB_REPO = '0xgruber/linux-health-checks'
```

### Task 4.3: Add debug logging for version checks
- [ ] Log "Checking for script updates..." at INFO level (user-visible)
- [ ] Log "Version check result: up-to-date/update-available/failed" at DEBUG level
- [ ] Log API errors at DEBUG level with exception details
- [ ] Log rate limiting at DEBUG level

**Acceptance Criteria**:
- Normal execution: only INFO message shown
- Debug mode: detailed logs available
- No sensitive information logged

### Task 4.4: Ensure silent failure on all errors
- [ ] Review all error paths in check_github_releases()
- [ ] Verify no exceptions propagate to caller
- [ ] Verify health checks continue on version check failure
- [ ] Test with various error conditions

**Acceptance Criteria**:
- Network failure → silent, checks continue
- API error → silent, checks continue
- Timeout → silent, checks continue
- Invalid JSON → silent, checks continue

### Task 4.5: Update README.md with version check documentation
- [ ] Add "Automated Update Checking" section
- [ ] Explain what version checking does
- [ ] Document DISABLE_VERSION_CHECK environment variable
- [ ] Document VERSION_CHECK_TIMEOUT configuration
- [ ] Mention rate limits (60 requests/hour)
- [ ] Note: no auto-update, manual upgrade required

**Acceptance Criteria**:
- Clear explanation of feature
- All configuration options documented
- Examples provided

### Task 4.6: Update CHANGELOG.md
- [ ] Add entry for version 1.1.0
- [ ] Document new feature: "Automated update checking"
- [ ] List new environment variables
- [ ] Follow Keep a Changelog format

**Acceptance Criteria**:
```markdown
## [1.1.0] - YYYY-MM-DD
### Added
- Automated update checking against GitHub Releases API
- INFO-level notification when newer version is available
- DISABLE_VERSION_CHECK environment variable to opt-out
- VERSION_CHECK_TIMEOUT configuration (default: 3 seconds)

### Security
- Version check uses 3-second timeout to prevent hanging
- Silent failure on network errors (does not break health checks)
- No auto-update functionality (manual upgrade required)
```

---

## Phase 5: Testing & Validation ✅

### Task 5.1: Run OpenSpec validation
- [ ] Run: `openspec validate add-version-check-notification --strict`
- [ ] Fix any validation errors
- [ ] Ensure proposal, tasks, design all valid
- [ ] Ensure no conflicting changes

**Acceptance Criteria**:
- `openspec validate` passes with no errors
- All required OpenSpec files present
- Proposal approved (if approval mechanism exists)

### Task 5.2: Manual test - newer version available
- [ ] Temporarily change __version__ to "0.9.0"
- [ ] Run script: `sudo ./linux_health_check.py`
- [ ] Verify INFO notification appears
- [ ] Verify upgrade instructions shown
- [ ] Verify URLs are correct
- [ ] Revert __version__ change

**Acceptance Criteria**:
- INFO issue shows: "New version available: 1.0.0 (current: 0.9.0)"
- wget command shows correct download URL
- Changelog link shows correct release URL

### Task 5.3: Manual test - up to date
- [ ] Run script with current version: `sudo ./linux_health_check.py`
- [ ] Verify NO version notification appears
- [ ] Verify all other checks run normally

**Acceptance Criteria**:
- No version notification in report
- Script runs normally

### Task 5.4: Manual test - network disconnected
- [ ] Disconnect network or block github.com
- [ ] Run script: `sudo ./linux_health_check.py`
- [ ] Verify no error messages shown
- [ ] Verify health checks complete successfully
- [ ] Check debug logs (if enabled) show network error

**Acceptance Criteria**:
- No error messages to user
- Script completes successfully
- Health checks run normally

### Task 5.5: Manual test - DISABLE_VERSION_CHECK=1
- [ ] Run: `DISABLE_VERSION_CHECK=1 sudo ./linux_health_check.py`
- [ ] Verify no API call made (check logs or network traffic)
- [ ] Verify no version notification
- [ ] Verify script runs normally

**Acceptance Criteria**:
- No GitHub API call made
- No version notification
- Script runs faster (no network delay)

### Task 5.6: Test all export formats
- [ ] Test Markdown (default)
- [ ] Test JSON: `EXPORT_FORMAT=json sudo ./linux_health_check.py`
- [ ] Test XML: `EXPORT_FORMAT=xml sudo ./linux_health_check.py`
- [ ] Test text: `EXPORT_FORMAT=text sudo ./linux_health_check.py`
- [ ] Verify version notification appears in all formats

**Acceptance Criteria**:
- Version notification in Markdown report
- Version notification in JSON output
- Version notification in XML output
- Version notification in text output

### Task 5.7: Test on multiple distributions
- [ ] Test on Debian 12
- [ ] Test on Debian 13
- [ ] Test on Ubuntu 22.04
- [ ] Test on Ubuntu 24.04
- [ ] Test on Rocky Linux 9
- [ ] Test on Rocky Linux 10
- [ ] Test on openSUSE Leap
- [ ] Test on openSUSE Tumbleweed

**Acceptance Criteria**:
- Works on all 8 supported distributions
- No distribution-specific errors
- urllib.request available on all platforms

### Task 5.8: Performance test
- [ ] Measure script execution time without version check
- [ ] Measure script execution time with version check
- [ ] Verify version check adds < 5 seconds to execution time
- [ ] Test with slow network (should timeout at 3 seconds)

**Acceptance Criteria**:
- Version check adds minimal overhead (< 5 seconds)
- Timeout prevents hanging on slow networks
- Overall script performance acceptable

---

## Phase 6: Pull Request & Release 🚀

### Task 6.1: Review code for quality
- [ ] Run pylint or flake8 (if used)
- [ ] Check for PEP 8 compliance
- [ ] Review error handling
- [ ] Review logging statements
- [ ] Review code comments and docstrings

**Acceptance Criteria**:
- Code follows project style guidelines
- No linter warnings
- Well-commented and documented

### Task 6.2: Update IMPROVEMENTS.md
- [ ] Mark Feature #6 as "✅ Implemented in v1.1.0"
- [ ] Update feature status from "Planned" to "Completed"
- [ ] Add implementation date

**Acceptance Criteria**:
- Feature #6 marked as completed
- Version 1.1.0 referenced

### Task 6.3: Commit all changes
- [ ] Stage all modified files
- [ ] Create commit with message: "feat: add automated version checking (1.1.0)"
- [ ] Include detailed commit body with summary
- [ ] Push to feature branch

**Commit Message**:
```
feat: add automated version checking (1.1.0)

Implements Feature #6 from IMPROVEMENTS.md: Automated Update Checking

Changes:
- Add version comparison logic (parse_semantic_version, compare_versions)
- Add GitHub Releases API integration (check_github_releases)
- Add version check to health report (INFO-level notification)
- Add DISABLE_VERSION_CHECK environment variable
- Add VERSION_CHECK_TIMEOUT configuration (default: 3s)
- Update README.md with version check documentation
- Update CHANGELOG.md for v1.1.0

Features:
- Checks GitHub Releases API for newer versions
- Shows INFO-level notification with upgrade instructions
- Silent failure on network errors (does not break health checks)
- 3-second timeout prevents hanging
- Can be disabled with DISABLE_VERSION_CHECK=1
- No auto-update functionality (manual upgrade only)

Testing:
- Tested on all 8 supported distributions
- Tested all export formats (Markdown, JSON, XML, text)
- Tested error conditions (network failure, timeout, rate limit)
- Tested with version check disabled

OpenSpec: openspec/changes/add-version-check-notification/
```

### Task 6.4: Create pull request
- [ ] Push feature branch to GitHub
- [ ] Create PR: feature/version-check-notification → main
- [ ] Write PR description with:
  - Summary of changes
  - Link to OpenSpec proposal
  - Testing performed
  - Screenshots/examples
- [ ] Request review from maintainer

**PR Title**: "feat: Add automated version checking (1.1.0)"

**PR Description Template**:
```markdown
## Summary
Implements Feature #6 from IMPROVEMENTS.md: Automated Update Checking

Adds version checking that queries GitHub Releases API to detect newer versions and includes upgrade notifications in health reports.

## Changes
- ✅ Version comparison logic
- ✅ GitHub Releases API integration
- ✅ INFO-level notification in health reports
- ✅ DISABLE_VERSION_CHECK environment variable
- ✅ VERSION_CHECK_TIMEOUT configuration
- ✅ Documentation updates

## OpenSpec Proposal
See: `openspec/changes/add-version-check-notification/proposal.md`

## Testing
- ✅ Tested on all 8 supported distributions
- ✅ Tested all export formats (Markdown, JSON, XML, text)
- ✅ Tested error conditions (network failure, timeout)
- ✅ Tested with version check disabled

## Example Output
[Include screenshot or example of INFO notification]

## Breaking Changes
None - this is a MINOR version bump (1.0.0 → 1.1.0)

## Checklist
- [x] OpenSpec proposal approved
- [x] All tests passing
- [x] Documentation updated
- [x] CHANGELOG.md updated
- [x] Tested on all supported distributions
```

### Task 6.5: Address review feedback
- [ ] Respond to review comments
- [ ] Make requested changes
- [ ] Push updates to feature branch
- [ ] Re-request review if needed

**Acceptance Criteria**:
- All review comments addressed
- Maintainer approves PR

### Task 6.6: Merge to main and tag release
- [ ] Merge PR to main branch
- [ ] Tag commit as v1.1.0: `git tag -a v1.1.0 -m "Version 1.1.0"`
- [ ] Push tag: `git push origin v1.1.0`
- [ ] Verify GitHub Actions creates release
- [ ] Verify release notes generated

**Acceptance Criteria**:
- PR merged successfully
- Tag v1.1.0 created
- GitHub Release v1.1.0 published
- Release includes linux_health_check.py asset

### Task 6.7: Verify release
- [ ] Download linux_health_check.py from GitHub Release
- [ ] Verify __version__ == "1.1.0"
- [ ] Run script and verify version check works
- [ ] Check release notes are accurate

**Acceptance Criteria**:
- Release v1.1.0 available on GitHub
- Script downloads and runs correctly
- Version check feature works as expected

---

## Post-Release Tasks 📝

### Task 7.1: Mark OpenSpec change as complete
- [ ] Run: `openspec complete add-version-check-notification`
- [ ] Archive proposal if using archive directory
- [ ] Update openspec/changes/ status

**Acceptance Criteria**:
- OpenSpec change marked as completed
- Proposal archived or marked complete

### Task 7.2: Monitor for issues
- [ ] Monitor GitHub Issues for bug reports
- [ ] Monitor for rate limiting complaints
- [ ] Monitor for timeout issues
- [ ] Be ready to hotfix if critical bug found

**Acceptance Criteria**:
- No critical bugs reported in first week
- Feature works as expected in production

### Task 7.3: Plan future enhancements (optional)
- [ ] Consider caching version check results
- [ ] Consider adding version check interval (daily/weekly)
- [ ] Consider adding GitHub authentication for higher rate limits
- [ ] Add to IMPROVEMENTS.md if needed

**Acceptance Criteria**:
- Future enhancements documented for consideration

---

## Summary

**Total Tasks**: 40+
**Estimated Effort**: 4-8 hours
**Target Version**: 1.1.0 (MINOR release)
**Priority**: Medium

**Key Milestones**:
1. ✅ Version comparison logic implemented and tested
2. ✅ GitHub API integration working
3. ✅ Report integration complete in all formats
4. ✅ Configuration and safety measures in place
5. ✅ All tests passing
6. ✅ PR merged and v1.1.0 released

**Success Criteria**:
- Version checking works reliably
- Silent failure on all errors
- No performance impact
- Works on all 8 distributions
- Documentation complete
- Users can upgrade smoothly
