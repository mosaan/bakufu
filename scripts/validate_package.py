#!/usr/bin/env python3
"""
Package validation script for bakufu.

This script validates that the built package contains only intended files
and excludes development/internal files.
"""

import subprocess
import sys
import zipfile
from pathlib import Path


def build_package() -> Path:
    """Build the package and return the path to the wheel."""
    print("🔨 Building package...")
    result = subprocess.run(["python", "-m", "build", "--wheel"], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Build failed: {result.stderr}")
        sys.exit(1)

    # Find the wheel file
    dist_dir = Path("dist")
    wheel_files = list(dist_dir.glob("*.whl"))

    if not wheel_files:
        print("❌ No wheel file found")
        sys.exit(1)

    wheel_path = wheel_files[-1]  # Get the latest wheel
    print(f"✅ Package built: {wheel_path}")
    return wheel_path


def validate_package_contents(wheel_path: Path) -> None:  # noqa: PLR0912
    """Validate the contents of the package."""
    print(f"🔍 Validating package contents: {wheel_path}")

    # Files that MUST be included
    required_files = [
        "bakufu/",
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "examples/",
        "docs/API.md",
        "docs/USER_GUIDE.md",
    ]

    # Files that MUST NOT be included
    forbidden_files = [
        "dev-docs/",
        "CLAUDE.md",
        "README_ja.md",
        "tests/",
        "htmlcov/",
        "bakufu.yml",
        "uv.lock",
        ".env",
        ".github/",
        "scripts/",
    ]

    # Extract and examine wheel contents
    with zipfile.ZipFile(wheel_path, "r") as wheel:
        file_list = wheel.namelist()

        print(f"📦 Package contains {len(file_list)} files")

        # Check required files
        missing_required = []
        for required in required_files:
            if required.endswith("/"):
                # Check for directory
                if not any(f.startswith(required) for f in file_list):
                    missing_required.append(required)
            # Check for specific file
            elif required not in file_list:
                missing_required.append(required)

        if missing_required:
            print("❌ Missing required files:")
            for missing in missing_required:
                print(f"  - {missing}")
            return False

        # Check forbidden files
        found_forbidden = []
        for forbidden in forbidden_files:
            if forbidden.endswith("/"):
                # Check for directory
                forbidden_found = [f for f in file_list if f.startswith(forbidden)]
                if forbidden_found:
                    found_forbidden.extend(forbidden_found)
            # Check for specific file
            elif forbidden in file_list:
                found_forbidden.append(forbidden)

        if found_forbidden:
            print("❌ Found forbidden files:")
            for forbidden in found_forbidden:
                print(f"  - {forbidden}")
            return False

        print("✅ Package contents validation passed")

        # Print summary of included files
        print("\n📋 Package contents summary:")
        dirs = set()
        for f in file_list:
            if "/" in f:
                dirs.add(f.split("/")[0])
            else:
                print(f"  📄 {f}")

        for d in sorted(dirs):
            dir_files = [f for f in file_list if f.startswith(f"{d}/")]
            print(f"  📁 {d}/ ({len(dir_files)} files)")

        return True


def main():
    """Main validation function."""
    print("🚀 Starting package validation...")

    # Ensure we're in the project root
    if not Path("pyproject.toml").exists():
        print("❌ Must be run from project root")
        sys.exit(1)

    # Clean previous builds
    dist_dir = Path("dist")
    if dist_dir.exists():
        import shutil

        shutil.rmtree(dist_dir)
        print("🧹 Cleaned previous builds")

    # Build and validate
    wheel_path = build_package()
    success = validate_package_contents(wheel_path)

    if success:
        print("\n🎉 Package validation successful!")
        print("📦 Ready for distribution")
    else:
        print("\n💥 Package validation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
