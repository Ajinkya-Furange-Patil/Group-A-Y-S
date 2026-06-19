"""
Unit tests for the License Scanner module (scanner/modules/license_scanner.py).
"""

import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from scanner.models import FindingCategory, RiskLevel
from scanner.modules import license_scanner


class TestLicenseScanner(unittest.TestCase):
    def test_scan_py_file_ast_docstring(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            file_path = temp_path / "copyleft_script.py"
            
            # Script with AGPL mention in module docstring
            code_content = '''"""
This module is distributed under the AGPL license terms.
"""
import sys

def main():
    pass
'''
            file_path.write_text(code_content, encoding="utf-8")
            
            findings = license_scanner.scan_py_file_ast(file_path)
            
            # We expect a finding for the AGPL header
            self.assertEqual(len(findings), 1)
            f = findings[0]
            self.assertEqual(f.category, FindingCategory.CONFIGURATION)
            self.assertEqual(f.risk_level, RiskLevel.CRITICAL)
            self.assertIn("AGPL Header", f.title)
            self.assertEqual(f.details["license_detected"], "AGPL")

    def test_scan_py_file_ast_imports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            file_path = temp_path / "imports_script.py"
            
            # Script with GPL PyQt5 import
            code_content = '''
import sys
from PyQt5.QtWidgets import QApplication
import mysql.connector

def main():
    pass
'''
            file_path.write_text(code_content, encoding="utf-8")
            
            findings = license_scanner.scan_py_file_ast(file_path)
            
            # We expect findings for:
            # 1. PyQt5 (GPL, RiskLevel.HIGH)
            # 2. mysql.connector (GPL, RiskLevel.HIGH)
            self.assertEqual(len(findings), 2)
            
            libs = [f.details["library_imported"] for f in findings]
            self.assertIn("PyQt5.QtWidgets", libs)
            self.assertIn("mysql.connector", libs)
            for f in findings:
                self.assertEqual(f.risk_level, RiskLevel.HIGH)
                self.assertEqual(f.details["license_type"], "GPL")

    def test_scan_workspace_license_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            
            # Write a LICENSE file
            license_file = temp_path / "LICENSE"
            license_file.write_text("Copyright (c) 2026. This is licensed under MIT terms.", encoding="utf-8")
            
            findings = license_scanner.scan_workspace_license_files(temp_path)
            
            self.assertEqual(len(findings), 1)
            f = findings[0]
            self.assertEqual(f.category, FindingCategory.CONFIGURATION)
            self.assertEqual(f.risk_level, RiskLevel.INFO)
            self.assertEqual(f.details["license_detected"], "MIT")
            self.assertEqual(f.details["status"], "Approved")

    @patch("pathlib.Path.cwd")
    def test_run_traversal(self, mock_cwd):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            mock_cwd.return_value = temp_path

            # Create test project directory structure
            (temp_path / "subdir").mkdir()
            (temp_path / "venv").mkdir()
            
            # Valid file in root
            (temp_path / "app.py").write_text('"""AGPL license"""\n', encoding="utf-8")
            # Valid file in subdir
            (temp_path / "subdir" / "util.py").write_text('import PyQt5\n', encoding="utf-8")
            # File in excluded venv dir (should be skipped)
            (temp_path / "venv" / "lib.py").write_text('import PyQt5\n', encoding="utf-8")

            findings, info = license_scanner.run(scan_folder=str(temp_path), max_depth=2)

            self.assertEqual(info.status, "success")
            self.assertEqual(info.findings_count, len(findings))
            
            # Findings should be:
            # 1. app.py (AGPL)
            # 2. subdir/util.py (PyQt5)
            # And should NOT contain venv/lib.py
            self.assertEqual(len(findings), 2)
            
            files = [f.details["file_path"] for f in findings]
            self.assertTrue(any("app.py" in fl for fl in files))
            self.assertTrue(any("util.py" in fl for fl in files))
            self.assertFalse(any("lib.py" in fl for fl in files))

    def test_class_wrapper(self):
        scanner = license_scanner.LicenseScanner(scan_folder="some_folder", max_depth=3)
        self.assertEqual(scanner.MODULE_NAME, "LicenseScanner")
        self.assertEqual(scanner.MODULE_NUMBER, 9)
        self.assertEqual(scanner.scan_folder, "some_folder")
        self.assertEqual(scanner.max_depth, 3)

        with patch.object(license_scanner, "run") as mock_run:
            mock_run.return_value = ([], license_scanner.ModuleInfo(name="LicenseScanner", module_number=9))
            findings = scanner.scan()
            self.assertEqual(findings, [])
            mock_run.assert_called_once_with("some_folder", 3)


if __name__ == "__main__":
    unittest.main()
