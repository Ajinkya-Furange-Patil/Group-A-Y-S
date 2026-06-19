import unittest
import os
import tempfile
import pathlib
import json
from unittest.mock import patch, MagicMock

from scanner.modules.package_scanner import (
    _get_package_metadata_hash,
    _verify_against_baseline,
    run
)
from scanner.models import Finding, RiskLevel


class TestPackageVerification(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for fake package files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pkg_dir = pathlib.Path(self.temp_dir.name) / "testpkg"
        self.pkg_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_package_metadata_hash_npm(self):
        # Create a dummy package.json
        package_json = self.pkg_dir / "package.json"
        package_json.write_text('{"name": "testpkg", "version": "1.0.0"}', encoding="utf-8")

        calc_hash = _get_package_metadata_hash("testpkg", "1.0.0", str(self.pkg_dir), "npm")
        self.assertIsNotNone(calc_hash)
        self.assertEqual(len(calc_hash), 64)  # SHA-256 length

    @patch("scanner.modules.package_scanner._verify_against_baseline")
    @patch("scanner.modules.package_scanner._get_package_metadata_hash")
    @patch("scanner.modules.package_scanner._scan_pip")
    def test_run_package_scanner_flagging(self, mock_scan_pip, mock_get_hash, mock_verify):
        # Setup mock findings
        finding_tampered = Finding(
            module_name="PackageScanner",
            title="Package: openai (1.58.1)",
            description="openai library",
            source="loc1",
            details={
                "package_name": "openai",
                "version": "1.58.1",
                "installer": "pip",
                "install_location": "loc1"
            }
        )

        finding_verified = Finding(
            module_name="PackageScanner",
            title="Package: psutil (7.2.2)",
            description="psutil library",
            source="loc2",
            details={
                "package_name": "psutil",
                "version": "7.2.2",
                "installer": "pip",
                "install_location": "loc2"
            }
        )

        mock_scan_pip.return_value = [finding_tampered, finding_verified]
        
        # Mocks hash calculation & baseline lookup
        mock_get_hash.side_effect = lambda name, ver, loc, inst: "hash_xyz"
        mock_verify.side_effect = lambda installer, name, version, calc_hash: (
            ("tampered", False, True) if name == "openai" else ("verified", True, False)
        )

        # Run scanner
        findings, info = run()

        # Find findings by package name
        f_openai = next(f for f in findings if f.details.get("package_name") == "openai")
        f_psutil = next(f for f in findings if f.details.get("package_name") == "psutil")

        # openai should be flagged as TAMPERED with HIGH risk
        self.assertEqual(f_openai.risk_level, RiskLevel.HIGH)
        self.assertTrue(f_openai.title.startswith("[TAMPERED]"))
        self.assertIn("WARNING: Cryptographic hash does not match baseline", f_openai.description)

        # psutil should be verified with INFO risk
        self.assertEqual(f_psutil.risk_level, RiskLevel.INFO)
        self.assertFalse(f_psutil.title.startswith("[TAMPERED]"))
        self.assertIn("Verified package integrity", f_psutil.description)

    def test_verify_against_baseline_not_found(self):
        status, verified, tampered = _verify_against_baseline("pip", "nonexistent-pkg", "1.0.0", "hash")
        self.assertEqual(status, "unverified")
        self.assertFalse(verified)
        self.assertFalse(tampered)


if __name__ == "__main__":
    unittest.main()
