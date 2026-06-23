import unittest
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from scanner.repo_scanner import parse_github_url, download_repo_zip, extract_zip, scan_repository, run_repo_scan

class TestRepoScanner(unittest.TestCase):
    
    def test_parse_github_url(self):
        # Valid URLs
        self.assertEqual(parse_github_url("https://github.com/owner/repo"), ("owner", "repo"))
        self.assertEqual(parse_github_url("https://github.com/owner/repo.git"), ("owner", "repo"))
        self.assertEqual(parse_github_url("https://github.com/owner/repo/"), ("owner", "repo"))
        # Invalid URLs
        self.assertIsNone(parse_github_url("https://google.com/owner/repo"))
        self.assertIsNone(parse_github_url("not_a_url"))

    @patch("urllib.request.urlopen")
    def test_download_repo_zip(self, mock_urlopen):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.read.return_value = b"zip_content_mock"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = download_repo_zip("owner", "repo", tmp_dir)
            self.assertIsNotNone(zip_path)
            self.assertTrue(os.path.exists(zip_path))
            with open(zip_path, "rb") as f:
                self.assertEqual(f.read(), b"zip_content_mock")

    def test_scan_repository_mock(self):
        # Create a mock repository directory structure with dependencies and code files
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            
            # 1. Add requirements.txt with torch and openai
            req_file = repo_path / "requirements.txt"
            with open(req_file, "w", encoding="utf-8") as f:
                f.write("torch>=2.0.0\nopenai\n")
                
            # 2. Add an agent code file
            agent_file = repo_path / "agent.py"
            with open(agent_file, "w", encoding="utf-8") as f:
                f.write("from langchain.chat_models import ChatOpenAI\n")
                f.write("agent = AgentExecutor(tools=[])\n")
                f.write("print('gpt-4')\n")
                
            # 3. Add a config env file
            env_file = repo_path / ".env"
            with open(env_file, "w", encoding="utf-8") as f:
                f.write("OPENAI_API_KEY=sk-proj-xxxx\n")
                
            # Run scan
            report = scan_repository(tmp_dir, "https://github.com/owner/repo")
            
            self.assertEqual(report["repository"], "https://github.com/owner/repo")
            self.assertIn("Python", report["languages"])
            # Frameworks
            self.assertIn("openai", report["frameworks"])
            # Models
            self.assertIn("gpt-4", report["models"])
            # Components
            self.assertIn("Agent", report["components"])
            # Confidence score - Ecosystem + Code + Config = 95
            self.assertEqual(report["confidence_score"], 95)
            
            # Findings structure
            self.assertGreater(len(report["findings"]), 0)
            finding = report["findings"][0]
            self.assertIn("file", finding)
            self.assertIn("line", finding)
            self.assertIn("category", finding)
            self.assertIn("snippet", finding)

if __name__ == "__main__":
    unittest.main()
