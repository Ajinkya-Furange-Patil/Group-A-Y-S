"""
MODULE 10 — Regulatory Compliance Scanner (Developer B)

Integrates compliance rules targeting the Indian regulatory landscape:
- DPDP Act: Flags agents transmitting user data externally without enterprise routing.
- SEBI CSCRF: Checks if SBOM is verified and telemetry is logged.
- CERT-In: Audits logging mechanisms to confirm incident readiness.
"""

from __future__ import annotations

import logging
import os
import pathlib
import time

from scanner.models import Finding, FindingCategory, ModuleInfo, RiskLevel

logger = logging.getLogger(__name__)

MODULE_NAME = "ComplianceScanner"
MODULE_NUMBER = 10

def _is_private_ip(ip: str) -> bool:
    """Check if an IPv4 address is in RFC1918 private space."""
    if ip in ("127.0.0.1", "::1") or ip.startswith("127."):
        return True
    if ip.startswith("10."):
        return True
    if ip.startswith("192.168."):
        return True
    if ip.startswith("172."):
        parts = ip.split(".")
        if len(parts) == 4 and parts[1].isdigit():
            if 16 <= int(parts[1]) <= 31:
                return True
    return False

def scan_dpdp() -> list[Finding]:
    """Scan for DPDP Act violations.
    
    Checks if active processes (agents) have external network connections
    to non-private IPs, which might indicate transmitting user data without
    enterprise routing.
    """
    findings: list[Finding] = []
    try:
        import psutil
        for p in psutil.process_iter(['pid', 'name']):
            try:
                name = p.info['name']
                if not name:
                    continue
                name_lower = name.lower()
                
                is_agent = any(agent in name_lower for agent in ["ollama", "lmstudio", "chatgpt", "claude", "python", "node", "interpreter"])
                if not is_agent:
                    continue
                
                conns = psutil.net_connections(kind='inet')
                process_conns = [c for c in conns if c.pid == p.info['pid'] and c.status == 'ESTABLISHED']
                
                for conn in process_conns:
                    if conn.raddr:
                        ip = conn.raddr.ip
                        if not _is_private_ip(ip):
                            findings.append(Finding(
                                module_name=MODULE_NAME,
                                title=f"DPDP Act Risk: External Data Transmission by {name}",
                                description=(
                                    f"Process '{name}' (PID: {p.info['pid']}) is communicating with an external IP ({ip}). "
                                    f"Under the DPDP Act, transmitting user data externally without enterprise routing "
                                    f"must be audited and consented."
                                ),
                                source=f"process:{p.info['pid']}->{ip}",
                                category=FindingCategory.CONFIGURATION,
                                risk_level=RiskLevel.HIGH,
                                confidence=0.85,
                                details={
                                    "pid": p.info['pid'],
                                    "process_name": name,
                                    "remote_ip": ip,
                                    "remote_port": conn.raddr.port,
                                    "compliance_framework": "DPDP Act"
                                }
                            ))
                            break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        logger.debug("ComplianceScanner: Failed to scan DPDP network connections: %s", e)
    
    return findings

def scan_sebi_cscrf(scan_folder: pathlib.Path) -> list[Finding]:
    """Scan for SEBI CSCRF compliance."""
    findings: list[Finding] = []
    
    baseline_path = pathlib.Path(__file__).parent.parent / "baseline" / "hashes.json"
    if not baseline_path.exists():
        findings.append(Finding(
            module_name=MODULE_NAME,
            title="SEBI CSCRF Risk: Missing SBOM Verification Baseline",
            description="The SBOM verification baseline (hashes.json) is missing. SEBI CSCRF requires active software supply chain verification.",
            source="scanner/baseline/hashes.json",
            category=FindingCategory.CONFIGURATION,
            risk_level=RiskLevel.HIGH,
            confidence=0.95,
            details={"compliance_framework": "SEBI CSCRF", "check": "SBOM Verification"}
        ))
    
    db_path = scan_folder / "ai_scanner_history.db"
    if not db_path.exists():
        findings.append(Finding(
            module_name=MODULE_NAME,
            title="SEBI CSCRF Risk: Telemetry Logging Inactive",
            description="The scan telemetry database (ai_scanner_history.db) is not found. SEBI CSCRF requires agent telemetry to be logged.",
            source="ai_scanner_history.db",
            category=FindingCategory.CONFIGURATION,
            risk_level=RiskLevel.MEDIUM,
            confidence=0.9,
            details={"compliance_framework": "SEBI CSCRF", "check": "Telemetry Logging"}
        ))

    return findings

def scan_cert_in(scan_folder: pathlib.Path) -> list[Finding]:
    """Scan for CERT-In compliance."""
    findings: list[Finding] = []
    
    log_path = scan_folder / "ai_scanner.log"
    if not log_path.exists():
        findings.append(Finding(
            module_name=MODULE_NAME,
            title="CERT-In Risk: Missing Audit Logging",
            description="The primary audit log (ai_scanner.log) is missing. CERT-In mandates active logging for incident readiness and forensic timelines.",
            source="ai_scanner.log",
            category=FindingCategory.CONFIGURATION,
            risk_level=RiskLevel.HIGH,
            confidence=0.9,
            details={"compliance_framework": "CERT-In", "check": "Audit Logging"}
        ))
    else:
        if not os.access(log_path, os.W_OK):
            findings.append(Finding(
                module_name=MODULE_NAME,
                title="CERT-In Risk: Audit Log Not Writable",
                description="The primary audit log (ai_scanner.log) is read-only. Incident logging will fail.",
                source="ai_scanner.log",
                category=FindingCategory.CONFIGURATION,
                risk_level=RiskLevel.HIGH,
                confidence=0.95,
                details={"compliance_framework": "CERT-In", "check": "Audit Logging"}
            ))
            
    return findings

def run(scan_folder: str | None = None, max_depth: int | None = None) -> tuple[list[Finding], ModuleInfo]:
    """Execute the Compliance Scanner module."""
    module_info = ModuleInfo(name=MODULE_NAME, module_number=MODULE_NUMBER)
    findings: list[Finding] = []
    start_time = time.monotonic()

    target_dir = pathlib.Path(scan_folder) if scan_folder else pathlib.Path.cwd()

    try:
        findings.extend(scan_dpdp())
        findings.extend(scan_sebi_cscrf(target_dir))
        findings.extend(scan_cert_in(target_dir))
        module_info.status = "success"
    except Exception as exc:
        module_info.status = "error"
        module_info.error_message = str(exc)
        logger.error("ComplianceScanner encountered an error: %s", exc)
    finally:
        module_info.duration_sec = time.monotonic() - start_time
        module_info.findings_count = len(findings)

    return findings, module_info

class ComplianceScanner:
    """Wrapper class for Module 10 ComplianceScanner to conform to the Discovery Engine interface."""

    MODULE_NAME = MODULE_NAME
    MODULE_NUMBER = MODULE_NUMBER

    def __init__(self, scan_folder: str | None = None, max_depth: int | None = None) -> None:
        self.scan_folder = scan_folder
        self.max_depth = max_depth

    def scan(self) -> list[Finding]:
        findings, _ = run(self.scan_folder, self.max_depth)
        return findings
