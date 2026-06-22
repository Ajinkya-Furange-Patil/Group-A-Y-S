#!/usr/bin/env python3
"""
Auto Version Bump Script

Automatically increments the version number after changes.
Run this script after making any code changes to update the version.

Usage:
    python auto_version_bump.py [patch|minor|major]
    
    patch: Bug fixes and minor changes (default) - 1.0.0 -> 1.0.1
    minor: New features - 1.0.0 -> 1.1.0
    major: Breaking changes - 1.0.0 -> 2.0.0
"""

import sys
import os
from pathlib import Path

# Add scanner module to path
sys.path.insert(0, str(Path(__file__).parent))

from scanner.version_manager import increment_version, get_version


def main():
    """Run the auto version bump."""
    bump_type = "patch"
    
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["major", "minor", "patch"]:
            bump_type = arg
        else:
            print(f"Invalid bump type: {arg}")
            print("Valid options: major, minor, patch")
            return 1
    
    old_version = get_version()
    new_version = increment_version(bump_type)
    
    print("\n" + "=" * 60)
    print("VERSION UPDATE COMPLETE")
    print("=" * 60)
    print(f"Old Version: {old_version}")
    print(f"New Version: {new_version}")
    print(f"Bump Type:   {bump_type}")
    print("=" * 60)
    print("\nVersion updated successfully!")
    print("Remember to rebuild the executables if distributing.")
    print("\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
