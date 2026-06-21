#!/usr/bin/env python3
"""
AI Discovery Scanner — Cross-Platform Release Builder

This script orchestrates the PyInstaller build process across different platforms.
It requires PyInstaller to be installed (`pip install pyinstaller`).

Since PyInstaller natively compiles for the architecture it is run on, you must run
this script on a macOS host to build the `.app` macOS binary, on Linux to build the
Linux ELF binary, and on Windows to build the `.exe`.
"""

import os
import platform
import subprocess
import sys

def main():
    current_os = platform.system()
    print(f"Building AI Discovery Scanner for: {current_os}")

    # Ensure pyinstaller is available
    try:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], check=True, capture_output=True)
    except Exception:
        print("Error: PyInstaller is not installed or not available in the path.")
        print("Run: python -m pip install pyinstaller")
        sys.exit(1)

    # Use the unified ai_scanner.spec file which works across all platforms
    spec_file = "ai_scanner.spec"
    
    if not os.path.exists(spec_file):
        print(f"Error: Could not find '{spec_file}' in the current directory.")
        sys.exit(1)

    print("Executing PyInstaller compilation...")
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", spec_file]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n[SUCCESS] Build complete!")
        print("Check the 'dist' folder for the compiled standalone executable.")
    except subprocess.CalledProcessError as e:
        print(f"\n[FAIL] Build process failed with code {e.returncode}.")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
