"""
MODULE 03 — Process Scanner
===========================
Scans running system processes to detect active AI services, tools, or runtimes
(e.g., Ollama, LM Studio, vLLM) or Python processes running AI/ML workloads.

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

logger = logging.getLogger(__name__)

MODULE_NAME = "ProcessScanner"
MODULE_NUMBER = 3

# Target process name keywords (case-insensitive)
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


def run() -> tuple[list[Finding], ModuleInfo]:
    """Execute the Process Scanner module.

    Queries all running processes and filters for known AI runtimes or AI-related
    Python executions.

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
                matched_keyword = ""
                description = ""
                title = name

                # Check 1: Directly matches known AI process keywords
                for kw in AI_PROCESS_KEYWORDS:
                    if kw in name_lower or kw in os.path.basename(exe).lower():
                        is_ai_process = True
                        matched_keyword = kw
                        description = f"Running Ollama service" if "ollama" in kw else f"Running {kw} process"
                        break

                # Check 2: Python process running AI workload
                if not is_ai_process and ("python" in name_lower or "python" in exe.lower()):
                    for kw in AI_CMDLINE_KEYWORDS:
                        if kw in cmdline_str:
                            is_ai_process = True
                            matched_keyword = kw
                            # Try to extract the script name from cmdline
                            script_name = ""
                            for arg in cmdline:
                                if arg.endswith(".py"):
                                    script_name = os.path.basename(arg)
                                    break
                            
                            if script_name:
                                title = f"{name} ({script_name})"
                                description = f"Running AI process executing script '{script_name}' (matched: {kw})"
                            else:
                                title = f"{name} (AI script)"
                                description = f"Running AI process (matched command line keyword: {kw})"
                            break

                if is_ai_process:
                    # Collect metadata
                    username = _get_process_safe(proc, "username", "N/A")
                    cpu_percent = _get_process_safe(proc, "cpu_percent", 0.0)
                    
                    # Memory info
                    mem_info = _get_process_safe(proc, "memory_info", None)
                    memory_rss_mb = round(mem_info.rss / (1024 ** 2), 2) if mem_info else 0.0

                    # Creation time
                    create_time_raw = _get_process_safe(proc, "create_time", 0.0)
                    create_time_str = (
                        datetime.fromtimestamp(create_time_raw).isoformat()
                        if create_time_raw > 0
                        else "N/A"
                    )

                    finding = Finding(
                        module_name=MODULE_NAME,
                        title=title,
                        description=description,
                        source=name,  # E.g. "ollama"
                        category=FindingCategory.LLM_RUNTIME,  # Classifier will override / verify
                        risk_level=RiskLevel.MEDIUM,  # Active running service
                        details={
                            "pid": pid,
                            "name": name,
                            "exe": exe or "N/A",
                            "cmdline": cmdline or "N/A",
                            "username": username,
                            "cpu_percent": cpu_percent,
                            "memory_rss_mb": memory_rss_mb,
                            "create_time": create_time_str,
                            "matched_keyword": matched_keyword,
                        },
                    )
                    findings.append(finding)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        module_info.status = "success"

    except Exception as exc:
        module_info.status = "error"
        module_info.error_message = str(exc)

    finally:
        module_info.duration_sec = time.monotonic() - start_time
        module_info.findings_count = len(findings)

    return findings, module_info


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
