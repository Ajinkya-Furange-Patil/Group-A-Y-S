"""
MODULE 09 — License Scanner & AST Parser
=========================================
Monitors local developer workspaces for license compliance.
Codifies a license taxonomy database (MIT, Apache 2.0, LGPL, GPL, AGPL, Polyform Shield, Proprietary).
Uses Python AST (Abstract Syntax Tree) parsing to scan Python files, docstrings,
and imports to flag instances where restrictive licenses (e.g. AGPL/GPL copyleft) are used.
"""

from __future__ import annotations

import ast
import logging
import os
import pathlib
import re
import time
from typing import Any, Generator

from scanner.models import Finding, FindingCategory, ModuleInfo, RiskLevel

logger = logging.getLogger(__name__)

MODULE_NAME = "LicenseScanner"
MODULE_NUMBER = 9

# License taxonomy mapping (SEBI CSCRF compliant license governance)
LICENSE_TAXONOMY = {
    "MIT": {
        "provider": "Massachusetts Institute of Technology",
        "status": "Approved",
        "risk_level": RiskLevel.INFO,
        "description": "Permissive license. Allowed for enterprise usage.",
        "keywords": [r"\bmit\b"]
    },
    "Apache 2.0": {
        "provider": "Apache Software Foundation",
        "status": "Approved",
        "risk_level": RiskLevel.INFO,
        "description": "Permissive license with patent grants. Allowed for enterprise usage.",
        "keywords": [r"\bapache\s*(2\.0|2)?\b"]
    },
    "LGPL": {
        "provider": "Free Software Foundation",
        "status": "Moderate",
        "risk_level": RiskLevel.MEDIUM,
        "description": "Weak copyleft. Dynamic linking is acceptable, but review is recommended.",
        "keywords": [r"\blgpl\b", r"\blesser\s+gpl\b"]
    },
    "GPL": {
        "provider": "Free Software Foundation",
        "status": "Review / Banned",
        "risk_level": RiskLevel.HIGH,
        "description": "Strong copyleft. Restricts distribution and proprietary links. Flagged for legal review.",
        "keywords": [r"\bgpl\b", r"\bgeneral\s+public\s+license\b"]
    },
    "AGPL": {
        "provider": "Free Software Foundation",
        "status": "Review / Banned",
        "risk_level": RiskLevel.CRITICAL,
        "description": "Affero GPL. Restrictive network-triggered copyleft. Strictly flagged/banned in enterprise contexts.",
        "keywords": [r"\bagpl\b", r"\baffero\b"]
    },
    "Polyform Shield": {
        "provider": "Polyform Project",
        "status": "Review / Banned",
        "risk_level": RiskLevel.HIGH,
        "description": "Non-commercial restrictive license. Excludes commercial SaaS usage.",
        "keywords": [r"\bpolyform\s+shield\b", r"\bpolyform\b"]
    },
    "Proprietary": {
        "provider": "Commercial Entity",
        "status": "Review / Banned",
        "risk_level": RiskLevel.MEDIUM,
        "description": "Custom proprietary terms. Requires legal approval.",
        "keywords": [r"\bproprietary\b", r"\ball\s+rights\s+reserved\b", r"\bconfidential\b"]
    }
}

# Restrictive imports dictionary mapping libraries to their license types
RESTRICTED_IMPORTS = {
    "PyQt5": {"license": "GPL", "risk": RiskLevel.HIGH},
    "PyQt6": {"license": "GPL", "risk": RiskLevel.HIGH},
    "mysql.connector": {"license": "GPL", "risk": RiskLevel.HIGH},
    "pygobject": {"license": "LGPL", "risk": RiskLevel.MEDIUM},
    "readline": {"license": "GPL", "risk": RiskLevel.HIGH},
}


def check_imports(tree: ast.AST, file_path: pathlib.Path) -> list[Finding]:
    """
    Check for restrictive imports in AST using ast.walk().
    
    Detects:
    - ast.Import nodes (direct imports like "import PyQt5")
    - ast.ImportFrom nodes (from-imports like "from PyQt5 import QtCore")
    
    Args:
        tree: Parsed AST tree
        file_path: Path to the Python file being analyzed
    
    Returns:
        List of Finding objects for detected restrictive imports
    """
    findings: list[Finding] = []
    
    for node in ast.walk(tree):
        # Check direct imports: import PyQt5
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_name = alias.name
                
                # Check against restricted imports
                # First try exact match, then try base module match
                matched_key = None
                for restricted_name in RESTRICTED_IMPORTS.keys():
                    # Exact match (case-insensitive)
                    if import_name.lower() == restricted_name.lower():
                        matched_key = restricted_name
                        break
                    # Check if import starts with restricted name (for submodules)
                    elif import_name.lower().startswith(restricted_name.lower() + '.'):
                        matched_key = restricted_name
                        break
                    # Check if restricted name starts with import (for multi-part like mysql.connector)
                    elif restricted_name.lower().startswith(import_name.lower() + '.'):
                        matched_key = restricted_name
                        break
                
                if matched_key:
                    restriction_data = RESTRICTED_IMPORTS[matched_key]
                    lic_type = restriction_data["license"]
                    risk = restriction_data["risk"]
                    
                    findings.append(Finding(
                        module_name=MODULE_NAME,
                        title=f"Restrictive Import: {import_name} ({lic_type})",
                        description=(
                            f"Import of potentially restrictive library '{import_name}' (licensed under {lic_type}) "
                            f"detected in '{file_path.name}' at line {node.lineno}."
                        ),
                        source=f"{str(file_path.resolve()).replace('\\', '/')}:{node.lineno}",
                        category=FindingCategory.CONFIGURATION,
                        risk_level=risk,
                        confidence=0.85,
                        details={
                            "file_path": str(file_path.resolve()).replace("\\", "/"),
                            "line_number": node.lineno,
                            "imported_library": import_name,
                            "license_type": lic_type,
                            "license_provider": LICENSE_TAXONOMY.get(lic_type, {}).get("provider", "Unknown"),
                            "detection_method": "AST Import Analyzer"
                        }
                    ))
        
        # Check from-imports: from PyQt5 import QtCore
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                import_name = node.module
                
                # Check against restricted imports
                matched_key = None
                for restricted_name in RESTRICTED_IMPORTS.keys():
                    # Exact match (case-insensitive)
                    if import_name.lower() == restricted_name.lower():
                        matched_key = restricted_name
                        break
                    # Check if import starts with restricted name (for submodules)
                    elif import_name.lower().startswith(restricted_name.lower() + '.'):
                        matched_key = restricted_name
                        break
                    # Check if restricted name starts with import (for multi-part like mysql.connector)
                    elif restricted_name.lower().startswith(import_name.lower() + '.'):
                        matched_key = restricted_name
                        break
                
                if matched_key:
                    restriction_data = RESTRICTED_IMPORTS[matched_key]
                    lic_type = restriction_data["license"]
                    risk = restriction_data["risk"]
                    
                    findings.append(Finding(
                        module_name=MODULE_NAME,
                        title=f"Restrictive Import: {import_name} ({lic_type})",
                        description=(
                            f"Import of potentially restrictive library '{import_name}' (licensed under {lic_type}) "
                            f"detected in '{file_path.name}' at line {node.lineno}."
                        ),
                        source=f"{str(file_path.resolve()).replace('\\', '/')}:{node.lineno}",
                        category=FindingCategory.CONFIGURATION,
                        risk_level=risk,
                        confidence=0.85,
                        details={
                            "file_path": str(file_path.resolve()).replace("\\", "/"),
                            "line_number": node.lineno,
                            "imported_library": import_name,
                            "license_type": lic_type,
                            "license_provider": LICENSE_TAXONOMY.get(lic_type, {}).get("provider", "Unknown"),
                            "detection_method": "AST Import Analyzer"
                        }
                    ))
    
    return findings


def scan_py_file_ast(file_path: pathlib.Path) -> list[Finding]:
    """Parse a python file to AST and extract declared docstring licenses and restrictive imports."""
    findings: list[Finding] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content, filename=str(file_path))

        # 1. Inspect Module Docstring for license details
        docstring = ast.get_docstring(tree)
        if docstring:
            for lic_name, tax in LICENSE_TAXONOMY.items():
                matched = False
                for kw in tax["keywords"]:
                    if re.search(kw, docstring, re.IGNORECASE):
                        snippet = docstring[:100] + "..." if len(docstring) > 100 else docstring
                        findings.append(Finding(
                            module_name=MODULE_NAME,
                            title=f"Code License: {lic_name} Header",
                            description=(
                                f"License signature '{lic_name}' detected in file docstring header of '{file_path.name}'. "
                                f"Taxonomy classification: {tax['status']}. {tax['description']}"
                            ),
                            source=f"{str(file_path.resolve()).replace('\\', '/')}:1",
                            category=FindingCategory.CONFIGURATION,
                            risk_level=tax["risk_level"],
                            confidence=0.90,
                            details={
                                "file_path": str(file_path.resolve()).replace("\\", "/"),
                                "license_detected": lic_name,
                                "status": tax["status"],
                                "detection_method": "AST Docstring Parser",
                                "snippet": snippet
                            }
                        ))
                        matched = True
                        break
                if matched:
                    break

        # 2. Inspect AST Nodes for imports of copyleft/restrictive packages
        findings.extend(check_imports(tree, file_path))

    except Exception as e:
        logger.debug("LicenseScanner: AST parse failed for %s: %s", file_path, e)

    return findings


def scan_file_for_snippets(file_path: pathlib.Path) -> list[Finding]:
    """Scan raw text for inline copyleft comments/signatures in code snippets."""
    findings: list[Finding] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        # Split into lines for snippet extraction
        lines = content.splitlines()
        
        for i, line in enumerate(lines):
            for lic_name, tax in LICENSE_TAXONOMY.items():
                if tax["status"] not in ("Review / Banned", "Moderate"):
                    continue
                for kw in tax["keywords"]:
                    if re.search(kw, line, re.IGNORECASE):
                        # Construct a multi-line snippet for context
                        start_idx = max(0, i - 1)
                        end_idx = min(len(lines), i + 2)
                        snippet = "\n".join(lines[start_idx:end_idx]).strip()
                        if len(snippet) > 200:
                            snippet = snippet[:197] + "..."
                            
                        findings.append(Finding(
                            module_name=MODULE_NAME,
                            title=f"Code Snippet: {lic_name} Mention",
                            description=(
                                f"Possible copyleft / restrictive license signature '{lic_name}' detected inline in "
                                f"'{file_path.name}' at line {i+1}. This may indicate an inadvertently copied AI snippet."
                            ),
                            source=f"{str(file_path.resolve()).replace('\\', '/')}:{i+1}",
                            category=FindingCategory.CONFIGURATION,
                            risk_level=tax["risk_level"],
                            confidence=0.85,
                            details={
                                "file_path": str(file_path.resolve()).replace("\\", "/"),
                                "line_number": i + 1,
                                "license_detected": lic_name,
                                "status": tax["status"],
                                "detection_method": "Inline Regex Scanner",
                                "snippet": snippet
                            }
                        ))
                        break
    except Exception as e:
        logger.debug("LicenseScanner: snippet scan failed for %s: %s", file_path, e)
    return findings


def scan_workspace_license_files(scan_dir: pathlib.Path) -> list[Finding]:
    """Scan root directories for license text files."""
    findings: list[Finding] = []
    license_files = ["LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING", "COPYING.txt"]
    for lf in license_files:
        p = scan_dir / lf
        try:
            if p.exists() and p.is_file():
                content = p.read_text(encoding="utf-8", errors="ignore")
                for lic_name, tax in LICENSE_TAXONOMY.items():
                    matched = False
                    for kw in tax["keywords"]:
                        if re.search(kw, content, re.IGNORECASE):
                            findings.append(Finding(
                                module_name=MODULE_NAME,
                                title=f"Workspace License File: {lic_name}",
                                description=(
                                    f"Declared workspace license file '{lf}' matches taxonomy '{lic_name}'. "
                                    f"Status: {tax['status']}. Details: {tax['description']}"
                                ),
                                source=str(p.resolve()).replace("\\", "/"),
                                category=FindingCategory.CONFIGURATION,
                                risk_level=tax["risk_level"],
                                confidence=0.95,
                                details={
                                    "license_file_path": str(p.resolve()).replace("\\", "/"),
                                    "license_detected": lic_name,
                                    "status": tax["status"],
                                    "detection_method": "License Content Heuristic"
                                }
                            ))
                            matched = True
                            break
                    if matched:
                        break
        except Exception as e:
            logger.debug("LicenseScanner: failed to read license file %s: %s", p, e)
    return findings


def run(scan_folder: str | None = None, max_depth: int | None = None) -> tuple[list[Finding], ModuleInfo]:
    """Execute the License Scanner and AST Parser module."""
    module_info = ModuleInfo(name=MODULE_NAME, module_number=MODULE_NUMBER)
    findings: list[Finding] = []
    start_time = time.monotonic()

    target_dir = pathlib.Path(scan_folder) if scan_folder else pathlib.Path.cwd()
    depth_val = max_depth if max_depth is not None else 5

    try:
        # 1. Scan for declared workspace license files
        findings.extend(scan_workspace_license_files(target_dir))

        # 2. Walk directory and parse Python files with AST
        skip_dirs = {
            ".git", "node_modules", "venv", ".venv", "env", "__pycache__",
            "AppData", "Library", "site-packages", "dist", "build"
        }

        root_depth = len(target_dir.parts)
        for root, dirs, files in os.walk(target_dir, topdown=True, onerror=lambda _: None):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]

            curr_path = pathlib.Path(root)
            curr_depth = len(curr_path.parts) - root_depth

            for f in files:
                file_path = curr_path / f
                if f.endswith(".py"):
                    findings.extend(scan_py_file_ast(file_path))
                    findings.extend(scan_file_for_snippets(file_path))
                elif f.endswith((".js", ".ts", ".jsx", ".tsx", ".cpp", ".c", ".h", ".hpp", ".java", ".go", ".rs")):
                    findings.extend(scan_file_for_snippets(file_path))

            if curr_depth >= depth_val:
                dirs.clear()

        module_info.status = "success"

    except Exception as exc:
        module_info.status = "error"
        module_info.error_message = str(exc)

    finally:
        module_info.duration_sec = time.monotonic() - start_time
        module_info.findings_count = len(findings)

    return findings, module_info


class LicenseScanner:
    """Wrapper class for Module 09 LicenseScanner to conform to the Discovery Engine interface."""

    MODULE_NAME = MODULE_NAME
    MODULE_NUMBER = MODULE_NUMBER

    def __init__(self, scan_folder: str | None = None, max_depth: int | None = None) -> None:
        self.scan_folder = scan_folder
        self.max_depth = max_depth

    def scan(self) -> list[Finding]:
        findings, _ = run(self.scan_folder, self.max_depth)
        return findings
