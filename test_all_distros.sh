#!/bin/bash
#
# Multi-Distribution Test Suite for Linux Health Check
# Tests the script across multiple Linux distributions in Docker containers
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="${SCRIPT_DIR}/linux_health_check.py"
RESULTS_DIR="${SCRIPT_DIR}/test_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create results directory
mkdir -p "${RESULTS_DIR}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "======================================================================"
echo "Linux Health Check - Multi-Distribution Test Suite"
echo "======================================================================"
echo "Timestamp: $(date)"
echo "Script: ${SCRIPT_PATH}"
echo "Results: ${RESULTS_DIR}"
echo ""

# Define distributions to test
declare -a DISTROS=(
    "debian:12"
    "debian:13"
    "ubuntu:22.04"
    "ubuntu:24.04"
    "rockylinux:9"
    "rockylinux/rockylinux:10"
    "opensuse/leap:15"
    "opensuse/tumbleweed:latest"
)

declare -A DISTRO_NAMES=(
    ["debian:12"]="Debian 12 Bookworm"
    ["debian:13"]="Debian 13 Trixie"
    ["ubuntu:22.04"]="Ubuntu 22.04 LTS"
    ["ubuntu:24.04"]="Ubuntu 24.04 LTS"
    ["rockylinux:9"]="Rocky Linux 9"
    ["rockylinux/rockylinux:10"]="Rocky Linux 10"
    ["opensuse/leap:15"]="openSUSE Leap 15"
    ["opensuse/tumbleweed:latest"]="openSUSE Tumbleweed"
)

# Function to create Dockerfile for a distro
create_dockerfile() {
    local base_image="$1"
    local distro_name="$2"
    local dockerfile="${RESULTS_DIR}/Dockerfile.${distro_name}"
    
    cat > "${dockerfile}" <<'DOCKERFILEEOF'
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

# Install Python 3 and basic utilities based on distro
RUN if command -v apt-get &> /dev/null; then \
        export DEBIAN_FRONTEND=noninteractive && \
        apt-get update && \
        apt-get install -y python3 python3-minimal systemctl procps iproute2 2>&1 | grep -v "^debconf: " || true && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*; \
    elif command -v dnf &> /dev/null; then \
        dnf install -y python3 systemd procps-ng iproute && \
        dnf clean all; \
    elif command -v yum &> /dev/null; then \
        yum install -y python3 systemd procps-ng iproute && \
        yum clean all; \
    elif command -v zypper &> /dev/null; then \
        zypper install -y python3 systemd procps iproute2 && \
        zypper clean; \
    fi

# Copy the health check script
COPY linux_health_check.py /usr/local/bin/linux_health_check.py
RUN chmod +x /usr/local/bin/linux_health_check.py

# Set Python 3 as default python if not already
RUN if ! command -v python &> /dev/null; then \
        ln -sf /usr/bin/python3 /usr/local/bin/python || true; \
    fi

WORKDIR /tmp

CMD ["/usr/local/bin/linux_health_check.py"]
DOCKERFILEEOF
    
    echo "${dockerfile}"
}

# Function to test a single distribution
test_distribution() {
    local base_image="$1"
    local distro_name=$(echo "${base_image}" | tr '/:' '_')
    local display_name="${DISTRO_NAMES[$base_image]}"
    
    echo ""
    echo -e "${BLUE}======================================================================"
    echo "Testing: ${display_name}"
    echo "Base Image: ${base_image}"
    echo -e "======================================================================${NC}"
    
    local dockerfile=$(create_dockerfile "${base_image}" "${distro_name}")
    local image_name="linux-health-check-test:${distro_name}"
    local result_file="${RESULTS_DIR}/${distro_name}_${TIMESTAMP}.log"
    local json_file="${RESULTS_DIR}/${distro_name}_${TIMESTAMP}.json"
    local status_file="${RESULTS_DIR}/${distro_name}.status"
    
    # Build the image
    echo -n "Building Docker image... "
    if docker build -f "${dockerfile}" --build-arg BASE_IMAGE="${base_image}" -t "${image_name}" "${SCRIPT_DIR}" > "${result_file}.build" 2>&1; then
        echo -e "${GREEN}✓ Success${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        echo "BUILD_FAILED" > "${status_file}"
        cat "${result_file}.build" | tail -20
        return 1
    fi
    
    # Run the health check with JSON output
    echo -n "Running health check... "
    if docker run --rm -e EXPORT_FORMAT=json "${image_name}" bash -c '/usr/local/bin/linux_health_check.py 2>&1; cat /root/health_report_*.json /tmp/health_report_*.json 2>/dev/null || true' > "${result_file}" 2>&1; then
        echo -e "${GREEN}✓ Success (exit 1 = issues found)${NC}"
        
        # Extract JSON from container output
        if grep -q '"hostname"' "${result_file}"; then
            # Extract JSON using awk
            awk '/^{/,/^}/' "${result_file}" > "${json_file}" 2>/dev/null
            
            # Count issues by severity
            if [ -f "${json_file}" ] && [ -s "${json_file}" ]; then
                local counts=$(python3 -c "import sys,json; d=json.load(open('${json_file}')); print(f\"{sum(1 for i in d['issues'] if i['severity']=='CRITICAL')}/{sum(1 for i in d['issues'] if i['severity']=='HIGH')}/{sum(1 for i in d['issues'] if i['severity']=='MEDIUM')}/{sum(1 for i in d['issues'] if i['severity']=='LOW')}/{sum(1 for i in d['issues'] if i['severity']=='INFO')}\")" 2>/dev/null || echo "0/0/0/0/0")
                
                IFS='/' read -r critical high medium low info <<< "$counts"
                local total=$((critical + high + medium + low + info))
                
                echo "  Issues found: ${total} total (🔴 ${critical} | 🟠 ${high} | 🟡 ${medium} | 🔵 ${low} | ℹ️  ${info})"
                echo "PASSED|${critical}/${high}/${medium}/${low}/${info}" > "${status_file}"
            else
                echo "  Warning: Could not parse JSON output"
                echo "PASSED|N/A" > "${status_file}"
            fi
        else
            echo "  Warning: No JSON output found"
            echo "PASSED|N/A" > "${status_file}"
        fi
    else
        # Exit codes 1 and 2 are normal (indicates issues found: 1=HIGH, 2=CRITICAL)
        local exit_code=$?
        if ([ $exit_code -eq 1 ] || [ $exit_code -eq 2 ]) && grep -q "Health Check Complete" "${result_file}"; then
            echo -e "${GREEN}✓ Success (issues found, normal)${NC}"
            
            # Try to extract results even on exit 1/2
            if grep -q '"hostname"' "${result_file}"; then
                awk '/^{/,/^}/' "${result_file}" > "${json_file}" 2>/dev/null
                
                if [ -f "${json_file}" ] && [ -s "${json_file}" ]; then
                    local counts=$(python3 -c "import sys,json; d=json.load(open('${json_file}')); print(f\"{sum(1 for i in d['issues'] if i['severity']=='CRITICAL')}/{sum(1 for i in d['issues'] if i['severity']=='HIGH')}/{sum(1 for i in d['issues'] if i['severity']=='MEDIUM')}/{sum(1 for i in d['issues'] if i['severity']=='LOW')}/{sum(1 for i in d['issues'] if i['severity']=='INFO')}\")" 2>/dev/null || echo "0/0/0/0/0")
                    
                    IFS='/' read -r critical high medium low info <<< "$counts"
                    local total=$((critical + high + medium + low + info))
                    
                    echo "  Issues found: ${total} total (🔴 ${critical} | 🟠 ${high} | 🟡 ${medium} | 🔵 ${low} | ℹ️  ${info})"
                    echo "PASSED|${critical}/${high}/${medium}/${low}/${info}" > "${status_file}"
                else
                    echo "PASSED|N/A" > "${status_file}"
                fi
            else
                echo "PASSED|N/A" > "${status_file}"
            fi
        else
            echo -e "${RED}✗ Failed (exit code: ${exit_code})${NC}"
            echo "RUN_FAILED" > "${status_file}"
            tail -20 "${result_file}"
            return 1
        fi
    fi
    
    # Cleanup build log
    rm -f "${result_file}.build"
    
    return 0
}

# Test all distributions sequentially for now (parallel was causing issues)
echo ""
echo "Running distribution tests..."
echo ""

for base_image in "${DISTROS[@]}"; do
    test_distribution "${base_image}" || true
    echo ""
done

echo ""
echo "======================================================================"
echo "TEST SUMMARY"
echo "======================================================================"
echo ""

# Count results
passed=0
failed=0

for base_image in "${DISTROS[@]}"; do
    distro_name=$(echo "${base_image}" | tr '/:' '_')
    display_name="${DISTRO_NAMES[$base_image]}"
    status_file="${RESULTS_DIR}/${distro_name}.status"
    
    if [ -f "${status_file}" ]; then
        status=$(cat "${status_file}")
        if [[ "${status}" == PASSED* ]]; then
            issues=$(echo "${status}" | cut -d'|' -f2)
            echo -e "${GREEN}✓ PASSED${NC} - ${display_name} (Issues: ${issues})"
            ((passed++))
        else
            echo -e "${RED}✗ ${status}${NC} - ${display_name}"
            ((failed++))
        fi
    else
        echo -e "${RED}✗ NO_RESULT${NC} - ${display_name}"
        ((failed++))
    fi
done

echo ""
echo "======================================================================"
echo "Total: $((passed + failed)) distributions"
echo -e "${GREEN}Passed: ${passed}${NC}"
if [ ${failed} -gt 0 ]; then
    echo -e "${RED}Failed: ${failed}${NC}"
else
    echo "Failed: 0"
fi
echo "======================================================================"

# Generate markdown report
REPORT_FILE="${RESULTS_DIR}/DISTRO_TEST_REPORT.md"
cat > "${REPORT_FILE}" <<EOF
# Distribution Compatibility Test Report

**Test Date:** $(date '+%Y-%m-%d %H:%M:%S %Z')  
**Script:** linux_health_check.py  
**Test Results:** ${RESULTS_DIR}

## Summary

✅ **Passed:** ${passed} / $((passed + failed)) distributions  
❌ **Failed:** ${failed} / $((passed + failed)) distributions

## Test Results

| Distribution | Status | Issues (C/H/M/L/I) |
|-------------|--------|-------------------|
EOF

for base_image in "${DISTROS[@]}"; do
    distro_name=$(echo "${base_image}" | tr '/:' '_')
    display_name="${DISTRO_NAMES[$base_image]}"
    status_file="${RESULTS_DIR}/${distro_name}.status"
    
    if [ -f "${status_file}" ]; then
        status=$(cat "${status_file}")
        if [[ "${status}" == PASSED* ]]; then
            issues=$(echo "${status}" | cut -d'|' -f2)
            echo "| ${display_name} | ✅ PASSED | ${issues} |" >> "${REPORT_FILE}"
        else
            echo "| ${display_name} | ❌ ${status} | N/A |" >> "${REPORT_FILE}"
        fi
    else
        echo "| ${display_name} | ❌ NO_RESULT | N/A |" >> "${REPORT_FILE}"
    fi
done

cat >> "${REPORT_FILE}" <<EOF

## Legend

- **C**: Critical issues (🔴)
- **H**: High severity issues (🟠)
- **M**: Medium severity issues (🟡)
- **L**: Low severity issues (🔵)
- **I**: Informational findings (ℹ️)

## Notes

- Tests run in minimal Docker containers with base system packages only
- Some checks may report INFO/LOW findings due to missing optional packages (smartctl, sensors, etc.)
- Exit code 1 is expected when issues are found (normal operation)
- Tests validate script functionality and cross-distribution compatibility
- All Debian-based and RPM-based distributions are officially supported
- Production environments will have different findings based on actual configuration

## Supported Distributions

### Officially Supported ✅

- **Debian:** 12 (Bookworm), 13 (Trixie)
- **Ubuntu:** 22.04 LTS (Jammy), 24.04 LTS (Noble)
- **Rocky Linux:** 9
- **openSUSE:** Leap 15, Tumbleweed

### Experimental ⚠️

- **Arch Linux:** Not officially supported or tested. May work but YMMV.

## Test Logs

Individual test logs and JSON outputs are available in:
\`\`\`
${RESULTS_DIR}/
\`\`\`

EOF

echo ""
echo "Report generated: ${REPORT_FILE}"
echo ""

# Cleanup Docker images
echo "Cleaning up Docker images..."
for base_image in "${DISTROS[@]}"; do
    distro_name=$(echo "${base_image}" | tr '/:' '_')
    image_name="linux-health-check-test:${distro_name}"
    docker rmi -f "${image_name}" > /dev/null 2>&1 || true
done

# Cleanup status files
rm -f "${RESULTS_DIR}"/*.status

echo "Cleanup complete!"
echo ""

# Exit with appropriate code
if [ ${failed} -gt 0 ]; then
    echo -e "${YELLOW}Some tests failed - check logs for details${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
