"""
MODULE 04 — Package Scanner
===========================
Scans the current Python environment using `pip list --format=json` to discover
installed AI/ML frameworks and libraries (e.g. torch, tensorflow, transformers,
langchain, crewai, autogen, llama-index, openai, anthropic).

Author: Person B
Day: 3
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
from typing import Any

from scanner.models import Finding, FindingCategory, ModuleInfo, RiskLevel

logger = logging.getLogger(__name__)

MODULE_NAME = "PackageScanner"
MODULE_NUMBER = 4

TARGET_PACKAGES = {
    "torch",
    "tensorflow",
    "transformers",
    "langchain",
    "crewai",
    "autogen",
    "llama-index",
    "openai",
    "anthropic"
}


def run() -> tuple[list[Finding], ModuleInfo]:
    """Execute the Package Scanner module.

    Runs `pip list --format=json` using the active Python executable and parses
    the JSON response to identify target AI packages.

    Returns:
        Tuple of (findings_list, module_info)
    """
    module_info = ModuleInfo(name=MODULE_NAME, module_number=MODULE_NUMBER)
    findings: list[Finding] = []
    start_time = time.monotonic()

    packages: list[dict[str, Any]] = []
    try:
        # Run pip list in JSON format using active python process
        cmd = [sys.executable, "-m", "pip", "list", "--format=json"]
        logger.debug("Running PackageScanner command: %s", " ".join(cmd))
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout.strip():
            packages = json.loads(result.stdout)
        else:
            logger.warning("PackageScanner: pip list returned empty output.")
    except Exception as exc:
        logger.warning(
            "PackageScanner: Failed running pip command: %s. Falling back to importlib.metadata",
            exc
        )
        # Fallback to importlib.metadata
        try:
            import importlib.metadata
            for pkg in TARGET_PACKAGES:
                try:
                    version = importlib.metadata.version(pkg)
                    packages.append({"name": pkg, "version": version})
                except importlib.metadata.PackageNotFoundError:
                    # Also try pyautogen for autogen
                    if pkg == "autogen":
                        try:
                            version = importlib.metadata.version("pyautogen")
                            packages.append({"name": "pyautogen", "version": version})
                        except importlib.metadata.PackageNotFoundError:
                            pass
        except Exception as fallback_exc:
            logger.error("PackageScanner: Fallback methods failed: %s", fallback_exc)
            module_info.status = "error"
            module_info.error_message = f"Failed to list packages: {exc}"
            module_info.duration_sec = time.monotonic() - start_time
            return findings, module_info

    try:
        # Process and filter packages
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

            # Check for pyautogen matching autogen target
            if name_lower == "pyautogen":
                matched_pkg = "autogen"

            if matched_pkg:
                # Differentiate category: Agent frameworks vs ML frameworks
                if matched_pkg in {"langchain", "crewai", "autogen"}:
                    category = FindingCategory.AI_AGENT
                else:
                    category = FindingCategory.ML_FRAMEWORK

                finding = Finding(
                    module_name=MODULE_NAME,
                    title=f"Package: {name} ({version})",
                    description=f"Detected installed AI package: {name} (version {version})",
                    source=f"pip://{name}",
                    category=category,
                    risk_level=RiskLevel.INFO,
                    confidence=0.9,
                    details={
                        "package_name": name,
                        "version": version,
                        "installer": "pip",
                    },
                )
                findings.append(finding)

        module_info.status = "success"

    except Exception as exc:
        logger.error("PackageScanner: Error parsing packages: %s", exc, exc_info=True)
        module_info.status = "error"
        module_info.error_message = str(exc)

    finally:
        module_info.duration_sec = time.monotonic() - start_time
        module_info.findings_count = len(findings)

    return findings, module_info


class PackageScanner:
    """Wrapper class for Module 04 PackageScanner to conform to the Discovery Engine interface."""

    MODULE_NAME = MODULE_NAME
    MODULE_NUMBER = MODULE_NUMBER

    def scan(self) -> list[Finding]:
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
