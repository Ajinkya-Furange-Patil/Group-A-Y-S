"""
Unit tests for the Signature and Hash Verifier module (scanner/signature_verifier.py).
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from scanner import signature_verifier


class TestSignatureVerifier(unittest.TestCase):
    def test_calculate_sha256_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            temp_name = tf.name

        try:
            # Hash of an empty file is well-known
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            actual = signature_verifier.calculate_sha256(temp_name)
            self.assertEqual(actual, expected)
        finally:
            os.remove(temp_name)

    def test_calculate_sha256_with_content(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b"Hello World")
            temp_name = tf.name

        try:
            expected = "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
            actual = signature_verifier.calculate_sha256(temp_name)
            self.assertEqual(actual, expected)
        finally:
            os.remove(temp_name)

    def test_calculate_sha256_non_existent(self):
        actual = signature_verifier.calculate_sha256("non_existent_file_path.xyz")
        self.assertEqual(actual, "")

    def test_verify_windows_signature_python_exe(self):
        # On Windows, python.exe should have a valid signature
        if sys.platform == "win32":
            res = signature_verifier.verify_windows_signature(sys.executable)
            # Some local dev Pythons might be unsigned, but standard distributions are signed
            # We check that it returns a structured dict
            self.assertIn("verified", res)
            self.assertIn("status", res)
            self.assertIn("subject", res)
            self.assertIn("issuer", res)
        else:
            res = signature_verifier.verify_windows_signature("/bin/sh")
            self.assertEqual(res["status"], "Unsupported on this OS")

    def test_verify_executable_empty_test_binary(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            temp_name = tf.name

        try:
            res = signature_verifier.verify_executable(temp_name)
            self.assertEqual(res["sha256_hash"], "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
            self.assertTrue(res["hash_verified"])
            self.assertEqual(res["approved_client"], "GitHub Copilot")
            self.assertEqual(res["description"], "Empty Test Binary (Verified Baseline)")
        finally:
            os.remove(temp_name)

    def test_verify_executable_unverified_hash(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b"unverified content")
            temp_name = tf.name

        try:
            res = signature_verifier.verify_executable(temp_name)
            self.assertFalse(res["hash_verified"])
            self.assertIsNone(res["approved_client"])
            self.assertIsNone(res["description"])
        finally:
            os.remove(temp_name)


if __name__ == "__main__":
    unittest.main()
