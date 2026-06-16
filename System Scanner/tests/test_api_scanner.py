"""
Unit tests for the API Scanner module (scanner/modules/api_scanner.py).
"""

import os
import pathlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from scanner.modules.api_scanner import APIScanner
from scanner.models import FindingCategory, RiskLevel


class TestAPIScanner(unittest.TestCase):
    def setUp(self):
        self.scanner = APIScanner(target_dir=".")

    def test_mask_key(self):
        # Long key masking
        masked = self.scanner._mask_key("sk-proj-1234567890abcdef1234567890abcdef12345678", "sk-...")
        self.assertEqual(masked, "sk-...5678")

        # Short key masking
        masked_short = self.scanner._mask_key("123", "key...")
        self.assertEqual(masked_short, "********")

    def test_scan_file_openai_key(self):
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".env", delete=False) as f:
            f.write("OPENAI_API_KEY=\"sk-proj-abcdef1234567890abcdef1234567890abcdef12\"\n")
            file_path = f.name

        try:
            findings = self.scanner._scan_file(file_path)
            self.assertEqual(len(findings), 1)
            finding = findings[0]
            self.assertEqual(finding.title, "Exposed OpenAI API Key")
            self.assertEqual(finding.category, FindingCategory.CONFIGURATION)
            self.assertEqual(finding.risk_level, RiskLevel.CRITICAL)
            self.assertEqual(finding.details["masked_key"], "sk-...ef12")
        finally:
            os.unlink(file_path)

    def test_scan_file_generic_and_aws(self):
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as f:
            # Match Generic and AWS key
            f.write("api_token = 'my_secure_api_token_value_longer_than_20'\n")
            f.write("aws_id = 'AKIAIOSFODNN7EXAMPLE'\n")
            file_path = f.name

        try:
            findings = self.scanner._scan_file(file_path)
            # Should match generic key and AWS Access Key ID
            self.assertEqual(len(findings), 2)
            
            generic_finding = next(f for f in findings if "Generic" in f.title)
            self.assertEqual(generic_finding.risk_level, RiskLevel.HIGH)
            self.assertEqual(generic_finding.details["masked_key"], "key...n_20" if len(generic_finding.details["masked_key"]) > 8 else "********")

            aws_finding = next(f for f in findings if "AWS Access" in f.title)
            self.assertEqual(aws_finding.risk_level, RiskLevel.CRITICAL)
            self.assertEqual(aws_finding.details["masked_key"], "AKIA...MPLE")
        finally:
            os.unlink(file_path)

    @patch("os.environ")
    def test_scan_environment(self, mock_environ):
        mock_environ.items.return_value = [
            ("OPENAI_API_KEY", "sk-proj-testkeyforopenaienviromentvalues12"),
            ("NORMAL_VAR", "some_value"),
            ("AWS_SECRET_ACCESS_KEY", "awssecretaccesskeyvalueforawsconfig40chars"),
        ]

        findings = self.scanner._scan_environment()
        self.assertEqual(len(findings), 2)

        openai_env = next(f for f in findings if "OPENAI_API_KEY" in f.title)
        self.assertEqual(openai_env.risk_level, RiskLevel.CRITICAL)
        self.assertEqual(openai_env.details["masked_key"], "sk-...es12")

        aws_env = next(f for f in findings if "AWS_SECRET_ACCESS_KEY" in f.title)
        self.assertEqual(aws_env.risk_level, RiskLevel.CRITICAL)
        self.assertEqual(aws_env.details["masked_key"], "aws...hars")


if __name__ == "__main__":
    unittest.main()
