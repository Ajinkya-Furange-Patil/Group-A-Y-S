"""
MODULE 03 — Process Scanner
===========================
Scans running system processes to detect active AI services, tools, or runtimes
(e.g., Ollama, LM Studio, vLLM, ChatGPTHelper, Claude) or Python processes running
AI/ML workloads. Also performs active memory scanning on flagged AI daemon processes
to gather additional telemetry (memory maps, open files, connections).

Author: Person B
Day: 2
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from typing import Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from scanner.models import Finding, FindingCategory, ModuleInfo, RiskLevel
from scanner import signature_verifier

logger = logging.getLogger(__name__)

MODULE_NAME = "ProcessScanner"
MODULE_NUMBER = 3

# Target process name keywords (case-insensitive) — local AI runtimes
AI_PROCESS_KEYWORDS = {
    "ollama",
    "lmstudio",
    "lm-studio",
    "llama.cpp",
    "vllm",
    "llama-bench",
    "llama-server",
    "localai",
}

# Known AI daemon executable names — matched exactly (case-insensitive).
# These are background service processes installed by cloud/desktop AI clients.
AI_DAEMON_NAMES: dict[str, str] = {
    # OpenAI / ChatGPT desktop
    "chatgpthelper.exe":        "ChatGPT Desktop Helper",
    "chatgpt.exe":              "ChatGPT Desktop App",
    "openai.exe":               "OpenAI Process",
    # Anthropic Claude
    "claude.exe":               "Claude Desktop App",
    "claudehelper.exe":         "Claude Desktop Helper",
    # Microsoft Copilot
    "microsoftcopilot.exe":     "Microsoft Copilot",
    "copilotruntime.exe":       "Microsoft Copilot Runtime",
    # Google Gemini / AI
    "gemini.exe":               "Google Gemini",
    "googlegeminiplugin.exe":   "Google Gemini Plugin",
    # GitHub Copilot agent
    "copilot-language-server.exe": "GitHub Copilot Language Server",
    "gh-copilot.exe":           "GitHub Copilot CLI",
    # Cursor / Windsurf / similar AI-first editors
    "cursor.exe":               "Cursor AI Editor",
    "windsurf.exe":             "Windsurf AI Editor",
    # Generic AI assistant helpers (partial-match prefix below)
}

# Partial-match prefixes for AI daemon detection (case-insensitive).
# Catches versioned variants like "chatgpthelper_2.exe", "claude-3.exe", etc.
AI_DAEMON_PREFIXES: tuple[str, ...] = (
    "chatgpthelper",
    "claude",
    "claudehelper",
    "copilotruntime",
    "microsoftcopilot",
    "geminihelper",
)

# Command-line keywords indicating AI-related Python runs
AI_CMDLINE_KEYWORDS = {
    "ollama",
    "lmstudio",
    "lm-studio",
    "llama",
    "vllm",
    "transformers",
    "torch",
    "pytorch",
    "tensorflow",
    "langchain",
    "crewai",
    "autogen",
    "gradio",
    "streamlit",
    "jupyter",
    "notebook",
}


def _get_process_safe(proc: psutil.Process, attr: str, default: Any = None) -> Any:
    """Safely query a process attribute, handling exceptions."""
    try:
        val = getattr(proc, attr)
        if callable(val):
            return val()
        return val
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, AttributeError, PermissionError):
        return default


def _collect_memory_telemetry(proc: psutil.Process) -> dict[str, Any]:
    """Perform active memory scanning on a flagged AI daemon process.

    Collects memory maps, open file handles, and network connections
    from the process's address space to provide richer telemetry without
    suspending or injecting into the process.

    Args:
        proc: A live psutil.Process object.

    Returns:
        Dictionary with keys: memory_maps, open_files, connections, memory_full_mb.
        Each sub-list is capped at 20 entries to avoid bloating the report.
    """
    telemetry: dict[str, Any] = {
        "memory_maps": [],
        "open_files": [],
        "connections": [],
        "memory_full_mb": None,
    }

    # ── Full memory info (USS/PSS where available) ────────────────────────
    try:
        full_mem = proc.memory_full_info()
        # USS (Unique Set Size) gives actual exclusive memory consumption
        uss_mb = round(full_mem.uss / (1024 ** 2), 2) if hasattr(full_mem, "uss") else None
        rss_mb = round(full_mem.rss / (1024 ** 2), 2)
        telemetry["memory_full_mb"] = {"rss_mb": rss_mb, "uss_mb": uss_mb}
    except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError, AttributeError):
        pass

    # ── Memory-mapped files — reveals model files loaded into memory ──────
    try:
        maps = proc.memory_maps(grouped=False)
        ai_map_keywords = (
            ".gguf", ".safetensors", ".pt", ".pth", ".onnx", ".bin",
            "model", "weights", "llama", "claude", "gpt", "gemini",
        )
        mapped_paths: list[str] = []
        for mmap in maps:
            path_lower = mmap.path.lower()
            if any(kw in path_lower for kw in ai_map_keywords):
                mapped_paths.append(mmap.path)
        # Deduplicate while preserving order, cap at 20
        seen: set[str] = set()
        for p in mapped_paths:
            if p not in seen:
                seen.add(p)
                telemetry["memory_maps"].append(p)
                if len(telemetry["memory_maps"]) >= 20:
                    break
    except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError, AttributeError, NotImplementedError):
        pass

    # ── Open file handles — surfaces config/cache files being read ────────
    try:
        open_files = proc.open_files()
        ai_file_keywords = (
            "config", "settings", "cache", "model", ".json", ".yaml",
            "token", "credential", "session", ".gguf",
        )
        for of in open_files[:50]:
            path_lower = of.path.lower()
            if any(kw in path_lower for kw in ai_file_keywords):
                telemetry["open_files"].append(of.path)
                if len(telemetry["open_files"]) >= 20:
                    break
    except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError, AttributeError):
        pass

    # ── Network connections — detects active API/telemetry outbound calls ─
    try:
        conns = proc.connections(kind="inet")
        for conn in conns[:20]:
            try:
                status = conn.status if hasattr(conn, "status") else "N/A"
                remote = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
                local = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
                telemetry["connections"].append({
                    "local": local,
                    "remote": remote,
                    "status": status,
                })
            except AttributeError:
                continue
    except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError, AttributeError):
        pass

    return telemetry


def _match_ai_daemon(name: str, exe: str) -> tuple[bool, str, str]:
    """Check if a process name matches a known AI daemon.

    Checks both exact matches in AI_DAEMON_NAMES and prefix matches
    in AI_DAEMON_PREFIXES against the process name and exe basename.

    Args:
        name: Process name as reported by the OS.
        exe:  Full path to the executable.

    Returns:
        Tuple of (is_daemon, matched_key, daemon_label).
    """
    name_lower = name.lower()
    exe_basename = os.path.basename(exe).lower() if exe else ""

    # Exact match against known daemon dict
    for key, label in AI_DAEMON_NAMES.items():
        if name_lower == key or exe_basename == key:
            return True, key, label

    # Prefix match for versioned / variant executables
    for prefix in AI_DAEMON_PREFIXES:
        if name_lower.startswith(prefix) or exe_basename.startswith(prefix):
            # Derive a human-readable label from the prefix
            label = prefix.replace("helper", " Helper").replace("runtime", " Runtime").title()
            return True, prefix, label

    return False, "", ""


def run() -> tuple[list[Finding], ModuleInfo]:
    """Execute the Process Scanner module.

    Queries all running processes and filters for:
      1. Known AI runtimes (Ollama, LM Studio, vLLM, etc.)
      2. Known AI daemon processes (ChatGPTHelper, Claude, Copilot, etc.)
      3. AI-related Python script executions

    For any flagged AI daemon, active memory telemetry is collected via
    _collect_memory_telemetry() to surface loaded model files, open config
    handles, and outbound network connections.

    Returns:
        Tuple of (findings_list, module_info)
    """
    module_info = ModuleInfo(name=MODULE_NAME, module_number=MODULE_NUMBER)
    findings: list[Finding] = []
    start_time = time.monotonic()

    if not PSUTIL_AVAILABLE:
        module_info.status = "skipped"
        module_info.error_message = "psutil is not installed."
        return findings, module_info

    try:
        for proc in psutil.process_iter():
            try:
                pid = proc.pid
                name = _get_process_safe(proc, "name", "")
                if not name:
                    continue

                name_lower = name.lower()
                cmdline = _get_process_safe(proc, "cmdline", []) or []
                cmdline_str = " ".join(cmdline).lower()
                exe = _get_process_safe(proc, "exe", "") or ""

                is_ai_process = False
                is_daemon = False
                matched_keyword = ""
                description = ""
                title = name

                # ── Check 1: Known AI daemon executables (with memory scan) ─────
                daemon_match, daemon_key, daemon_label = _match_ai_daemon(name, exe)
                if daemon_match:
                    is_ai_process = True
                    is_daemon = True
                    matched_keyword = daemon_key
                    title = daemon_label
                    description = (
                        f"AI daemon detected: {daemon_label} (PID {pid}) is running "
                        f"as a background process."
                    )

                # ── Check 2: Directly matches known AI runtime keywords ──────────
                if not is_ai_process:
                    for kw in AI_PROCESS_KEYWORDS:
                        if kw in name_lower or kw in os.path.basename(exe).lower():
                            is_ai_process = True
                            matched_keyword = kw
                            description = (
                                f"Running Ollama service"
                                if "ollama" in kw
                                else f"Running {kw} process"
                            )
                            break

                # ── Check 3: Python process running AI workload ──────────────────
                if not is_ai_process and ("python" in name_lower or "python" in exe.lower()):
                    for kw in AI_CMDLINE_KEYWORDS:
                        if kw in cmdline_str:
                            is_ai_process = True
                            matched_keyword = kw
                            script_name = ""
                            for arg in cmdline:
                                if arg.endswith(".py"):
                                    script_name = os.path.basename(arg)
                                    break

                            if script_name:
                                title = f"{name} ({script_name})"
                                description = (
                                    f"Running AI process executing script "
                                    f"'{script_name}' (matched: {kw})"
                                )
                            else:
                                title = f"{name} (AI script)"
                                description = (
                                    f"Running AI process (matched command line keyword: {kw})"
                                )
                            break

                if is_ai_process:
                    # ── Base process metadata ────────────────────────────────────
                    username = _get_process_safe(proc, "username", "N/A")
                    cpu_percent = _get_process_safe(proc, "cpu_percent", 0.0)

                    mem_info = _get_process_safe(proc, "memory_info", None)
                    memory_rss_mb = round(mem_info.rss / (1024 ** 2), 2) if mem_info else 0.0

                    create_time_raw = _get_process_safe(proc, "create_time", 0.0)
                    create_time_str = (
                        datetime.fromtimestamp(create_time_raw).isoformat()
                        if create_time_raw > 0
                        else "N/A"
                    )

                    details: dict = {
                        "pid": pid,
                        "name": name,
                        "exe": exe or "N/A",
                        "cmdline": cmdline or "N/A",
                        "username": username,
                        "cpu_percent": cpu_percent,
                        "memory_rss_mb": memory_rss_mb,
                        "create_time": create_time_str,
                        "matched_keyword": matched_keyword,
                        "is_ai_daemon": is_daemon,
                    }

                    # Cryptographic signature and hash verifier check
                    if exe and os.path.exists(exe):
                        sig_info = signature_verifier.verify_executable(exe)
                        details["signature_info"] = sig_info

                    # ── Active memory telemetry for AI daemons ───────────────────
                    # Only performed for explicitly known AI daemon processes to
                    # avoid the overhead of full memory map enumeration on every
                    # matched Python script process.
                    if is_daemon:
                        logger.debug(
                            "ProcessScanner: Collecting memory telemetry for daemon '%s' (PID %d)",
                            title, pid,
                        )
                        mem_telemetry = _collect_memory_telemetry(proc)
                        details["memory_telemetry"] = mem_telemetry

                    # Daemons carry higher risk than local runtimes since they
                    # represent persistent background services that may beacon home.
                    risk = RiskLevel.HIGH if is_daemon else RiskLevel.MEDIUM

                    finding = Finding(
                        module_name=MODULE_NAME,
                        title=title,
                        description=description,
                        source=name,
                        category=FindingCategory.LLM_RUNTIME,
                        risk_level=risk,
                        details=details,
                    )
                    findings.append(finding)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, PermissionError, OSError):
                continue

        module_info.status = "success"

    except Exception as exc:
        module_info.status = "error"
        module_info.error_message = str(exc)

    finally:
        module_info.duration_sec = time.monotonic() - start_time
        module_info.findings_count = len(findings)

    return findings, module_info


class ProcessScanner:
    """Wrapper class for Module 03 ProcessScanner to conform to the Discovery Engine interface."""

    MODULE_NAME = MODULE_NAME
    MODULE_NUMBER = MODULE_NUMBER

    def scan(self) -> list[Finding]:
        findings, _ = run()
        return findings


if __name__ == "__main__":
    import json

    print("Running MODULE 03 - ProcessScanner standalone test...\n")
    findings, info = run()

    print(f"Module Status : {info.status}")
    print(f"Duration      : {info.duration_sec:.3f}s")
    print(f"Findings count: {info.findings_count}\n")

    for f in findings:
        print(f"[{f.finding_id}] {f.title}")
        print(f"  Description: {f.description}")
        print(f"  Source     : {f.source}")
        print(f"  Details    : {json.dumps(f.details, indent=2)}")
        print()
