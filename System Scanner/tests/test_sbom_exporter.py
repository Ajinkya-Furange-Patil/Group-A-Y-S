import unittest
import os
import tempfile
import json

from scanner.models import ScanResult, Finding, FindingCategory, RiskLevel
from scanner.reporter.exporter import export_sbom_json


class TestSBOMExporter(unittest.TestCase):
    def setUp(self):
        # Create a temp file path
        self.tmpfile = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        self.tmpfile.close()

        # Create dummy scan result
        self.scan_result = ScanResult(
            hostname="test-host",
            os_info="Windows 11",
        )
        # Add a package scanner finding
        self.scan_result.findings.append(
            Finding(
                module_name="PackageScanner",
                title="Package: openai (1.58.1)",
                description="openai client library",
                source="pip://openai",
                category=FindingCategory.ML_FRAMEWORK,
                risk_level=RiskLevel.INFO,
                details={
                    "package_name": "openai",
                    "version": "1.58.1",
                    "installer": "pip",
                    "install_location": "venv/site-packages/openai",
                    "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    "verification_status": "verified",
                    "verified": True,
                    "tampered": False
                }
            )
        )
        self.scan_result.compute_summary()

    def tearDown(self):
        if os.path.exists(self.tmpfile.name):
            os.remove(self.tmpfile.name)

    def test_export_cyclonedx(self):
        export_sbom_json(self.scan_result, self.tmpfile.name, "cyclonedx")
        self.assertTrue(os.path.exists(self.tmpfile.name))

        with open(self.tmpfile.name, encoding="utf-8") as f:
            sbom = json.load(f)

        # Validate CycloneDX structure
        self.assertEqual(sbom.get("bomFormat"), "CycloneDX")
        self.assertEqual(sbom.get("specVersion"), "1.5")
        self.assertIn("metadata", sbom)
        self.assertIn("components", sbom)

        components = sbom["components"]
        self.assertEqual(len(components), 1)
        comp = components[0]
        self.assertEqual(comp.get("name"), "openai")
        self.assertEqual(comp.get("version"), "1.58.1")
        self.assertEqual(comp.get("purl"), "pkg:pip/openai@1.58.1")

        # Validate hashes
        hashes = comp.get("hashes", [])
        self.assertEqual(len(hashes), 1)
        self.assertEqual(hashes[0]["alg"], "SHA-256")
        self.assertEqual(hashes[0]["content"], "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

        # Validate SEBI properties
        properties = comp.get("properties", [])
        self.assertTrue(any(
            p["name"] == "sebi:cscrf:verification" and p["value"] == "verified"
            for p in properties
        ))

    def test_export_spdx(self):
        export_sbom_json(self.scan_result, self.tmpfile.name, "spdx")
        self.assertTrue(os.path.exists(self.tmpfile.name))

        with open(self.tmpfile.name, encoding="utf-8") as f:
            sbom = json.load(f)

        # Validate SPDX structure
        self.assertEqual(sbom.get("spdxVersion"), "SPDX-2.3")
        self.assertIn("creationInfo", sbom)
        self.assertIn("packages", sbom)

        packages = sbom["packages"]
        self.assertEqual(len(packages), 1)
        pkg = packages[0]
        self.assertEqual(pkg.get("name"), "openai")
        self.assertEqual(pkg.get("versionInfo"), "1.58.1")

        # Validate checksum
        checksums = pkg.get("checksums", [])
        self.assertEqual(len(checksums), 1)
        self.assertEqual(checksums[0]["algorithm"], "SHA256")
        self.assertEqual(checksums[0]["checksumValue"], "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

        # Validate comment fields
        comment = pkg.get("comment", "")
        self.assertIn("SEBI CSCRF Verification Status: verified", comment)


if __name__ == "__main__":
    unittest.main()
