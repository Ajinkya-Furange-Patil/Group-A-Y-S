"""
Unit tests for the MCP Config Scanner module (scanner/modules/mcp_scanner.py).

Tests cover:
  - JSON parsing of all supported config schemas
  - MCP server extraction from various config structures
  - Risk level classification logic
  - Credential masking in env blocks
  - Discovery of generic config files via filesystem walk
  - Full run() integration with mocked filesystem
"""

from __future__ import annotations

import json
import os
import pathlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from scanner.models import FindingCategory, RiskLevel
from scanner.modules.mcp_scanner import (
    MCPScanner,
    _classify_server_risk,
    _extract_mcp_servers,
    _parse_config_file,
    _resolve_config_locations,
    run,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _write_json(directory: pathlib.Path, filename: str, data: dict) -> pathlib.Path:
    """Write a JSON file to a temporary directory and return its path."""
    path = directory / filename
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ── _extract_mcp_servers ──────────────────────────────────────────────────────

class TestExtractMcpServers(unittest.TestCase):

    def test_direct_mcpServers_key(self):
        data = {
            "mcpServers": {
                "filesystem": {"command": "node", "args": ["fs.js"]},
            }
        }
        result = _extract_mcp_servers(data)
        self.assertIn("filesystem", result)
        self.assertEqual(result["filesystem"]["command"], "node")

    def test_vscode_mcp_mcpServers(self):
        data = {
            "mcp": {
                "mcpServers": {
                    "github": {"command": "npx", "args": ["-y", "@mcp/github"]}
                }
            }
        }
        result = _extract_mcp_servers(data)
        self.assertIn("github", result)

    def test_vscode_mcp_servers(self):
        data = {
            "mcp": {
                "servers": {
                    "brave-search": {"command": "npx", "args": ["brave-mcp"]}
                }
            }
        }
        result = _extract_mcp_servers(data)
        self.assertIn("brave-search", result)

    def test_flat_servers_dict(self):
        data = {
            "servers": {
                "memory": {"command": "npx", "args": ["@modelcontextprotocol/server-memory"]}
            }
        }
        result = _extract_mcp_servers(data)
        self.assertIn("memory", result)

    def test_flat_servers_list_normalised_to_dict(self):
        data = {
            "servers": [
                {"name": "fetch", "command": "npx", "args": ["mcp-fetch"]},
                {"name": "puppeteer", "command": "npx", "args": ["mcp-puppeteer"]},
            ]
        }
        result = _extract_mcp_servers(data)
        self.assertIn("fetch", result)
        self.assertIn("puppeteer", result)

    def test_empty_data_returns_empty(self):
        self.assertEqual(_extract_mcp_servers({}), {})
        self.assertEqual(_extract_mcp_servers({"unrelated": True}), {})

    def test_non_dict_mcpServers_ignored(self):
        # If mcpServers is not a dict, should return empty
        data = {"mcpServers": ["not", "a", "dict"]}
        self.assertEqual(_extract_mcp_servers(data), {})


# ── _classify_server_risk ─────────────────────────────────────────────────────

class TestClassifyServerRisk(unittest.TestCase):

    def test_filesystem_is_critical(self):
        risk = _classify_server_risk(
            "filesystem",
            {"command": "node", "args": ["/path/server.js"]}
        )
        self.assertEqual(risk, RiskLevel.CRITICAL)

    def test_postgres_is_critical(self):
        risk = _classify_server_risk(
            "postgres",
            {"command": "npx", "args": ["-y", "@mcp/postgres"]}
        )
        self.assertEqual(risk, RiskLevel.CRITICAL)

    def test_docker_command_is_high(self):
        risk = _classify_server_risk(
            "custom-server",
            {"command": "docker", "args": ["run", "mcp-image"]}
        )
        self.assertEqual(risk, RiskLevel.HIGH)

    def test_secret_env_var_is_high(self):
        risk = _classify_server_risk(
            "my-server",
            {
                "command": "npx",
                "args": ["my-mcp"],
                "env": {"GITHUB_TOKEN": "ghp_secret123"},
            }
        )
        self.assertEqual(risk, RiskLevel.HIGH)

    def test_sse_transport_is_high(self):
        risk = _classify_server_risk(
            "remote-server",
            {"url": "https://example.com/mcp", "transport": "sse"}
        )
        # Because example.com is not in the whitelist, this is CRITICAL now.
        self.assertEqual(risk, RiskLevel.CRITICAL)

    def test_github_server_is_medium(self):
        risk = _classify_server_risk(
            "github",
            {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]}
        )
        self.assertEqual(risk, RiskLevel.MEDIUM)

    def test_unknown_server_is_low(self):
        risk = _classify_server_risk(
            "my-custom-tool",
            {"command": "node", "args": ["tool.js"]}
        )
        self.assertEqual(risk, RiskLevel.LOW)


# ── _parse_config_file ────────────────────────────────────────────────────────

class TestParseConfigFile(unittest.TestCase):

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        shutil.rmtree(str(self.tmpdir), ignore_errors=True)

    def test_claude_desktop_style_config(self):
        config = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    "env": {},
                },
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_abc123"},
                },
            }
        }
        path = _write_json(self.tmpdir, "claude_desktop_config.json", config)
        findings = _parse_config_file(path, "Claude Desktop (test)")

        self.assertEqual(len(findings), 2)

        fs_finding = next(f for f in findings if "filesystem" in f.title.lower())
        self.assertEqual(fs_finding.risk_level, RiskLevel.CRITICAL)
        self.assertEqual(fs_finding.details["server_name"], "filesystem")
        self.assertEqual(fs_finding.details["command"], "npx")
        self.assertEqual(fs_finding.category, FindingCategory.CONFIGURATION)

        gh_finding = next(f for f in findings if "github" in f.title.lower())
        self.assertEqual(gh_finding.risk_level, RiskLevel.HIGH)
        # Secret env var should be masked, not stored raw
        self.assertTrue(gh_finding.details["has_secret_env"])
        masked_val = gh_finding.details["env_vars"].get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
        self.assertNotEqual(masked_val, "ghp_abc123")
        self.assertIn("...", masked_val)

    def test_vscode_settings_json_style(self):
        config = {
            "editor.fontSize": 14,
            "mcp": {
                "mcpServers": {
                    "brave-search": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                        "env": {"BRAVE_API_KEY": "BSAsome_key_value_123"},
                    }
                }
            },
        }
        path = _write_json(self.tmpdir, "settings.json", config)
        findings = _parse_config_file(path, "VS Code settings.json")

        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f.details["server_name"], "brave-search")
        self.assertTrue(f.details["has_secret_env"])

    def test_mcp_json_cursor_style(self):
        config = {
            "mcpServers": {
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                },
                "sequential-thinking": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
                },
            }
        }
        path = _write_json(self.tmpdir, "mcp.json", config)
        findings = _parse_config_file(path, "Cursor IDE (test)")

        self.assertEqual(len(findings), 2)
        names = {f.details["server_name"] for f in findings}
        self.assertIn("memory", names)
        self.assertIn("sequential-thinking", names)

    def test_sse_transport_remote_server(self):
        config = {
            "mcpServers": {
                "remote-agent": {
                    "url": "https://mcp.example.com/agent",
                    "transport": "sse",
                }
            }
        }
        path = _write_json(self.tmpdir, "mcp-config.json", config)
        findings = _parse_config_file(path, "Generic MCP config")

        self.assertEqual(len(findings), 1)
        f = findings[0]
        # example.com is not whitelisted, so it should be CRITICAL
        self.assertEqual(f.risk_level, RiskLevel.CRITICAL)
        self.assertEqual(f.details["url"], "https://mcp.example.com/agent")
        self.assertEqual(f.details["transport"], "sse")

    def test_invalid_json_returns_empty(self):
        bad_path = self.tmpdir / "bad.json"
        bad_path.write_text("{this is not valid json at all!!!", encoding="utf-8")
        findings = _parse_config_file(bad_path, "bad config")
        self.assertEqual(findings, [])

    def test_json_with_comments_and_trailing_commas(self):
        """VS Code settings.json allows comments and trailing commas."""
        raw = """{
    // VS Code MCP settings
    "mcp": {
        "mcpServers": {
            "fetch": {
                "command": "npx",
                "args": ["-y", "mcp-fetch"],
            },
        },
    },
}"""
        path = self.tmpdir / "settings.json"
        path.write_text(raw, encoding="utf-8")
        findings = _parse_config_file(path, "VS Code (with comments)")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].details["server_name"], "fetch")

    def test_no_mcpservers_returns_empty(self):
        config = {"editor.fontSize": 14, "theme": "dark"}
        path = _write_json(self.tmpdir, "settings.json", config)
        findings = _parse_config_file(path, "VS Code settings (no MCP)")
        self.assertEqual(findings, [])

    def test_env_vars_without_secrets_not_masked(self):
        config = {
            "mcpServers": {
                "my-server": {
                    "command": "node",
                    "args": ["server.js"],
                    "env": {"LOG_LEVEL": "debug", "PORT": "3000"},
                }
            }
        }
        path = _write_json(self.tmpdir, "mcp.json", config)
        findings = _parse_config_file(path, "Test")

        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertFalse(f.details["has_secret_env"])
        # Non-secret env vars should be stored as-is
        self.assertEqual(f.details["env_vars"]["LOG_LEVEL"], "debug")
        self.assertEqual(f.details["env_vars"]["PORT"], "3000")


# ── run() integration ─────────────────────────────────────────────────────────

class TestMcpScannerRun(unittest.TestCase):

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        shutil.rmtree(str(self.tmpdir), ignore_errors=True)

    def _mock_locations(self, configs: dict[str, dict]):
        """Write config files to tmpdir and build a locations list."""
        locations = []
        for filename, data in configs.items():
            path = _write_json(self.tmpdir, filename, data)
            locations.append((path, f"test: {filename}"))
        return locations

    @patch("scanner.modules.mcp_scanner._discover_generic_configs", return_value=[])
    @patch("scanner.modules.mcp_scanner._resolve_config_locations")
    def test_run_success_with_mocked_configs(self, mock_resolve, _mock_discover):
        configs = {
            "claude_desktop_config.json": {
                "mcpServers": {
                    "filesystem": {"command": "node", "args": ["fs.js"]},
                    "postgres": {"command": "npx", "args": ["-y", "pg-mcp"], "env": {"DB_PASSWORD": "s3cr3t!"}},
                }
            }
        }
        mock_resolve.return_value = self._mock_locations(configs)

        findings, info = run()

        self.assertEqual(info.status, "success")
        self.assertEqual(info.findings_count, 2)
        self.assertEqual(len(findings), 2)

        names = {f.details["server_name"] for f in findings}
        self.assertIn("filesystem", names)
        self.assertIn("postgres", names)

        pg = next(f for f in findings if f.details["server_name"] == "postgres")
        self.assertEqual(pg.risk_level, RiskLevel.CRITICAL)
        self.assertTrue(pg.details["has_secret_env"])

    @patch("scanner.modules.mcp_scanner._discover_generic_configs", return_value=[])
    @patch("scanner.modules.mcp_scanner._resolve_config_locations", return_value=[])
    def test_run_no_configs_returns_empty(self, _mock_resolve, _mock_discover):
        findings, info = run()
        self.assertEqual(info.status, "success")
        self.assertEqual(len(findings), 0)

    @patch("scanner.modules.mcp_scanner._discover_generic_configs")
    @patch("scanner.modules.mcp_scanner._resolve_config_locations", return_value=[])
    def test_run_discovers_generic_config(self, _mock_resolve, mock_discover):
        config_path = _write_json(
            self.tmpdir,
            ".mcp.json",
            {"mcpServers": {"slack": {"command": "npx", "args": ["slack-mcp"]}}},
        )
        mock_discover.return_value = [(config_path, "Generic MCP config (.mcp.json)")]

        findings, info = run()

        self.assertEqual(info.status, "success")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].details["server_name"], "slack")
        self.assertEqual(findings[0].details["config_source"], "Generic MCP config (.mcp.json)")

    @patch("scanner.modules.mcp_scanner._discover_generic_configs")
    @patch("scanner.modules.mcp_scanner._resolve_config_locations")
    def test_run_deduplicates_same_config_path(self, mock_resolve, mock_discover):
        """The same config file referenced in both known and generic locations
        should only be parsed once."""
        config_path = _write_json(
            self.tmpdir,
            "mcp.json",
            {"mcpServers": {"memory": {"command": "npx", "args": ["mem-mcp"]}}},
        )
        mock_resolve.return_value = [(config_path, "Cursor IDE (test)")]
        mock_discover.return_value = [(config_path, "Generic MCP config (mcp.json)")]

        findings, info = run()

        self.assertEqual(len(findings), 1)  # deduplicated

    def test_class_wrapper(self):
        scanner = MCPScanner()
        self.assertEqual(scanner.MODULE_NAME, "MCPScanner")
        self.assertEqual(scanner.MODULE_NUMBER, 8)

        with patch("scanner.modules.mcp_scanner.run") as mock_run:
            mock_run.return_value = (
                [],
                __import__("scanner.models", fromlist=["ModuleInfo"]).ModuleInfo(
                    name="MCPScanner", module_number=8
                ),
            )
            result = scanner.scan()
            self.assertEqual(result, [])
            mock_run.assert_called_once()


# ── _resolve_config_locations ─────────────────────────────────────────────────

class TestResolveConfigLocations(unittest.TestCase):

    def test_returns_only_existing_files(self):
        """All returned paths must exist as files."""
        locations = _resolve_config_locations()
        for path, label in locations:
            self.assertTrue(
                path.exists() and path.is_file(),
                msg=f"Non-existent path returned: {path} ({label})",
            )

    def test_returns_list_of_tuples(self):
        locations = _resolve_config_locations()
        self.assertIsInstance(locations, list)
        for item in locations:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 2)
            path, label = item
            self.assertIsInstance(path, pathlib.Path)
            self.assertIsInstance(label, str)


if __name__ == "__main__":
    unittest.main()
