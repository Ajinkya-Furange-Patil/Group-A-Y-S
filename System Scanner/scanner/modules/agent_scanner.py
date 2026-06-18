"""
MODULE 05 — Agent Scanner
=========================
Walks Python project files (.py) in the current working directory (CWD) and the
user's home directory to inspect the source code for AI Agent architectures
and frameworks (LangChain, CrewAI, AutoGen) using regular expressions.

Author: Person B
Day: 3
"""

from __future__ import annotations

import logging
import os
import pathlib
import re
import time
from typing import Generator

from scanner.models import Finding, FindingCategory, ModuleInfo, RiskLevel

logger = logging.getLogger(__name__)

MODULE_NAME = "AgentScanner"
MODULE_NUMBER = 5

# Exclude list to avoid walking inside dependency folders or library code
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
    "dist",
    "build",
}

# Key regex patterns to identify Agentic framework imports & instantiations
PATTERNS = {
    "LangChain Import": re.compile(r"\bfrom\s+langchain\b|\bimport\s+langchain\b"),
    "CrewAI Import": re.compile(r"\bfrom\s+crewai\b|\bimport\s+crewai\b"),
    "AutoGen Import": re.compile(r"\bfrom\s+autogen\b|\bimport\s+autogen\b"),
    "Agent Instantiation": re.compile(r"\bAgent\s*\("),
    "Crew Instantiation": re.compile(r"\bCrew\s*\("),
    "AssistantAgent Instantiation": re.compile(r"\bAssistantAgent\s*\("),
}


def _depth_limited_walk(
    root_path: pathlib.Path, max_depth: int
) -> Generator[tuple[pathlib.Path, list[str]], None, None]:
    """Traverse a directory structure up to a maximum depth.

    Prunes excluded directories in-place.
    """
    try:
        if not root_path.exists() or not root_path.is_dir():
            return
    except (PermissionError, FileNotFoundError, OSError):
        return

    try:
        root_depth = len(root_path.parts)
        for root, dirs, files in os.walk(root_path, topdown=True, onerror=lambda e: None):
            try:
                # Prune directories in place to avoid walking into them
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
            except (PermissionError, FileNotFoundError, OSError):
                dirs.clear()
                continue
    except Exception as e:
        logger.warning("Error traversing directory %s: %s", root_path, e)


def scan_file(file_path: pathlib.Path) -> list[Finding]:
    """Inspect a single python file line by line for Agent framework usage.

    Args:
        file_path: Path to the .py file to scan.

    Returns:
        List of Finding objects discovered.
    """
    findings: list[Finding] = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                clean_line = line.strip()
                if not clean_line or clean_line.startswith("#"):
                    continue

                for pattern_name, regex in PATTERNS.items():
                    if regex.search(clean_line):
                        snippet = (
                            clean_line[:100] + "..."
                            if len(clean_line) > 100
                            else clean_line
                        )
                        finding = Finding(
                            module_name=MODULE_NAME,
                            title=f"Agent Usage: {pattern_name}",
                            description=(
                                f"Potential AI Agent signature detected in script '{file_path.name}' "
                                f"at line {line_no} ({pattern_name})."
                            ),
                            source=f"{str(file_path.resolve()).replace('\\', '/')}:{line_no}",
                            category=FindingCategory.AI_AGENT,
                            risk_level=RiskLevel.MEDIUM,
                            confidence=0.85,
                            details={
                                "file_path": str(file_path.resolve()).replace("\\", "/"),
                                "line_number": line_no,
                                "matched_pattern": pattern_name,
                                "snippet": snippet,
                            },
                        )
                        findings.append(finding)
    except Exception as e:
        logger.debug("AgentScanner: Error reading %s: %s", file_path, e)

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
    """Execute the Agent Scanner module.

    Searches CWD and home directory up to specified depths for Python files
    containing references to LangChain, CrewAI, or AutoGen.

    Returns:
        Tuple of (findings_list, module_info)
    """
    module_info = ModuleInfo(name=MODULE_NAME, module_number=MODULE_NUMBER)
    findings: list[Finding] = []
    start_time = time.monotonic()

    try:
        home = pathlib.Path.home()
        cwd = pathlib.Path.cwd()
        scanned_files: set[str] = set()

        # Resolve repository root dynamically if we are inside a git repository
        repo_root = cwd
        path = cwd.resolve()
        for i, parent in enumerate([path] + list(path.parents)):
            if i > 3:
                break
            if (parent / ".git").exists():
                repo_root = parent
                break

        # Targets with their search depth
        # Scan local workspace (repo root) up to depth 6
        # Scan user home directory up to depth 3
        targets = [
            (repo_root, 6),
            (home, 3),
        ]

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
                targets.append((drive_target, 6))
            except Exception:
                targets.append((drive_target, 6))

        for target_dir, max_depth in targets:
            if not target_dir.exists() or not target_dir.is_dir():
                continue

            logger.debug(
                "AgentScanner: Scanning directory %s (depth limit: %d)",
                target_dir,
                max_depth,
            )

            try:
                for folder, files in _depth_limited_walk(target_dir, max_depth):
                    for file in files:
                        if file.endswith(".py"):
                            file_path = folder / file
                            abs_path_str = str(file_path.resolve()).replace("\\", "/")

                            if abs_path_str in scanned_files:
                                continue

                            scanned_files.add(abs_path_str)
                            file_findings = scan_file(file_path)
                            findings.extend(file_findings)
            except Exception as e:
                logger.error("AgentScanner: Error walking %s: %s", target_dir, e)

        module_info.status = "success"

    except Exception as exc:
        logger.error("AgentScanner: Unexpected error: %s", exc, exc_info=True)
        module_info.status = "error"
        module_info.error_message = str(exc)

    finally:
        module_info.duration_sec = time.monotonic() - start_time
        module_info.findings_count = len(findings)

    return findings, module_info


class AgentScanner:
    """Wrapper class for Module 05 AgentScanner to conform to the Discovery Engine interface."""

    MODULE_NAME = MODULE_NAME
    MODULE_NUMBER = MODULE_NUMBER

    def scan(self) -> list[Finding]:
        findings, _ = run()
        return findings


if __name__ == "__main__":
    print("Running MODULE 05 — AgentScanner standalone test...\n")
    findings, info = run()

    print(f"Module Status : {info.status}")
    print(f"Duration      : {info.duration_sec:.3f}s")
    print(f"Findings count: {info.findings_count}\n")

    for f in findings[:10]:
        print(f"[{f.finding_id}] {f.title}")
        print(f"  Source   : {f.source}")
        print(f"  Details  : {f.details}")
        print()
    if len(findings) > 10:
        print(f"... and {len(findings) - 10} more findings.")
