"""
Unit tests for the Package Scanner module (scanner/modules/package_scanner.py).
"""

import json
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from scanner.models import FindingCategory, RiskLevel
from scanner.modules import package_scanner


class TestPackageScanner(unittest.TestCase):
    @patch("subprocess.run")
    def test_run_success(self, mock_run):
        # Setup mock subprocess.run response
        mock_stdout = json.dumps([
            {"name": "torch", "version": "2.11.0"},
            {"name": "requests", "version": "2.31.0"},
            {"name": "openai", "version": "1.3.0"},
            {"name": "pyautogen", "version": "0.2.0"},
            {"name": "normal-pkg", "version": "1.0.0"}
        ])
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_stdout
        mock_run.return_value = mock_result

        findings, info = package_scanner.run()

        self.assertEqual(info.status, "success")
        self.assertEqual(len(findings), 3)
        self.assertEqual(info.findings_count, 3)

        # Check torch finding
        f_torch = next(f for f in findings if f.details["package_name"] == "torch")
        self.assertEqual(f_torch.title, "Package: torch (2.11.0)")
        self.assertEqual(f_torch.category, FindingCategory.ML_FRAMEWORK)
        self.assertEqual(f_torch.risk_level, RiskLevel.INFO)
        self.assertEqual(f_torch.details["version"], "2.11.0")

        # Check openai finding
        f_openai = next(f for f in findings if f.details["package_name"] == "openai")
        self.assertEqual(f_openai.title, "Package: openai (1.3.0)")
        self.assertEqual(f_openai.category, FindingCategory.ML_FRAMEWORK)

        # Check pyautogen finding (mapped to autogen target)
        f_autogen = next(f for f in findings if f.details["package_name"] == "pyautogen")
        self.assertEqual(f_autogen.title, "Package: pyautogen (0.2.0)")
        self.assertEqual(f_autogen.category, FindingCategory.AI_AGENT)

    @patch("subprocess.run")
    @patch("importlib.metadata.version")
    def test_run_subprocess_fails_fallback_success(self, mock_metadata_version, mock_run):
        # Subprocess fails
        mock_run.side_effect = subprocess.SubprocessError("pip is broken")

        # Mock importlib.metadata behavior
        def mock_version(pkg_name):
            if pkg_name == "tensorflow":
                return "2.14.0"
            elif pkg_name == "langchain":
                return "0.0.350"
            else:
                import importlib.metadata
                raise importlib.metadata.PackageNotFoundError()

        mock_metadata_version.side_effect = mock_version

        findings, info = package_scanner.run()

        # Should fallback and still succeed
        self.assertEqual(info.status, "success")
        self.assertEqual(len(findings), 2)
        
        f_tf = next(f for f in findings if f.details["package_name"] == "tensorflow")
        self.assertEqual(f_tf.title, "Package: tensorflow (2.14.0)")
        self.assertEqual(f_tf.category, FindingCategory.ML_FRAMEWORK)

        f_lc = next(f for f in findings if f.details["package_name"] == "langchain")
        self.assertEqual(f_lc.title, "Package: langchain (0.0.350)")
        self.assertEqual(f_lc.category, FindingCategory.AI_AGENT)

    @patch("subprocess.run")
    @patch("importlib.metadata.version")
    def test_run_both_fail(self, mock_metadata_version, mock_run):
        # Subprocess fails
        mock_run.side_effect = subprocess.SubprocessError("pip list failed")
        # Metadata version fallback fails
        mock_metadata_version.side_effect = Exception("metadata service is corrupted")

        findings, info = package_scanner.run()

        self.assertEqual(info.status, "error")
        self.assertIn("Failed to list packages", info.error_message)
        self.assertEqual(len(findings), 0)

    def test_class_wrapper(self):
        scanner = package_scanner.PackageScanner()
        self.assertEqual(scanner.MODULE_NAME, "PackageScanner")
        self.assertEqual(scanner.MODULE_NUMBER, 4)
        
        with patch.object(package_scanner, "run") as mock_run:
            mock_run.return_value = ([], package_scanner.ModuleInfo(name="PackageScanner", module_number=4))
            findings = scanner.scan()
            self.assertEqual(findings, [])
            mock_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
