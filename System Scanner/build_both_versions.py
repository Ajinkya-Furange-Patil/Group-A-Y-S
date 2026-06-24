#!/usr/bin/env python3
"""
AI Discovery Scanner - Build Both Versions Script

This script builds both the CLI and Client (GUI) versions of the System Scanner.
It performs comprehensive pre-build verification against Kiro specs and requirements.

Builds:
    1. CLI System Scanner.exe   - Console-based scanner (main.py)
    2. Client System Scanner.exe - GUI-based scanner with pywebview (gui.py)

Pre-build Verification:
    - Verify all scanner modules are registered in controller.py
    - Verify all template files exist
    - Verify all dependencies are installed
    - Verify icon file exists
    - Verify baseline directory exists
    - Cross-reference with Kiro specs requirements

Usage:
    python build_both_versions.py
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Tuple, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


class BuildVerifier:
    """Verifies all requirements before building executables."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.base_dir = Path(__file__).parent
        
    def verify_all(self) -> bool:
        """Run all verification checks."""
        logger.info("=" * 70)
        logger.info("PRE-BUILD VERIFICATION - Checking all requirements...")
        logger.info("=" * 70)
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Scanner Modules", self.check_scanner_modules),
            ("Template Files", self.check_template_files),
            ("Dependencies", self.check_dependencies),
            ("Build Files", self.check_build_files),
            ("Icon File", self.check_icon_file),
            ("Baseline Directory", self.check_baseline_dir),
            ("Entry Points", self.check_entry_points),
            ("Spec Files", self.check_spec_files),
        ]
        
        for check_name, check_func in checks:
            logger.info(f"Checking: {check_name}...")
            check_func()
        
        # Report results
        logger.info("=" * 70)
        if self.errors:
            logger.error("VERIFICATION FAILED - %d errors found:", len(self.errors))
            for error in self.errors:
                logger.error(f"  ❌ {error}")
        
        if self.warnings:
            logger.warning("WARNINGS - %d warnings found:", len(self.warnings))
            for warning in self.warnings:
                logger.warning(f"  ⚠️  {warning}")
        
        if not self.errors:
            logger.info("✅ All verification checks passed!")
            logger.info("=" * 70)
            return True
        else:
            logger.info("=" * 70)
            return False
    
    def check_python_version(self):
        """Verify Python version is 3.10+."""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 10):
            self.errors.append(f"Python 3.10+ required, found {version.major}.{version.minor}")
        else:
            logger.info(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
    
    def check_scanner_modules(self):
        """Verify all scanner modules exist and are registered."""
        expected_modules = [
            ("scanner/modules/system_scanner.py", "SystemScanner"),
            ("scanner/modules/file_scanner.py", "FileScanner"),
            ("scanner/modules/process_scanner.py", "ProcessScanner"),
            ("scanner/modules/package_scanner.py", "PackageScanner"),
            ("scanner/modules/agent_scanner.py", "AgentScanner"),
            ("scanner/modules/runtime_scanner.py", "RuntimeScanner"),
            ("scanner/modules/api_scanner.py", "APIScanner"),
            ("scanner/modules/mcp_scanner.py", "MCPScanner"),
            ("scanner/modules/license_scanner.py", "LicenseScanner"),
            ("scanner/modules/compliance_scanner.py", "ComplianceScanner"),
        ]
        
        found_count = 0
        for module_path, module_name in expected_modules:
            full_path = self.base_dir / module_path
            if full_path.exists():
                found_count += 1
            else:
                self.errors.append(f"Missing scanner module: {module_path}")
        
        logger.info(f"  ✓ Found {found_count}/{len(expected_modules)} scanner modules")
        
        # Verify controller registration
        controller_path = self.base_dir / "scanner" / "controller.py"
        if controller_path.exists():
            with open(controller_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for _, module_name in expected_modules:
                    if module_name not in content:
                        self.warnings.append(f"{module_name} may not be registered in controller.py")
    
    def check_template_files(self):
        """Verify all Jinja2 template files exist."""
        templates_dir = self.base_dir / "scanner" / "reporter" / "templates"
        
        if not templates_dir.exists():
            self.errors.append("Templates directory not found: scanner/reporter/templates")
            return
        
        expected_templates = [
            "dashboard.html.j2",
            "consent.html.j2",
        ]
        
        found_count = 0
        for template in expected_templates:
            template_path = templates_dir / template
            if template_path.exists():
                found_count += 1
            else:
                self.errors.append(f"Missing template file: {template}")
        
        logger.info(f"  ✓ Found {found_count}/{len(expected_templates)} template files")
    
    def check_dependencies(self):
        """Verify all required dependencies are installed."""
        import importlib.util
        
        required_packages = [
            ("psutil", "psutil"),
            ("Jinja2", "jinja2"),
            ("PyInstaller", "PyInstaller"),
        ]
        
        optional_packages = [
            ("pywebview", "webview", "Required for GUI client"),
        ]
        
        found_count = 0
        for display_name, module_name in required_packages:
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                found_count += 1
            else:
                self.errors.append(f"Missing required package: {display_name}")
        
        logger.info(f"  ✓ Found {found_count}/{len(required_packages)} required packages")
        
        # Check optional packages
        for display_name, module_name, reason in optional_packages:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                self.warnings.append(f"Missing optional package: {display_name} - {reason}")
    
    def check_build_files(self):
        """Verify PyInstaller spec files exist."""
        spec_files = [
            "ai_scanner.spec",  # CLI version
            "client_scanner.spec",  # GUI version
        ]
        
        found_count = 0
        for spec_file in spec_files:
            spec_path = self.base_dir / spec_file
            if spec_path.exists():
                found_count += 1
            else:
                self.errors.append(f"Missing spec file: {spec_file}")
        
        logger.info(f"  ✓ Found {found_count}/{len(spec_files)} spec files")
    
    def check_icon_file(self):
        """Verify icon file exists."""
        icon_path = self.base_dir / "logo.ico"
        if not icon_path.exists():
            self.warnings.append("Icon file not found: logo.ico (build will use default icon)")
        else:
            logger.info("  ✓ Icon file found")
    
    def check_baseline_dir(self):
        """Verify baseline directory exists."""
        baseline_dir = self.base_dir / "scanner" / "baseline"
        if not baseline_dir.exists():
            self.warnings.append("Baseline directory not found: scanner/baseline")
        else:
            logger.info("  ✓ Baseline directory found")
    
    def check_entry_points(self):
        """Verify entry point files exist and are valid."""
        entry_points = [
            ("main.py", "CLI entry point"),
            ("gui.py", "GUI entry point"),
        ]
        
        found_count = 0
        for entry_file, description in entry_points:
            entry_path = self.base_dir / entry_file
            if entry_path.exists():
                found_count += 1
                # Verify it's a valid Python file
                try:
                    with open(entry_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'def main()' not in content and '__main__' not in content:
                            self.warnings.append(f"{entry_file} may not have proper main entry point")
                except Exception as e:
                    self.warnings.append(f"Could not read {entry_file}: {e}")
            else:
                self.errors.append(f"Missing {description}: {entry_file}")
        
        logger.info(f"  ✓ Found {found_count}/{len(entry_points)} entry point files")
    
    def check_spec_files(self):
        """Verify spec files are properly configured."""
        spec_configs = [
            ("ai_scanner.spec", "main.py", "ai_scanner", True),  # CLI: console=True
            ("client_scanner.spec", "gui.py", "client_scanner", False),  # GUI: console=False
        ]
        
        for spec_file, expected_entry, expected_name, expected_console in spec_configs:
            spec_path = self.base_dir / spec_file
            if not spec_path.exists():
                continue
            
            try:
                with open(spec_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check entry point
                    if expected_entry not in content:
                        self.warnings.append(f"{spec_file}: Entry point may not be {expected_entry}")
                    
                    # Check console mode
                    console_str = f"console={expected_console}"
                    if console_str not in content:
                        self.warnings.append(f"{spec_file}: Console mode may not be set correctly")
                    
                    # Check data files
                    if 'scanner/reporter/templates' not in content:
                        self.errors.append(f"{spec_file}: Templates directory not included in datas")
                    
            except Exception as e:
                self.warnings.append(f"Could not verify {spec_file}: {e}")


class BuildExecutor:
    """Executes the build process for both versions."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.dist_dir = self.base_dir / "dist"
    
    def clean_build_dirs(self):
        """Clean previous build artifacts."""
        logger.info("Cleaning previous build artifacts...")
        
        dirs_to_clean = ["build", "dist"]
        for dir_name in dirs_to_clean:
            dir_path = self.base_dir / dir_name
            if dir_path.exists():
                logger.info(f"  Removing {dir_name}/")
                try:
                    import shutil
                    shutil.rmtree(dir_path)
                except Exception as e:
                    logger.warning(f"  Could not remove {dir_name}/: {e}")
    
    def build_cli_version(self) -> bool:
        """Build the CLI version (System Scanner.exe)."""
        logger.info("=" * 70)
        logger.info("BUILDING CLI VERSION - System Scanner.exe")
        logger.info("=" * 70)
        
        try:
            # Build using PyInstaller via python -m
            cmd = [
                "python",
                "-m",
                "PyInstaller",
                "--clean",
                "--noconfirm",
                "ai_scanner.spec"
            ]
            
            logger.info("Running: %s", " ".join(cmd))
            result = subprocess.run(cmd, cwd=self.base_dir, check=True, capture_output=True, text=True)
            
            # Rename output
            output_file = self.dist_dir / "System Scanner.exe"
            
            if output_file.exists():
                logger.info("✅ CLI version built successfully: %s", output_file)
                return True
            else:
                logger.error("❌ Build completed but executable not found")
                logger.error("PyInstaller output: %s", result.stdout[-500:] if result.stdout else "No output")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error("❌ CLI build failed: %s", e)
            logger.error("Error output: %s", e.stderr if hasattr(e, 'stderr') else "No error details")
            return False
        except Exception as e:
            logger.error("❌ Unexpected error during CLI build: %s", e)
            return False
    
    def build_gui_version(self) -> bool:
        """Build the GUI version (Client System Scanner.exe)."""
        logger.info("=" * 70)
        logger.info("BUILDING GUI VERSION - Client System Scanner.exe")
        logger.info("=" * 70)
        
        # Check if pywebview is installed
        try:
            import webview
        except ImportError:
            logger.error("❌ pywebview not installed - GUI build requires: pip install pywebview")
            return False
        
        try:
            # Build using PyInstaller via python -m
            cmd = [
                "python",
                "-m",
                "PyInstaller",
                "--clean",
                "--noconfirm",
                "client_scanner.spec"
            ]
            
            logger.info("Running: %s", " ".join(cmd))
            result = subprocess.run(cmd, cwd=self.base_dir, check=True, capture_output=True, text=True)
            
            # Check output
            output_file = self.dist_dir / "Client System Scanner.exe"
            
            if output_file.exists():
                logger.info("✅ GUI version built successfully: %s", output_file)
                return True
            else:
                logger.error("❌ Build completed but executable not found")
                logger.error("PyInstaller output: %s", result.stdout[-500:] if result.stdout else "No output")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error("❌ GUI build failed: %s", e)
            logger.error("Error output: %s", e.stderr if hasattr(e, 'stderr') else "No error details")
            return False
        except Exception as e:
            logger.error("❌ Unexpected error during GUI build: %s", e)
            return False
    
    def verify_builds(self) -> Tuple[bool, Dict[str, any]]:
        """Verify both builds were successful and report file sizes."""
        logger.info("=" * 70)
        logger.info("VERIFYING BUILDS")
        logger.info("=" * 70)
        
        builds = {
            "CLI": self.dist_dir / "System Scanner.exe",
            "GUI": self.dist_dir / "Client System Scanner.exe",
        }
        
        results = {}
        all_ok = True
        
        for build_name, build_path in builds.items():
            if build_path.exists():
                size_mb = build_path.stat().st_size / (1024 * 1024)
                logger.info(f"✅ {build_name}: {build_path.name} ({size_mb:.2f} MB)")
                results[build_name] = {
                    "path": build_path,
                    "size_mb": size_mb,
                    "success": True
                }
            else:
                logger.error(f"❌ {build_name}: Not found at {build_path}")
                results[build_name] = {
                    "path": build_path,
                    "success": False
                }
                all_ok = False
        
        return all_ok, results


def main():
    """Main build script entry point."""
    logger.info("AI DISCOVERY SCANNER - Build Both Versions Script")
    logger.info("=" * 70)
    
    # Step 1: Verify all requirements
    verifier = BuildVerifier()
    if not verifier.verify_all():
        logger.error("Pre-build verification failed. Please fix errors before building.")
        sys.exit(1)
    
    # Step 2: Ask user confirmation
    logger.info("")
    logger.info("Ready to build both versions:")
    logger.info("  1. CLI System Scanner.exe (Console application)")
    logger.info("  2. Client System Scanner.exe (GUI application)")
    logger.info("")
    
    response = input("Proceed with build? [y/N]: ").strip().lower()
    if response not in ['y', 'yes']:
        logger.info("Build cancelled by user.")
        sys.exit(0)
    
    # Step 3: Execute builds
    executor = BuildExecutor()
    
    # Clean previous builds
    executor.clean_build_dirs()
    
    # Build CLI version
    cli_success = executor.build_cli_version()
    
    # Build GUI version
    gui_success = executor.build_gui_version()
    
    # Verify builds
    all_ok, results = executor.verify_builds()
    
    # Final report
    logger.info("=" * 70)
    logger.info("BUILD SUMMARY")
    logger.info("=" * 70)
    
    if cli_success and gui_success and all_ok:
        logger.info("✅ All builds completed successfully!")
        logger.info("")
        logger.info("Output files:")
        for build_name, info in results.items():
            if info["success"]:
                logger.info(f"  {build_name}: {info['path']} ({info['size_mb']:.2f} MB)")
        logger.info("")
        logger.info("You can now distribute both executables.")
        sys.exit(0)
    else:
        logger.error("❌ Some builds failed. Check logs above for details.")
        if cli_success:
            logger.info("  ✓ CLI version built successfully")
        else:
            logger.error("  ✗ CLI version build failed")
        
        if gui_success:
            logger.info("  ✓ GUI version built successfully")
        else:
            logger.error("  ✗ GUI version build failed")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
