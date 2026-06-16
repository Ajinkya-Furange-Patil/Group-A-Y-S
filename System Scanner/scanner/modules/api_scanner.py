"""
MODULE 07 — API Scanner
======================
Scans project files (.env, .yaml, .yml, .json) for exposed AI API keys
(OpenAI, Anthropic, Google Gemini, Cohere, etc.), masks them for security,
and reports them as high-risk configuration findings.

Author: Person C
Day: 3
"""

import json
import os
import re
from typing import Any
from scanner.models import Finding, FindingCategory, RiskLevel


class APIScanner:
    """Scans local directories for exposed AI service credentials and API keys."""

    MODULE_NAME = "APIScanner"
    MODULE_NUMBER = 7

    def __init__(self, target_dir: str = ".") -> None:
        """Initialize the API Scanner with a target search directory."""
        self.target_dir = os.path.abspath(target_dir)
        
        # Regex patterns for matching API keys and credentials
        self.patterns = {
            "OpenAI API Key": {
                "regex": re.compile(r"(?:OPENAI_API_KEY|openai_key)[\s:=]+['\"]?((?:sk-[a-zA-Z0-9-]{32,})|(?:sk-proj-[a-zA-Z0-9-]{40,}))['\"]?", re.IGNORECASE),
                "risk": RiskLevel.CRITICAL,
                "mask_prefix": "sk-...",
            },
            "Anthropic API Key": {
                "regex": re.compile(r"(?:ANTHROPIC_API_KEY|anthropic_key)[\s:=]+['\"]?(sk-ant-sid[0-9a-zA-Z_-]{24,}|sk-ant-api[0-9a-zA-Z_-]{24,})['\"]?", re.IGNORECASE),
                "risk": RiskLevel.CRITICAL,
                "mask_prefix": "sk-ant-...",
            },
            "Google AI/Gemini API Key": {
                "regex": re.compile(r"(?:GOOGLE_API_KEY|gemini_api_key|gemini_key)[\s:=]+['\"]?(AIzaSy[a-zA-Z0-9_-]{33})['\"]?", re.IGNORECASE),
                "risk": RiskLevel.CRITICAL,
                "mask_prefix": "AIzaSy...",
            },
            "Cohere API Key": {
                "regex": re.compile(r"(?:COHERE_API_KEY|cohere_key)[\s:=]+['\"]?([a-zA-Z0-9]{32,})['\"]?", re.IGNORECASE),
                "risk": RiskLevel.HIGH,
                "mask_prefix": "co-...",
            },
            "Hugging Face Hub Token": {
                "regex": re.compile(r"(?:HF_TOKEN|HUGGINGFACE_API_TOKEN)[\s:=]+['\"]?(hf_[a-zA-Z0-9]{34,})['\"]?", re.IGNORECASE),
                "risk": RiskLevel.HIGH,
                "mask_prefix": "hf_...",
            }
        }
        
        # Folders to completely ignore during scan to avoid performance lags
        self.exclude_dirs = {
            "node_modules", ".git", ".github", "venv", ".venv", "env",
            "__pycache__", "build", "dist", ".idea", ".vscode"
        }
        # Extensions of interest
        self.include_extensions = {".env", ".yaml", ".yml", ".json"}

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

    def scan(self) -> list[Finding]:
        """Perform directory traversal and scan files for exposed credentials.

        Returns:
            List of Findings representing discovered API keys.
        """
        findings: list[Finding] = []

        # Walk targeted directories
        for root, dirs, files in os.walk(self.target_dir):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file in files:
                file_path = os.path.join(root, file)
                
                # Check file extension or name
                name_lower = file.lower()
                has_valid_ext = any(file_path.endswith(ext) for ext in self.include_extensions)
                is_env_file = name_lower.startswith(".env")
                
                if not (has_valid_ext or is_env_file):
                    continue

                try:
                    findings.extend(self._scan_file(file_path))
                except (PermissionError, FileNotFoundError):
                    # Skip files we cannot access
                    continue
                except Exception:
                    # Generic catch-all to prevent scanner crashes
                    continue

        return findings

    def _scan_file(self, file_path: str) -> list[Finding]:
        """Scan a single file line by line for any matched regex pattern.

        Args:
            file_path: Absolute path to the file to check.

        Returns:
            List of Finding objects discovered.
        """
        file_findings: list[Finding] = []
        rel_path = os.path.relpath(file_path, self.target_dir)

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                # Check each regular expression pattern
                for key_name, info in self.patterns.items():
                    matches = info["regex"].findall(line)
                    for match in matches:
                        # Findall might return tuples if group patterns are complex, extract string
                        raw_key = match[0] if isinstance(match, tuple) else match
                        raw_key = raw_key.strip()
                        
                        # Validate length and format briefly
                        if not raw_key:
                            continue
                            
                        masked_key = self._mask_key(raw_key, info["mask_prefix"])
                        
                        finding = Finding(
                            module_name=self.MODULE_NAME,
                            title=f"Exposed {key_name}",
                            description=(
                                f"A matching pattern for a {key_name} was discovered "
                                f"in config file '{rel_path}' at line {line_no}."
                            ),
                            source=f"{rel_path}:{line_no}",
                            category=FindingCategory.CONFIGURATION,
                            risk_level=info["risk"],
                            confidence=0.9,
                            details={
                                "file_path": rel_path,
                                "line_number": line_no,
                                "credential_type": key_name,
                                "masked_key": masked_key,
                            }
                        )
                        file_findings.append(finding)

        return file_findings


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
