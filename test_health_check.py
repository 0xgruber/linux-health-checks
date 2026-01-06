#!/usr/bin/env python3
"""
Test suite for linux_health_check.py
Validates all export formats and basic functionality
"""

import subprocess
import os
import json
import xml.etree.ElementTree as ET
import sys
from pathlib import Path


def run_test(description, command, expected_rc=None):
    """Run a test command and report results"""
    print(f"\n{'=' * 70}")
    print(f"TEST: {description}")
    print(f"COMMAND: {' '.join(command)}")
    print(f"{'=' * 70}")

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)

        print(f"Exit Code: {result.returncode}")

        if expected_rc is not None and result.returncode != expected_rc:
            print(
                f"❌ FAILED: Expected exit code {expected_rc}, got {result.returncode}"
            )
            return False

        print(f"✅ PASSED")
        return True

    except subprocess.TimeoutExpired:
        print(f"❌ FAILED: Command timed out")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def validate_json_output(filepath):
    """Validate JSON output format"""
    print(f"\n{'=' * 70}")
    print(f"VALIDATING: JSON output at {filepath}")
    print(f"{'=' * 70}")

    try:
        with open(filepath, "r") as f:
            data = json.load(f)

        # Check required fields
        required_fields = ["hostname", "timestamp", "os_info", "summary", "issues"]
        for field in required_fields:
            if field not in data:
                print(f"❌ FAILED: Missing required field '{field}'")
                return False

        # Validate issues structure
        if not isinstance(data["issues"], list):
            print(f"❌ FAILED: 'issues' must be a list")
            return False

        print(f"✅ PASSED: Valid JSON with {len(data['issues'])} issues")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ FAILED: Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def validate_xml_output(filepath):
    """Validate XML output format"""
    print(f"\n{'=' * 70}")
    print(f"VALIDATING: XML output at {filepath}")
    print(f"{'=' * 70}")

    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        if root.tag != "health_check_report":
            print(
                f"❌ FAILED: Root element should be 'health_check_report', got '{root.tag}'"
            )
            return False

        # Check for required elements
        metadata = root.find("metadata")
        summary = root.find("summary")
        issues = root.find("issues")

        if metadata is None:
            print(f"❌ FAILED: Missing 'metadata' element")
            return False

        if summary is None:
            print(f"❌ FAILED: Missing 'summary' element")
            return False

        if issues is None:
            print(f"❌ FAILED: Missing 'issues' element")
            return False

        issue_count = len(issues.findall("issue"))
        print(f"✅ PASSED: Valid XML with {issue_count} issues")
        return True

    except ET.ParseError as e:
        print(f"❌ FAILED: Invalid XML: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def validate_markdown_output(filepath):
    """Validate Markdown output format"""
    print(f"\n{'=' * 70}")
    print(f"VALIDATING: Markdown output at {filepath}")
    print(f"{'=' * 70}")

    try:
        with open(filepath, "r") as f:
            content = f.read()

        # Check for required sections
        required_sections = [
            "# Linux Health Check Report",
            "## Summary",
            "**Hostname:**",
            "**Date:**",
        ]

        for section in required_sections:
            if section not in content:
                print(f"❌ FAILED: Missing section '{section}'")
                return False

        print(f"✅ PASSED: Valid Markdown ({len(content)} bytes)")
        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("Linux Health Check - Comprehensive Test Suite")
    print("=" * 70)

    script_path = Path(__file__).parent / "linux_health_check.py"
    if not script_path.exists():
        print(f"❌ ERROR: Script not found at {script_path}")
        sys.exit(1)

    results = []

    # Test 1: Basic execution (default Markdown format)
    results.append(
        run_test(
            "Basic execution with Markdown export",
            [str(script_path)],
            expected_rc=1,  # Expect exit code 1 due to HIGH severity issues
        )
    )

    # Test 2: JSON export
    env_json = os.environ.copy()
    env_json["EXPORT_FORMAT"] = "json"
    results.append(run_test("JSON export format", [str(script_path)], expected_rc=1))

    # Test 3: XML export
    env_xml = os.environ.copy()
    env_xml["EXPORT_FORMAT"] = "xml"
    results.append(run_test("XML export format", [str(script_path)], expected_rc=1))

    # Test 4: Text export
    env_text = os.environ.copy()
    env_text["EXPORT_FORMAT"] = "text"
    results.append(
        run_test("Plain text export format", [str(script_path)], expected_rc=1)
    )

    # Validate output files
    import socket

    hostname = socket.gethostname()
    output_dir = "/tmp"

    # Validate JSON
    json_file = Path(output_dir) / f"health_report_{hostname}.json"
    if json_file.exists():
        results.append(validate_json_output(json_file))
    else:
        print(f"⚠️  WARNING: JSON file not found at {json_file}")
        results.append(False)

    # Validate XML
    xml_file = Path(output_dir) / f"health_report_{hostname}.xml"
    if xml_file.exists():
        results.append(validate_xml_output(xml_file))
    else:
        print(f"⚠️  WARNING: XML file not found at {xml_file}")
        results.append(False)

    # Validate Markdown
    md_file = Path(output_dir) / f"health_report_{hostname}.md"
    if md_file.exists():
        results.append(validate_markdown_output(md_file))
    else:
        print(f"⚠️  WARNING: Markdown file not found at {md_file}")
        results.append(False)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
