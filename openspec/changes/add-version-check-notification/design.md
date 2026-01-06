# Design Document: Automated Version Checking

## Overview
Technical design for implementing automated version checking in the Linux Health Check script. This feature queries the GitHub Releases API to detect newer versions and includes upgrade notifications in health reports.

**Change ID**: add-version-check-notification  
**Target Version**: 1.1.0 (MINOR release)  
**Estimated LOC**: ~150-200 lines (including tests and documentation)

---

## Architecture

### High-Level Flow
```
┌─────────────────────────────────────────────────────────────────┐
│ Main Execution                                                  │
│                                                                 │
│  1. Initialize script                                           │
│  2. Parse arguments                                             │
│  3. ┌─────────────────────────────────────┐                    │
│     │ check_version_update()              │  ← NEW FUNCTION    │
│     │  ↓                                   │                    │
│     │ check_github_releases()             │  ← NEW FUNCTION    │
│     │  ↓                                   │                    │
│     │ compare_versions()                  │  ← NEW FUNCTION    │
│     │  ↓                                   │                    │
│     │ Return issue[] or []                │                    │
│     └─────────────────────────────────────┘                    │
│  4. Run health checks (existing)                                │
│  5. Generate report                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Component Diagram
```
┌──────────────────────────────────────────────────────────────────┐
│ linux_health_check.py                                            │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Configuration Constants                                      │ │
│ │ • __version__ = "1.0.0"                                      │ │
│ │ • VERSION_CHECK_TIMEOUT = 3                                  │ │
│ │ • GITHUB_REPO = "0xgruber/linux-health-checks"              │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Version Parsing & Comparison                                 │ │
│ │                                                              │ │
│ │ parse_semantic_version(version_string)                       │ │
│ │   Input:  "1.2.3" or "v1.2.3"                               │ │
│ │   Output: (1, 2, 3)                                         │ │
│ │   Errors: Returns None for invalid input                     │ │
│ │                                                              │ │
│ │ compare_versions(current_tuple, latest_tuple)                │ │
│ │   Input:  (1, 0, 0), (1, 1, 0)                              │ │
│ │   Output: -1 (update available)                             │ │
│ │           0 (up to date)                                     │ │
│ │           1 (dev version)                                    │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ GitHub API Integration                                       │ │
│ │                                                              │ │
│ │ check_github_releases()                                      │ │
│ │   ↓                                                          │ │
│ │   Check DISABLE_VERSION_CHECK env var                        │ │
│ │   ↓                                                          │ │
│ │   Build API request (urllib.request)                         │ │
│ │   ↓                                                          │ │
│ │   Fetch with timeout                                         │ │
│ │   ↓                                                          │ │
│ │   Parse JSON response                                        │ │
│ │   ↓                                                          │ │
│ │   Return (version, release_url, changelog_url)               │ │
│ │   or (None, None, None) on error                            │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Report Integration                                           │ │
│ │                                                              │ │
│ │ check_version_update()                                       │ │
│ │   ↓                                                          │ │
│ │   Call check_github_releases()                               │ │
│ │   ↓                                                          │ │
│ │   Compare with __version__                                   │ │
│ │   ↓                                                          │ │
│ │   Format INFO-level issue if update available                │ │
│ │   ↓                                                          │ │
│ │   Return [] or [issue]                                      │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Function Specifications

### 1. `parse_semantic_version(version_string: str) -> Optional[Tuple[int, int, int]]`

**Purpose**: Parse a semantic version string into a tuple of integers.

**Parameters**:
- `version_string` (str): Version string in format "X.Y.Z" or "vX.Y.Z"

**Returns**:
- `Tuple[int, int, int]`: Version tuple (major, minor, patch)
- `None`: If parsing fails

**Algorithm**:
```python
def parse_semantic_version(version_string):
    """
    Parse semantic version string into tuple of integers.
    
    Args:
        version_string: Version in format "X.Y.Z" or "vX.Y.Z"
    
    Returns:
        Tuple of (major, minor, patch) or None if invalid
    
    Examples:
        >>> parse_semantic_version("1.2.3")
        (1, 2, 3)
        >>> parse_semantic_version("v1.2.3")
        (1, 2, 3)
        >>> parse_semantic_version("invalid")
        None
    """
    try:
        # Strip 'v' prefix if present
        version = version_string.lstrip('v')
        
        # Split on '.' and convert to integers
        parts = version.split('.')
        
        # Must have exactly 3 parts (MAJOR.MINOR.PATCH)
        if len(parts) != 3:
            return None
        
        major, minor, patch = [int(p) for p in parts]
        
        # Validate non-negative
        if major < 0 or minor < 0 or patch < 0:
            return None
        
        return (major, minor, patch)
    
    except (ValueError, AttributeError):
        return None
```

**Edge Cases**:
- `"1.2.3"` → `(1, 2, 3)` ✅
- `"v1.2.3"` → `(1, 2, 3)` ✅
- `"1.2"` → `None` (missing patch)
- `"1.2.3.4"` → `None` (too many parts)
- `"1.2.a"` → `None` (non-numeric)
- `"1.-2.3"` → `None` (negative version)
- `""` → `None` (empty string)
- `None` → `None` (null input)

**Testing**:
```python
# Unit tests
assert parse_semantic_version("1.2.3") == (1, 2, 3)
assert parse_semantic_version("v1.2.3") == (1, 2, 3)
assert parse_semantic_version("2.0.0") == (2, 0, 0)
assert parse_semantic_version("0.0.0") == (0, 0, 0)
assert parse_semantic_version("invalid") is None
assert parse_semantic_version("1.2") is None
assert parse_semantic_version("") is None
```

---

### 2. `compare_versions(current: Tuple[int, int, int], latest: Tuple[int, int, int]) -> int`

**Purpose**: Compare two semantic version tuples.

**Parameters**:
- `current` (Tuple[int, int, int]): Current version tuple
- `latest` (Tuple[int, int, int]): Latest version tuple

**Returns**:
- `-1`: current < latest (update available)
- `0`: current == latest (up to date)
- `1`: current > latest (dev/future version)

**Algorithm**:
```python
def compare_versions(current, latest):
    """
    Compare two semantic version tuples.
    
    Args:
        current: Current version tuple (major, minor, patch)
        latest: Latest version tuple (major, minor, patch)
    
    Returns:
        -1 if current < latest (update available)
         0 if current == latest (up to date)
         1 if current > latest (dev version)
    
    Examples:
        >>> compare_versions((1, 0, 0), (1, 1, 0))
        -1
        >>> compare_versions((1, 1, 0), (1, 1, 0))
        0
        >>> compare_versions((1, 2, 0), (1, 1, 0))
        1
    """
    # Python tuple comparison handles semantic versioning naturally
    if current < latest:
        return -1
    elif current == latest:
        return 0
    else:
        return 1
```

**Comparison Logic**:
Python's tuple comparison works left-to-right:
- `(1, 0, 0) < (1, 1, 0)` → True (MINOR version update)
- `(1, 0, 0) < (2, 0, 0)` → True (MAJOR version update)
- `(1, 0, 0) < (1, 0, 1)` → True (PATCH version update)
- `(1, 1, 0) == (1, 1, 0)` → True (same version)
- `(2, 0, 0) > (1, 9, 9)` → True (MAJOR takes precedence)

**Edge Cases**:
- Same version: `(1, 1, 0)` vs `(1, 1, 0)` → `0`
- MAJOR update: `(1, 0, 0)` vs `(2, 0, 0)` → `-1`
- MINOR update: `(1, 0, 0)` vs `(1, 1, 0)` → `-1`
- PATCH update: `(1, 0, 0)` vs `(1, 0, 1)` → `-1`
- Dev version: `(1, 2, 0)` vs `(1, 1, 0)` → `1`
- Large versions: `(99, 99, 99)` vs `(100, 0, 0)` → `-1`

**Testing**:
```python
# Unit tests
assert compare_versions((1, 0, 0), (1, 1, 0)) == -1
assert compare_versions((1, 0, 0), (1, 0, 1)) == -1
assert compare_versions((1, 0, 0), (2, 0, 0)) == -1
assert compare_versions((1, 1, 0), (1, 1, 0)) == 0
assert compare_versions((1, 2, 0), (1, 1, 0)) == 1
assert compare_versions((2, 0, 0), (1, 9, 9)) == 1
```

---

### 3. `check_github_releases() -> Tuple[Optional[str], Optional[str], Optional[str]]`

**Purpose**: Query GitHub Releases API for the latest version.

**Parameters**: None (uses module-level constants)

**Returns**:
- Success: `(version, release_url, changelog_url)`
  - `version` (str): Latest version without 'v' prefix (e.g., "1.1.0")
  - `release_url` (str): URL to release page
  - `changelog_url` (str): URL to changelog (same as release_url)
- Failure: `(None, None, None)`

**Algorithm**:
```python
import urllib.request
import urllib.error
import json
import os
import logging

def check_github_releases():
    """
    Query GitHub Releases API for latest version.
    
    Returns:
        Tuple of (version, release_url, changelog_url) on success
        Tuple of (None, None, None) on failure
    
    Environment Variables:
        DISABLE_VERSION_CHECK: Set to "1" to skip check
        VERSION_CHECK_TIMEOUT: Timeout in seconds (default: 3)
    """
    # Check if version checking is disabled
    if os.getenv('DISABLE_VERSION_CHECK', '0') == '1':
        logging.debug("Version check disabled via DISABLE_VERSION_CHECK")
        return None, None, None
    
    # Build API URL
    repo = GITHUB_REPO  # Module constant: "0xgruber/linux-health-checks"
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    
    # Get timeout from environment or use default
    timeout = int(os.getenv('VERSION_CHECK_TIMEOUT', '3'))
    
    try:
        # Create request with User-Agent header
        headers = {
            'User-Agent': f'linux-health-check/{__version__}',
            'Accept': 'application/vnd.github.v3+json'
        }
        request = urllib.request.Request(api_url, headers=headers)
        
        # Fetch with timeout
        logging.debug(f"Fetching latest release from: {api_url}")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        # Parse response
        tag_name = data.get('tag_name', '')
        version = tag_name.lstrip('v')  # Remove 'v' prefix
        release_url = data.get('html_url', '')
        changelog_url = release_url  # Same as release URL
        
        logging.debug(f"Latest version: {version}")
        return version, release_url, changelog_url
    
    except urllib.error.HTTPError as e:
        # HTTP errors (404, 403, etc.)
        logging.debug(f"GitHub API HTTP error: {e.code} {e.reason}")
        return None, None, None
    
    except urllib.error.URLError as e:
        # Network errors (no connection, DNS failure, etc.)
        logging.debug(f"GitHub API network error: {e.reason}")
        return None, None, None
    
    except json.JSONDecodeError as e:
        # Invalid JSON response
        logging.debug(f"GitHub API JSON parse error: {e}")
        return None, None, None
    
    except Exception as e:
        # Catch-all for any other errors
        logging.debug(f"GitHub API unexpected error: {e}")
        return None, None, None
```

**API Endpoint**:
- URL: `https://api.github.com/repos/0xgruber/linux-health-checks/releases/latest`
- Method: GET
- Headers:
  - `User-Agent: linux-health-check/1.0.0`
  - `Accept: application/vnd.github.v3+json`
- Timeout: 3 seconds (configurable)
- Rate Limit: 60 requests/hour (unauthenticated)

**Response Format**:
```json
{
  "tag_name": "v1.0.0",
  "html_url": "https://github.com/0xgruber/linux-health-checks/releases/tag/v1.0.0",
  "name": "Version 1.0.0",
  "body": "Release notes...",
  "published_at": "2026-01-05T12:00:00Z",
  ...
}
```

**Error Handling**:
| Error Type | Cause | Handling |
|------------|-------|----------|
| `HTTPError 404` | Release not found | Log debug, return None |
| `HTTPError 403` | Rate limited or forbidden | Log debug, return None |
| `URLError` | Network failure, DNS error | Log debug, return None |
| `Timeout` | Request takes > 3 seconds | Log debug, return None |
| `JSONDecodeError` | Invalid response body | Log debug, return None |
| Generic `Exception` | Any other error | Log debug, return None |

**Security Considerations**:
- ✅ Uses HTTPS only
- ✅ Validates SSL certificates (urllib default)
- ✅ 3-second timeout prevents hanging
- ✅ No credentials required (public API)
- ✅ No sensitive data in logs
- ✅ Silent failure (doesn't expose errors to user)

**Testing**:
```python
# Manual tests
# 1. Success case
version, release_url, changelog_url = check_github_releases()
assert version == "1.0.0"  # or current latest
assert "github.com" in release_url

# 2. Disabled case
os.environ['DISABLE_VERSION_CHECK'] = '1'
version, release_url, changelog_url = check_github_releases()
assert version is None

# 3. Network failure (disconnect network)
# Should return (None, None, None) without crashing

# 4. Timeout (set VERSION_CHECK_TIMEOUT=1 and use slow connection)
# Should timeout after 1 second
```

---

### 4. `check_version_update() -> List[Dict]`

**Purpose**: Check for version updates and return issue notification if newer version available.

**Parameters**: None (uses module-level `__version__`)

**Returns**:
- `List[Dict]`: List with one issue dict if update available, empty list otherwise

**Algorithm**:
```python
def check_version_update():
    """
    Check for script updates and return notification issue if available.
    
    Returns:
        List containing one issue dict if update available, empty list otherwise
    
    Issue Format:
        {
            "severity": "INFO",
            "description": "New version available: X.Y.Z (current: A.B.C)",
            "context": "Upgrade instructions and changelog link"
        }
    """
    # Query GitHub API for latest release
    latest_version_str, release_url, changelog_url = check_github_releases()
    
    # If check failed or disabled, return empty list
    if not latest_version_str:
        logging.debug("Version check skipped or failed")
        return []
    
    # Parse versions
    current_version = parse_semantic_version(__version__)
    latest_version = parse_semantic_version(latest_version_str)
    
    # Handle parsing errors
    if not current_version or not latest_version:
        logging.debug("Failed to parse version strings")
        return []
    
    # Compare versions
    comparison = compare_versions(current_version, latest_version)
    
    if comparison < 0:
        # Update available
        logging.info(f"New version available: {latest_version_str} (current: {__version__})")
        
        # Build download URL
        download_url = f"https://github.com/{GITHUB_REPO}/releases/download/v{latest_version_str}/linux_health_check.py"
        
        # Format issue
        issue = {
            "severity": "INFO",
            "description": f"New version available: {latest_version_str} (current: {__version__})",
            "context": (
                f"A newer version of this script is available.\n"
                f"\n"
                f"Upgrade instructions:\n"
                f"  wget {download_url}\n"
                f"  chmod +x linux_health_check.py\n"
                f"\n"
                f"Changelog: {changelog_url}"
            )
        }
        
        return [issue]
    
    elif comparison == 0:
        # Up to date
        logging.debug(f"Script is up to date (version {__version__})")
        return []
    
    else:
        # Running dev/future version
        logging.debug(f"Running dev/future version {__version__} (latest: {latest_version_str})")
        return []
```

**Output Format**:
```python
# When update available
[
    {
        "severity": "INFO",
        "description": "New version available: 1.1.0 (current: 1.0.0)",
        "context": "A newer version of this script is available.\n\n"
                   "Upgrade instructions:\n"
                   "  wget https://github.com/0xgruber/linux-health-checks/releases/download/v1.1.0/linux_health_check.py\n"
                   "  chmod +x linux_health_check.py\n\n"
                   "Changelog: https://github.com/0xgruber/linux-health-checks/releases/tag/v1.1.0"
    }
]

# When up to date or check failed
[]
```

**Integration Point**:
Add to main execution flow in `linux_health_check.py`:

```python
def main():
    """Main execution function"""
    # ... existing initialization ...
    
    # Initialize issues list
    issues = []
    
    # Check for version updates (NEW)
    logging.info("Checking for script updates...")
    issues.extend(check_version_update())
    
    # Run existing health checks
    logging.info("Running system health checks...")
    issues.extend(check_disk_space())
    issues.extend(check_memory_usage())
    # ... rest of checks ...
    
    # Generate report
    generate_report(issues)
```

**Testing**:
```python
# Test 1: Update available
__version__ = "0.9.0"  # Temporarily change
issues = check_version_update()
assert len(issues) == 1
assert issues[0]['severity'] == 'INFO'
assert '1.0.0' in issues[0]['description']

# Test 2: Up to date
__version__ = "1.0.0"  # Current version
issues = check_version_update()
assert len(issues) == 0

# Test 3: Check disabled
os.environ['DISABLE_VERSION_CHECK'] = '1'
issues = check_version_update()
assert len(issues) == 0

# Test 4: Network failure
# Disconnect network
issues = check_version_update()
assert len(issues) == 0  # Silent failure
```

---

## Data Structures

### Version Tuple
```python
# Semantic version represented as tuple of integers
VersionTuple = Tuple[int, int, int]

# Examples
(1, 0, 0)  # Version 1.0.0
(1, 1, 0)  # Version 1.1.0
(2, 0, 0)  # Version 2.0.0
```

### Issue Dictionary
```python
# Issue format (matches existing issue structure in script)
Issue = {
    "severity": str,      # "INFO", "WARNING", "ERROR", "CRITICAL"
    "description": str,   # Short summary
    "context": str        # Detailed information
}

# Example: Version update notification
{
    "severity": "INFO",
    "description": "New version available: 1.1.0 (current: 1.0.0)",
    "context": "A newer version of this script is available.\n\n"
               "Upgrade instructions:\n"
               "  wget https://github.com/.../v1.1.0/linux_health_check.py\n"
               "  chmod +x linux_health_check.py\n\n"
               "Changelog: https://github.com/.../tag/v1.1.0"
}
```

---

## Configuration

### Module Constants
```python
# Add to top of linux_health_check.py near __version__

# Version checking configuration
GITHUB_REPO = "0xgruber/linux-health-checks"
VERSION_CHECK_TIMEOUT = int(os.getenv('VERSION_CHECK_TIMEOUT', '3'))
```

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `DISABLE_VERSION_CHECK` | `0` | Set to `1` to disable version checking |
| `VERSION_CHECK_TIMEOUT` | `3` | API request timeout in seconds (1-60) |

**Usage Examples**:
```bash
# Disable version check
DISABLE_VERSION_CHECK=1 sudo ./linux_health_check.py

# Custom timeout (5 seconds)
VERSION_CHECK_TIMEOUT=5 sudo ./linux_health_check.py

# Combine with existing options
EXPORT_FORMAT=json DISABLE_VERSION_CHECK=1 sudo ./linux_health_check.py
```

---

## Error Handling Strategy

### Principle: Silent Failure
Version checking must NEVER break health checks. All errors fail silently with debug logging only.

### Error Categories

#### 1. Network Errors
- **Cause**: No internet, firewall, DNS failure
- **Handling**: Log at DEBUG level, return `(None, None, None)`
- **User Impact**: None (health checks proceed normally)

#### 2. HTTP Errors
- **Cause**: 404 (not found), 403 (rate limit), 500 (server error)
- **Handling**: Log at DEBUG level, return `(None, None, None)`
- **User Impact**: None

#### 3. Timeout Errors
- **Cause**: Slow network, API downtime
- **Handling**: Timeout after 3 seconds, log at DEBUG level
- **User Impact**: Minimal (3-second delay maximum)

#### 4. Parse Errors
- **Cause**: Invalid JSON, unexpected response format
- **Handling**: Log at DEBUG level, return `(None, None, None)`
- **User Impact**: None

#### 5. Version Parse Errors
- **Cause**: Invalid version format in response
- **Handling**: Log at DEBUG level, return empty list
- **User Impact**: None

### Error Flow Diagram
```
┌─────────────────────────┐
│ check_version_update()  │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ check_github_releases() │
└───────────┬─────────────┘
            ↓
       ┌────┴────┐
       │ Try API │
       └────┬────┘
            ↓
    ┌───────┴────────┐
    │ Success?       │
    └───┬────────┬───┘
        │        │
       Yes       No
        │        │
        ↓        ↓
    Return    Return
    data      None
        │        │
        └────┬───┘
             ↓
    ┌────────────────┐
    │ Parse version? │
    └────┬───────┬───┘
         │       │
        Yes      No
         │       │
         ↓       ↓
    ┌────────┐ ┌────────┐
    │Compare │ │Return[]│
    └────┬───┘ └────────┘
         ↓
    ┌────────────┐
    │ Update?    │
    └─┬────────┬─┘
      │        │
     Yes       No
      │        │
      ↓        ↓
  ┌──────┐ ┌────────┐
  │Issue │ │Return[]│
  └──────┘ └────────┘
```

---

## Performance Considerations

### Execution Time
- **Best Case**: ~0.5 seconds (cached DNS, fast API response)
- **Average Case**: ~1-2 seconds (typical API latency)
- **Worst Case**: 3 seconds (timeout)

### Optimization Strategies
1. **Timeout**: 3-second limit prevents hanging
2. **Silent Failure**: Errors don't slow down execution
3. **Single Request**: Only one API call per execution
4. **Stdlib Only**: No external dependencies to load

### Future Optimizations (Not in v1.1.0)
- Cache results for 24 hours (reduce API calls)
- Background check (non-blocking)
- Only check once per day
- Use conditional requests (If-Modified-Since header)

---

## Security Analysis

### Threat Model

#### Threat 1: Man-in-the-Middle (MITM) Attack
- **Attack**: Attacker intercepts GitHub API request and injects fake version
- **Mitigation**: HTTPS with certificate validation (urllib default)
- **Residual Risk**: Low (requires compromised CA)

#### Threat 2: GitHub Account Compromise
- **Attack**: Attacker gains access to GitHub repo and publishes malicious release
- **Mitigation**: Users must manually download and verify (no auto-update)
- **Residual Risk**: Medium (requires user action)

#### Threat 3: API Rate Limiting DoS
- **Attack**: Attacker causes rate limiting by making many requests from same IP
- **Mitigation**: Version check fails silently, can be disabled
- **Residual Risk**: Low (only affects version notifications)

#### Threat 4: Malicious Redirect
- **Attack**: GitHub redirects to malicious site
- **Mitigation**: Hard-coded github.com domain, HTTPS only
- **Residual Risk**: Low (requires GitHub compromise)

#### Threat 5: Information Disclosure
- **Attack**: Version check leaks sensitive information in logs
- **Mitigation**: Only version numbers logged, no sensitive data
- **Residual Risk**: Negligible

### Security Best Practices
- ✅ HTTPS only (no HTTP fallback)
- ✅ Certificate validation enabled
- ✅ No credentials required
- ✅ No auto-update (manual verification required)
- ✅ Timeout prevents hanging
- ✅ Silent failure (no error details to user)
- ✅ No eval/exec of remote code
- ✅ Read-only operation (no write access needed)

---

## Testing Strategy

### Unit Tests
```python
# test_version_checking.py

def test_parse_semantic_version_valid():
    assert parse_semantic_version("1.2.3") == (1, 2, 3)
    assert parse_semantic_version("v1.2.3") == (1, 2, 3)
    assert parse_semantic_version("0.0.0") == (0, 0, 0)

def test_parse_semantic_version_invalid():
    assert parse_semantic_version("invalid") is None
    assert parse_semantic_version("1.2") is None
    assert parse_semantic_version("") is None

def test_compare_versions():
    assert compare_versions((1, 0, 0), (1, 1, 0)) == -1
    assert compare_versions((1, 1, 0), (1, 1, 0)) == 0
    assert compare_versions((1, 2, 0), (1, 1, 0)) == 1

def test_check_version_update_disabled():
    os.environ['DISABLE_VERSION_CHECK'] = '1'
    assert check_version_update() == []
```

### Integration Tests
```bash
# Test 1: Update available (mock old version)
sed -i 's/__version__ = "1.0.0"/__version__ = "0.9.0"/' linux_health_check.py
sudo ./linux_health_check.py | grep "New version available"

# Test 2: Up to date
sudo ./linux_health_check.py | grep -v "New version available"

# Test 3: Network failure
# Disconnect network
sudo ./linux_health_check.py  # Should complete successfully

# Test 4: Disabled
DISABLE_VERSION_CHECK=1 sudo ./linux_health_check.py | grep -v "New version"
```

### Manual Tests
1. ✅ Run on all 8 supported distributions
2. ✅ Test all export formats (Markdown, JSON, XML, text)
3. ✅ Test with network disconnected
4. ✅ Test with slow network (< 3s and > 3s)
5. ✅ Test with version check disabled
6. ✅ Test with mocked old version
7. ✅ Verify upgrade instructions are correct

---

## Export Format Examples

### Markdown (Default)
```markdown
# Linux Health Check Report

## System Information
...

## Issues Found

### INFO: New version available: 1.1.0 (current: 1.0.0)
A newer version of this script is available.

Upgrade instructions:
  wget https://github.com/0xgruber/linux-health-checks/releases/download/v1.1.0/linux_health_check.py
  chmod +x linux_health_check.py

Changelog: https://github.com/0xgruber/linux-health-checks/releases/tag/v1.1.0

---
```

### JSON
```json
{
  "issues": [
    {
      "severity": "INFO",
      "description": "New version available: 1.1.0 (current: 1.0.0)",
      "context": "A newer version of this script is available.\n\nUpgrade instructions:\n  wget https://github.com/.../v1.1.0/linux_health_check.py\n  chmod +x linux_health_check.py\n\nChangelog: https://github.com/.../tag/v1.1.0"
    }
  ]
}
```

### XML
```xml
<issue>
  <severity>INFO</severity>
  <description>New version available: 1.1.0 (current: 1.0.0)</description>
  <context>A newer version of this script is available.

Upgrade instructions:
  wget https://github.com/.../v1.1.0/linux_health_check.py
  chmod +x linux_health_check.py

Changelog: https://github.com/.../tag/v1.1.0</context>
</issue>
```

### Text
```
[INFO] New version available: 1.1.0 (current: 1.0.0)
A newer version of this script is available.

Upgrade instructions:
  wget https://github.com/.../v1.1.0/linux_health_check.py
  chmod +x linux_health_check.py

Changelog: https://github.com/.../tag/v1.1.0
```

---

## Dependencies

### Standard Library Only
- ✅ `urllib.request` - HTTP requests
- ✅ `urllib.error` - Error handling
- ✅ `json` - JSON parsing
- ✅ `os` - Environment variables
- ✅ `logging` - Debug logging

### No External Dependencies
- ❌ `requests` - Not using (stick to stdlib)
- ❌ `httpx` - Not using
- ❌ `aiohttp` - Not using (no async needed)

---

## Rollback Plan

If critical bugs are found after v1.1.0 release:

### Option 1: Hotfix Release (v1.1.1)
```bash
# Fix bug
git checkout main
git checkout -b hotfix/version-check-bug
# ... fix code ...
git commit -m "fix: resolve version check crash"
git tag v1.1.1
git push origin v1.1.1
```

### Option 2: Disable by Default
```python
# Add to script
VERSION_CHECK_ENABLED = os.getenv('ENABLE_VERSION_CHECK', '0') == '1'
# Now opt-in instead of opt-out
```

### Option 3: Revert Feature
```bash
# Emergency revert
git revert <commit-hash>
git tag v1.0.1
git push origin v1.0.1
```

---

## Documentation Updates

### Files to Update
1. **README.md**: Add "Automated Update Checking" section
2. **CHANGELOG.md**: Add v1.1.0 entry
3. **IMPROVEMENTS.md**: Mark Feature #6 as implemented

### README.md Addition
```markdown
### Automated Update Checking

The script automatically checks for newer versions by querying the GitHub Releases API. If a newer version is available, an INFO-level notification is included in the health check report with upgrade instructions.

**Configuration**:
- `DISABLE_VERSION_CHECK=1` - Disable version checking
- `VERSION_CHECK_TIMEOUT=3` - API request timeout in seconds (default: 3)

**Example**:
```bash
# Disable version check
DISABLE_VERSION_CHECK=1 sudo ./linux_health_check.py

# Custom timeout
VERSION_CHECK_TIMEOUT=5 sudo ./linux_health_check.py
```

**Note**: Version checking requires internet access. If the check fails (network error, timeout, etc.), the script continues normally without showing any errors. No auto-update is performed - you must manually download and replace the script.
```

---

## Future Enhancements (Post-1.1.0)

### Potential Improvements
1. **Cache version check results** (24-hour TTL)
2. **Add check interval** (daily, weekly, never)
3. **GitHub authentication** (higher rate limits)
4. **Pre-release notifications** (opt-in)
5. **Version changelog in notification** (show what's new)
6. **Check frequency configuration** (not every run)
7. **Async/background checking** (non-blocking)

### Non-Goals (Explicitly Excluded)
- ❌ Auto-update functionality
- ❌ Binary patching
- ❌ Downgrade support
- ❌ Beta/pre-release versions
- ❌ Multiple release channels

---

## Summary

**Design Complete**: ✅  
**Estimated Complexity**: Low-Medium  
**Implementation Time**: 4-8 hours  
**Lines of Code**: ~150-200  
**Risk Level**: Low (silent failure, no breaking changes)  

**Key Design Decisions**:
1. ✅ Stdlib only (no external dependencies)
2. ✅ Silent failure (never breaks health checks)
3. ✅ 3-second timeout (prevents hanging)
4. ✅ INFO severity (non-intrusive notification)
5. ✅ Manual upgrade only (no auto-update)
6. ✅ Configurable via environment variables
7. ✅ Works in all export formats

**Ready for Implementation**: ✅  
**Next Step**: Run `openspec validate --strict` and begin implementation
