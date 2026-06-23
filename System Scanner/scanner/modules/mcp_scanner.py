"""
MODULE 08 — MCP Config Scanner
===============================
Parses and indexes Model Context Protocol (MCP) configuration files to discover
registered MCP servers, their transports, exposed tools, and any embedded
credentials or environment variables.

Supported config formats / locations
--------------------------------------
1. Anthropic Claude Desktop
     Windows : %APPDATA%\\Claude\\claude_desktop_config.json
     macOS   : ~/Library/Application Support/Claude/claude_desktop_config.json
     Linux   : ~/.config/Claude/claude_desktop_config.json

2. Cursor IDE
     Windows / macOS / Linux : ~/.cursor/mcp.json
     Workspace-level         : <cwd>/.cursor/mcp.json

3. VS Code / VS Code Insiders (Copilot / Continue / MCP extensions)
     Windows : %APPDATA%\\Code\\User\\settings.json
               %APPDATA%\\Code - Insiders\\User\\settings.json
     macOS   : ~/Library/Application Support/Code/User/settings.json
     Linux   : ~/.config/Code/User/settings.json

4. Windsurf IDE
     Windows / macOS / Linux : ~/.codeium/windsurf/mcp_config.json

5. Generic MCP config files discovered via filesystem walk:
     .mcp.json, mcp.json, mcp-config.json, mcp_config.json
     (searched up to depth 4 from home and CWD)

Schema understanding
--------------------
All supported formats normalise to the shared MCP servers object shape:

    {
      "mcpServers": {
        "<server-name>": {
          "command": "node",
          "args": ["server.js"],
          "env": { "API_KEY": "..." },
          "url": "https://...",          # SSE / HTTP transport variant
          "transport": "stdio" | "sse"
        }
      }
    }

Author: Person B / Person C
Day: 4
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
import platform
import re
import time
from typing import Any

from scanner.models import Finding, FindingCategory, ModuleInfo, RiskLevel

logger = logging.getLogger(__name__)

MODULE_NAME = "MCPScanner"
MODULE_NUMBER = 8

# ── Credential-like patterns inside MCP env blocks ───────────────────────────
# These are applied to environment variable *names* (not values) to flag
# likely secrets without storing the raw secret in the finding.
_SECRET_ENV_NAME_RE = re.compile(
    r"(key|token|secret|password|passwd|credential|auth|bearer|api_key|apikey)",
    re.IGNORECASE,
)

# Known high-risk MCP server packages / commands that imply elevated access
_HIGH_RISK_COMMANDS: frozenset[str] = frozenset({
    "npx", "uvx", "docker", "podman", "bash", "sh", "cmd", "powershell",
    "python", "python3", "node",
})

# MCP server names / commands associated with specific AI services
_SERVER_SERVICE_MAP: dict[str, str] = {
    "filesystem":   "Local filesystem access",
    "github":       "GitHub API access",
    "gitlab":       "GitLab API access",
    "postgres":     "PostgreSQL database access",
    "sqlite":       "SQLite database access",
    "puppeteer":    "Browser automation (Puppeteer)",
    "playwright":   "Browser automation (Playwright)",
    "slack":        "Slack workspace access",
    "discord":      "Discord API access",
    "google-drive": "Google Drive access",
    "gdrive":       "Google Drive access",
    "gmail":        "Gmail access",
    "calendar":     "Google Calendar access",
    "aws":          "AWS API access",
    "azure":        "Azure API access",
    "gcp":          "Google Cloud Platform access",
    "docker":       "Docker daemon access",
    "kubernetes":   "Kubernetes cluster access",
    "k8s":          "Kubernetes cluster access",
    "fetch":        "HTTP fetch / web requests",
    "memory":       "Persistent memory / knowledge graph",
    "sequential-thinking": "Sequential reasoning tool",
    "brave-search": "Brave web search",
    "exa":          "Exa web search",
}

# Whitelist of approved remote MCP servers
_APPROVED_MCP_DOMAINS: frozenset[str] = frozenset({
    "api.anthropic.com",
    "api.openai.com",
    "api.github.com",
    "mcp.codeium.com",
    "localhost",
    "127.0.0.1",
})


# ── Config file location resolution ──────────────────────────────────────────

def _resolve_config_locations() -> list[tuple[pathlib.Path, str]]:
    """Return all candidate MCP config file paths with their source labels.

    Returns:
        List of (path, source_label) tuples. Only existing files are included.
    """
    home = pathlib.Path.home()
    system = platform.system()
    locations: list[tuple[pathlib.Path, str]] = []

    def _add(path: pathlib.Path, label: str) -> None:
        if path.exists() and path.is_file():
            locations.append((path, label))

    # ── Claude Desktop ────────────────────────────────────────────────────
    if system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            _add(
                pathlib.Path(appdata) / "Claude" / "claude_desktop_config.json",
                "Claude Desktop (Windows)",
            )
    elif system == "Darwin":
        _add(
            home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
            "Claude Desktop (macOS)",
        )
    else:
        _add(
            home / ".config" / "Claude" / "claude_desktop_config.json",
            "Claude Desktop (Linux)",
        )

    # ── Cursor IDE ────────────────────────────────────────────────────────
    _add(home / ".cursor" / "mcp.json", "Cursor IDE (user-level)")
    _add(pathlib.Path.cwd() / ".cursor" / "mcp.json", "Cursor IDE (workspace-level)")

    # ── VS Code / VS Code Insiders ────────────────────────────────────────
    if system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            for edition, label in (
                ("Code", "VS Code"),
                ("Code - Insiders", "VS Code Insiders"),
            ):
                _add(
                    pathlib.Path(appdata) / edition / "User" / "settings.json",
                    f"{label} settings.json",
                )
    elif system == "Darwin":
        for edition, label in (
            ("Code", "VS Code"),
            ("Code - Insiders", "VS Code Insiders"),
        ):
            _add(
                home / "Library" / "Application Support" / edition / "User" / "settings.json",
                f"{label} settings.json",
            )
    else:
        for edition, label in (
            ("Code", "VS Code"),
            ("Code - Insiders", "VS Code Insiders"),
        ):
            _add(
                home / ".config" / edition / "User" / "settings.json",
                f"{label} settings.json",
            )

    # ── Windsurf IDE ──────────────────────────────────────────────────────
    _add(
        home / ".codeium" / "windsurf" / "mcp_config.json",
        "Windsurf IDE",
    )

    # ── Kiro IDE (.kiro/settings/mcp.json) ───────────────────────────────
    _add(pathlib.Path.cwd() / ".kiro" / "settings" / "mcp.json", "Kiro IDE (workspace)")
    _add(home / ".kiro" / "settings" / "mcp.json", "Kiro IDE (user-level)")

    return locations


def _discover_generic_configs(max_depth: int = 4) -> list[tuple[pathlib.Path, str]]:
    """Walk home directory and CWD for generic MCP config filenames.

    Targets:
      - .mcp.json
      - mcp.json
      - mcp-config.json
      - mcp_config.json

    Skips OS system directories and common non-project dirs.
    """
    target_names: frozenset[str] = frozenset({
        ".mcp.json", "mcp.json", "mcp-config.json", "mcp_config.json",
    })
    skip_dirs: frozenset[str] = frozenset({
        ".git", "node_modules", "__pycache__", "venv", ".venv", "env",
        "site-packages", ".cache", ".npm", ".yarn", "AppData", "Library",
        "Windows", "System32", "Program Files", "Program Files (x86)",
    })

    found: list[tuple[pathlib.Path, str]] = []
    seen: set[str] = set()

    def _walk(root: pathlib.Path) -> None:
        root_depth = len(root.resolve().parts)
        for dirpath, dirs, files in os.walk(root, topdown=True, onerror=lambda _: None):
            try:
                dirs[:] = [
                    d for d in dirs
                    if d not in skip_dirs and not d.startswith(".")
                ]
                current = pathlib.Path(dirpath)
                if len(current.parts) - root_depth >= max_depth:
                    dirs.clear()

                for fname in files:
                    if fname.lower() in target_names:
                        full = (current / fname).resolve()
                        key = str(full)
                        if key not in seen:
                            seen.add(key)
                            found.append((full, f"Generic MCP config ({fname})"))
            except (PermissionError, OSError):
                dirs.clear()

    for search_root in (pathlib.Path.home(), pathlib.Path.cwd().resolve()):
        try:
            _walk(search_root)
        except Exception as e:
            logger.debug("MCPScanner: walk failed for %s: %s", search_root, e)

    return found


# ── Config parsers ────────────────────────────────────────────────────────────

def _extract_mcp_servers(data: dict[str, Any]) -> dict[str, Any]:
    """Extract the mcpServers dict from various config schemas.

    Handles:
      - Direct:        {"mcpServers": {...}}
      - VS Code style: {"mcp": {"servers": {...}}} or {"mcp": {"mcpServers": {...}}}
      - Flat list:     {"servers": [...]}  (normalises to dict)
    """
    # Direct top-level key (Claude Desktop, Cursor, Windsurf, Kiro)
    if "mcpServers" in data:
        val = data["mcpServers"]
        if isinstance(val, dict):
            return val

    # VS Code extension keys
    for outer in ("mcp", "github.copilot", "continue", "cline"):
        if outer in data and isinstance(data[outer], dict):
            inner = data[outer]
            if "mcpServers" in inner and isinstance(inner["mcpServers"], dict):
                return inner["mcpServers"]
            if "servers" in inner and isinstance(inner["servers"], dict):
                return inner["servers"]

    # Flat "servers" key (some community configs)
    if "servers" in data:
        raw = data["servers"]
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, list):
            return {item.get("name", f"server_{i}"): item for i, item in enumerate(raw)}

    return {}


def _classify_server_risk(server_name: str, server_cfg: dict[str, Any]) -> RiskLevel:
    """Assign a risk level to an MCP server entry.

    Rules:
      CRITICAL — server exposes filesystem, database, or cloud credentials
      HIGH     — runs privileged command (docker, bash) or has secret env vars
      MEDIUM   — known AI service SDK servers with API access
      LOW      — read-only / search / utility servers
      INFO     — unknown / unrecognised server
    """
    name_lower = server_name.lower()
    command = str(server_cfg.get("command", "")).lower()
    env_block: dict = server_cfg.get("env", {}) or {}
    args: list = server_cfg.get("args", []) or []
    args_str = " ".join(str(a) for a in args).lower()

    # CRITICAL: explicit filesystem, DB, or cloud infra access
    if any(k in name_lower or k in args_str for k in (
        "filesystem", "postgres", "sqlite", "mysql", "mongodb",
        "aws", "azure", "gcp", "kubernetes", "k8s", "docker",
    )):
        return RiskLevel.CRITICAL

    # HIGH: shell-level command execution or embedded secrets in env
    has_secret_env = any(_SECRET_ENV_NAME_RE.search(k) for k in env_block)
    shell_commands = {"bash", "sh", "cmd", "powershell", "docker", "podman"}
    if has_secret_env or command in shell_commands:
        return RiskLevel.HIGH

    # Remote URL transport (SSE/HTTP MCP)
    if server_cfg.get("url") or server_cfg.get("transport") == "sse":
        url = str(server_cfg.get("url", ""))
        if url:
            from urllib.parse import urlparse
            try:
                hostname = urlparse(url).hostname
                if hostname and hostname.lower() not in _APPROVED_MCP_DOMAINS:
                    # CRITICAL: unauthorized remote server
                    return RiskLevel.CRITICAL
            except Exception:
                return RiskLevel.CRITICAL
        # If it's a remote transport but approved or no URL, treat as HIGH
        return RiskLevel.HIGH

    # MEDIUM: known AI/API-access services
    if any(k in name_lower for k in (
        "github", "gitlab", "slack", "discord", "gdrive",
        "gmail", "calendar", "fetch", "brave", "exa",
    )):
        return RiskLevel.MEDIUM

    return RiskLevel.LOW


def _parse_config_file(
    config_path: pathlib.Path,
    source_label: str,
) -> list[Finding]:
    """Parse a single MCP config file and produce one Finding per server entry.

    Args:
        config_path: Absolute path to the JSON config file.
        source_label: Human-readable label for the config source.

    Returns:
        List of Finding objects, one per discovered MCP server.
    """
    findings: list[Finding] = []

    try:
        raw_text = config_path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError) as e:
        logger.debug("MCPScanner: cannot read %s: %s", config_path, e)
        return findings

    # Parse JSON — tolerate trailing commas and comments via lenient parse
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        # Try stripping single-line comments and trailing commas (common in settings.json)
        try:
            cleaned = re.sub(r"//[^\n]*", "", raw_text)
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.debug("MCPScanner: JSON parse failed for %s: %s", config_path, e)
            return findings

    if not isinstance(data, dict):
        return findings

    servers = _extract_mcp_servers(data)
    if not servers:
        logger.debug("MCPScanner: no mcpServers found in %s", config_path)
        return findings

    config_path_str = str(config_path).replace("\\", "/")
    logger.info("MCPScanner: found %d server(s) in %s", len(servers), config_path)

    for server_name, server_cfg in servers.items():
        if not isinstance(server_cfg, dict):
            continue

        command = server_cfg.get("command", "")
        args: list = server_cfg.get("args", []) or []
        env_block: dict = server_cfg.get("env", {}) or {}
        transport = server_cfg.get("transport", "stdio")
        url = server_cfg.get("url", "")

        # Identify service description from known map
        service_desc = _SERVER_SERVICE_MAP.get(server_name.lower(), "")
        for keyword, desc in _SERVER_SERVICE_MAP.items():
            if keyword in server_name.lower() or keyword in " ".join(str(a) for a in args).lower():
                service_desc = desc
                break

        risk = _classify_server_risk(server_name, server_cfg)

        # Build masked env block — never store raw secret values
        masked_env: dict[str, str] = {}
        for env_key, env_val in env_block.items():
            if _SECRET_ENV_NAME_RE.search(env_key):
                val_str = str(env_val)
                masked_env[env_key] = (
                    f"{val_str[:4]}...{val_str[-2:]}"
                    if len(val_str) > 8
                    else "****"
                )
            else:
                masked_env[env_key] = str(env_val)

        title = f"MCP Server: {server_name}"
        if service_desc:
            title += f" ({service_desc})"

        description_parts = [
            f"MCP server '{server_name}' registered in {source_label}."
        ]
        
        # Check if it was flagged for unauthorized domain
        is_unauthorized = False
        if url:
            from urllib.parse import urlparse
            try:
                hostname = urlparse(url).hostname
                if hostname and hostname.lower() not in _APPROVED_MCP_DOMAINS:
                    is_unauthorized = True
            except Exception:
                is_unauthorized = True

        if is_unauthorized:
            description_parts.append(f"UNAUTHORIZED REMOTE SERVER (Poisoning Risk) — domain not in whitelist.")

        if command:
            description_parts.append(f"Command: {command} {' '.join(str(a) for a in args[:3])}")
        if url:
            description_parts.append(f"URL: {url}")
        if service_desc:
            description_parts.append(f"Service: {service_desc}")

        findings.append(
            Finding(
                module_name=MODULE_NAME,
                title=title,
                description=" ".join(description_parts),
                source=config_path_str,
                category=FindingCategory.CONFIGURATION,
                risk_level=risk,
                confidence=0.95,
                details={
                    "server_name": server_name,
                    "config_file": config_path_str,
                    "config_source": source_label,
                    "command": command,
                    "args": args,
                    "transport": transport,
                    "url": url,
                    "env_vars": masked_env,
                    "env_var_count": len(env_block),
                    "has_secret_env": bool(
                        any(_SECRET_ENV_NAME_RE.search(k) for k in env_block)
                    ),
                    "service_description": service_desc,
                },
            )
        )

    return findings


# ── Module entry point ────────────────────────────────────────────────────────

def run(scan_folder: str | None = None) -> tuple[list[Finding], ModuleInfo]:
    """Execute the MCP Config Scanner module.

    Steps:
      1. Resolve well-known config file locations (Claude Desktop, Cursor,
         VS Code, Windsurf, Kiro).
      2. Discover generic MCP config files via filesystem walk.
      3. Parse each unique config file and emit one Finding per MCP server.

    Returns:
        Tuple of (findings_list, module_info)
    """
    module_info = ModuleInfo(name=MODULE_NAME, module_number=MODULE_NUMBER)
    findings: list[Finding] = []
    start_time = time.monotonic()

    try:
        if scan_folder:
            folder_path = pathlib.Path(scan_folder).resolve()
            all_locations = []
            
            cursor_mcp = folder_path / ".cursor" / "mcp.json"
            if cursor_mcp.exists() and cursor_mcp.is_file():
                all_locations.append((cursor_mcp, "Cursor IDE (workspace-level)"))
            kiro_mcp = folder_path / ".kiro" / "settings" / "mcp.json"
            if kiro_mcp.exists() and kiro_mcp.is_file():
                all_locations.append((kiro_mcp, "Kiro IDE (workspace)"))
            
            # Walk directory for generic configs
            generic_locations = []
            target_names = {".mcp.json", "mcp.json", "mcp-config.json", "mcp_config.json"}
            skip_dirs = {".git", "node_modules", "__pycache__", "venv", ".venv", "env", "dist", "build"}
            seen = set()
            root_depth = len(folder_path.parts)
            for dirpath, dirs, files in os.walk(folder_path, topdown=True, onerror=lambda _: None):
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                current = pathlib.Path(dirpath)
                if len(current.parts) - root_depth >= 4:
                    dirs.clear()
                for fname in files:
                    if fname.lower() in target_names:
                        full = (current / fname).resolve()
                        key = str(full)
                        if key not in seen:
                            seen.add(key)
                            generic_locations.append((full, f"Generic MCP config ({fname})"))
            all_locations.extend(generic_locations)
        else:
            # ── Step 1: Well-known locations ──────────────────────────────────
            known_locations = _resolve_config_locations()
            logger.info("MCPScanner: found %d known config location(s)", len(known_locations))

            # ── Step 2: Generic config discovery ──────────────────────────────
            generic_locations = _discover_generic_configs()
            logger.info("MCPScanner: discovered %d generic config file(s)", len(generic_locations))

            all_locations = known_locations + generic_locations

        # ── Step 3: Merge and deduplicate ─────────────────────────────────
        seen_paths: set[str] = set()
        unique_locations: list[tuple[pathlib.Path, str]] = []
        for path, label in all_locations:
            try:
                key = str(path.resolve())
            except OSError:
                key = str(path)
            if key not in seen_paths:
                seen_paths.add(key)
                unique_locations.append((path, label))

        # ── Step 4: Parse each config ──────────────────────────────────────
        for config_path, label in unique_locations:
            try:
                file_findings = _parse_config_file(config_path, label)
                findings.extend(file_findings)
            except Exception as exc:
                logger.warning("MCPScanner: error parsing %s: %s", config_path, exc)

        module_info.status = "success"

    except Exception as exc:
        module_info.status = "error"
        module_info.error_message = str(exc)

    finally:
        module_info.duration_sec = time.monotonic() - start_time
        module_info.findings_count = len(findings)

    return findings, module_info


class MCPScanner:
    """Wrapper class for Module 08 MCPScanner to conform to the Discovery Engine interface."""

    MODULE_NAME = MODULE_NAME
    MODULE_NUMBER = MODULE_NUMBER

    def __init__(self, scan_folder: str | None = None) -> None:
        self.scan_folder = scan_folder

    def scan(self) -> list[Finding]:
        findings, _ = run(scan_folder=self.scan_folder)
        return findings


# ── Standalone test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print("Running MODULE 08 — MCPScanner standalone test...\n")
    findings, info = run()

    print(f"Module Status  : {info.status}")
    print(f"Duration       : {info.duration_sec:.3f}s")
    print(f"Findings count : {info.findings_count}\n")

    for f in findings:
        print(f"[{f.risk_level}] {f.title}")
        print(f"  Source  : {f.source}")
        print(f"  Config  : {f.details.get('config_source')}")
        print(f"  Command : {f.details.get('command')} {f.details.get('args', [])}")
        if f.details.get("env_vars"):
            print(f"  Env     : {f.details['env_vars']}")
        print()
