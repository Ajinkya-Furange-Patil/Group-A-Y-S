"""
Unit tests for the Package Scanner module (scanner/modules/package_scanner.py).

These tests target the pip scanner sub-function (_scan_pip) directly to keep
them isolated from the other global package scanners (npm, pipx, uv, homebrew,
conda) that are covered in test_package_scanner_global.py.
"""

import json
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from scanner.models import FindingCategory, RiskLevel
from scanner.modules import package_scanner
from scanner.modules.package_scanner import _scan_pip


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

        # Test _scan_pip directly — isolated from npm/pipx/uv/conda scanners
        findings = _scan_pip()

        self.assertEqual(len(findings), 3)

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

        # Test _scan_pip fallback path directly
        findings = _scan_pip()

        self.assertEqual(len(findings), 2)

        f_tf = next(f for f in findings if f.details["package_name"] == "tensorflow")
        self.assertEqual(f_tf.title, "Package: tensorflow (2.14.0)")
        self.assertEqual(f_tf.category, FindingCategory.ML_FRAMEWORK)

        f_lc = next(f for f in findings if f.details["package_name"] == "langchain")
        self.assertEqual(f_lc.title, "Package: langchain (0.0.350)")
        self.assertEqual(f_lc.category, FindingCategory.AI_AGENT)

    @patch("scanner.modules.package_scanner._scan_npm_global", return_value=[])
    @patch("scanner.modules.package_scanner._scan_pipx", return_value=[])
    @patch("scanner.modules.package_scanner._scan_uv_tools", return_value=[])
    @patch("scanner.modules.package_scanner._scan_homebrew", return_value=[])
    @patch("scanner.modules.package_scanner._scan_conda", return_value=[])
    @patch("scanner.modules.package_scanner._scan_pip_global_envs", return_value=[])
    @patch("scanner.modules.package_scanner._scan_pip", side_effect=RuntimeError("pip totally broken"))
    def test_run_both_fail(
        self,
        _mock_pip,
        _mock_pip_global,
        _mock_conda,
        _mock_brew,
        _mock_uv,
        _mock_pipx,
        _mock_npm,
    ):
        # All scanners are mocked — pip raises, all others return [].
        # errors is populated by pip's exception; findings is empty → status = error.
        findings, info = package_scanner.run()

        self.assertEqual(info.status, "error")
        self.assertIn("pip", info.error_message)
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
