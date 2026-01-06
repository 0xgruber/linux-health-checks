#!/bin/bash
# Docker Container Test Script for Linux Health Check
# Run this with: sudo ./run_docker_tests.sh

set -e

echo "========================================================================"
echo "Linux Health Check - Docker Container Tests"
echo "========================================================================"
echo ""

# Build the container
echo "Building Ubuntu test container..."
docker build -f Dockerfile.test -t linux-health-check-test:ubuntu .
echo "✅ Container built successfully"
echo ""

# Test 1: Run with default Markdown output
echo "========================================================================"
echo "TEST 1: Default Markdown output"
echo "========================================================================"
docker run --rm linux-health-check-test:ubuntu /usr/local/bin/linux_health_check.py
echo ""

# Test 2: Run with JSON output
echo "========================================================================"
echo "TEST 2: JSON output"
echo "========================================================================"
docker run --rm -e EXPORT_FORMAT=json linux-health-check-test:ubuntu /usr/local/bin/linux_health_check.py
echo ""

# Test 3: Run with XML output
echo "========================================================================"
echo "TEST 3: XML output"
echo "========================================================================"
docker run --rm -e EXPORT_FORMAT=xml linux-health-check-test:ubuntu /usr/local/bin/linux_health_check.py
echo ""

# Test 4: Run with text output
echo "========================================================================"
echo "TEST 4: Text output"
echo "========================================================================"
docker run --rm -e EXPORT_FORMAT=text linux-health-check-test:ubuntu /usr/local/bin/linux_health_check.py
echo ""

# Test 5: Extract and validate JSON output
echo "========================================================================"
echo "TEST 5: Extract and validate JSON output"
echo "========================================================================"
docker run --rm -e EXPORT_FORMAT=json linux-health-check-test:ubuntu bash -c '
    /usr/local/bin/linux_health_check.py > /dev/null 2>&1 || true
    if [ -f /root/health_report_*.json ]; then
        cat /root/health_report_*.json | python3 -m json.tool > /dev/null && echo "✅ Valid JSON"
        echo "Sample output:"
        cat /root/health_report_*.json | python3 -m json.tool | head -30
    fi
'
echo ""

# Test 6: Check exit codes
echo "========================================================================"
echo "TEST 6: Exit code validation"
echo "========================================================================"
docker run --rm linux-health-check-test:ubuntu bash -c '
    /usr/local/bin/linux_health_check.py > /dev/null 2>&1
    exitcode=$?
    echo "Exit code: $exitcode"
    if [ $exitcode -eq 0 ] || [ $exitcode -eq 1 ] || [ $exitcode -eq 2 ]; then
        echo "✅ Valid exit code (0=OK, 1=HIGH, 2=CRITICAL)"
    else
        echo "❌ Unexpected exit code"
    fi
'
echo ""

# Test 7: Run automated test suite inside container
echo "========================================================================"
echo "TEST 7: Automated test suite"
echo "========================================================================"
docker run --rm -v $(pwd)/test_health_check.py:/test_health_check.py linux-health-check-test:ubuntu python3 /test_health_check.py
echo ""

echo "========================================================================"
echo "All Docker container tests completed!"
echo "========================================================================"
