# Change Proposal: Add Version Check Notification

## Metadata
- **Change ID**: `add-version-check-notification`
- **Type**: Feature Enhancement
- **Priority**: Medium
- **Estimated Effort**: 2-4 hours
- **Version Target**: 1.1.0 (MINOR release - new backward-compatible feature)

## Summary
Add automatic version checking that queries GitHub Releases API to detect if a newer version is available. When a newer version is detected, include an informational notice in the generated health report with upgrade instructions. The script must NOT automatically update itself.

## Problem Statement
Currently, administrators running the Linux Health Check script have no way to know if a newer version with bug fixes, security patches, or new features is available. This leads to:

1. **Security risk**: Missing critical security patches
2. **Missed improvements**: Not benefiting from bug fixes and new checks
3. **Manual burden**: Administrators must manually check GitHub for updates
4. **Version drift**: Production environments running outdated versions unknowingly

## Proposed Solution
Implement a lightweight version checker that:

1. Reads the current `__version__` from the script
2. Queries GitHub Releases API (`https://api.github.com/repos/0xgruber/linux-health-checks/releases/latest`)
3. Compares semantic versions (current vs latest)
4. If newer version exists, adds an INFO-level issue to the report
5. Includes upgrade instructions and changelog link in the notification

### Key Design Decisions

**Network Failure Handling**: Version check failures (network timeout, API errors) are silently logged but do NOT fail the entire health check run or generate report issues.

**Performance**: Version check happens asynchronously during script initialization with a 3-second timeout to avoid delaying health checks.

**Privacy**: No telemetry or tracking - only fetches public release data from GitHub.

**No Auto-Update**: Explicitly NOT implementing auto-update functionality for security and stability reasons.

## Success Criteria
- [ ] Script successfully queries GitHub Releases API
- [ ] Semantic version comparison works correctly (1.0.0 < 1.1.0 < 2.0.0)
- [ ] Newer version notification appears in generated reports (all formats: Markdown, JSON, XML, text)
- [ ] Network failures are handled gracefully without disrupting health checks
- [ ] Version check has configurable timeout (default: 3 seconds)
- [ ] Can be disabled via environment variable: `DISABLE_VERSION_CHECK=1`
- [ ] Upgrade instructions are clear and actionable
- [ ] No external dependencies added (uses stdlib `urllib` only)

## User Experience

### Before (Current Behavior)
```
# Run health check
sudo ./linux_health_check.py

# Report generated with no version information
# User has no idea if updates are available
```

### After (With Version Check)
```
# Run health check
sudo ./linux_health_check.py

# If newer version available, report includes:
# ℹ️ [INFO] System: New version available: 1.2.0 (current: 1.1.0)
#   Details: A newer version of this script is available
#   Upgrade: wget https://github.com/0xgruber/linux-health-checks/releases/download/v1.2.0/linux_health_check.py
#   Changelog: https://github.com/0xgruber/linux-health-checks/releases/tag/v1.2.0
```

## Implementation Approach

### Phase 1: Version Comparison Logic
- Implement semantic version parsing and comparison
- Handle pre-release versions (ignore for now)
- Unit tests for version comparison

### Phase 2: GitHub API Integration
- Implement GitHub Releases API query with urllib
- Parse JSON response and extract latest version
- Handle network errors, timeouts, rate limiting
- Respect GitHub API rate limits (60 requests/hour unauthenticated)

### Phase 3: Report Integration
- Add version check as INFO-level issue when newer version found
- Format upgrade instructions for all export formats
- Test in Markdown, JSON, XML, and text outputs

### Phase 4: Configuration & Safety
- Add `DISABLE_VERSION_CHECK` environment variable
- Add configurable timeout (default: 3 seconds)
- Ensure silent failure on network/API errors
- Log version check results for troubleshooting

## Non-Goals (Explicit Exclusions)
- ❌ **Auto-update functionality**: Users must manually upgrade
- ❌ **Version check frequency limits**: Checks on every run (lightweight, <1s overhead)
- ❌ **Pre-release/beta version notifications**: Only stable releases
- ❌ **Offline mode detection**: Simply fails silently if no network
- ❌ **Caching version check results**: Always fresh check
- ❌ **GitHub authentication**: Uses public API only

## Security Considerations

### Threat Model
1. **MITM attacks**: GitHub API uses HTTPS, certificate validation enforced
2. **API response manipulation**: Only uses version number and release URL from API
3. **Malicious upgrade instructions**: URLs always point to official GitHub releases
4. **Information disclosure**: No data sent to GitHub (only public API read)

### Mitigations
- HTTPS enforced for GitHub API
- Certificate validation enabled (default in urllib)
- Timeout prevents hanging on network issues
- No execution of remote code
- No credentials or tokens required
- Can be completely disabled via environment variable

## Testing Strategy

### Unit Tests
- Version comparison: `1.0.0 < 1.1.0`, `1.9.0 < 2.0.0`, `2.0.0-alpha < 2.0.0`
- API response parsing with mock responses
- Error handling for network failures

### Integration Tests
- Test with real GitHub API (rate limit aware)
- Test with version check disabled
- Test with network timeout
- Test report generation with version notification

### Manual Testing
1. Run script with current version (should show no notification)
2. Temporarily lower `__version__` to test notification
3. Test with network disconnected (should fail gracefully)
4. Test with `DISABLE_VERSION_CHECK=1` (should skip check)
5. Verify all export formats include notification

## Rollout Plan

### Version 1.1.0 Release
- Implement version check feature
- Update CHANGELOG.md
- Update README.md with version check documentation
- Release as MINOR version (backward-compatible feature)

### Documentation Updates
- README: Add "Version Update Notifications" section
- IMPROVEMENTS.md: Mark feature #6 as completed
- CONTRIBUTING.md: No changes needed (follows existing process)

## Alternatives Considered

### Alternative 1: Cron-based version checker
**Rejected**: Adds complexity, requires separate script

### Alternative 2: Check once per day (caching)
**Rejected**: Adds complexity for minimal benefit, check is fast (<1s)

### Alternative 3: Email notification separate from report
**Rejected**: Consolidating in report is simpler, already has email delivery

### Alternative 4: Check on script exit
**Rejected**: Users may not see exit messages in cron/automated runs

## Dependencies
- None (uses Python stdlib `urllib.request` for HTTP)
- Requires network connectivity to GitHub (gracefully degrades)

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| GitHub API rate limiting | Version check fails | Medium | Silent failure, users can disable |
| Network latency | Slow script startup | Low | 3-second timeout, async check |
| Breaking API changes | Version check fails | Low | Silent failure, defensive parsing |
| False positives (incorrect version comparison) | Confusing notifications | Low | Comprehensive unit tests |

## Open Questions
- ~~Should we cache version check results?~~ **Decision: No, always check**
- ~~Should we support checking for pre-release versions?~~ **Decision: No, stable only**
- ~~Should we add a `--check-version` CLI flag?~~ **Decision: Defer to future enhancement**

## Approval
This proposal requires approval before implementation begins.

**Approved by**: _Pending_  
**Approval date**: _Pending_
