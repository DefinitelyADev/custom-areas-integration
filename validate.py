#!/usr/bin/env python3
"""Simple validation script for the Custom Areas Integration."""

import json
import sys
from pathlib import Path


def validate_manifest():
    """Validate manifest.json."""
    manifest_path = Path("custom_components/custom_areas/manifest.json")
    if not manifest_path.exists():
        print("❌ manifest.json not found")
        return False

    try:
        with open(manifest_path) as f:
            manifest = json.load(f)

        required_fields = [
            "domain",
            "name",
            "version",
            "config_flow",
            "integration_type",
        ]
        for field in required_fields:
            if field not in manifest:
                print(f"❌ Missing required field in manifest: {field}")
                return False

        if manifest["domain"] != "custom_areas":
            print("❌ Domain should be 'custom_areas'")
            return False

        print("✅ manifest.json is valid")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in manifest.json: {e}")
        return False


def validate_translations():
    """Validate translation files."""
    strings_path = Path("custom_components/custom_areas/strings.json")
    en_path = Path("custom_components/custom_areas/translations/en.json")

    if not strings_path.exists():
        print("❌ strings.json not found")
        return False

    if not en_path.exists():
        print("❌ translations/en.json not found")
        return False

    try:
        with open(strings_path) as f:
            strings = json.load(f)

        with open(en_path) as f:
            en = json.load(f)

        # Check that en.json has all keys from strings.json
        def check_keys(base, target, path=""):
            for key, value in base.items():
                current_path = f"{path}.{key}" if path else key
                if key not in target:
                    print(f"❌ Missing translation key: {current_path}")
                    return False
                if isinstance(value, dict) and isinstance(target[key], dict):
                    if not check_keys(value, target[key], current_path):
                        return False
            return True

        if check_keys(strings, en):
            print("✅ Translation files are valid")
            return True
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in translation files: {e}")
        return False


def validate_structure():
    """Validate basic file structure."""
    required_files = [
        "custom_components/custom_areas/__init__.py",
        "custom_components/custom_areas/config_flow.py",
        "custom_components/custom_areas/sensor.py",
        "custom_components/custom_areas/const.py",
        "custom_components/custom_areas/manifest.json",
        "custom_components/custom_areas/strings.json",
        "custom_components/custom_areas/translations/en.json",
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"  - {file}")
        return False

    print("✅ All required files present")
    return True


def main():
    """Run all validations."""
    print("🔍 Validating Custom Areas Integration...")

    all_valid = True
    all_valid &= validate_structure()
    all_valid &= validate_manifest()
    all_valid &= validate_translations()

    if all_valid:
        print("\n🎉 Integration structure is valid!")
        return 0
    else:
        print("\n❌ Validation failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
