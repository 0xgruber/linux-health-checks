# Version Checking Specification

## ADDED Requirements

### Requirement: Semantic Version Parsing
The system SHALL parse semantic version strings in format "X.Y.Z" or "vX.Y.Z" into a tuple of integers (major, minor, patch) and return None for invalid formats.

#### Scenario: Valid version without prefix
- **WHEN** parse_semantic_version("1.2.3") is called
- **THEN** function returns tuple (1, 2, 3)

#### Scenario: Valid version with v prefix
- **WHEN** parse_semantic_version("v1.2.3") is called
- **THEN** function returns tuple (1, 2, 3)

#### Scenario: Zero version
- **WHEN** parse_semantic_version("0.0.0") is called
- **THEN** function returns tuple (0, 0, 0)

#### Scenario: Invalid version format
- **WHEN** parse_semantic_version("invalid") is called
- **THEN** function returns None

#### Scenario: Incomplete version
- **WHEN** parse_semantic_version("1.2") is called
- **THEN** function returns None (missing patch version)

#### Scenario: Negative version component
- **WHEN** parse_semantic_version("1.-2.3") is called
- **THEN** function returns None

### Requirement: Version Comparison
The system SHALL compare two semantic version tuples and return -1 if current version is older, 0 if versions are equal, and 1 if current version is newer.

#### Scenario: Update available - MINOR version
- **WHEN** compare_versions((1, 0, 0), (1, 1, 0)) is called
- **THEN** function returns -1

#### Scenario: Update available - MAJOR version
- **WHEN** compare_versions((1, 0, 0), (2, 0, 0)) is called
- **THEN** function returns -1

#### Scenario: Update available - PATCH version
- **WHEN** compare_versions((1, 0, 0), (1, 0, 1)) is called
- **THEN** function returns -1

#### Scenario: Versions are equal
- **WHEN** compare_versions((1, 1, 0), (1, 1, 0)) is called
- **THEN** function returns 0

#### Scenario: Running dev/future version
- **WHEN** compare_versions((1, 2, 0), (1, 1, 0)) is called
- **THEN** function returns 1

#### Scenario: MAJOR version takes precedence
- **WHEN** compare_versions((1, 9, 9), (2, 0, 0)) is called
- **THEN** function returns -1

### Requirement: GitHub API Integration
The system SHALL query the GitHub Releases API to fetch the latest release version, URL, and changelog URL with a 3-second timeout and return (None, None, None) on any error.

#### Scenario: Successful API call
- **WHEN** check_github_releases() is called with internet connectivity
- **THEN** function returns (version_string, release_url, changelog_url) with valid data

#### Scenario: Version check disabled
- **WHEN** DISABLE_VERSION_CHECK environment variable is set to "1"
- **THEN** function returns (None, None, None) without making API call

#### Scenario: Network failure
- **WHEN** check_github_releases() is called without internet connectivity
- **THEN** function returns (None, None, None) and logs error at DEBUG level only

#### Scenario: API timeout
- **WHEN** GitHub API response takes more than 3 seconds
- **THEN** request times out and function returns (None, None, None)

#### Scenario: Custom timeout
- **WHEN** VERSION_CHECK_TIMEOUT environment variable is set to "5"
- **THEN** request times out after 5 seconds instead of default 3

#### Scenario: HTTP 404 error
- **WHEN** GitHub API returns HTTP 404 (repository or release not found)
- **THEN** function returns (None, None, None) and logs error at DEBUG level

#### Scenario: HTTP 403 rate limit
- **WHEN** GitHub API returns HTTP 403 due to rate limiting
- **THEN** function returns (None, None, None) and logs rate limit warning at DEBUG level

#### Scenario: Invalid JSON response
- **WHEN** GitHub API returns malformed JSON
- **THEN** function catches JSONDecodeError and returns (None, None, None)

#### Scenario: HTTPS with certificate validation
- **WHEN** check_github_releases() makes API request
- **THEN** request uses HTTPS protocol and validates SSL certificate

#### Scenario: User-Agent header included
- **WHEN** check_github_releases() makes API request
- **THEN** request includes User-Agent header in format "linux-health-check/VERSION"

### Requirement: Version Update Notification
The system SHALL check for newer versions by comparing current version with GitHub API latest version and return INFO-level issue if update is available, empty list otherwise.

#### Scenario: Update available
- **WHEN** current version is "1.0.0" AND latest version is "1.1.0"
- **THEN** check_version_update() returns list with one INFO-level issue containing upgrade instructions

#### Scenario: Up to date
- **WHEN** current version equals latest version
- **THEN** check_version_update() returns empty list

#### Scenario: Running dev/future version
- **WHEN** current version is "1.2.0" AND latest version is "1.1.0"
- **THEN** check_version_update() returns empty list and logs at DEBUG level

#### Scenario: Version check failed
- **WHEN** check_github_releases() returns (None, None, None)
- **THEN** check_version_update() returns empty list (silent failure)

#### Scenario: Version parsing error
- **WHEN** current or latest version cannot be parsed
- **THEN** check_version_update() returns empty list and logs error at DEBUG level

#### Scenario: Issue format with upgrade instructions
- **WHEN** update is available
- **THEN** issue contains severity "INFO", description with version numbers, and context with wget command and changelog URL

### Requirement: Report Integration
The system SHALL integrate version checking into health report execution flow, running after initialization but before other health checks, and include version notification in all export formats.

#### Scenario: Version check runs at startup
- **WHEN** script executes
- **THEN** check_version_update() is called after initialization and logs "Checking for script updates..." at INFO level

#### Scenario: Version check does not block health checks
- **WHEN** version check times out or fails
- **THEN** all other health checks run normally without interruption

#### Scenario: Version notification in Markdown export
- **WHEN** update is available AND export format is Markdown
- **THEN** INFO-level issue appears in Markdown report with formatted upgrade instructions

#### Scenario: Version notification in JSON export
- **WHEN** update is available AND export format is JSON
- **THEN** INFO-level issue appears in JSON issues array with all required fields

#### Scenario: Version notification in XML export
- **WHEN** update is available AND export format is XML
- **THEN** INFO-level issue appears as XML element with proper escaping

#### Scenario: Version notification in text export
- **WHEN** update is available AND export format is text
- **THEN** INFO-level issue appears in plain text report with readable formatting

### Requirement: Configuration and Opt-Out
The system SHALL support disabling version checking via DISABLE_VERSION_CHECK environment variable and configuring timeout via VERSION_CHECK_TIMEOUT environment variable.

#### Scenario: Disable version check via environment
- **WHEN** DISABLE_VERSION_CHECK=1 is set
- **THEN** no GitHub API call is made and no version notification appears

#### Scenario: Enable version check explicitly
- **WHEN** DISABLE_VERSION_CHECK=0 is set or not set
- **THEN** version check proceeds normally

#### Scenario: Custom timeout configuration
- **WHEN** VERSION_CHECK_TIMEOUT=5 is set
- **THEN** GitHub API request times out after 5 seconds

#### Scenario: Invalid timeout value
- **WHEN** VERSION_CHECK_TIMEOUT is set to non-numeric value
- **THEN** system falls back to default 3-second timeout

#### Scenario: Configuration constants defined
- **WHEN** script loads
- **THEN** VERSION_CHECK_TIMEOUT and GITHUB_REPO constants are defined near top of file

### Requirement: Logging and Observability
The system SHALL log version check operations at appropriate levels: INFO for user-visible actions, DEBUG for detailed diagnostics, and no ERROR logging for expected failures.

#### Scenario: INFO log for version check start
- **WHEN** version check begins
- **THEN** system logs "Checking for script updates..." at INFO level

#### Scenario: DEBUG log for API success
- **WHEN** GitHub API call succeeds
- **THEN** system logs "Latest version: X.Y.Z" at DEBUG level

#### Scenario: DEBUG log for network error
- **WHEN** network error occurs
- **THEN** system logs "GitHub API network error: REASON" at DEBUG level

#### Scenario: DEBUG log for timeout
- **WHEN** API request times out
- **THEN** system logs timeout error at DEBUG level

#### Scenario: DEBUG log for disabled check
- **WHEN** DISABLE_VERSION_CHECK=1 is set
- **THEN** system logs "Version check disabled via DISABLE_VERSION_CHECK" at DEBUG level

#### Scenario: No error messages to user
- **WHEN** any version check error occurs
- **THEN** no error messages are displayed to user (silent failure)

### Requirement: Security and Safety
The system SHALL implement security best practices including HTTPS-only connections, certificate validation, no auto-update functionality, and graceful failure that never breaks health checks.

#### Scenario: HTTPS enforced
- **WHEN** GitHub API URL is constructed
- **THEN** URL uses "https://" protocol (no HTTP fallback)

#### Scenario: SSL certificate validation enabled
- **WHEN** urllib.request makes HTTPS request
- **THEN** SSL certificate is validated (urllib default behavior)

#### Scenario: No credentials required
- **WHEN** GitHub API call is made
- **THEN** no authentication credentials are used (public API access)

#### Scenario: No auto-update functionality
- **WHEN** newer version is detected
- **THEN** system only displays notification with manual upgrade instructions (no automatic download or installation)

#### Scenario: Manual upgrade required
- **WHEN** INFO notification is shown
- **THEN** context includes wget command that user must manually execute

#### Scenario: Health checks continue on error
- **WHEN** version check throws exception
- **THEN** exception is caught and health checks proceed normally

#### Scenario: No sensitive data logged
- **WHEN** version check operations are logged
- **THEN** logs contain only version numbers and error types (no tokens, credentials, or user data)

#### Scenario: Timeout prevents hanging
- **WHEN** GitHub API is slow or unresponsive
- **THEN** request times out after 3 seconds (or custom timeout) preventing script from hanging

### Requirement: Cross-Distribution Compatibility
The system SHALL work on all 8 supported Linux distributions using only Python standard library without external dependencies.

#### Scenario: Works on Debian 12
- **WHEN** script runs on Debian 12
- **THEN** version check completes successfully using stdlib urllib

#### Scenario: Works on Ubuntu 22.04
- **WHEN** script runs on Ubuntu 22.04
- **THEN** version check completes successfully

#### Scenario: Works on Rocky Linux 9
- **WHEN** script runs on Rocky Linux 9
- **THEN** version check completes successfully

#### Scenario: Works on openSUSE Leap
- **WHEN** script runs on openSUSE Leap
- **THEN** version check completes successfully

#### Scenario: No external dependencies
- **WHEN** script imports version checking functions
- **THEN** only Python standard library modules are used (urllib.request, urllib.error, json, os, logging)

#### Scenario: Python 3.6+ compatibility
- **WHEN** script runs on Python 3.6.15 (openSUSE Leap 15) or any supported Python 3.6+ version
- **THEN** all version checking code executes without syntax or compatibility errors

### Requirement: Performance and Efficiency
The system SHALL complete version checking within 5 seconds under normal conditions and add minimal overhead to script execution time.

#### Scenario: Fast API response
- **WHEN** GitHub API responds within 1 second
- **THEN** version check completes in approximately 1 second

#### Scenario: Slow API response within timeout
- **WHEN** GitHub API responds in 2.5 seconds
- **THEN** version check completes successfully and reports result

#### Scenario: Timeout enforced
- **WHEN** GitHub API takes more than 3 seconds
- **THEN** request times out and version check fails gracefully

#### Scenario: Minimal execution overhead
- **WHEN** version check is enabled
- **THEN** total script execution time increases by less than 5 seconds

#### Scenario: No overhead when disabled
- **WHEN** DISABLE_VERSION_CHECK=1 is set
- **THEN** version check adds negligible overhead (only environment variable check)

### Requirement: Documentation and User Guidance
The system SHALL provide clear documentation in README.md explaining the version checking feature, configuration options, and upgrade process.

#### Scenario: Feature documented in README
- **WHEN** user reads README.md
- **THEN** document includes "Automated Update Checking" section explaining the feature

#### Scenario: Environment variables documented
- **WHEN** user reads documentation
- **THEN** DISABLE_VERSION_CHECK and VERSION_CHECK_TIMEOUT are documented with examples

#### Scenario: Upgrade instructions provided
- **WHEN** version notification appears
- **THEN** context includes complete wget command and chmod instructions for manual upgrade

#### Scenario: Rate limits mentioned
- **WHEN** user reads documentation
- **THEN** GitHub API rate limits (60 requests/hour) are documented

#### Scenario: CHANGELOG updated
- **WHEN** feature is released
- **THEN** CHANGELOG.md contains entry for v1.1.0 with version checking feature listed

#### Scenario: No auto-update clarified
- **WHEN** user reads documentation
- **THEN** documentation explicitly states no auto-update functionality (manual upgrade only)
