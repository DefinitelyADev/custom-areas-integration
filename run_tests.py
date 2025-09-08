#!/usr/bin/env python3
"""Test runner for the Rooms integration."""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run the test suite."""
    print("🧪 Running tests for Rooms integration...")

    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("❌ pytest not found. Install with: pip install -r requirements-dev.txt")
        return False

    # Run tests
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "custom_components/rooms/tests/",
        "-v",
        "--tb=short"
    ], capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode == 0

def main():
    """Main entry point."""
    if run_tests():
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
