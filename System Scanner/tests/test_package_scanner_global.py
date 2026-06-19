"""
Unit tests for the global package scanner extensions in package_scanner.py.

Covers:
  - _scan_npm_global    : NPM global node_modules detection
  - _scan_pipx          : pipx isolated environment detection
  - _scan_uv_tools      : uv tool list detection
  - _scan_homebrew      : Homebrew formula detection (macOS/Linux)
  - _scan_conda         : conda environment package detection
  - run()               : integration — multi-scanner orchestration
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from scanner.models import FindingCategory, RiskLevel
from scanner.modules import package_scanner
from scanner.modules.package_scanner import (
    _check_npm_entry,
    _emit_pipx_finding,
    _run_cmd,
    _scan_conda,
    _scan_homebrew,
    _scan_npm_global,
    _scan_pip,
    _scan_pipx,
    _scan_uv_tools,
)


class TestRunCmd(unittest.TestCase):
    """_run_cmd helper."""

    @patch("subprocess.run")
    def test_returns_stdout_on_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="hello world\n")
        result = _run_cmd(["echo", "hello"])
        self.assertEqual(result, "hello world")

    @patch("subprocess.run")
    def test_returns_none_on_nonzero(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        self.assertIsNone(_run_cmd(["bad_cmd"]))

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_returns_none_on_file_not_found(self, _mock):
        self.assertIsNone(_run_cmd(["nonexistent_tool"]))


# ── NPM global scanner ────────────────────────────────────────────────────────

class TestScanNpmGlobal(unittest.TestCase):

    def _make_nm_dir(self, tmp_path: Path, packages: dict[str, dict]) -> Path:
        """Create a fake node_modules directory with package.json files."""
        nm = tmp_path / "node_modules"
        nm.mkdir()
        for pkg_name, meta in packages.items():
            if pkg_name.startswith("@"):
                scope, name = pkg_name.split("/", 1)
                pkg_dir = nm / scope / name
            else:
                pkg_dir = nm / pkg_name
            pkg_dir.mkdir(parents=True)
            (pkg_dir / "package.json").write_text(json.dumps(meta), encoding="utf-8")
        return nm

    @patch("scanner.modules.package_scanner._resolve_npm_global_prefix")
    def test_detects_exact_match(self, mock_prefix):
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            nm = self._make_nm_dir(tmp_path, {
                "openai": {"version": "4.0.0", "description": "OpenAI SDK"},
            })
            mock_prefix.return_value = [nm]
            findings = _scan_npm_global()

        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertIn("openai", f.title.lower())
        self.assertEqual(f.details["version"], "4.0.0")
        self.assertEqual(f.details["installer"], "npm (global)")

    @patch("scanner.modules.package_scanner._resolve_npm_global_prefix")
    def test_detects_scoped_package(self, mock_prefix):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            nm = self._make_nm_dir(tmp_path, {
                "@anthropic-ai/claude-code": {"version": "1.2.3"},
            })
            mock_prefix.return_value = [nm]
            findings = _scan_npm_global()

        self.assertEqual(len(findings), 1)
        self.assertIn("claude", findings[0].title.lower())

    @patch("scanner.modules.package_scanner._resolve_npm_global_prefix")
    def test_detects_mcp_server_as_ai_service(self, mock_prefix):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            nm = self._make_nm_dir(tmp_path, {
                "@modelcontextprotocol/sdk": {"version": "0.5.0"},
            })
            mock_prefix.return_value = [nm]
            findings = _scan_npm_global()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, FindingCategory.AI_SERVICE)

    @patch("scanner.modules.package_scanner._resolve_npm_global_prefix")
    def test_ignores_non_ai_packages(self, mock_prefix):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            nm = self._make_nm_dir(tmp_path, {
                "lodash": {"version": "4.17.21"},
                "express": {"version": "4.18.0"},
            })
            mock_prefix.return_value = [nm]
            findings = _scan_npm_global()

        self.assertEqual(len(findings), 0)

    @patch("scanner.modules.package_scanner._resolve_npm_global_prefix")
    def test_returns_empty_when_no_nm_dirs(self, mock_prefix):
        mock_prefix.return_value = []
        self.assertEqual(_scan_npm_global(), [])

    @patch("scanner.modules.package_scanner._resolve_npm_global_prefix")
    def test_detects_keyword_match_variant(self, mock_prefix):
        """Package not in exact dict but name contains AI keyword."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            nm = self._make_nm_dir(tmp_path, {
                "my-gpt-wrapper": {"version": "0.1.0"},
            })
            mock_prefix.return_value = [nm]
            findings = _scan_npm_global()

        self.assertEqual(len(findings), 1)


# ── pipx scanner ─────────────────────────────────────────────────────────────

class TestScanPipx(unittest.TestCase):

    @patch("scanner.modules.package_scanner._run_cmd")
    def test_parses_pipx_list_json(self, mock_cmd):
        pipx_json = json.dumps({
            "venvs": {
                "llm": {
                    "metadata": {
                        "main_package": {
                            "package": "llm",
                            "package_version": "0.16",
                        }
                    }
                },
                "aider-chat": {
                    "metadata": {
                        "main_package": {
                            "package": "aider-chat",
                            "package_version": "0.50.1",
                        }
                    }
                },
            }
        })
        mock_cmd.return_value = pipx_json
        findings = _scan_pipx()
        names = {f.details["package_name"] for f in findings}
        self.assertIn("llm", names)
        self.assertIn("aider-chat", names)
        for f in findings:
            self.assertEqual(f.details["installer"], "pipx")

    @patch("scanner.modules.package_scanner._run_cmd", return_value=None)
    @patch("scanner.modules.package_scanner._resolve_pipx_home")
    def test_fallback_to_venv_dir(self, mock_home, _mock_cmd):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            venvs = Path(tmp) / "venvs"
            venvs.mkdir()
            # Create a fake pipx venv for "llm"
            llm_venv = venvs / "llm"
            llm_venv.mkdir()
            meta = {"main_package": {"package_version": "0.17"}}
            (llm_venv / "pipx_metadata.json").write_text(json.dumps(meta))
            mock_home.return_value = venvs
            findings = _scan_pipx()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].details["package_name"], "llm")

    @patch("scanner.modules.package_scanner._run_cmd", return_value=None)
    @patch("scanner.modules.package_scanner._resolve_pipx_home", return_value=None)
    def test_returns_empty_when_nothing_found(self, _mock_home, _mock_cmd):
        self.assertEqual(_scan_pipx(), [])

    def test_emit_pipx_finding_known_tool(self):
        findings: list = []
        _emit_pipx_finding("llm", "0.16", findings)
        self.assertEqual(len(findings), 1)
        self.assertIn("llm", findings[0].title)

    def test_emit_pipx_finding_unknown_non_ai(self):
        findings: list = []
        _emit_pipx_finding("requests", "2.31.0", findings)
        self.assertEqual(len(findings), 0)

    def test_emit_pipx_finding_keyword_match(self):
        """Package not in dict but name contains 'gpt'."""
        findings: list = []
        _emit_pipx_finding("mygpt-tool", "1.0", findings)
        self.assertEqual(len(findings), 1)


# ── uv tool scanner ───────────────────────────────────────────────────────────

class TestScanUvTools(unittest.TestCase):

    @patch("scanner.modules.package_scanner._run_cmd")
    def test_parses_uv_tool_list(self, mock_cmd):
        mock_cmd.return_value = "llm v0.18\naider-chat v0.52.0\nrequests v2.31.0"
        findings = _scan_uv_tools()
        names = {f.details["package_name"] for f in findings}
        self.assertIn("llm", names)
        self.assertIn("aider-chat", names)
        self.assertNotIn("requests", names)

    @patch("scanner.modules.package_scanner._run_cmd")
    def test_installer_label_set_to_uv(self, mock_cmd):
        mock_cmd.return_value = "llm v0.18"
        findings = _scan_uv_tools()
        self.assertEqual(findings[0].details["installer"], "uv (tool)")

    @patch("scanner.modules.package_scanner._run_cmd", return_value=None)
    def test_returns_empty_when_uv_not_found(self, _mock):
        self.assertEqual(_scan_uv_tools(), [])


# ── Homebrew scanner ──────────────────────────────────────────────────────────

class TestScanHomebrew(unittest.TestCase):

    @patch("platform.system", return_value="Darwin")
    @patch("scanner.modules.package_scanner._run_cmd")
    def test_detects_ollama_formula(self, mock_cmd, _mock_platform):
        def cmd_side_effect(args, **kwargs):
            if args == ["brew", "list", "--formula", "--versions"]:
                return "ollama 0.1.40\ngit 2.44.0\n"
            if args[0] == "brew" and args[1] == "--prefix":
                return "/opt/homebrew/Cellar/ollama/0.1.40"
            return None

        mock_cmd.side_effect = cmd_side_effect
        findings = _scan_homebrew()
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertIn("ollama", f.title.lower())
        self.assertEqual(f.details["installer"], "homebrew")
        self.assertEqual(f.details["version"], "0.1.40")

    @patch("platform.system", return_value="Windows")
    def test_skipped_on_windows(self, _mock):
        self.assertEqual(_scan_homebrew(), [])

    @patch("platform.system", return_value="Darwin")
    @patch("scanner.modules.package_scanner._run_cmd", return_value=None)
    def test_returns_empty_when_brew_unavailable(self, _mock_cmd, _mock_platform):
        self.assertEqual(_scan_homebrew(), [])


# ── conda scanner ─────────────────────────────────────────────────────────────

class TestScanConda(unittest.TestCase):

    @patch("scanner.modules.package_scanner._run_cmd")
    def test_detects_torch_in_conda(self, mock_cmd):
        conda_json = json.dumps([
            {"name": "torch", "version": "2.2.0", "channel": "pytorch"},
            {"name": "numpy", "version": "1.26.0", "channel": "defaults"},
            {"name": "transformers", "version": "4.40.0", "channel": "conda-forge"},
        ])
        mock_cmd.return_value = conda_json
        findings = _scan_conda()
        names = {f.details["package_name"] for f in findings}
        self.assertIn("torch", names)
        self.assertIn("transformers", names)
        self.assertNotIn("numpy", names)

    @patch("scanner.modules.package_scanner._run_cmd", return_value=None)
    def test_returns_empty_when_conda_not_found(self, _mock):
        self.assertEqual(_scan_conda(), [])

    @patch("scanner.modules.package_scanner._run_cmd")
    def test_handles_invalid_json(self, mock_cmd):
        mock_cmd.return_value = "not json"
        self.assertEqual(_scan_conda(), [])


# ── run() integration ─────────────────────────────────────────────────────────

class TestPackageScannerRun(unittest.TestCase):

    @patch("scanner.modules.package_scanner._scan_conda", return_value=[])
    @patch("scanner.modules.package_scanner._scan_homebrew", return_value=[])
    @patch("scanner.modules.package_scanner._scan_uv_tools", return_value=[])
    @patch("scanner.modules.package_scanner._scan_pipx", return_value=[])
    @patch("scanner.modules.package_scanner._scan_npm_global", return_value=[])
    @patch("scanner.modules.package_scanner._scan_pip_global_envs", return_value=[])
    @patch("scanner.modules.package_scanner._scan_pip")
    def test_run_aggregates_all_scanners(
        self, mock_pip, mock_pip_global, mock_npm, mock_pipx, mock_uv, mock_brew, mock_conda
    ):
        from scanner.models import Finding, FindingCategory, RiskLevel
        fake_finding = Finding(
            module_name="PackageScanner",
            title="Package: openai (1.0)",
            description="test",
            source="pip://openai",
            category=FindingCategory.ML_FRAMEWORK,
            risk_level=RiskLevel.INFO,
        )
        mock_pip.return_value = [fake_finding]
        findings, info = package_scanner.run()

        self.assertEqual(info.status, "success")
        self.assertEqual(len(findings), 1)
        mock_npm.assert_called_once()
        mock_pip_global.assert_called_once()
        mock_pipx.assert_called_once()
        mock_uv.assert_called_once()
        mock_brew.assert_called_once()
        mock_conda.assert_called_once()

    @patch("scanner.modules.package_scanner._scan_conda", return_value=[])
    @patch("scanner.modules.package_scanner._scan_homebrew", return_value=[])
    @patch("scanner.modules.package_scanner._scan_uv_tools", return_value=[])
    @patch("scanner.modules.package_scanner._scan_pipx", return_value=[])
    @patch("scanner.modules.package_scanner._scan_npm_global", return_value=[])
    @patch("scanner.modules.package_scanner._scan_pip", side_effect=RuntimeError("boom"))
    def test_run_handles_scanner_exception_gracefully(
        self, _mock_pip, *_rest
    ):
        findings, info = package_scanner.run()
        # Other scanners return [], so overall still success (some succeeded)
        self.assertIn(info.status, ("success", "error"))

    def test_class_wrapper(self):
        scanner = package_scanner.PackageScanner()
        self.assertEqual(scanner.MODULE_NAME, "PackageScanner")
        self.assertEqual(scanner.MODULE_NUMBER, 4)
        with patch.object(package_scanner, "run") as mock_run:
            mock_run.return_value = ([], package_scanner.ModuleInfo(name="PackageScanner", module_number=4))
            findings = scanner.scan()
            self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
