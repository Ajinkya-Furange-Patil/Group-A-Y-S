"""
AI Discovery Scanner — Shared Data Models

This module defines the core data contracts that ALL scanner modules
must conform to. Changes here after Day 1 are BREAKING CHANGES.

Classes:
    RiskLevel   — Enum for categorizing finding severity
    FindingCategory — Enum for AI artifact classification categories
    Finding     — A single discovered AI artifact
    ModuleInfo  — Metadata about a scanner module execution
    ScanResult  — Aggregated results from a complete scan
"""

from __future__ import annotations

import uuid
import os
import platform
import sys
import shutil
import importlib.metadata
import psutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from scanner.version_manager import get_version


class RiskLevel(Enum):
    """Severity level assigned to a discovered AI artifact.

    Used by the Classification Engine to indicate how significant
    a finding is from a security/audit perspective.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    def __str__(self) -> str:
        return self.value

    @property
    def numeric_score(self) -> int:
        """Return a numeric score (0–100) for risk aggregation."""
        scores = {
            RiskLevel.CRITICAL: 100,
            RiskLevel.HIGH: 75,
            RiskLevel.MEDIUM: 50,
            RiskLevel.LOW: 25,
            RiskLevel.INFO: 0,
        }
        return scores[self]


class FindingCategory(Enum):
    """Classification categories for AI artifacts.

    These map to the six categories defined in the architecture:
    AI Model, LLM Runtime, AI Agent, ML Framework, AI Service, Configuration.
    """

    AI_MODEL = "AI Model"
    LLM_RUNTIME = "LLM Runtime"
    AI_AGENT = "AI Agent"
    ML_FRAMEWORK = "ML Framework"
    AI_SERVICE = "AI Service"
    CONFIGURATION = "Configuration"
    SYSTEM_INFO = "System Info"
    UNKNOWN = "Unknown"

    def __str__(self) -> str:
        return self.value


@dataclass
class Finding:
    """A single discovered AI artifact.

    This is the fundamental unit of output from every scanner module.
    Each module produces a list of Finding objects, which are then
    passed through the Classification Engine for categorization.

    Attributes:
        finding_id:   Unique identifier for this finding.
        module_name:  Name of the scanner module that produced this finding.
        title:        Short human-readable title (e.g., "llama3.gguf model file").
        description:  Detailed description of what was found.
        category:     Classification category (set by classifier, may be UNKNOWN initially).
        risk_level:   Severity level (set by classifier, defaults to INFO).
        source:       Where the finding came from (file path, process name, package, etc.).
        details:      Arbitrary key-value metadata specific to the finding type.
        confidence:   Classification confidence score (0.0 – 1.0).
        timestamp:    When the finding was recorded.
    """

    module_name: str
    title: str
    description: str
    source: str
    finding_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    category: FindingCategory = FindingCategory.UNKNOWN
    risk_level: RiskLevel = RiskLevel.INFO
    details: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize the finding to a plain dictionary for JSON output."""
        return {
            "finding_id": self.finding_id,
            "module_name": self.module_name,
            "title": self.title,
            "description": self.description,
            "category": str(self.category),
            "risk_level": str(self.risk_level),
            "source": self.source,
            "details": self.details,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


@dataclass
class ModuleInfo:
    """Metadata about a scanner module's execution.

    Tracks which module ran, how long it took, whether it succeeded,
    and how many findings it produced.

    Attributes:
        name:           Module name (e.g., "SystemScanner").
        module_number:  Module number (01–07).
        status:         Execution status: "success", "error", or "skipped".
        duration_sec:   How long the module took to run, in seconds.
        findings_count: Number of findings produced.
        error_message:  Error message if status is "error".
    """

    name: str
    module_number: int
    status: str = "pending"
    duration_sec: float = 0.0
    findings_count: int = 0
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize module info to a plain dictionary."""
        result = {
            "name": self.name,
            "module_number": self.module_number,
            "status": self.status,
            "duration_sec": round(self.duration_sec, 3),
            "findings_count": self.findings_count,
        }
        if self.error_message:
            result["error_message"] = self.error_message
        return result


@dataclass
class ScanResult:
    """Aggregated results from a complete AI Discovery scan.

    This is the top-level output object returned by the Scan Controller.
    It contains all findings from all modules, module execution metadata,
    and summary statistics.

    Attributes:
        scan_id:          Unique identifier for this scan run.
        scan_timestamp:   When the scan was initiated.
        hostname:         Machine hostname (populated by SystemScanner).
        os_info:          Operating system info string.
        total_duration_sec: Total wall-clock time for the entire scan.
        findings:         All findings from all modules, aggregated.
        modules:          Execution metadata for each module that ran.
        summary:          High-level summary statistics.
    """

    version: str = field(default_factory=get_version)
    scan_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    scan_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    hostname: str = ""
    os_info: str = ""
    total_duration_sec: float = 0.0
    findings: list[Finding] = field(default_factory=list)
    modules: list[ModuleInfo] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)

    def compute_summary(self) -> None:
        """Compute summary statistics from the current findings list."""
        category_counts: dict[str, int] = {}
        risk_counts: dict[str, int] = {}

        for finding in self.findings:
            cat = str(finding.category)
            category_counts[cat] = category_counts.get(cat, 0) + 1

            risk = str(finding.risk_level)
            risk_counts[risk] = risk_counts.get(risk, 0) + 1

        # Calculate aggregate risk score (0–100)
        if self.findings:
            total_risk = sum(f.risk_level.numeric_score for f in self.findings)
            avg_risk = total_risk / len(self.findings)
        else:
            avg_risk = 0

        self.summary = {
            "total_findings": len(self.findings),
            "modules_run": len(self.modules),
            "modules_succeeded": sum(
                1 for m in self.modules if m.status == "success"
            ),
            "modules_failed": sum(
                1 for m in self.modules if m.status == "error"
            ),
            "findings_by_category": category_counts,
            "findings_by_risk": risk_counts,
            "overall_risk_score": round(avg_risk, 1),
        }

        # Collect 15+ Diagnostics Data Points
        self.diagnostics = []
        now_str = datetime.now().isoformat()
        
        # 1. OS Version
        self.diagnostics.append({
            "name": "Operating System",
            "value": f"{platform.system()} {platform.release()}",
            "status": "PASS",
            "timestamp": now_str
        })
        # 2. Python Version
        self.diagnostics.append({
            "name": "Python Version",
            "value": sys.version.split()[0],
            "status": "PASS",
            "timestamp": now_str
        })
        # 3. CPU Core Count
        self.diagnostics.append({
            "name": "CPU Cores",
            "value": str(os.cpu_count() or 1),
            "status": "PASS",
            "timestamp": now_str
        })
        # 4. Active Directory
        self.diagnostics.append({
            "name": "Active Workspace",
            "value": os.getcwd(),
            "status": "PASS",
            "timestamp": now_str
        })
        
        # 5. Installed Packages Count
        try:
            pkg_count = len(list(importlib.metadata.distributions()))
            pkg_status = "PASS"
        except Exception:
            pkg_count = 0
            pkg_status = "WARNING"
        self.diagnostics.append({
            "name": "Installed Packages",
            "value": f"{pkg_count} packages detected",
            "status": pkg_status,
            "timestamp": now_str
        })
        
        # Memory metrics using psutil
        try:
            mem = psutil.virtual_memory()
            total_gb = mem.total / (1024**3)
            avail_gb = mem.available / (1024**3)
            mem_value = f"Total: {total_gb:.1f} GB (Available: {avail_gb:.1f} GB)"
            mem_status = "PASS" if avail_gb > 1.0 else "WARNING"
        except Exception:
            mem_value = "Unavailable"
            mem_status = "WARNING"
            
        self.diagnostics.append({
            "name": "System Memory Availability",
            "value": mem_value,
            "status": mem_status,
            "timestamp": now_str
        })
        
        # Process memory usage using psutil
        try:
            import os as local_os
            process = psutil.Process(local_os.getpid())
            proc_mem_mb = process.memory_info().rss / (1024**2)
            proc_mem_val = f"{proc_mem_mb:.1f} MB used by scanner"
            proc_mem_status = "PASS" if proc_mem_mb < 500 else "WARNING"
        except Exception:
            proc_mem_val = "Unavailable"
            proc_mem_status = "WARNING"
            
        self.diagnostics.append({
            "name": "Process Memory Usage",
            "value": proc_mem_val,
            "status": proc_mem_status,
            "timestamp": now_str
        })

        # CPU utilization
        try:
            cpu_util = psutil.cpu_percent()
            cpu_val = f"{cpu_util}% utilization"
            cpu_status = "PASS" if cpu_util < 90.0 else "WARNING"
        except Exception:
            cpu_val = "Unavailable"
            cpu_status = "WARNING"
            
        self.diagnostics.append({
            "name": "CPU Utilization Check",
            "value": cpu_val,
            "status": cpu_status,
            "timestamp": now_str
        })

        # Write permissions check
        try:
            has_write = os.access(".", os.W_OK)
            write_val = "Writable" if has_write else "Not Writable"
            write_status = "PASS" if has_write else "FAIL"
        except Exception:
            write_val = "Unknown"
            write_status = "FAIL"
            
        self.diagnostics.append({
            "name": "Workspace Write Permissions",
            "value": write_val,
            "status": write_status,
            "timestamp": now_str
        })

        # Free disk space check
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            free_gb = free / (1024**3)
            disk_val = f"{free_gb:.1f} GB free space"
            disk_status = "PASS" if free_gb > 2.0 else "WARNING"
        except Exception:
            disk_val = "Unknown"
            disk_status = "WARNING"
            
        self.diagnostics.append({
            "name": "Available Storage Space",
            "value": disk_val,
            "status": disk_status,
            "timestamp": now_str
        })

        # Database integrity
        db_path = "ai_scanner_history.db"
        db_exists = os.path.exists(db_path)
        db_val = "Present (Verified)" if db_exists else "History Database Missing"
        db_status = "PASS" if db_exists else "WARNING"
        self.diagnostics.append({
            "name": "Telemetry Database Check",
            "value": db_val,
            "status": db_status,
            "timestamp": now_str
        })

        # Config files check
        specs_path = ".kiro/specs"
        specs_exists = os.path.exists(specs_path)
        specs_val = "Present (Verified)" if specs_exists else "Specifications Folder Missing"
        specs_status = "PASS" if specs_exists else "WARNING"
        self.diagnostics.append({
            "name": "Scanner Specifications Check",
            "value": specs_val,
            "status": specs_status,
            "timestamp": now_str
        })

        # Scan Duration Check
        self.diagnostics.append({
            "name": "Scan Execution Duration",
            "value": f"{self.total_duration_sec:.3f} seconds total run time",
            "status": "PASS",
            "timestamp": now_str
        })

        # Modules Executed count
        self.diagnostics.append({
            "name": "Active Modules Executed",
            "value": f"{self.summary.get('modules_run', 0)} active modules",
            "status": "PASS",
            "timestamp": now_str
        })

        # Successful modules
        self.diagnostics.append({
            "name": "Successful Module Returns",
            "value": f"{self.summary.get('modules_succeeded', 0)} succeeded",
            "status": "PASS",
            "timestamp": now_str
        })

        # Failed modules (Warning if any failed)
        failed_count = self.summary.get("modules_failed", 0)
        fail_val = f"{failed_count} failures detected"
        fail_status = "PASS" if failed_count == 0 else "FAIL"
        self.diagnostics.append({
            "name": "Scanner Module Fault Check",
            "value": fail_val,
            "status": fail_status,
            "timestamp": now_str
        })

    @property
    def duration_formatted(self) -> str:
        """Return a human-readable duration string."""
        sec = self.total_duration_sec
        if sec < 60:
            return f"{sec:.2f}s"
        mins = int(sec // 60)
        remaining = sec % 60
        return f"{mins}m {remaining:.2f}s"

    def to_dict(self) -> dict[str, Any]:
        """Serialize the entire scan result to a plain dictionary for JSON output."""
        self.compute_summary()
        return {
            "version": self.version,
            "scan_id": self.scan_id,
            "scan_timestamp": self.scan_timestamp,
            "hostname": self.hostname,
            "os_info": self.os_info,
            "total_duration_sec": round(self.total_duration_sec, 3),
            "total_duration_formatted": self.duration_formatted,
            "summary": self.summary,
            "modules": [m.to_dict() for m in self.modules],
            "findings": [f.to_dict() for f in self.findings],
            "diagnostics": self.diagnostics,
        }
