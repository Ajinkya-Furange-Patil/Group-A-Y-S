"""
MODULE 06 — Runtime Scanner
===========================
Identifies active LLM runtimes (e.g. Ollama, LM Studio, llama.cpp) by
combining active port scanning (ports 11434, 8000, 5000, 8080) with local
directory checks (~/.ollama, ~/lmstudio).

Author: Person B
Day: 3
"""

from __future__ import annotations

import logging
import os
import pathlib
import socket
import time
from typing import Any

from scanner.models import Finding, FindingCategory, ModuleInfo, RiskLevel

logger = logging.getLogger(__name__)

MODULE_NAME = "RuntimeScanner"
MODULE_NUMBER = 6

# Port mapping to common AI runtimes
PORT_MAP = {
    11434: "Ollama (LLM Service)",
    1234: "LM Studio (Local API Server)",
    8000: "vLLM / LocalAI / LiteLLM",
    5000: "Flask AI / Ollama Service",
    8080: "llama.cpp / LocalAI Server",
}

# Directories related to AI/LLM runtimes in user's home directory
DIR_MAP = {
    ".ollama": "Ollama local storage directory",
    "lmstudio": "LM Studio local files directory",
    ".lmstudio": "LM Studio dotfiles directory",
}


def _check_port(port: int) -> bool:
    """Check if a port is open on localhost using a short timeout.

    Args:
        port: The port number to test.

    Returns:
        True if the port is open and accepting connections, False otherwise.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            # Try to connect to 127.0.0.1
            result = s.connect_ex(("127.0.0.1", port))
            return result == 0
    except Exception as e:
        logger.debug("RuntimeScanner: Socket check failed on port %d: %s", port, e)
        return False


def _find_process_for_port(port: int) -> dict[str, Any] | None:
    """Find process info listening on a local port using psutil.

    Returns a dict with process details (pid, name, cmdline) or None.
    """
    try:
        import psutil
    except ImportError:
        logger.debug("RuntimeScanner: psutil is not available")
        return None

    # First try psutil.net_connections() which is fast but might raise AccessDenied on some systems
    try:
        conns = psutil.net_connections(kind="inet")
        for conn in conns:
            if conn.laddr and conn.laddr.port == port and conn.status == "LISTEN":
                if conn.pid is not None:
                    try:
                        p = psutil.Process(conn.pid)
                        return {
                            "process_id": conn.pid,
                            "process_name": p.name(),
                            "process_cmdline": p.cmdline(),
                        }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        return {
                            "process_id": conn.pid,
                            "process_name": "Unknown (Access Denied)",
                            "process_cmdline": [],
                        }
    except (psutil.AccessDenied, PermissionError):
        # Fall back to process iteration
        pass
    except Exception as e:
        logger.debug("RuntimeScanner: Global net_connections check failed: %s", e)

    # Fallback: iterate over all processes and inspect connections
    try:
        for p in psutil.process_iter(["pid", "name"]):
            try:
                conns = p.connections(kind="inet")
                for conn in conns:
                    if conn.laddr and conn.laddr.port == port and conn.status == "LISTEN":
                        return {
                            "process_id": p.pid,
                            "process_name": p.name(),
                            "process_cmdline": p.cmdline(),
                        }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logger.debug("RuntimeScanner: Process connections iteration failed: %s", e)

    return None


def _scan_repo_runtimes(folder: pathlib.Path) -> list[Finding]:
    """Scan the repository for runtime configurations and AI-specific container images."""
    findings: list[Finding] = []

    for root, dirs, files in os.walk(folder):
        rel_root = pathlib.Path(root).relative_to(folder)
        depth = len(rel_root.parts)
        if depth > 5:
            dirs.clear()
            continue

        for d in list(dirs):
            if d.startswith(".") or d in ("node_modules", "venv", ".venv", "env", ".env", "build", "dist", "__pycache__"):
                dirs.remove(d)

        for file in files:
            file_lower = file.lower()
            full_path = pathlib.Path(root) / file
            rel_path = full_path.relative_to(folder)
            source_str = str(rel_path).replace("\\", "/")

            if file_lower == ".python-version":
                try:
                    version = full_path.read_text(encoding="utf-8", errors="ignore").strip()
                    if version:
                        findings.append(Finding(
                            module_name=MODULE_NAME,
                            title=f"Python Version Pinning: {version}",
                            description=f"Detected Python version config in repository: {version} (via .python-version)",
                            source=source_str,
                            category=FindingCategory.LLM_RUNTIME,
                            risk_level=RiskLevel.INFO,
                            confidence=0.90,
                            details={"runtime": "Python", "version": version, "config_file": source_str}
                        ))
                except Exception as e:
                    logger.debug("Error reading %s: %s", full_path, e)

            elif file_lower in (".nvmrc", ".node-version"):
                try:
                    version = full_path.read_text(encoding="utf-8", errors="ignore").strip()
                    if version:
                        findings.append(Finding(
                            module_name=MODULE_NAME,
                            title=f"Node.js Version Pinning: {version}",
                            description=f"Detected Node.js version config in repository: {version} (via {file})",
                            source=source_str,
                            category=FindingCategory.LLM_RUNTIME,
                            risk_level=RiskLevel.INFO,
                            confidence=0.90,
                            details={"runtime": "Node.js", "version": version, "config_file": source_str}
                        ))
                except Exception as e:
                    logger.debug("Error reading %s: %s", full_path, e)

            elif file_lower == "runtime.txt":
                try:
                    version = full_path.read_text(encoding="utf-8", errors="ignore").strip()
                    if "python" in version.lower():
                        findings.append(Finding(
                            module_name=MODULE_NAME,
                            title=f"Python Runtime Config: {version}",
                            description=f"Detected runtime specification in repository: {version} (via runtime.txt)",
                            source=source_str,
                            category=FindingCategory.LLM_RUNTIME,
                            risk_level=RiskLevel.INFO,
                            confidence=0.90,
                            details={"runtime": "Python", "version": version, "config_file": source_str}
                        ))
                except Exception as e:
                    logger.debug("Error reading %s: %s", full_path, e)

            elif file_lower == ".tool-versions":
                try:
                    content = full_path.read_text(encoding="utf-8", errors="ignore")
                    runtimes = {}
                    for line in content.splitlines():
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            runtimes[parts[0]] = parts[1]
                    if runtimes:
                        findings.append(Finding(
                            module_name=MODULE_NAME,
                            title="asdf Tool Versions Config",
                            description=f"Detected tool versions in repository: {', '.join(f'{k} {v}' for k, v in runtimes.items())} (via .tool-versions)",
                            source=source_str,
                            category=FindingCategory.LLM_RUNTIME,
                            risk_level=RiskLevel.INFO,
                            confidence=0.90,
                            details={"runtimes": runtimes, "config_file": source_str}
                        ))
                except Exception as e:
                    logger.debug("Error reading %s: %s", full_path, e)

            elif file_lower == "pyproject.toml":
                try:
                    content = full_path.read_text(encoding="utf-8", errors="ignore")
                    import re
                    py_match = re.search(r'python\s*=\s*["\']([^"\']+)["\']', content)
                    if py_match:
                        py_ver = py_match.group(1).strip()
                        findings.append(Finding(
                            module_name=MODULE_NAME,
                            title=f"Python Target Version: {py_ver}",
                            description=f"Detected Python target version in pyproject.toml: {py_ver}",
                            source=source_str,
                            category=FindingCategory.LLM_RUNTIME,
                            risk_level=RiskLevel.INFO,
                            confidence=0.90,
                            details={"runtime": "Python", "version": py_ver, "config_file": source_str}
                        ))
                except Exception as e:
                    logger.debug("Error reading %s: %s", full_path, e)

            elif file_lower == "dockerfile":
                try:
                    content = full_path.read_text(encoding="utf-8", errors="ignore")
                    import re
                    from_matches = re.findall(r'(?i)^\s*FROM\s+([a-zA-Z0-9_\-\./:]+)', content, re.MULTILINE)
                    for image in from_matches:
                        image_lower = image.lower()
                        is_ai = False
                        label = ""
                        if "pytorch" in image_lower:
                            is_ai = True
                            label = "PyTorch AI Base Image"
                        elif "tensorflow" in image_lower:
                            is_ai = True
                            label = "TensorFlow AI Base Image"
                        elif "nvidia/cuda" in image_lower:
                            is_ai = True
                            label = "NVIDIA CUDA GPU Base Image"
                        elif "ollama" in image_lower:
                            is_ai = True
                            label = "Ollama LLM Service Image"
                        elif "vllm" in image_lower:
                            is_ai = True
                            label = "vLLM Base Image"
                        elif "miniconda" in image_lower or "anaconda" in image_lower:
                            is_ai = True
                            label = "Conda Base Image"

                        if is_ai:
                            findings.append(Finding(
                                module_name=MODULE_NAME,
                                title=f"AI Docker Image: {image}",
                                description=f"Detected AI base image in Dockerfile: {image} ({label})",
                                source=source_str,
                                category=FindingCategory.LLM_RUNTIME,
                                risk_level=RiskLevel.LOW,
                                confidence=0.95,
                                details={"runtime": "Docker/Container", "image": image, "label": label, "config_file": source_str}
                            ))
                except Exception as e:
                    logger.debug("Error reading %s: %s", full_path, e)

            elif file_lower in ("docker-compose.yml", "docker-compose.yaml"):
                try:
                    content = full_path.read_text(encoding="utf-8", errors="ignore")
                    import re
                    image_matches = re.findall(r'(?i)^\s*image:\s*([a-zA-Z0-9_\-\./:]+)', content, re.MULTILINE)
                    for image in image_matches:
                        image_lower = image.lower()
                        is_ai = False
                        label = ""
                        if "pytorch" in image_lower:
                            is_ai = True
                            label = "PyTorch Container"
                        elif "tensorflow" in image_lower:
                            is_ai = True
                            label = "TensorFlow Container"
                        elif "nvidia/cuda" in image_lower:
                            is_ai = True
                            label = "NVIDIA CUDA GPU Container"
                        elif "ollama" in image_lower:
                            is_ai = True
                            label = "Ollama LLM Service Container"
                        elif "vllm" in image_lower:
                            is_ai = True
                            label = "vLLM Server Container"
                        elif "localai" in image_lower:
                            is_ai = True
                            label = "LocalAI Server Container"

                        if is_ai:
                            findings.append(Finding(
                                module_name=MODULE_NAME,
                                title=f"AI Service Container: {image}",
                                description=f"Detected AI service container in docker-compose: {image} ({label})",
                                source=source_str,
                                category=FindingCategory.LLM_RUNTIME,
                                risk_level=RiskLevel.LOW,
                                confidence=0.95,
                                details={"runtime": "Docker/Compose", "image": image, "label": label, "config_file": source_str}
                            ))
                except Exception as e:
                    logger.debug("Error reading %s: %s", full_path, e)

    return findings


def run(scan_folder: str | None = None) -> tuple[list[Finding], ModuleInfo]:
    """Execute the Runtime Scanner module.

    Performs port scanning on known AI runtime ports and checks for specific
    runtime directories in the user's home directory.

    Returns:
        Tuple of (findings_list, module_info)
    """
    module_info = ModuleInfo(name=MODULE_NAME, module_number=MODULE_NUMBER)
    findings: list[Finding] = []
    start_time = time.monotonic()

    try:
        if scan_folder:
            findings = _scan_repo_runtimes(pathlib.Path(scan_folder))
        else:
            home = pathlib.Path.home()
            open_ports: dict[int, str] = {}
            found_dirs: dict[str, str] = {}

            # ── Step 1: Scan target ports ───────────────────────────────────
            for port, label in PORT_MAP.items():
                if _check_port(port):
                    open_ports[port] = label
                    logger.info("RuntimeScanner: Open port detected: %d (%s)", port, label)

            # ── Step 2: Check target directories ────────────────────────────
            for dir_name, desc in DIR_MAP.items():
                try:
                    dir_path = home / dir_name
                    if dir_path.exists() and dir_path.is_dir():
                        found_dirs[dir_name] = desc
                        logger.info("RuntimeScanner: Directory detected: %s (%s)", dir_name, desc)
                except (PermissionError, FileNotFoundError, OSError):
                    continue

            # Check local AppData on Windows for LM Studio
            if os.name == "nt":
                local_appdata = os.environ.get("LOCALAPPDATA")
                if local_appdata:
                    try:
                        lm_local = pathlib.Path(local_appdata) / "lm-studio"
                        if lm_local.exists() and lm_local.is_dir():
                            found_dirs["lmstudio"] = "LM Studio local files directory"
                            logger.info("RuntimeScanner: Directory detected via AppData: %s (%s)", lm_local, "LM Studio local files directory")
                    except (PermissionError, FileNotFoundError, OSError):
                        pass


            # ── Step 3: Produce Findings with cross-confirmation ──────────
            # Check 3.1: Ollama confirmation
            ollama_active = 11434 in open_ports
            ollama_installed = ".ollama" in found_dirs

            if ollama_active or ollama_installed:
                if ollama_active and ollama_installed:
                    title = "Ollama LLM Runtime (Active & Installed)"
                    description = (
                        "Ollama is actively running (listening on port 11434) and "
                        "its local storage directory (~/.ollama) was detected. "
                        "This confirms a complete, active LLM runtime environment."
                    )
                    risk_level = RiskLevel.MEDIUM
                elif ollama_active:
                    title = "Ollama Service Listening (Active)"
                    description = (
                        "An active service is listening on port 11434 (typically Ollama), "
                        "but the default local directory (~/.ollama) was not found."
                    )
                    risk_level = RiskLevel.MEDIUM
                else:
                    title = "Ollama Local Directory (Installed)"
                    description = (
                        "Ollama local storage directory (~/.ollama) was found, "
                        "but no active process is currently listening on port 11434."
                    )
                    risk_level = RiskLevel.LOW

                details = {
                    "port_11434_open": ollama_active,
                    "dir_ollama_exists": ollama_installed,
                    "runtime": "Ollama",
                }
                if ollama_active:
                    p_info = _find_process_for_port(11434)
                    if p_info:
                        details["process_id"] = p_info["process_id"]
                        details["process_name"] = p_info["process_name"]
                        details["process_cmdline"] = p_info["process_cmdline"]

                findings.append(
                    Finding(
                        module_name=MODULE_NAME,
                        title=title,
                        description=description,
                        source="ollama",
                        category=FindingCategory.LLM_RUNTIME,
                        risk_level=risk_level,
                        confidence=0.95 if (ollama_active and ollama_installed) else 0.85,
                        details=details,
                    )
                )

            # Check 3.2: LM Studio confirmation
            lmstudio_installed = "lmstudio" in found_dirs or ".lmstudio" in found_dirs
            # LM Studio doesn't run on a standard constant service port by default,
            # but commonly runs a local server on port 1234 or 8080/8000 depending on config.
            if lmstudio_installed:
                findings.append(
                    Finding(
                        module_name=MODULE_NAME,
                        title="LM Studio Local Install Detected",
                        description=(
                            "LM Studio application directories were discovered in the home directory. "
                            "LM Studio allows users to run LLMs locally on their GPU/CPU."
                        ),
                        source="lmstudio",
                        category=FindingCategory.LLM_RUNTIME,
                        risk_level=RiskLevel.LOW,
                        confidence=0.90,
                        details={
                            "dir_lmstudio_exists": "lmstudio" in found_dirs,
                            "dir_dot_lmstudio_exists": ".lmstudio" in found_dirs,
                            "runtime": "LM Studio",
                        },
                    )
                )

            # Check 3.3: Remaining general ports
            for port, label in open_ports.items():
                if port == 11434:
                    continue  # Already handled above
                
                p_details = {
                    "port": port,
                    "label": label,
                    "host": "127.0.0.1",
                }
                p_info = _find_process_for_port(port)
                if p_info:
                    p_details["process_id"] = p_info["process_id"]
                    p_details["process_name"] = p_info["process_name"]
                    p_details["process_cmdline"] = p_info["process_cmdline"]

                findings.append(
                    Finding(
                        module_name=MODULE_NAME,
                        title=f"Active LLM Service Port: {port}",
                        description=(
                            f"An active service was detected listening on port {port} ({label}). "
                            "This port is commonly used by local LLM APIs, services, or model servers."
                        ),
                        source=f"127.0.0.1:{port}",
                        category=FindingCategory.LLM_RUNTIME,
                        risk_level=RiskLevel.MEDIUM,
                        confidence=0.80,
                        details=p_details,
                    )
                )

        module_info.status = "success"

    except Exception as exc:
        logger.error("RuntimeScanner: Unexpected error: %s", exc, exc_info=True)
        module_info.status = "error"
        module_info.error_message = str(exc)

    finally:
        module_info.duration_sec = time.monotonic() - start_time
        module_info.findings_count = len(findings)

    return findings, module_info


class RuntimeScanner:
    """Wrapper class for Module 06 RuntimeScanner to conform to the Discovery Engine interface."""

    MODULE_NAME = MODULE_NAME
    MODULE_NUMBER = MODULE_NUMBER

    def __init__(self, scan_folder: str | None = None):
        self._scan_folder = scan_folder

    def scan(self) -> list[Finding]:
        findings, _ = run(scan_folder=self._scan_folder)
        return findings


if __name__ == "__main__":
    import json

    print("Running MODULE 06 — RuntimeScanner standalone test...\n")
    findings, info = run()

    print(f"Module Status : {info.status}")
    print(f"Duration      : {info.duration_sec:.3f}s")
    print(f"Findings count: {info.findings_count}\n")

    for f in findings:
        print(f"[{f.finding_id}] {f.title}")
        print(f"  Risk Level : {f.risk_level}")
        print(f"  Source     : {f.source}")
        print(f"  Details    : {json.dumps(f.details, indent=2)}")
        print()
