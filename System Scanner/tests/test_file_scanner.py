"""
Unit tests for the File Scanner module (scanner/modules/file_scanner.py).
"""

import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from scanner.modules import file_scanner
from scanner.models import FindingCategory, RiskLevel


class TestFileScanner(unittest.TestCase):
    def test_format_size(self):
        self.assertEqual(file_scanner._format_size(100), "100.00 B")
        self.assertEqual(file_scanner._format_size(1024), "1.00 KB")
        self.assertEqual(file_scanner._format_size(1024 * 1024 * 5.5), "5.50 MB")
        self.assertEqual(file_scanner._format_size(1024 * 1024 * 1024 * 2.3), "2.30 GB")

    def test_scan_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)

            # Create test files
            (temp_path / "model1.gguf").write_bytes(b"dummy gguf content")
            (temp_path / "model2.safetensors").write_bytes(b"dummy safetensors content")
            (temp_path / "normal_file.txt").write_text("hello world")

            # Excluded directory
            git_dir = temp_path / ".git"
            git_dir.mkdir()
            (git_dir / "hidden_model.gguf").write_bytes(b"dummy")

            # Normal subdirectory
            sub_dir = temp_path / "projects" / "ai"
            sub_dir.mkdir(parents=True)
            (sub_dir / "model3.pt").write_bytes(b"dummy pyTorch")

            # Deep subdirectory (beyond depth 4)
            deep_dir = sub_dir / "level1" / "level2" / "level3" / "level4"
            deep_dir.mkdir(parents=True)
            (deep_dir / "deep_model.onnx").write_bytes(b"too deep")

            # Scan temp directory with depth 4
            scanned_files = set()
            findings = file_scanner.scan_directory(temp_path, max_depth=4, scanned_files=scanned_files)

            # Assertions
            titles = [f.title for f in findings]
            self.assertIn("model1.gguf", titles)
            self.assertIn("model2.safetensors", titles)
            self.assertIn("model3.pt", titles)

            # Should exclude hidden/excluded directories and deep directories
            self.assertNotIn("hidden_model.gguf", titles)
            self.assertNotIn("deep_model.onnx", titles)
            self.assertNotIn("normal_file.txt", titles)

            # Check details of a finding
            f_model1 = next(f for f in findings if f.title == "model1.gguf")
            self.assertEqual(f_model1.category, FindingCategory.AI_MODEL)
            self.assertEqual(f_model1.risk_level, RiskLevel.INFO)
            self.assertEqual(f_model1.details["extension"], ".gguf")
            self.assertEqual(f_model1.details["file_size_bytes"], 18)
            self.assertEqual(f_model1.details["file_size_formatted"], "18.00 B")

    @patch("pathlib.Path.home")
    def test_run_with_mocked_home(self, mock_home):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            mock_home.return_value = temp_path

            # Create standard folders under mocked home
            downloads = temp_path / "Downloads"
            downloads.mkdir()
            (downloads / "downloaded_model.gguf").write_bytes(b"download")

            cache_hf = temp_path / ".cache" / "huggingface"
            cache_hf.mkdir(parents=True)
            (cache_hf / "cached_model.safetensors").write_bytes(b"cache")

            # Execute run
            findings, info = file_scanner.run()

            self.assertEqual(info.status, "success")
            self.assertEqual(len(findings), 2)
            self.assertEqual(info.findings_count, 2)

            titles = [f.title for f in findings]
            self.assertIn("downloaded_model.gguf", titles)
            self.assertIn("cached_model.safetensors", titles)

    @patch("pathlib.Path.home")
    def test_wrapper_and_env_targets(self, mock_home):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            mock_home.return_value = temp_path

            # Mock local appdata path to be in our temp directory
            mock_appdata = temp_path / "LocalAppData"
            mock_lm_studio = mock_appdata / "lm-studio"
            mock_lm_studio.mkdir(parents=True)
            (mock_lm_studio / "lm_model.onnx").write_bytes(b"lm")

            with patch.dict("os.environ", {"LOCALAPPDATA": str(mock_appdata)}):
                # Create standard folders under mocked home
                cache_lm = temp_path / ".cache" / "lm-studio"
                cache_lm.mkdir(parents=True)
                (cache_lm / "cached_lm_model.safetensors").write_bytes(b"cached_lm")

                # Instantiate and scan
                scanner = file_scanner.FileScanner()
                self.assertEqual(scanner.MODULE_NAME, "FileScanner")
                self.assertEqual(scanner.MODULE_NUMBER, 2)
                
                findings = scanner.scan()
                titles = [f.title for f in findings]
                self.assertIn("lm_model.onnx", titles)
                self.assertIn("cached_lm_model.safetensors", titles)


if __name__ == "__main__":
    unittest.main()
