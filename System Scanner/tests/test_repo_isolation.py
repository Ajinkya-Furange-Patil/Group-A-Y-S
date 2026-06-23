"""
Unit tests for GitHub Repository Isolation & Folder-Aware scanning features.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from scanner.controller import ScanController
from scanner.models import FindingCategory, RiskLevel


class TestRepoIsolation(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory structure simulating a repository
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)

        # 1. Write requirements.txt
        reqs_content = (
            "torch==2.1.0\n"
            "openai>=1.2.0\n"
            "requests==2.31.0\n"  # should be ignored (not AI package)
        )
        (self.test_path / "requirements.txt").write_text(reqs_content, encoding="utf-8")

        # 2. Write package.json
        pkg_content = {
            "name": "test-repo",
            "version": "1.0.0",
            "dependencies": {
                "@anthropic-ai/claude-code": "^0.1.0",
                "lodash": "^4.17.21"  # ignored
            }
        }
        (self.test_path / "package.json").write_text(json.dumps(pkg_content), encoding="utf-8")

        # 3. Write .mcp.json
        mcp_content = {
            "mcpServers": {
                "sqlite": {
                    "command": "uvx",
                    "args": ["mcp-server-sqlite", "--db-path", "test.db"]
                }
            }
        }
        (self.test_path / ".mcp.json").write_text(json.dumps(mcp_content), encoding="utf-8")

        # 4. Write .python-version
        (self.test_path / ".python-version").write_text("3.11.5\n", encoding="utf-8")

        # 5. Write Dockerfile
        docker_content = (
            "FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime\n"
            "COPY . /app\n"
            "WORKDIR /app\n"
        )
        (self.test_path / "Dockerfile").write_text(docker_content, encoding="utf-8")

    def tearDown(self):
        # Cleanup temporary files
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_repo_scan_isolation(self):
        # Initialize controller in repo_mode
        controller = ScanController(
            scan_folder=self.test_dir,
            repo_mode=True,
            max_depth=5
        )

        # Execute scan
        result = controller.run_scan()

        # 1. Assert Host Identity override
        self.assertEqual(result.os_info, "Remote Repository Scan")
        self.assertTrue(result.hostname.startswith("GitHub Repo:"))

        # 2. Assert module registration: System and Process scanners MUST be skipped
        modules_run = [mod.name for mod in result.modules]
        self.assertNotIn("SystemScanner", modules_run)
        self.assertNotIn("ProcessScanner", modules_run)

        # 3. Verify PackageScanner findings
        pkg_findings = [f for f in result.findings if f.module_name == "PackageScanner"]
        # Should have found torch, openai, and claude-code, but not requests or lodash
        self.assertEqual(len(pkg_findings), 3)

        torch_finding = next(f for f in pkg_findings if f.details.get("package_name") == "torch")
        self.assertEqual(torch_finding.details.get("version"), "2.1.0")
        self.assertEqual(torch_finding.details.get("installer"), "repo:requirements.txt")
        self.assertEqual(torch_finding.details.get("verification_status"), "unverified")
        self.assertFalse(torch_finding.details.get("tampered"))

        openai_finding = next(f for f in pkg_findings if f.details.get("package_name") == "openai")
        self.assertEqual(openai_finding.details.get("version"), "1.2.0")
        self.assertEqual(openai_finding.details.get("installer"), "repo:requirements.txt")

        claude_finding = next(f for f in pkg_findings if f.details.get("package_name") == "@anthropic-ai/claude-code")
        self.assertEqual(claude_finding.details.get("version"), "0.1.0")
        self.assertEqual(claude_finding.details.get("installer"), "repo:package.json")

        # 4. Verify MCPScanner findings
        mcp_findings = [f for f in result.findings if f.module_name == "MCPScanner"]
        self.assertEqual(len(mcp_findings), 1)
        sqlite_mcp = mcp_findings[0]
        self.assertEqual(sqlite_mcp.details.get("server_name"), "sqlite")
        self.assertEqual(sqlite_mcp.details.get("command"), "uvx")
        self.assertEqual(sqlite_mcp.risk_level, RiskLevel.CRITICAL)  # Exposes database

        # 5. Verify RuntimeScanner findings
        runtime_findings = [f for f in result.findings if f.module_name == "RuntimeScanner"]
        self.assertEqual(len(runtime_findings), 2)
        
        py_ver_finding = next(f for f in runtime_findings if "Python Version Pinning" in f.title)
        self.assertEqual(py_ver_finding.details.get("version"), "3.11.5")
        
        docker_finding = next(f for f in runtime_findings if "AI Docker Image" in f.title)
        self.assertEqual(docker_finding.details.get("image"), "pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime")


if __name__ == "__main__":
    unittest.main()
