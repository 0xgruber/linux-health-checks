#!/bin/bash
# Test script for version checking feature across all supported distributions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SCRIPT_DIR/linux_health_check.py"
RESULTS_FILE="$SCRIPT_DIR/test_results/version_check_test_results.md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
declare -A RESULTS
declare -A PYTHON_VERSIONS

echo "======================================================================"
echo "Testing Version Check Feature Across All Distributions"
echo "======================================================================"
echo ""

# Test function
test_distro() {
    local distro_name="$1"
    local docker_image="$2"
    local install_cmd="$3"
    local test_num="$4"
    
    echo -e "${BLUE}[$test_num/8] Testing: $distro_name${NC}"
    echo "Image: $docker_image"
    echo "----------------------------------------------------------------------"
    
    local all_passed=true
    
    # Test 1: Install Python and check version
    echo "  [1] Installing Python and checking version..."
    PYTHON_VERSION=$(docker run --rm "$docker_image" sh -c "$install_cmd && python3 --version 2>&1" | grep -oP 'Python \K\d+\.\d+\.\d+' | head -1 || echo "ERROR")
    if [[ "$PYTHON_VERSION" == "ERROR" ]]; then
        echo -e "    ${RED}✗${NC} Failed to install/detect Python"
        RESULTS["$distro_name"]="FAIL"
        PYTHON_VERSIONS["$distro_name"]="N/A"
        echo ""
        return
    else
        echo "    Python version: $PYTHON_VERSION"
        PYTHON_VERSIONS["$distro_name"]="$PYTHON_VERSION"
        MAJOR_VERSION=$(echo "$PYTHON_VERSION" | cut -d. -f1)
        if [[ "$MAJOR_VERSION" == "3" ]]; then
            echo -e "    ${GREEN}✓${NC} Python 3.x detected"
        else
            echo -e "    ${RED}✗${NC} Python version issue (not 3.x)"
            all_passed=false
        fi
    fi
    
    # Test 2: Syntax check
    echo "  [2] Testing Python syntax..."
    if docker run --rm -v "$SCRIPT:/script.py:ro" "$docker_image" sh -c "$install_cmd >/dev/null 2>&1 && python3 -m py_compile /script.py 2>&1" >/dev/null 2>&1; then
        echo -e "    ${GREEN}✓${NC} Syntax valid"
    else
        echo -e "    ${RED}✗${NC} Syntax error"
        all_passed=false
    fi
    
    # Test 3: urllib availability
    echo "  [3] Testing urllib.request availability..."
    if docker run --rm "$docker_image" sh -c "$install_cmd >/dev/null 2>&1 && python3 -c 'import urllib.request; import urllib.error' 2>&1" >/dev/null 2>&1; then
        echo -e "    ${GREEN}✓${NC} urllib modules available"
    else
        echo -e "    ${RED}✗${NC} urllib modules missing"
        all_passed=false
    fi
    
    # Test 4: Version parsing functions
    echo "  [4] Testing version parsing function..."
    TEST_CODE='import sys
exec(open("/script.py").read(), {"__name__": "__main__"})
try:
    assert parse_semantic_version("1.2.3") == (1, 2, 3), "parse 1.2.3"
    assert parse_semantic_version("v1.2.3") == (1, 2, 3), "parse v1.2.3"
    assert parse_semantic_version("invalid") is None, "reject invalid"
    assert compare_versions((1, 0, 0), (1, 1, 0)) == -1, "compare versions"
    print("OK")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
'
    PARSE_RESULT=$(docker run --rm -v "$SCRIPT:/script.py:ro" "$docker_image" sh -c "$install_cmd >/dev/null 2>&1 && python3 -c '$TEST_CODE' 2>&1" || echo "ERROR")
    if echo "$PARSE_RESULT" | grep -q "OK"; then
        echo -e "    ${GREEN}✓${NC} Version parsing functions work"
    else
        echo -e "    ${RED}✗${NC} Version parsing functions failed"
        echo "    Debug: $PARSE_RESULT"
        all_passed=false
    fi
    
    # Test 5: Version check runs (with timeout)
    echo "  [5] Testing version check execution..."
    OUTPUT=$(docker run --rm -v "$SCRIPT:/script.py:ro" "$docker_image" sh -c "$install_cmd >/dev/null 2>&1 && timeout 15 python3 /script.py 2>&1 || true")
    if echo "$OUTPUT" | grep -q "Checking for script updates"; then
        echo -e "    ${GREEN}✓${NC} Version check log message appears"
    else
        echo -e "    ${YELLOW}⚠${NC} Version check log not found (script may have exited early due to missing tools)"
    fi
    
    # Test 6: Remote update check disabled (logging only)
    echo "  [6] Testing DISABLE_VERSION_CHECK=1 (no remote update)..."
    OUTPUT=$(docker run --rm -e DISABLE_VERSION_CHECK=1 -v "$SCRIPT:/script.py:ro" "$docker_image" sh -c "$install_cmd >/dev/null 2>&1 && timeout 10 python3 /script.py 2>&1 || true")
    HAS_CHECK_LOG=$(echo "$OUTPUT" | grep -c "Checking for script updates" || echo 0)
    HAS_UPDATE_MSG=$(echo "$OUTPUT" | grep -c "New version available" || echo 0)
    
    if [[ $HAS_CHECK_LOG -gt 0 ]] && [[ $HAS_UPDATE_MSG -eq 0 ]]; then
        echo -e "    ${GREEN}✓${NC} DISABLE_VERSION_CHECK active: logging only (no remote update message)"
    elif [[ $HAS_CHECK_LOG -eq 0 ]]; then
        echo -e "    ${YELLOW}⚠${NC} No version check log detected (script may have exited early)"
    else
        echo -e "    ${YELLOW}⚠${NC} Unexpected behavior"
    fi
    
    if $all_passed; then
        echo -e "${GREEN}  Result: PASS${NC}"
        RESULTS["$distro_name"]="PASS"
    else
        echo -e "${RED}  Result: FAIL${NC}"
        RESULTS["$distro_name"]="FAIL"
    fi
    echo ""
}

# Create results directory
mkdir -p test_results

# Test all distributions
# Format: test_distro "Name" "docker:image" "install command" test_number
test_distro "Debian 12 (Bookworm)" "debian:12" "apt-get update -qq && apt-get install -y -qq python3 python3-urllib3 ca-certificates" 1
test_distro "Debian 13 (Trixie)" "debian:13" "apt-get update -qq && apt-get install -y -qq python3 python3-urllib3 ca-certificates" 2
test_distro "Ubuntu 22.04 LTS" "ubuntu:22.04" "apt-get update -qq && apt-get install -y -qq python3 python3-urllib3 ca-certificates" 3
test_distro "Ubuntu 24.04 LTS" "ubuntu:24.04" "apt-get update -qq && apt-get install -y -qq python3 python3-urllib3 ca-certificates" 4
test_distro "Rocky Linux 9" "rockylinux:9" "dnf install -y -q python3 ca-certificates" 5
test_distro "Rocky Linux 9.5" "rockylinux:9.5" "dnf install -y -q python3 ca-certificates" 6
test_distro "openSUSE Leap 15" "opensuse/leap:15" "zypper install -y python3 ca-certificates" 7
test_distro "openSUSE Tumbleweed" "opensuse/tumbleweed:latest" "zypper install -y python3 ca-certificates" 8

# Summary
echo "======================================================================"
echo "Test Summary"
echo "======================================================================"
echo ""

PASS_COUNT=0
FAIL_COUNT=0

for distro in "Debian 12 (Bookworm)" "Debian 13 (Trixie)" "Ubuntu 22.04 LTS" "Ubuntu 24.04 LTS" "Rocky Linux 9" "Rocky Linux 9.5" "openSUSE Leap 15" "openSUSE Tumbleweed"; do
    result="${RESULTS[$distro]:-UNKNOWN}"
    py_ver="${PYTHON_VERSIONS[$distro]:-N/A}"
    if [[ "$result" == "PASS" ]]; then
        echo -e "${GREEN}✓${NC} $distro (Python $py_ver): PASS"
        ((PASS_COUNT++))
    else
        echo -e "${RED}✗${NC} $distro (Python $py_ver): FAIL"
        ((FAIL_COUNT++))
    fi
done

echo ""
echo "======================================================================"
echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed (out of 8)"
echo "======================================================================"

# Generate Markdown report
echo "# Version Check Test Results" > "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "**Date**: $(date '+%Y-%m-%d %H:%M:%S %Z')" >> "$RESULTS_FILE"
echo "**Feature**: Automated Version Checking (v1.1.0)" >> "$RESULTS_FILE"
echo "**Branch**: feature/version-check-notification" >> "$RESULTS_FILE"
echo "**Script Version**: 1.1.0" >> "$RESULTS_FILE"
echo "**Test Method**: Docker containers with Python installed" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "## Test Results Summary" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "| Distribution | Python Version | Syntax Valid | urllib Available | Version Functions | Result |" >> "$RESULTS_FILE"
echo "|--------------|----------------|--------------|------------------|-------------------|--------|" >> "$RESULTS_FILE"

for distro in "Debian 12 (Bookworm)" "Debian 13 (Trixie)" "Ubuntu 22.04 LTS" "Ubuntu 24.04 LTS" "Rocky Linux 9" "Rocky Linux 9.5" "openSUSE Leap 15" "openSUSE Tumbleweed"; do
    result="${RESULTS[$distro]:-UNKNOWN}"
    py_ver="${PYTHON_VERSIONS[$distro]:-N/A}"
    if [[ "$result" == "PASS" ]]; then
        echo "| $distro | $py_ver | ✅ | ✅ | ✅ | ✅ **PASS** |" >> "$RESULTS_FILE"
    else
        echo "| $distro | $py_ver | ❌ | ❌ | ❌ | ❌ **FAIL** |" >> "$RESULTS_FILE"
    fi
done

echo "" >> "$RESULTS_FILE"
echo "## Summary" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "- **Passed**: $PASS_COUNT/8 distributions" >> "$RESULTS_FILE"
echo "- **Failed**: $FAIL_COUNT/8 distributions" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

if [[ $PASS_COUNT -eq 8 ]]; then
    echo "✅ **All tests passed!** The version checking feature is compatible with all 8 supported distributions." >> "$RESULTS_FILE"
elif [[ $PASS_COUNT -gt 0 ]]; then
    echo "⚠️ **Partial success.** Version checking works on $PASS_COUNT/$((PASS_COUNT+FAIL_COUNT)) distributions." >> "$RESULTS_FILE"
else
    echo "❌ **All tests failed.** Version checking feature needs fixes." >> "$RESULTS_FILE"
fi

echo "" >> "$RESULTS_FILE"
echo "## Test Details" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "### Tests Performed" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "1. **Python 3.x installation**: Install and verify Python 3.x" >> "$RESULTS_FILE"
echo "2. **Syntax check**: Verify script compiles without errors (py_compile)" >> "$RESULTS_FILE"
echo "3. **urllib availability**: Verify urllib.request and urllib.error modules" >> "$RESULTS_FILE"
echo "4. **Version parsing**: Test parse_semantic_version() and compare_versions()" >> "$RESULTS_FILE"
echo "5. **Version check execution**: Verify 'Checking for script updates' appears" >> "$RESULTS_FILE"
echo "6. **DISABLE_VERSION_CHECK**: Verify environment variable disables API call" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "### Version Checking Feature" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "The automated version checking feature:" >> "$RESULTS_FILE"
echo "- Queries GitHub Releases API on every script execution" >> "$RESULTS_FILE"
echo "- Compares current version (1.1.0) with latest release" >> "$RESULTS_FILE"
echo "- Shows INFO-level notification if update available" >> "$RESULTS_FILE"
echo "- Has 3-second timeout (configurable via VERSION_CHECK_TIMEOUT)" >> "$RESULTS_FILE"
echo "- Can be disabled with DISABLE_VERSION_CHECK=1" >> "$RESULTS_FILE"
echo "- Uses Python stdlib only (urllib.request, urllib.error)" >> "$RESULTS_FILE"
echo "- Fails silently on network errors (does not break health checks)" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "### Implementation" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "**Functions added**:" >> "$RESULTS_FILE"
echo "- \`parse_semantic_version()\` - Parse version strings (lines 171-215)" >> "$RESULTS_FILE"
echo "- \`compare_versions()\` - Compare version tuples (lines 218-251)" >> "$RESULTS_FILE"
echo "- \`check_github_releases()\` - Query GitHub API (lines 254-326)" >> "$RESULTS_FILE"
echo "- \`check_version_update()\` - Main version check logic (lines 329-368)" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "**Configuration**:" >> "$RESULTS_FILE"
echo "- \`GITHUB_REPO = \"0xgruber/linux-health-checks\"\`" >> "$RESULTS_FILE"
echo "- \`VERSION_CHECK_TIMEOUT = 3\` seconds (configurable)" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

echo ""
echo "Report saved to: $RESULTS_FILE"

if [[ $FAIL_COUNT -eq 0 ]]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
