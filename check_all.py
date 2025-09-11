#!/usr/bin/env python3
"""Run all validations and checks for the Custom Areas Integration."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n🔍 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def main():
    """Run all validations."""
    print("🚀 Running all validations for Custom Areas Integration...")

    all_passed = True

    # Check if we're in the right directory
    if not Path("custom_components/areas").exists():
        print("❌ Not in the correct directory. Please run from the project root.")
        return 1

    # Run custom validation
    if not run_command("python3 validate.py", "Custom validation"):
        all_passed = False

    # Run tests
    if not run_command("python3 run_tests.py", "Tests"):
        all_passed = False

    # Run type checking
    if not run_command("pyright", "Type checking"):
        all_passed = False

    # Run linting
    if not run_command("black --check --diff custom_components/areas/", "Black formatting check"):
        all_passed = False

    if not run_command("isort --check-only --diff custom_components/areas/", "Import sorting check"):
        all_passed = False

    if not run_command("flake8 custom_components/areas/", "Flake8 linting"):
        all_passed = False

    # Run pre-commit (if available)
    if Path(".pre-commit-config.yaml").exists():
        if not run_command("pre-commit run --all-files", "Pre-commit hooks"):
            all_passed = False

    if all_passed:
        print("\n🎉 All validations passed!")
        return 0
    else:
        print("\n❌ Some validations failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
