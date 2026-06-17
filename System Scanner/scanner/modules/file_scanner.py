"""
MODULE 02 — File Scanner
========================
Scans the filesystem to discover AI model files (e.g., GGUF, Safetensors,
PyTorch, ONNX, and Keras models).

Author: Person B
Day: 2
"""

from __future__ import annotations

import logging
import os
import pathlib
import time
from datetime import datetime
from typing import Generator

from scanner.models import Finding, FindingCategory, ModuleInfo, RiskLevel

logger = logging.getLogger(__name__)

MODULE_NAME = "FileScanner"
MODULE_NUMBER = 2

# Core extensions to scan for
MODEL_EXTENSIONS = {
    ".gguf",
    ".safetensors",
    ".pt",
    ".pth",
    ".onnx",
    ".ckpt",
    ".h5",
}

# Directories to exclude from general traversal to prevent performance bottlenecks
EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    "AppData",
    "Application Data",
    "Local Settings",
    "Library",
    "Cookies",
    "SendTo",
    "NetHood",
    "PrintHood",
    "Templates",
    "Recent",
    "My Documents",
    "System Volume Information",
    "$RECYCLE.BIN",
    "site-packages",
    "dist-packages",
    ".cache",
    ".pytest_cache",
    "target",
    "out",
    "bin",
    "obj",
}


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable units."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def _depth_limited_walk(
    root_path: pathlib.Path, max_depth: int = 4
) -> Generator[tuple[pathlib.Path, list[str]], None, None]:
    """Traverse a directory structure up to a maximum depth.

    Prunes excluded directories in-place.
    """
    if not root_path.exists() or not root_path.is_dir():
        return

    root_depth = len(root_path.parts)
    for root, dirs, files in os.walk(root_path, topdown=True):
        # Prune excluded directories and hidden directories
        dirs[:] = [
            d
            for d in dirs
            if d not in EXCLUDED_DIRS and not d.startswith(".")
        ]

        current_path = pathlib.Path(root)
        current_depth = len(current_path.parts) - root_depth

        yield current_path, files

        # Stop descending if we reached the depth limit
        if current_depth >= max_depth:
            dirs.clear()


def scan_directory(
    dir_path: pathlib.Path, max_depth: int, scanned_files: set[str]
) -> list[Finding]:
    """Scan a specific directory for model files up to a given depth.

    Handles all file access errors gracefully.
    """
    findings: list[Finding] = []
    if not dir_path.exists() or not dir_path.is_dir():
        return findings

    logger.debug("Scanning directory: %s (depth limit: %d)", dir_path, max_depth)
    
    try:
        for folder, files in _depth_limited_walk(dir_path, max_depth):
            for file_name in files:
                suffix = pathlib.Path(file_name).suffix.lower()
                if suffix in MODEL_EXTENSIONS:
                    file_path = folder / file_name
                    file_path_str = str(file_path.resolve()).replace("\\", "/")

                    if file_path_str in scanned_files:
                        continue

                    scanned_files.add(file_path_str)

                    try:
                        file_size = file_path.stat().st_size
                        mtime = file_path.stat().st_mtime
                        last_mod = datetime.fromtimestamp(mtime).isoformat()
                    except (PermissionError, FileNotFoundError, OSError):
                        file_size = 0
                        last_mod = "Unknown"

                    formatted_size = _format_size(file_size)
                    
                    finding = Finding(
                        module_name=MODULE_NAME,
                        title=file_name,
                        description=f"Discovered AI model file: {file_name} ({formatted_size})",
                        source=file_path_str,
                        category=FindingCategory.AI_MODEL,
                        risk_level=RiskLevel.INFO,  # Will be classified further by classifier
                        details={
                            "file_path": file_path_str,
                            "file_size_bytes": file_size,
                            "file_size_formatted": formatted_size,
                            "extension": suffix,
                            "last_modified": last_mod,
                        },
                    )
                    findings.append(finding)
    except Exception as e:
        logger.error("Error during scan of %s: %s", dir_path, e)

    return findings


def get_drive_targets() -> list[pathlib.Path]:
    """Discover user/developer directories across all logical drives to ensure accurate discovery."""
    import sys
    # Skip checking real logical drives during unit testing to prevent escaping mock filesystems.
    if "unittest" in sys.modules or "pytest" in sys.modules:
        return []

    targets: list[pathlib.Path] = []
    system_dirs = {
        "windows", "program files", "program files (x86)", "programdata",
        "$recycle.bin", "system volume information", "recovery", "config.msi",
        "documents and settings", "intel", "msocache", "perflogs", "boot",
        "sys", "proc", "dev", "lib", "lib64", "bin", "sbin", "usr", "var",
        "etc", "tmp", "run", "boot", "mnt", "media", "srv", "opt", "lost+found"
    }

    # 1. Gather all drives/mountpoints
    drives: list[str] = []
    try:
        import psutil
        for part in psutil.disk_partitions(all=False):
            if part.mountpoint:
                drives.append(part.mountpoint)
    except Exception:
        pass

    if not drives:
        if os.name == "nt":
            for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path):
                    drives.append(drive_path)
        else:
            drives.append("/")

    # 2. List immediate subdirectories on each drive
    for drive in drives:
        try:
            drive_path = pathlib.Path(drive)
            if not drive_path.exists():
                continue
            for child in drive_path.iterdir():
                try:
                    if child.is_dir():
                        name_lower = child.name.lower()
                        if name_lower not in system_dirs and not child.name.startswith("."):
                            targets.append(child)
                except Exception:
                    continue
        except Exception:
            # Fallback to drive root if not C:\
            d_path = pathlib.Path(drive)
            if d_path.anchor.lower() != "c:\\":
                targets.append(d_path)

    return list(set(targets))


def run() -> tuple[list[Finding], ModuleInfo]:
    """Execute the File Scanner module.

    Walks specific high-probability AI cache folders (HuggingFace, Ollama, Downloads)
    with a deep limit, and the user's home directory with a shallow limit.

    Returns:
        Tuple of (findings_list, module_info)
    """
    module_info = ModuleInfo(name=MODULE_NAME, module_number=MODULE_NUMBER)
    findings: list[Finding] = []
    start_time = time.monotonic()

    try:
        home = pathlib.Path.home()
        scanned_files: set[str] = set()

        # Find repo root
        repo_root = pathlib.Path.cwd()
        path = repo_root.resolve()
        for parent in [path] + list(path.parents):
            if (parent / ".git").exists():
                repo_root = parent
                break

        # Define targets with search depth
        # For Hugging Face and Ollama we scan deeply since they are standard stores
        targets = [
            (home / ".cache" / "huggingface", 10),
            (home / ".cache" / "lm-studio", 10),
            (home / ".ollama", 10),
            (home / "Downloads", 10),
            (repo_root, 10),
            # General home directory scan with a depth limit of 10
            (home, 10),
        ]

        # Add Local AppData on Windows for local software cache (like lm-studio)
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            targets.append((pathlib.Path(local_appdata) / "lm-studio", 10))


        # Dynamically discover other drive directories
        for drive_target in get_drive_targets():
            try:
                # Avoid duplicating home or repo_root
                drive_target_res = drive_target.resolve()
                home_res = home.resolve()
                repo_res = repo_root.resolve()
                if drive_target_res == home_res or drive_target_res == repo_res:
                    continue
                if drive_target_res == home_res.parent:
                    continue
                targets.append((drive_target, 10))
            except Exception:
                targets.append((drive_target, 10))

        for target_dir, max_depth in targets:
            if target_dir.exists() and target_dir.is_dir():
                findings.extend(scan_directory(target_dir, max_depth, scanned_files))

        module_info.status = "success"

    except Exception as exc:
        module_info.status = "error"
        module_info.error_message = str(exc)

    finally:
        module_info.duration_sec = time.monotonic() - start_time
        module_info.findings_count = len(findings)

    return findings, module_info


class FileScanner:
    """Wrapper class for Module 02 FileScanner to conform to the Discovery Engine interface."""

    MODULE_NAME = MODULE_NAME
    MODULE_NUMBER = MODULE_NUMBER

    def scan(self) -> list[Finding]:
        findings, _ = run()
        return findings


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO)
    print("Running MODULE 02 - FileScanner standalone test...\n")
    findings, info = run()

    print(f"Module Status : {info.status}")
    print(f"Duration      : {info.duration_sec:.3f}s")
    print(f"Findings count: {info.findings_count}\n")

    for f in findings[:10]:  # Limit output
        print(f"[{f.finding_id}] {f.title}")
        print(f"  Source   : {f.source}")
        print(f"  Details  : {json.dumps(f.details, indent=2)}")
        print()
    if len(findings) > 10:
        print(f"... and {len(findings) - 10} more findings.")
