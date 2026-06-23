"""
MODULE 04 — Package Scanner
===========================
Scans multiple package ecosystems to discover installed AI/ML frameworks and
developer-focused AI CLI agents:

  1. Active Python environment (pip list)
  2. Global NPM prefix (npm root -g / APPDATA/npm)
  3. pipx isolated environments
  4. uv tool environments
  5. Homebrew formulae/casks (macOS/Linux)
  6. conda environments (base + named envs)

Author: Person B
Day: 3
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
import platform
import subprocess
import sys
import time
from typing import Any

from scanner.models import Finding, FindingCategory, ModuleInfo, RiskLevel

logger = logging.getLogger(__name__)

MODULE_NAME = "PackageScanner"
MODULE_NUMBER = 4

# ── pip / Python package targets ─────────────────────────────────────────────
TARGET_PACKAGES = {
    "torch",
    "tensorflow",
    "transformers",
    "langchain",
    "crewai",
    "autogen",
    "llama-index",
    "openai",
    "anthropic",
    # Additional AI SDK packages
    "google-generativeai",
    "cohere",
    "mistralai",
    "groq",
    "together",
    "litellm",
    "ollama",
    "llama-cpp-python",
    "huggingface-hub",
    "diffusers",
    "sentence-transformers",
    "langchain-openai",
    "langchain-anthropic",
    "langchain-google-genai",
    "llama-index-core",
    "semantic-kernel",
    "pydantic-ai",
    "instructor",
    "guidance",
    "dspy-ai",
    "haystack-ai",
    "agno",
    "langgraph",
    "chromadb",
    "faiss",
    "qdrant-client",
    "pinecone",
}

# ── NPM global AI CLI agent targets ──────────────────────────────────────────
# Keyed by npm package name → human label.
NPM_AI_PACKAGES: dict[str, str] = {
    # OpenAI / ChatGPT
    "openai":               "OpenAI Node.js SDK",
    "@openai/codex":        "OpenAI Codex CLI",
    # Anthropic
    "@anthropic-ai/sdk":    "Anthropic Claude Node.js SDK",
    "@anthropic-ai/claude-code": "Claude Code CLI Agent",
    # Google
    "@google/generative-ai": "Google Generative AI SDK",
    "@google-cloud/vertexai": "Google Vertex AI SDK",
    # Microsoft / GitHub
    "@github-copilot/cli":  "GitHub Copilot CLI",
    "@microsoft/teams-ai":  "Microsoft Teams AI SDK",
    # LLM orchestration / agent frameworks
    "langchain":            "LangChain Node.js",
    "@langchain/core":      "LangChain Core (Node)",
    "llamaindex":           "LlamaIndex (Node.js)",
    "ai":                   "Vercel AI SDK",
    "@ai-sdk/openai":       "Vercel AI SDK (OpenAI)",
    "@ai-sdk/anthropic":    "Vercel AI SDK (Anthropic)",
    "ollama":               "Ollama Node.js Client",
    # MCP tooling
    "@modelcontextprotocol/sdk": "MCP SDK (Node.js)",
    "@modelcontextprotocol/server-filesystem": "MCP Filesystem Server",
    "@modelcontextprotocol/server-github":     "MCP GitHub Server",
    "@modelcontextprotocol/server-puppeteer":  "MCP Puppeteer Server",
    "@modelcontextprotocol/server-slack":      "MCP Slack Server",
    "@modelcontextprotocol/server-postgres":   "MCP PostgreSQL Server",
    # Cursor / Windsurf tooling
    "cursor-tools":         "Cursor AI Tools CLI",
    # Generic agents
    "mastra":               "Mastra AI Agent Framework",
    "genkit":               "Google Genkit AI",
    "genaiscript":          "GenAIScript CLI",
}

# Partial name matching for NPM (catches scoped packages and variations)
NPM_AI_KEYWORDS: tuple[str, ...] = (
    "openai", "anthropic", "claude", "gemini", "langchain", "llama",
    "copilot", "modelcontextprotocol", "ai-sdk", "ollama", "cohere",
    "huggingface", "mistral", "groq", "together-ai", "gpt", "vertexai",
)

# ── Homebrew formula targets ──────────────────────────────────────────────────
HOMEBREW_AI_FORMULAE: dict[str, str] = {
    "ollama":           "Ollama LLM Runtime",
    "llama.cpp":        "llama.cpp inference engine",
    "huggingface-cli":  "Hugging Face CLI",
    "whisper":          "OpenAI Whisper (audio transcription)",
    "stable-diffusion": "Stable Diffusion",
    "aichat":           "AIChat CLI",
    "mods":             "Mods AI CLI",
    "sgpt":             "ShellGPT CLI",
    "jan":              "Jan.ai local LLM",
}

# ── pipx / uv tool targets ────────────────────────────────────────────────────
PIPX_AI_PACKAGES: dict[str, str] = {
    "llm":              "Simon Willison's LLM CLI",
    "aider-chat":       "Aider AI coding assistant",
    "gptme":            "GPTme terminal agent",
    "open-interpreter": "Open Interpreter",
    "shell-gpt":        "ShellGPT CLI",
    "fabric":           "Fabric AI patterns CLI",
    "elia":             "Elia terminal AI chat",
    "chatblade":        "ChatBlade CLI",
    "private-gpt":      "PrivateGPT",
    "autogen":          "AutoGen agent framework",
    "crewai":           "CrewAI agent framework",
    "langchain-cli":    "LangChain CLI",
    "agno":             "Agno agent framework",
}


def _run_cmd(cmd: list[str], timeout: int = 10) -> str | None:
    """Run a subprocess command and return stdout as a string, or None on failure."""
    try:
        kwargs = {}
        if platform.system() == "Windows":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            **kwargs
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError, OSError):
        pass
    return None


def _make_finding(
    title: str,
    description: str,
    source: str,
    package_name: str,
    version: str,
    installer: str,
    install_location: str,
    category: FindingCategory = FindingCategory.ML_FRAMEWORK,
    extra_details: dict[str, Any] | None = None,
) -> Finding:
    """Build a standardised package Finding."""
    details: dict[str, Any] = {
        "package_name": package_name,
        "version": version,
        "installer": installer,
        "install_location": install_location,
    }
    if extra_details:
        details.update(extra_details)
    return Finding(
        module_name=MODULE_NAME,
        title=title,
        description=description,
        source=source,
        category=category,
        risk_level=RiskLevel.INFO,
        confidence=0.9,
        details=details,
    )


# ── Scanner A: pip (active environment) ──────────────────────────────────────

def _scan_pip() -> list[Finding]:
    """Scan the active Python environment for AI packages via pip list."""
    findings: list[Finding] = []
    packages: list[dict[str, Any]] = []

    try:
        if hasattr(sys, "frozen"):
            cmd = ["pip", "list", "--format=json"]
        else:
            cmd = [sys.executable, "-m", "pip", "list", "--format=json"]

        raw = _run_cmd(cmd)
        if raw:
            packages = json.loads(raw)
    except Exception as exc:
        logger.debug("PackageScanner [pip]: subprocess failed: %s — trying importlib.metadata", exc)
        try:
            import importlib.metadata
            for pkg in TARGET_PACKAGES:
                try:
                    version = importlib.metadata.version(pkg)
                    packages.append({"name": pkg, "version": version})
                except importlib.metadata.PackageNotFoundError:
                    if pkg == "autogen":
                        try:
                            version = importlib.metadata.version("pyautogen")
                            packages.append({"name": "pyautogen", "version": version})
                        except importlib.metadata.PackageNotFoundError:
                            pass
        except Exception as fallback_exc:
            logger.error("PackageScanner [pip]: fallback failed: %s", fallback_exc)
            return findings

    for pkg in packages:
        name = pkg.get("name", "")
        version = pkg.get("version", "")
        if not name:
            continue

        name_lower = name.lower()
        norm_name = name_lower.replace("_", "-")

        matched_pkg = None
        for target in TARGET_PACKAGES:
            if norm_name == target or name_lower == target:
                matched_pkg = target
                break
        if name_lower == "pyautogen":
            matched_pkg = "autogen"

        if not matched_pkg:
            continue

        if matched_pkg in {"langchain", "crewai", "autogen", "pydantic-ai",
                           "semantic-kernel", "agno", "dspy-ai", "haystack-ai"}:
            category = FindingCategory.AI_AGENT
        else:
            category = FindingCategory.ML_FRAMEWORK

        # Resolve install location
        install_location = f"pip://{name}"
        try:
            import importlib.metadata
            dist = importlib.metadata.distribution(name)
            loc = dist.locate_file("")
            install_location = str(pathlib.Path(str(loc)).resolve()).replace("\\", "/")
        except Exception:
            pass

        if install_location.startswith("pip://"):
            try:
                import importlib.util
                chk = name_lower.replace("-", "_")
                spec = importlib.util.find_spec(chk)
                if spec and spec.submodule_search_locations:
                    install_location = str(
                        pathlib.Path(spec.submodule_search_locations[0]).resolve()
                    ).replace("\\", "/")
                elif spec and spec.origin:
                    install_location = str(
                        pathlib.Path(spec.origin).parent.resolve()
                    ).replace("\\", "/")
            except Exception:
                pass

        findings.append(
            _make_finding(
                title=f"Package: {name} ({version})",
                description=f"Detected installed AI package: {name} (version {version})",
                source=install_location,
                package_name=name,
                version=version,
                installer="pip",
                install_location=install_location,
                category=category,
            )
        )

    return findings


# ── Scanner B: NPM global packages ───────────────────────────────────────────

def _resolve_npm_global_prefix() -> list[pathlib.Path]:
    """Return candidate global NPM node_modules directories.

    Checks (in priority order):
      1. ``npm root -g`` — authoritative npm output
      2. %APPDATA%\\npm\\node_modules          — Windows default (npm installer)
      3. %APPDATA%\\Roaming\\npm\\node_modules  — alternate APPDATA form
      4. %ProgramFiles%\\nodejs\\node_modules   — system-wide Node installs
      5. NVM for Windows (%NVM_HOME% / APPDATA\\nvm)
      6. Volta (~/.volta/tools/shared/node_modules)
      7. pnpm global store (pnpm root -g / LOCALAPPDATA\\pnpm\\global)
      8. Yarn global (~/.yarn/global/node_modules, LOCALAPPDATA\\Yarn\\global)
      9. Unix common locations (/usr/local/lib, /usr/lib, Homebrew)
    """
    candidates: list[pathlib.Path] = []

    # ── 1. npm root -g (most reliable cross-platform) ────────────────────
    raw = _run_cmd(["npm", "root", "-g"], timeout=8)
    if raw:
        p = pathlib.Path(raw.strip())
        if p.is_dir():
            candidates.append(p)

    # ── 2 & 3. Windows APPDATA npm prefix ────────────────────────────────
    for env_var in ("APPDATA",):
        appdata = os.environ.get(env_var)
        if appdata:
            for sub in (
                pathlib.Path(appdata) / "npm" / "node_modules",
                pathlib.Path(appdata) / "Roaming" / "npm" / "node_modules",
            ):
                if sub.is_dir():
                    candidates.append(sub)

    # ── 4. System-wide Node.js on Windows (Program Files) ────────────────
    for pf_var in ("ProgramFiles", "ProgramW6432"):
        pf = os.environ.get(pf_var)
        if pf:
            p = pathlib.Path(pf) / "nodejs" / "node_modules"
            if p.is_dir():
                candidates.append(p)

    # ── 5. NVM for Windows ───────────────────────────────────────────────
    nvm_home = os.environ.get("NVM_HOME") or (
        str(pathlib.Path(os.environ["APPDATA"]) / "nvm")
        if os.environ.get("APPDATA") else None
    )
    if nvm_home:
        nvm_root = pathlib.Path(nvm_home)
        # NVM stores each Node version under nvm_home/vX.Y.Z/node_modules
        if nvm_root.is_dir():
            try:
                for version_dir in sorted(nvm_root.iterdir(), reverse=True):
                    nm = version_dir / "node_modules"
                    if nm.is_dir():
                        candidates.append(nm)
                        break  # Only the latest NVM version
            except (PermissionError, OSError):
                pass

    # ── 6. Volta (~/.volta/tools/shared/node_modules) ────────────────────
    volta_shared = pathlib.Path.home() / ".volta" / "tools" / "shared" / "node_modules"
    if volta_shared.is_dir():
        candidates.append(volta_shared)

    # ── 7. pnpm global (pnpm root -g, LOCALAPPDATA\\pnpm\\global) ─────────
    pnpm_raw = _run_cmd(["pnpm", "root", "-g"], timeout=8)
    if pnpm_raw:
        p = pathlib.Path(pnpm_raw.strip())
        if p.is_dir():
            candidates.append(p)
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        pnpm_win = pathlib.Path(local_appdata) / "pnpm" / "global" / "node_modules"
        if pnpm_win.is_dir():
            candidates.append(pnpm_win)

    # ── 8. Yarn global ────────────────────────────────────────────────────
    yarn_raw = _run_cmd(["yarn", "global", "dir"], timeout=8)
    if yarn_raw:
        p = pathlib.Path(yarn_raw.strip()) / "node_modules"
        if p.is_dir():
            candidates.append(p)
    for yarn_path in (
        pathlib.Path.home() / ".yarn" / "global" / "node_modules",
        pathlib.Path(local_appdata) / "Yarn" / "Data" / "global" / "node_modules"
        if local_appdata else None,
    ):
        if yarn_path and yarn_path.is_dir():
            candidates.append(yarn_path)

    # ── 9. Unix common locations ─────────────────────────────────────────
    for unix_path in (
        pathlib.Path.home() / ".npm-global" / "lib" / "node_modules",
        pathlib.Path("/usr/local/lib/node_modules"),
        pathlib.Path("/usr/lib/node_modules"),
        pathlib.Path("/opt/homebrew/lib/node_modules"),
    ):
        if unix_path.is_dir():
            candidates.append(unix_path)

    # Deduplicate by resolved path
    seen: set[str] = set()
    unique: list[pathlib.Path] = []
    for c in candidates:
        try:
            key = str(c.resolve())
        except OSError:
            key = str(c)
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def _read_npm_package_json(pkg_dir: pathlib.Path) -> dict[str, Any]:
    """Read and parse package.json from an npm package directory."""
    try:
        pj = pkg_dir / "package.json"
        if pj.exists():
            return json.loads(pj.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        pass
    return {}


def _scan_npm_global() -> list[Finding]:
    """Scan global NPM node_modules for known AI CLI agents and SDKs."""
    findings: list[Finding] = []

    nm_dirs = _resolve_npm_global_prefix()
    if not nm_dirs:
        logger.debug("PackageScanner [npm]: no global node_modules found.")
        return findings

    for nm_dir in nm_dirs:
        logger.debug("PackageScanner [npm]: scanning %s", nm_dir)
        try:
            for entry in nm_dir.iterdir():
                # Handle scoped packages (@org/pkg)
                if entry.is_dir() and entry.name.startswith("@"):
                    for scoped_entry in entry.iterdir():
                        if scoped_entry.is_dir():
                            full_name = f"{entry.name}/{scoped_entry.name}"
                            _check_npm_entry(full_name, scoped_entry, nm_dir, findings)
                elif entry.is_dir():
                    _check_npm_entry(entry.name, entry, nm_dir, findings)
        except (PermissionError, OSError) as e:
            logger.debug("PackageScanner [npm]: cannot read %s: %s", nm_dir, e)

    return findings


def _check_npm_entry(
    pkg_name: str,
    pkg_dir: pathlib.Path,
    nm_dir: pathlib.Path,
    findings: list[Finding],
) -> None:
    """Check a single NPM package directory against AI targets and emit a finding if matched."""
    label = NPM_AI_PACKAGES.get(pkg_name)

    # Fallback: keyword match on package name
    if label is None:
        name_lower = pkg_name.lower()
        if not any(kw in name_lower for kw in NPM_AI_KEYWORDS):
            return
        label = pkg_name  # use the raw package name as label

    pj = _read_npm_package_json(pkg_dir)
    version = pj.get("version", "unknown")
    description_text = pj.get("description", "")

    # Determine category: MCP servers → AI_SERVICE, agent frameworks → AI_AGENT, else ML_FRAMEWORK
    pkg_lower = pkg_name.lower()
    if "modelcontextprotocol" in pkg_lower or "mcp" in pkg_lower:
        category = FindingCategory.AI_SERVICE
    elif any(kw in pkg_lower for kw in ("langchain", "agent", "crewai", "mastra", "genkit")):
        category = FindingCategory.AI_AGENT
    else:
        category = FindingCategory.ML_FRAMEWORK

    install_location = str(pkg_dir.resolve()).replace("\\", "/")

    findings.append(
        _make_finding(
            title=f"NPM Global: {pkg_name} ({version})",
            description=(
                f"Global NPM AI package detected: {label}"
                + (f" — {description_text}" if description_text else "")
            ),
            source=install_location,
            package_name=pkg_name,
            version=version,
            installer="npm (global)",
            install_location=install_location,
            category=category,
            extra_details={
                "npm_modules_dir": str(nm_dir).replace("\\", "/"),
                "label": label,
            },
        )
    )


# ── Scanner C: pipx isolated environments ────────────────────────────────────

def _resolve_pipx_home() -> pathlib.Path | None:
    """Return the pipx venvs directory, respecting PIPX_HOME env var."""
    # Explicit override
    pipx_home = os.environ.get("PIPX_HOME")
    if pipx_home:
        p = pathlib.Path(pipx_home) / "venvs"
        if p.is_dir():
            return p

    # Default locations
    if platform.system() == "Windows":
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        candidates = [
            pathlib.Path(local_appdata) / "pipx" / "venvs" if local_appdata else None,
            pathlib.Path.home() / ".local" / "pipx" / "venvs",
        ]
    else:
        candidates = [
            pathlib.Path.home() / ".local" / "pipx" / "venvs",
            pathlib.Path.home() / ".local" / "share" / "pipx" / "venvs",
        ]

    for c in candidates:
        if c and c.is_dir():
            return c
    return None


def _scan_pipx() -> list[Finding]:
    """Scan pipx isolated venv directories for known AI CLI tools."""
    findings: list[Finding] = []

    # Prefer `pipx list --json` for accurate metadata
    raw = _run_cmd(["pipx", "list", "--json"], timeout=15)
    if raw:
        try:
            data = json.loads(raw)
            # pipx JSON schema: {"venvs": {"pkg_name": {"metadata": {"main_package": {"package": ..., "package_version": ...}}}}}
            venvs: dict = data.get("venvs", {})
            for venv_name, venv_data in venvs.items():
                meta = venv_data.get("metadata", {})
                main_pkg = meta.get("main_package", {})
                pkg_name = main_pkg.get("package", venv_name)
                version = main_pkg.get("package_version", "unknown")
                _emit_pipx_finding(pkg_name, version, findings)
            return findings
        except Exception as e:
            logger.debug("PackageScanner [pipx]: JSON parse failed: %s", e)

    # Fallback: read venv directories directly
    venvs_dir = _resolve_pipx_home()
    if venvs_dir:
        try:
            for entry in venvs_dir.iterdir():
                if entry.is_dir():
                    pkg_name = entry.name
                    # Try to read version from pipx metadata JSON
                    version = _read_pipx_metadata_version(entry)
                    _emit_pipx_finding(pkg_name, version, findings)
        except (PermissionError, OSError) as e:
            logger.debug("PackageScanner [pipx]: cannot read venvs dir: %s", e)

    return findings


def _read_pipx_metadata_version(venv_dir: pathlib.Path) -> str:
    """Read the package version from pipx's internal pipx_metadata.json."""
    try:
        meta_file = venv_dir / "pipx_metadata.json"
        if meta_file.exists():
            data = json.loads(meta_file.read_text(encoding="utf-8", errors="ignore"))
            return (
                data.get("main_package", {}).get("package_version", "unknown")
            )
    except Exception:
        pass
    return "unknown"


def _emit_pipx_finding(pkg_name: str, version: str, findings: list[Finding]) -> None:
    """Emit a Finding if the pipx package matches an AI tool target."""
    name_lower = pkg_name.lower().replace("_", "-")
    label = PIPX_AI_PACKAGES.get(name_lower)

    if label is None:
        # Fallback: keyword match
        if not any(kw in name_lower for kw in (
            "llm", "gpt", "ai", "openai", "anthropic", "claude", "aider",
            "langchain", "crewai", "autogen", "ollama", "copilot", "fabric",
        )):
            return
        label = pkg_name

    category = (
        FindingCategory.AI_AGENT
        if any(kw in name_lower for kw in ("crewai", "autogen", "langchain", "agno", "aider"))
        else FindingCategory.ML_FRAMEWORK
    )

    findings.append(
        _make_finding(
            title=f"pipx Tool: {pkg_name} ({version})",
            description=f"AI CLI tool installed via pipx: {label}",
            source=f"pipx://{pkg_name}",
            package_name=pkg_name,
            version=version,
            installer="pipx",
            install_location=f"pipx://{pkg_name}",
            category=category,
            extra_details={"label": label},
        )
    )


# ── Scanner D: uv tool environments ──────────────────────────────────────────

def _scan_uv_tools() -> list[Finding]:
    """Scan uv tool environments for AI CLI tools.

    `uv tool list` outputs lines like:  package-name v0.1.2
    """
    findings: list[Finding] = []
    raw = _run_cmd(["uv", "tool", "list"], timeout=10)
    if not raw:
        return findings

    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("-"):
            continue
        parts = line.split()
        if not parts:
            continue
        pkg_name = parts[0].rstrip(",")
        version = parts[1].lstrip("v") if len(parts) > 1 else "unknown"
        _emit_pipx_finding(pkg_name, version, findings)
        # Fix installer label for uv
        for f in findings:
            if f.details.get("package_name") == pkg_name and f.details.get("installer") == "pipx":
                f.details["installer"] = "uv (tool)"
                f.source = f"uv://{pkg_name}"
                f.details["install_location"] = f"uv://{pkg_name}"

    return findings


# ── Scanner E: Homebrew (macOS / Linux) ──────────────────────────────────────

def _scan_homebrew() -> list[Finding]:
    """Scan Homebrew installed formulae and casks for AI tools."""
    findings: list[Finding] = []

    # Only relevant on macOS and Linux
    if platform.system() not in ("Darwin", "Linux"):
        return findings

    raw = _run_cmd(["brew", "list", "--formula", "--versions"], timeout=20)
    if not raw:
        return findings

    for line in raw.splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        formula_name = parts[0]
        version = parts[1] if len(parts) > 1 else "unknown"
        name_lower = formula_name.lower()

        label = HOMEBREW_AI_FORMULAE.get(name_lower)
        if label is None:
            if not any(kw in name_lower for kw in (
                "llm", "gpt", "ai", "llama", "ollama", "whisper",
                "stable-diffusion", "huggingface", "copilot",
            )):
                continue
            label = formula_name

        brew_prefix = _run_cmd(["brew", "--prefix", formula_name], timeout=8) or "brew"

        findings.append(
            _make_finding(
                title=f"Homebrew: {formula_name} ({version})",
                description=f"AI tool installed via Homebrew: {label}",
                source=brew_prefix,
                package_name=formula_name,
                version=version,
                installer="homebrew",
                install_location=brew_prefix,
                category=FindingCategory.ML_FRAMEWORK,
                extra_details={"label": label},
            )
        )

    return findings


# ── Scanner F: conda environments ─────────────────────────────────────────────

def _scan_conda() -> list[Finding]:
    """Scan conda environments (base + all named envs) for AI packages.

    First queries the base environment via ``conda list --json``, then
    discovers named environments via ``conda env list --json`` and queries
    each one individually so that packages installed in isolated conda envs
    are not missed.
    """
    findings: list[Finding] = []
    seen_names: set[str] = set()

    def _process_conda_pkg_list(raw: str, env_label: str) -> list[Finding]:
        """Parse a conda list --json output and return AI-matched findings."""
        local_findings: list[Finding] = []
        try:
            packages: list[dict] = json.loads(raw)
        except Exception as e:
            logger.debug("PackageScanner [conda]: JSON parse failed for %s: %s", env_label, e)
            return local_findings

        for pkg in packages:
            name = pkg.get("name", "")
            version = pkg.get("version", "unknown")
            channel = pkg.get("channel", "")
            if not name:
                continue

            name_lower = name.lower().replace("_", "-")
            dedup_key = f"{env_label}:{name_lower}"
            if dedup_key in seen_names:
                continue

            if name_lower not in TARGET_PACKAGES and not any(
                kw in name_lower for kw in (
                    "torch", "tensorflow", "llama", "openai",
                    "anthropic", "huggingface", "diffuser",
                    "transformers", "langchain", "ollama",
                )
            ):
                continue

            seen_names.add(dedup_key)
            category = (
                FindingCategory.AI_AGENT
                if any(kw in name_lower for kw in ("langchain", "crewai", "autogen"))
                else FindingCategory.ML_FRAMEWORK
            )

            local_findings.append(
                _make_finding(
                    title=f"conda ({env_label}): {name} ({version})",
                    description=f"AI package installed in conda environment '{env_label}': {name}",
                    source=f"conda://{env_label}/{name}",
                    package_name=name,
                    version=version,
                    installer="conda",
                    install_location=f"conda://{env_label}/{name}",
                    category=category,
                    extra_details={"channel": channel, "conda_env": env_label},
                )
            )
        return local_findings

    # ── Base environment ──────────────────────────────────────────────────
    raw_base = _run_cmd(["conda", "list", "--json"], timeout=20)
    if raw_base:
        findings.extend(_process_conda_pkg_list(raw_base, "base"))

    # ── Named environments ────────────────────────────────────────────────
    raw_envs = _run_cmd(["conda", "env", "list", "--json"], timeout=15)
    if raw_envs:
        try:
            env_data = json.loads(raw_envs)
            env_paths: list[str] = env_data.get("envs", [])
            for env_path in env_paths:
                env_name = pathlib.Path(env_path).name
                if env_name in ("base", "root", ""):
                    continue
                raw_named = _run_cmd(["conda", "list", "--prefix", env_path, "--json"], timeout=20)
                if raw_named:
                    findings.extend(_process_conda_pkg_list(raw_named, env_name))
        except Exception as e:
            logger.debug("PackageScanner [conda]: env list parse failed: %s", e)

    return findings


# ── Scanner G: global Python environments (non-active) ───────────────────────

# Well-known locations where standalone Python installations keep their
# site-packages — separate from the currently active venv.
def _resolve_global_python_site_packages() -> list[pathlib.Path]:
    """Return site-packages directories from global Python installs.

    Checks:
      - Windows: %ProgramFiles%\\Python3*/Lib/site-packages,
                 %LOCALAPPDATA%\\Programs\\Python\\Python*/Lib/site-packages
      - macOS:   /usr/local/lib/python*/site-packages,
                 /opt/homebrew/lib/python*/site-packages,
                 ~/Library/Python/*/lib/python/site-packages
      - Linux:   /usr/lib/python3/dist-packages,
                 /usr/local/lib/python*/dist-packages
    """
    import glob
    candidates: list[pathlib.Path] = []
    active_prefix = sys.prefix  # avoid rescanning the current environment

    def _add(pattern: str) -> None:
        for path in glob.glob(pattern):
            p = pathlib.Path(path)
            if p.is_dir() and active_prefix not in str(p.resolve()):
                candidates.append(p)

    if platform.system() == "Windows":
        pf = os.environ.get("ProgramFiles", "C:\\Program Files")
        la = os.environ.get("LOCALAPPDATA", "")
        _add(f"{pf}\\Python3*\\Lib\\site-packages")
        _add(f"{pf}\\Python\\Python3*\\Lib\\site-packages")
        if la:
            _add(f"{la}\\Programs\\Python\\Python3*\\Lib\\site-packages")
    elif platform.system() == "Darwin":
        _add("/usr/local/lib/python3*/site-packages")
        _add("/opt/homebrew/lib/python3*/site-packages")
        _add(str(pathlib.Path.home() / "Library/Python/3*/lib/python/site-packages"))
    else:
        _add("/usr/lib/python3/dist-packages")
        _add("/usr/local/lib/python3/dist-packages")
        _add("/usr/lib/python3*/dist-packages")
        _add("/usr/local/lib/python3*/dist-packages")

    return list(set(candidates))


def _scan_pip_global_envs() -> list[Finding]:
    """Scan global (non-active) Python site-packages for AI packages.

    Reads ``<site-packages>/<pkg>.dist-info/METADATA`` to extract the
    package name and version without executing any subprocess.
    """
    findings: list[Finding] = []
    seen: set[str] = set()

    site_dirs = _resolve_global_python_site_packages()
    if not site_dirs:
        return findings

    for site_dir in site_dirs:
        logger.debug("PackageScanner [pip-global]: scanning %s", site_dir)
        try:
            for entry in site_dir.iterdir():
                if not entry.is_dir():
                    continue
                # dist-info directories are named  pkg-version.dist-info
                if not entry.name.endswith(".dist-info"):
                    continue

                metadata_file = entry / "METADATA"
                if not metadata_file.exists():
                    metadata_file = entry / "PKG-INFO"
                if not metadata_file.exists():
                    continue

                try:
                    name = ""
                    version = "unknown"
                    for line in metadata_file.read_text(
                        encoding="utf-8", errors="ignore"
                    ).splitlines():
                        if line.startswith("Name:"):
                            name = line.split(":", 1)[1].strip()
                        elif line.startswith("Version:"):
                            version = line.split(":", 1)[1].strip()
                        if name and version != "unknown":
                            break
                except (OSError, PermissionError):
                    continue

                if not name:
                    continue

                name_lower = name.lower().replace("_", "-")
                dedup_key = f"{site_dir}:{name_lower}"
                if dedup_key in seen:
                    continue

                if name_lower not in TARGET_PACKAGES and not any(
                    kw in name_lower for kw in (
                        "openai", "anthropic", "gemini", "langchain", "llama",
                        "transformers", "torch", "tensorflow", "crewai",
                        "autogen", "ollama", "huggingface", "diffuser",
                    )
                ):
                    continue

                seen.add(dedup_key)
                install_loc = str(site_dir).replace("\\", "/")
                category = (
                    FindingCategory.AI_AGENT
                    if any(kw in name_lower for kw in ("langchain", "crewai", "autogen"))
                    else FindingCategory.ML_FRAMEWORK
                )

                findings.append(
                    _make_finding(
                        title=f"Python (global): {name} ({version})",
                        description=(
                            f"AI package found in global Python environment: {name} "
                            f"(version {version})"
                        ),
                        source=install_loc,
                        package_name=name,
                        version=version,
                        installer="pip (global install)",
                        install_location=install_loc,
                        category=category,
                        extra_details={"site_packages_dir": install_loc},
                    )
                )
        except (PermissionError, OSError) as e:
            logger.debug("PackageScanner [pip-global]: cannot read %s: %s", site_dir, e)

    return findings


def _get_package_metadata_hash(name: str, version: str, install_location: str, inst_type: str) -> str | None:
    """Locate package metadata file and compute its SHA-256 hash."""
    import hashlib

    # 1. Python pip packages (using importlib.metadata to locate files)
    if inst_type == "pip":
        try:
            import importlib.metadata
            dist = importlib.metadata.distribution(name)
            p = None
            if dist.files:
                for f in dist.files:
                    if str(f).endswith("METADATA"):
                        p = dist.locate_file(f)
                        break
            if p and p.exists():
                return hashlib.sha256(p.read_bytes()).hexdigest()
        except Exception:
            pass

        # Fallback 1: search for METADATA file in directory
        try:
            p_dir = pathlib.Path(install_location)
            if p_dir.is_dir():
                parent = p_dir.parent
                for item in parent.glob(f"{name.replace('_', '-')}-{version}*.dist-info"):
                    meta = item / "METADATA"
                    if meta.exists():
                        return hashlib.sha256(meta.read_bytes()).hexdigest()
                for item in parent.glob(f"{name.replace('-', '_')}-{version}*.dist-info"):
                    meta = item / "METADATA"
                    if meta.exists():
                        return hashlib.sha256(meta.read_bytes()).hexdigest()
        except Exception:
            pass

    # 2. NPM packages (hash package.json)
    elif inst_type == "npm":
        try:
            p_path = pathlib.Path(install_location) / "package.json"
            if p_path.exists():
                return hashlib.sha256(p_path.read_bytes()).hexdigest()
        except Exception:
            pass

    # Fallback/Generic (if we have a direct path, check if it's a file)
    try:
        p_path = pathlib.Path(install_location)
        if p_path.is_file():
            return hashlib.sha256(p_path.read_bytes()).hexdigest()
    except Exception:
        pass

    return None


def _verify_against_baseline(installer: str, pkg_name: str, version: str, calc_hash: str) -> tuple[str, bool, bool]:
    """Verify calculated hash against scanner/baseline/hashes.json.

    Returns:
        (status, is_verified, is_tampered)
    """
    baseline_path = pathlib.Path(__file__).parent.parent / "baseline" / "hashes.json"
    if not baseline_path.exists():
        return "unverified", False, False

    try:
        with open(baseline_path, encoding="utf-8") as f:
            db = json.load(f)

        ecosystem = db.get(installer)
        if not ecosystem:
            return "unverified", False, False

        pkg_data = None
        for key, val in ecosystem.items():
            if key.lower().replace("_", "-") == pkg_name.lower().replace("_", "-"):
                pkg_data = val
                break

        if not pkg_data or not isinstance(pkg_data, dict):
            return "unverified", False, False

        expected_hash = pkg_data.get(version)
        if not expected_hash:
            return "unverified", False, False

        if calc_hash == expected_hash:
            return "verified", True, False
        else:
            return "tampered", False, True

    except Exception as e:
        logger.warning("Error reading baseline hashes database: %s", e)
        return "unverified", False, False


def run() -> tuple[list[Finding], ModuleInfo]:
    """Execute the Package Scanner module across all supported package ecosystems.

    Runs scanners for:
      A. pip (active Python environment)
      B. pip-global (non-active global Python installations)
      C. NPM global prefix (npm, NVM, Volta, pnpm, Yarn)
      D. pipx isolated environments
      E. uv tool environments
      F. Homebrew formulae (macOS/Linux)
      G. conda environments (base + all named envs)

    Returns:
        Tuple of (findings_list, module_info)
    """
    module_info = ModuleInfo(name=MODULE_NAME, module_number=MODULE_NUMBER)
    findings: list[Finding] = []
    start_time = time.monotonic()

    scanners = [
        ("pip",         _scan_pip),
        ("pip-global",  _scan_pip_global_envs),
        ("npm",         _scan_npm_global),
        ("pipx",        _scan_pipx),
        ("uv",          _scan_uv_tools),
        ("homebrew",    _scan_homebrew),
        ("conda",       _scan_conda),
    ]

    errors: list[str] = []
    for name, scanner_fn in scanners:
        try:
            results = scanner_fn()
            if results:
                logger.info("PackageScanner [%s]: found %d AI packages", name, len(results))
            findings.extend(results)
        except Exception as exc:
            logger.warning("PackageScanner [%s]: scanner failed: %s", name, exc)
            errors.append(f"{name}: {exc}")

    # Centralized package verification against the baseline
    verified_findings = []
    for finding in findings:
        pkg_name = finding.details.get("package_name")
        version = finding.details.get("version")
        installer = finding.details.get("installer", "")
        install_loc = finding.details.get("install_location")

        if pkg_name and version and install_loc:
            # Determine normalized installer type (pip or npm)
            inst_type = "pip"
            if "npm" in installer.lower():
                inst_type = "npm"
            elif "brew" in installer.lower():
                inst_type = "homebrew"
            elif "conda" in installer.lower():
                inst_type = "conda"

            calc_hash = _get_package_metadata_hash(pkg_name, version, install_loc, inst_type)
            if calc_hash:
                finding.details["sha256_hash"] = calc_hash
                status, is_verified, is_tampered = _verify_against_baseline(inst_type, pkg_name, version, calc_hash)
                finding.details["verification_status"] = status
                finding.details["verified"] = is_verified
                finding.details["tampered"] = is_tampered

                # Flag unverified / tampered packages
                if is_tampered:
                    finding.risk_level = RiskLevel.HIGH
                    finding.title = f"[TAMPERED] {finding.title}"
                    finding.description += f" WARNING: Cryptographic hash does not match baseline! Calculated: {calc_hash}."
                elif not is_verified:
                    finding.risk_level = RiskLevel.LOW
                    finding.title = f"[UNVERIFIED] {finding.title}"
                    finding.description += " Note: This package has not been verified against the baseline database."
                else:
                    finding.details["verification_status"] = "verified"
                    finding.details["verified"] = True
                    finding.details["tampered"] = False
                    finding.description += " (Verified package integrity)"
            else:
                finding.details["verified"] = False
                finding.details["tampered"] = False
                finding.details["verification_status"] = "unverified"
                finding.risk_level = RiskLevel.LOW
                finding.title = f"[UNVERIFIED] {finding.title}"
                finding.description += " Note: Could not compute metadata hash. Package integrity unverified."
        else:
            # Missing basic package info
            finding.details["verified"] = False
            finding.details["tampered"] = False
            finding.details["verification_status"] = "unverified"

        verified_findings.append(finding)

    findings = verified_findings

    if errors and not findings:
        module_info.status = "error"
        module_info.error_message = "; ".join(errors)
    else:
        module_info.status = "success"

    module_info.duration_sec = time.monotonic() - start_time
    module_info.findings_count = len(findings)
    return findings, module_info


def _scan_folder_packages(scan_folder: str) -> list[Finding]:
    """Scan local repository folder recursively for requirements.txt and package.json files."""
    import re
    findings: list[Finding] = []
    folder_path = pathlib.Path(scan_folder).resolve()
    
    exclude_dirs = {".git", "node_modules", "venv", ".venv", "env", "dist", "build"}
    
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            file_path = pathlib.Path(root) / file
            rel_path = os.path.relpath(file_path, folder_path).replace("\\", "/")
            
            if file == "requirements.txt":
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().lower()
                        for dep in TARGET_PACKAGES:
                            if re.search(rf"\b{re.escape(dep)}\b", content):
                                findings.append(
                                    _make_finding(
                                        title=f"Dependency: {dep}",
                                        description=f"Detected Python dependency '{dep}' declared in {rel_path}.",
                                        source=f"{str(file_path.resolve()).replace('\\', '/')}:requirements",
                                        package_name=dep,
                                        version="declared",
                                        installer="pip",
                                        install_location=str(file_path.resolve()).replace("\\", "/"),
                                        category=FindingCategory.ML_FRAMEWORK if dep not in {"langchain", "crewai", "autogen", "agno"} else FindingCategory.AI_AGENT
                                    )
                                )
                except Exception as e:
                    logger.debug("Failed reading %s: %s", rel_path, e)
                    
            elif file == "package.json":
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        data = json.load(f)
                        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                        for dep in NPM_AI_PACKAGES:
                            if dep in deps:
                                version = deps[dep]
                                label = NPM_AI_PACKAGES[dep]
                                findings.append(
                                    _make_finding(
                                        title=f"NPM Dependency: {dep} ({version})",
                                        description=f"Detected Node.js dependency '{label}' ({dep}) declared in {rel_path}.",
                                        source=f"{str(file_path.resolve()).replace('\\', '/')}:package.json",
                                        package_name=dep,
                                        version=version,
                                        installer="npm",
                                        install_location=str(file_path.resolve()).replace("\\", "/"),
                                        category=FindingCategory.ML_FRAMEWORK if "mcp" not in dep.lower() else FindingCategory.AI_SERVICE
                                    )
                                )
                except Exception as e:
                    logger.debug("Failed reading %s: %s", rel_path, e)
    return findings


class PackageScanner:
    """Wrapper class for Module 04 PackageScanner to conform to the Discovery Engine interface."""

    MODULE_NAME = MODULE_NAME
    MODULE_NUMBER = MODULE_NUMBER

    def __init__(self, scan_folder: str | None = None) -> None:
        self.scan_folder = scan_folder

    def scan(self) -> list[Finding]:
        if self.scan_folder:
            return _scan_folder_packages(self.scan_folder)
        findings, _ = run()
        return findings


if __name__ == "__main__":
    print("Running MODULE 04 — PackageScanner standalone test...\n")
    findings, info = run()

    print(f"Module Status : {info.status}")
    print(f"Duration      : {info.duration_sec:.3f}s")
    print(f"Findings count: {info.findings_count}\n")

    for f in findings:
        print(f"[{f.finding_id}] {f.title}")
        print(f"  Category   : {f.category}")
        print(f"  Risk Level : {f.risk_level}")
        print(f"  Source     : {f.source}")
        print(f"  Details    : {json.dumps(f.details, indent=2)}")
        print()
