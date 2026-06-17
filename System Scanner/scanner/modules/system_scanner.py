"""
MODULE 01 — System Scanner
==========================
Collects host machine metadata: hostname, OS, CPU, RAM, IP address,
disk info, and Python runtime details.

This is the simplest module and serves as the reference implementation
for the Finding interface that all other modules must follow.

Author: Person B
Day: 1
"""

import logging
import platform
import socket
import time
from typing import Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

from scanner.models import Finding, FindingCategory, ModuleInfo, RiskLevel


MODULE_NAME = "SystemScanner"
MODULE_NUMBER = 1


def _get_ip_address() -> str:
    """Attempt to get the machine's primary outbound IP address.

    Uses a UDP connect trick (no data is sent) to determine which
    network interface would be used for external connections.

    Returns:
        IP address string, or 'N/A' if detection fails.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(1)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "N/A"


def _get_cpu_info() -> dict[str, Any]:
    """Collect CPU information using psutil if available.

    Returns:
        Dictionary with cpu_physical_cores, cpu_logical_cores,
        cpu_freq_mhz, and cpu_percent_usage.
    """
    if not PSUTIL_AVAILABLE:
        return {"cpu_info": "psutil not available"}

    freq = psutil.cpu_freq()
    return {
        "cpu_physical_cores": psutil.cpu_count(logical=False),
        "cpu_logical_cores": psutil.cpu_count(logical=True),
        "cpu_freq_mhz": round(freq.current, 1) if freq else "N/A",
        "cpu_percent_usage": psutil.cpu_percent(interval=0.5),
    }


def _get_ram_info() -> dict[str, Any]:
    """Collect RAM (virtual memory) information using psutil.

    Returns:
        Dictionary with total_gb, available_gb, used_percent.
    """
    if not PSUTIL_AVAILABLE:
        return {"ram_info": "psutil not available"}

    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2),
        "used_percent": mem.percent,
    }


def _get_disk_info() -> list[dict[str, Any]]:
    """Collect disk partition usage information using psutil.

    Skips partitions that raise PermissionError or are not ready
    (common on Windows with removable drives / optical drives).

    Returns:
        List of dicts, one per readable partition, with device,
        mountpoint, filesystem, total_gb, free_gb, used_percent.
    """
    if not PSUTIL_AVAILABLE:
        return []

    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "filesystem": part.fstype,
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "free_gb": round(usage.free / (1024 ** 3), 2),
                "used_percent": usage.percent,
            })
        except (PermissionError, OSError):
            # Drive not ready or access denied — skip silently
            continue
    return disks


def run() -> tuple[list[Finding], ModuleInfo]:
    """Execute the System Scanner module.

    Collects host machine metadata and returns it as a list of
    Finding objects conforming to the shared data contract.

    Returns:
        Tuple of:
          - List[Finding]: findings produced (system info findings)
          - ModuleInfo:    execution metadata for this module run
    """
    logger.info("SystemScanner: Starting host metadata collection...")
    module_info = ModuleInfo(name=MODULE_NAME, module_number=MODULE_NUMBER)
    findings: list[Finding] = []
    start_time = time.monotonic()

    try:
        # ── Gather all platform data ────────────────────────────────────
        hostname = socket.gethostname()
        os_name = platform.system()
        os_version = platform.version()
        os_release = platform.release()
        architecture = platform.machine()
        processor = platform.processor() or "N/A"
        python_version = platform.python_version()
        logger.debug("Querying IP address, CPU info, RAM info, and disk partitions...")
        ip_address = _get_ip_address()
        cpu_info = _get_cpu_info()
        ram_info = _get_ram_info()
        disk_info = _get_disk_info()

        logger.info("SystemScanner: Target identified as hostname=%s, OS=%s", hostname, os_name)

        # ── Build the primary System Info finding ───────────────────────
        system_finding = Finding(
            module_name=MODULE_NAME,
            title=f"Host Machine: {hostname}",
            description=(
                f"System scan target identified: {hostname} running "
                f"{os_name} {os_release} ({architecture})"
            ),
            source=f"hostname={hostname}",
            category=FindingCategory.SYSTEM_INFO,
            risk_level=RiskLevel.INFO,
            confidence=1.0,
            details={
                "hostname": hostname,
                "ip_address": ip_address,
                "os": {
                    "name": os_name,
                    "release": os_release,
                    "version": os_version,
                    "architecture": architecture,
                    "processor": processor,
                },
                "python_version": python_version,
                "cpu": cpu_info,
                "ram": ram_info,
                "disks": disk_info,
            },
        )
        findings.append(system_finding)
        logger.debug("SystemScanner: Main system details recorded.")

        # ── GPU detection (best-effort, non-blocking) ───────────────────
        gpu_info = _detect_gpu()
        if gpu_info:
            gpu_finding = Finding(
                module_name=MODULE_NAME,
                title=f"GPU Detected: {gpu_info.get('name', 'Unknown GPU')}",
                description=(
                    "A GPU was detected on this machine. GPUs are commonly "
                    "used to accelerate AI/ML model inference and training."
                ),
                source="system_gpu_detection",
                category=FindingCategory.SYSTEM_INFO,
                risk_level=RiskLevel.INFO,
                confidence=0.9,
                details=gpu_info,
            )
            findings.append(gpu_finding)

        module_info.status = "success"

    except Exception as exc:  # pragma: no cover — catch-all for unexpected errors
        logger.error("SystemScanner: Unexpected error encountered: %s", exc, exc_info=True)
        module_info.status = "error"
        module_info.error_message = str(exc)

    finally:
        duration = time.monotonic() - start_time
        module_info.duration_sec = duration
        module_info.findings_count = len(findings)
        logger.info("SystemScanner: Completed in %.3fs with %d findings", duration, len(findings))

    return findings, module_info


def _detect_gpu() -> dict[str, Any] | None:
    """Best-effort GPU detection without requiring heavy dependencies.

    Tries common cross-platform approaches in order:
      1. nvidia-smi via subprocess (NVIDIA GPUs)
      2. wmic path win32_VideoController (Windows, any GPU)

    Returns:
        Dictionary with GPU info if detected, else None.
    """
    import subprocess
    logger.debug("SystemScanner: Performing best-effort GPU detection...")

    # ── Attempt 1: nvidia-smi (works on any OS with NVIDIA drivers) ──
    try:
        logger.debug("SystemScanner: Trying nvidia-smi query...")
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = [p.strip() for p in result.stdout.strip().split(",")]
            gpu_data = {
                "name": parts[0] if len(parts) > 0 else "NVIDIA GPU",
                "vram_mb": parts[1] if len(parts) > 1 else "N/A",
                "driver_version": parts[2] if len(parts) > 2 else "N/A",
                "vendor": "NVIDIA",
                "detection_method": "nvidia-smi",
            }
            logger.info("SystemScanner: NVIDIA GPU detected: %s", gpu_data["name"])
            return gpu_data
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
        logger.debug("SystemScanner: nvidia-smi check skipped/failed: %s", e)

    # ── Attempt 2: wmic (Windows only) ───────────────────────────────
    if platform.system() == "Windows":
        try:
            logger.debug("SystemScanner: Trying WMIC video controller query...")
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "Name,AdapterRAM"],
                capture_output=True,
                text=True,
                timeout=8,
            )
            if result.returncode == 0:
                lines = [
                    line.strip()
                    for line in result.stdout.strip().splitlines()
                    if line.strip() and "Name" not in line
                ]
                if lines:
                    # Parse the first GPU entry
                    parts = lines[0].rsplit(None, 1)
                    gpu_name = parts[0].strip() if len(parts) > 1 else lines[0]
                    vram_bytes = parts[1].strip() if len(parts) > 1 else "N/A"
                    try:
                        vram_mb = round(int(vram_bytes) / (1024 ** 2), 0)
                    except (ValueError, TypeError):
                        vram_mb = "N/A"
                    gpu_data = {
                        "name": gpu_name,
                        "vram_mb": vram_mb,
                        "vendor": "Unknown",
                        "detection_method": "wmic",
                    }
                    logger.info("SystemScanner: GPU detected via WMIC: %s", gpu_data["name"])
                    return gpu_data
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
            logger.debug("SystemScanner: WMIC check failed: %s", e)

    logger.debug("SystemScanner: No GPU detected.")
    return None



# ── Standalone test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    print("Running MODULE 01 - SystemScanner standalone test...\n")
    findings, info = run()

    print(f"Module Status : {info.status}")
    print(f"Duration      : {info.duration_sec:.3f}s")
    print(f"Findings count: {info.findings_count}\n")

    for f in findings:
        print(f"[{f.finding_id}] {f.title}")
        print(f"  Category : {f.category}")
        print(f"  Risk     : {f.risk_level}")
        print(f"  Details  :")
        print(json.dumps(f.details, indent=4))
        print()
