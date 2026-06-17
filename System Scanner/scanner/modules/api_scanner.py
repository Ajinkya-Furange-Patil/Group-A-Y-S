"""
MODULE 07 — API Scanner
======================
Scans project files (.env, .yaml, .yml, .json, .py, .js, .ts, etc.) for exposed AI API keys
(OpenAI, Anthropic, Google Gemini, Cohere, etc.) and active system environment variables,
masks them for security, and reports them as configuration findings.

Author: Person C
Day: 3
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
import re
from typing import Any
from scanner.models import Finding, FindingCategory, RiskLevel

logger = logging.getLogger(__name__)


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


class APIScanner:
    """Scans local directories and active environments for credentials and API keys."""

    MODULE_NAME = "APIScanner"
    MODULE_NUMBER = 7

    def __init__(self, target_dir: str = ".") -> None:
        """Initialize the API Scanner and setup directories, exclusions, and regex patterns."""
        self.target_dir = os.path.abspath(target_dir)

        # Resolve repository root dynamically if we are inside a git repository
        repo_root = self.target_dir
        path = pathlib.Path(self.target_dir).resolve()
        for i, parent in enumerate([path] + list(path.parents)):
            if i > 3:
                break
            if (parent / ".git").exists():
                repo_root = str(parent)
                break

        # Define targets to scan along with maximum depths
        home = pathlib.Path.home()
        self.targets = [
            (home / "Downloads", 10),
            (pathlib.Path(repo_root), 10),
            (home, 10),  # general home scan last
        ]

        # Dynamically discover other drive directories
        for drive_target in get_drive_targets():
            try:
                # Avoid duplicating home or repo_root
                drive_target_res = drive_target.resolve()
                home_res = home.resolve()
                repo_res = pathlib.Path(repo_root).resolve()
                if drive_target_res == home_res or drive_target_res == repo_res:
                    continue
                if drive_target_res == home_res.parent:
                    continue
                self.targets.append((drive_target, 10))
            except Exception:
                self.targets.append((drive_target, 10))
        
        # Regex patterns for matching API keys and credentials
        self.patterns = {
            "OpenAI API Key": {
                "regex": re.compile(
                    r"\b((?:sk-[a-zA-Z0-9-]{32,})|(?:sk-proj-[a-zA-Z0-9-]{40,}))\b",
                    re.IGNORECASE
                ),
                "risk": RiskLevel.CRITICAL,
                "mask_prefix": "sk-...",
            },
            "Anthropic API Key": {
                "regex": re.compile(
                    r"\b(sk-ant-sid[0-9a-zA-Z_-]{24,}|sk-ant-api[0-9a-zA-Z_-]{24,})\b",
                    re.IGNORECASE
                ),
                "risk": RiskLevel.CRITICAL,
                "mask_prefix": "sk-ant-...",
            },
            "Google AI/Gemini API Key": {
                "regex": re.compile(
                    r"\b(AIzaSy[a-zA-Z0-9_-]{33})\b"
                ),
                "risk": RiskLevel.CRITICAL,
                "mask_prefix": "AIzaSy...",
            },
            "Cohere API Key": {
                "regex": re.compile(
                    r"(?:COHERE_API_KEY|cohere_key|api_key|apikey)[\s:=]+['\"]?([a-zA-Z0-9]{32,})['\"]?",
                    re.IGNORECASE
                ),
                "risk": RiskLevel.HIGH,
                "mask_prefix": "co-...",
            },
            "NVIDIA API Key": {
                "regex": re.compile(
                    r"\b(nvapi-[a-zA-Z0-9_-]{50,})\b",
                    re.IGNORECASE
                ),
                "risk": RiskLevel.CRITICAL,
                "mask_prefix": "nvapi-...",
            },
            "Cloudflare User Token": {
                "regex": re.compile(
                    r"\b(cfut_[a-zA-Z0-9_-]{30,})\b",
                    re.IGNORECASE
                ),
                "risk": RiskLevel.HIGH,
                "mask_prefix": "cfut_...",
            },
            "Hugging Face Hub Token": {
                "regex": re.compile(
                    r"\b(hf_[a-zA-Z0-9]{34,})\b",
                    re.IGNORECASE
                ),
                "risk": RiskLevel.HIGH,
                "mask_prefix": "hf_...",
            },
            "AWS Access Key ID": {
                "regex": re.compile(
                    r"\b((?:AKIA|ASIA)[0-9A-Z]{16})\b"
                ),
                "risk": RiskLevel.CRITICAL,
                "mask_prefix": "AKIA...",
            },
            "AWS Secret Access Key": {
                "regex": re.compile(
                    r"(?:AWS_SECRET_ACCESS_KEY|aws_secret|secret_key)[\s:=]+['\"]?([a-zA-Z0-9+/]{40})['\"]?",
                    re.IGNORECASE
                ),
                "risk": RiskLevel.CRITICAL,
                "mask_prefix": "aws-secret...",
            },
            "GitHub Personal Access Token": {
                "regex": re.compile(
                    r"\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})\b"
                ),
                "risk": RiskLevel.HIGH,
                "mask_prefix": "ghp_...",
            },
            "Generic API Key/Token": {
                "regex": re.compile(
                    r"(?:api_key|apikey|api_token|apitoken|secret_key|secretkey|access_token|accesstoken|auth_token|bearer_token)[\s:=]+['\"]?([a-zA-Z0-9_\-]{20,})['\"]?",
                    re.IGNORECASE
                ),
                "risk": RiskLevel.HIGH,
                "mask_prefix": "key...",
            }
        }
        
        # Folders to completely ignore during scan to avoid performance lags
        self.exclude_dirs = {
            "node_modules", ".git", ".github", "venv", ".venv", "env",
            "__pycache__", "build", "dist", ".idea", ".vscode", "AppData",
            "Application Data", "Local Settings", "Library", "Cookies",
            "SendTo", "NetHood", "PrintHood", "Templates", "Recent", "My Documents",
            "System Volume Information", "$RECYCLE.BIN", "site-packages",
            "dist-packages", ".cache", ".pytest_cache", "target", "out", "bin", "obj"
        }
        # Extensions of interest
        self.include_extensions = {
            ".env", ".yaml", ".yml", ".json", ".py", ".js", ".ts",
            ".toml", ".ini", ".conf", ".txt"
        }

    def _mask_key(self, key: str, prefix: str) -> str:
        """Mask an API key so it is secure to show in a report.

        Args:
            key: The raw API key string.
            prefix: Default masking prefix.

        Returns:
            Masked API key.
        """
        if len(key) <= 8:
            return "********"
        return f"{prefix}{key[-4:]}"

    def _depth_limited_walk(self, root_path: pathlib.Path, max_depth: int):
        """Traverse a directory structure up to a maximum depth.

        Prunes excluded directories in-place.
        """
        if not root_path.exists() or not root_path.is_dir():
            return

        root_depth = len(root_path.parts)
        for root, dirs, files in os.walk(root_path, topdown=True):
            dirs[:] = [
                d
                for d in dirs
                if d not in self.exclude_dirs and not d.startswith(".")
            ]

            current_path = pathlib.Path(root)
            current_depth = len(current_path.parts) - root_depth

            yield current_path, files

            if current_depth >= max_depth:
                dirs.clear()

    def _scan_file(self, file_path: str) -> list[Finding]:
        """Scan a single file line by line for any matched regex pattern.

        Args:
            file_path: Absolute path to the file to check.

        Returns:
            List of Finding objects discovered.
        """
        file_findings: list[Finding] = []
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_no, line in enumerate(f, 1):
                    # Check each regular expression pattern
                    matched_on_line = set()
                    for key_name, info in self.patterns.items():
                        matches = info["regex"].findall(line)
                        for match in matches:
                            raw_key = match[0] if isinstance(match, tuple) else match
                            raw_key = raw_key.strip()
                            
                            # Validate length
                            if not raw_key or len(raw_key) < 16:
                                continue
                            
                            # Skip if we already matched this exact credential value on the same line
                            if raw_key in matched_on_line:
                                continue
                                
                            # Basic check to avoid normal word false positives on Generic rules
                            if key_name == "Generic API Key/Token":
                                if not (any(c.isdigit() for c in raw_key) and any(c.isalpha() for c in raw_key)):
                                    continue
                            
                            matched_on_line.add(raw_key)
                            masked_key = self._mask_key(raw_key, info["mask_prefix"])
                            
                            finding = Finding(
                                module_name=self.MODULE_NAME,
                                title=f"Exposed {key_name}",
                                description=(
                                    f"A matching pattern for a {key_name} was discovered "
                                    f"in config file '{file_path}' at line {line_no}."
                                ),
                                source=f"{file_path}:{line_no}",
                                category=FindingCategory.CONFIGURATION,
                                risk_level=info["risk"],
                                confidence=0.9,
                                details={
                                    "file_path": file_path,
                                    "line_number": line_no,
                                    "credential_type": key_name,
                                    "masked_key": masked_key,
                                }
                            )
                            file_findings.append(finding)
        except Exception:
            pass

        return file_findings

    def _scan_environment(self) -> list[Finding]:
        """Iterate through active process environment variables for keys.

        Returns:
            List of environment credentials findings.
        """
        env_findings: list[Finding] = []
        env_keywords = {"KEY", "TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL"}
        
        for key, value in os.environ.items():
            key_upper = key.upper()
            if any(kw in key_upper for kw in env_keywords):
                if value and len(value) >= 12:
                    provider = "Unknown"
                    risk = RiskLevel.HIGH
                    mask_prefix = "env_key..."
                    
                    if "OPENAI" in key_upper:
                        provider = "OpenAI"
                        risk = RiskLevel.CRITICAL
                        mask_prefix = "sk-..."
                    elif "ANTHROPIC" in key_upper:
                        provider = "Anthropic"
                        risk = RiskLevel.CRITICAL
                        mask_prefix = "sk-ant-..."
                    elif "GOOGLE" in key_upper or "GEMINI" in key_upper:
                        provider = "Google/Gemini"
                        risk = RiskLevel.CRITICAL
                        mask_prefix = "AIzaSy..."
                    elif "HF_" in key_upper or "HUGGINGFACE" in key_upper:
                        provider = "Hugging Face"
                        risk = RiskLevel.HIGH
                        mask_prefix = "hf_..."
                    elif "AWS" in key_upper:
                        provider = "AWS"
                        risk = RiskLevel.CRITICAL
                        mask_prefix = "aws..."
                        
                    masked = self._mask_key(value, mask_prefix)
                    
                    finding = Finding(
                        module_name=self.MODULE_NAME,
                        title=f"Environment Variable: {key}",
                        description=f"Active environment variable '{key}' contains a potential {provider} credential.",
                        source=f"env://{key}",
                        category=FindingCategory.CONFIGURATION,
                        risk_level=risk,
                        confidence=0.95,
                        details={
                            "env_var_name": key,
                            "credential_type": f"{provider} Environment Credential",
                            "masked_key": masked,
                        }
                    )
                    env_findings.append(finding)
                    
        return env_findings

    def scan(self) -> list[Finding]:
        """Perform directory traversal, file extraction, scanning, and active environments checks.

        Returns:
            List of Findings representing discovered API keys.
        """
        findings: list[Finding] = []

        # ── Step 1: File Gathering ──────────────────────────────────────
        candidate_files: list[pathlib.Path] = []
        for target_path, max_depth in self.targets:
            try:
                if not target_path.exists():
                    continue

                if target_path.is_file():
                    candidate_files.append(target_path)
                    continue

                for folder, files in self._depth_limited_walk(target_path, max_depth):
                    for file in files:
                        name_lower = file.lower()
                        has_valid_ext = any(file.endswith(ext) for ext in self.include_extensions)
                        is_env_file = name_lower.startswith(".env")
                        
                        if has_valid_ext or is_env_file:
                            candidate_files.append(folder / file)
            except Exception as e:
                logger.error("Error gathering files under %s: %s", target_path, e)

        # ── Step 2: Deduplication ───────────────────────────────────────
        unique_files: list[tuple[str, pathlib.Path]] = []
        seen: set[str] = set()
        for path in candidate_files:
            try:
                abs_path_str = str(path.resolve()).replace("\\", "/")
                if abs_path_str not in seen:
                    seen.add(abs_path_str)
                    unique_files.append((abs_path_str, path))
            except Exception:
                continue

        # ── Step 3: Sequential Scanning ─────────────────────────────────
        for abs_path_str, path in unique_files:
            try:
                file_findings = self._scan_file(abs_path_str)
                # ── Step 4: Regex Matching & Counting ─────────────────────
                findings.extend(file_findings)
            except Exception as e:
                logger.error("Error scanning file %s: %s", abs_path_str, e)

        # ── Active Environment Variables ────────────────────────────────
        try:
            env_findings = self._scan_environment()
            findings.extend(env_findings)
        except Exception as e:
            logger.error("Error scanning environment variables: %s", e)

        return findings


# Standalone test runner
if __name__ == "__main__":
    print("Running MODULE 07 — APIScanner standalone test...\n")
    scanner = APIScanner()
    findings = scanner.scan()
    print(f"Total API key findings: {len(findings)}")
    for f in findings:
        print(f"[{f.risk_level.value.upper()}] {f.title} in {f.source}")
        print(f"  Details: {f.details}")
        print()
