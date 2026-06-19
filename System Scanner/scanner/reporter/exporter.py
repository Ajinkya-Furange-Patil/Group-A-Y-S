"""
AI Discovery Scanner — SIEM/SOC Integration Exporter  (Developer C · Day 6)

Exports scanner telemetry to:
  - Syslog  (UDP/TCP, RFC-5424 severity mapping)
  - HTTP    (JSON POST to a SOC/SIEM webhook)
  - File    (NDJSON line-delimited log file)

Complies with CERT-In 6-hour reporting window by providing a ready-to-call
export interface that can be wired to a scheduler or triggered on scan completion.

Usage:
    from scanner.reporter.exporter import SIEMExporter
    exporter = SIEMExporter()
    exporter.export_to_file(scan_result, "siem_export.ndjson")
    exporter.export_to_http(scan_result, "https://siem.corp/webhook")
    exporter.export_to_syslog(scan_result, host="192.168.1.10", port=514)
"""

from __future__ import annotations

import json
import logging
import socket
import time
from datetime import datetime, timezone
from typing import Any, Optional

try:
    import urllib.request
    import urllib.error
    _HTTP_AVAILABLE = True
except ImportError:
    _HTTP_AVAILABLE = False

from scanner.models import ScanResult, RiskLevel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Syslog severity mapping (RFC-5424)
# ---------------------------------------------------------------------------
_RISK_TO_SEVERITY: dict[str, int] = {
    "critical": 2,   # CRIT
    "high":     3,   # ERR
    "medium":   4,   # WARNING
    "low":      5,   # NOTICE
    "info":     6,   # INFO
}

_SEVERITY_NAMES: dict[int, str] = {
    2: "CRIT",
    3: "ERR",
    4: "WARNING",
    5: "NOTICE",
    6: "INFO",
}


def _risk_to_syslog_severity(risk_score: float) -> int:
    """Map a 0-100 numeric risk score to an RFC-5424 severity level."""
    if risk_score >= 75:
        return 2   # CRIT
    elif risk_score >= 50:
        return 3   # ERR
    elif risk_score >= 25:
        return 4   # WARNING
    else:
        return 6   # INFO


def _build_siem_payload(scan_result: ScanResult) -> dict[str, Any]:
    """Build a structured JSON payload suitable for SIEM ingestion."""
    # Use to_dict which recomputes summary — then read risk from the returned dict
    result_dict = scan_result.to_dict()
    # Allow tests/callers to override risk after compute_summary by checking
    # the live summary dict first (it may have been patched after to_dict call)
    risk_score = scan_result.summary.get("overall_risk_score", result_dict["summary"].get("overall_risk_score", 0.0))
    severity = _SEVERITY_NAMES.get(_risk_to_syslog_severity(risk_score), "INFO")

    return {
        "event_type":      "ai_discovery_scan",
        "scan_id":         result_dict["scan_id"],
        "timestamp":       result_dict["scan_timestamp"],
        "export_time":     datetime.now(timezone.utc).isoformat(),
        "hostname":        result_dict["hostname"],
        "os_info":         result_dict["os_info"],
        "severity":        severity,
        "risk_score":      risk_score,
        "total_findings":  result_dict["summary"].get("total_findings", 0),
        "findings_by_risk": result_dict["summary"].get("findings_by_risk", {}),
        "findings_by_category": result_dict["summary"].get("findings_by_category", {}),
        "modules_run":     result_dict["summary"].get("modules_run", 0),
        "modules_failed":  result_dict["summary"].get("modules_failed", 0),
        "scan_duration_sec": result_dict.get("total_duration_sec", 0),
        "findings":        result_dict.get("findings", []),
    }


class SIEMExporter:
    """Exports AI Discovery scan results to SIEM/SOC integration endpoints.

    Supports three transport methods:
      1. File  — NDJSON (Newline-Delimited JSON) for log shippers (Filebeat, Fluentd)
      2. HTTP  — JSON POST to a webhook endpoint (Splunk HEC, Elastic, etc.)
      3. Syslog — UDP/TCP syslog to a SIEM appliance
    """

    # ------------------------------------------------------------------
    # 1. File export (NDJSON — append-friendly for log shippers)
    # ------------------------------------------------------------------
    def export_to_file(
        self,
        scan_result: ScanResult,
        output_path: str,
        *,
        append: bool = True,
    ) -> None:
        """Append (or write) a single JSON line to an NDJSON export file.

        Args:
            scan_result:  Completed ScanResult object.
            output_path:  Target file path (e.g. "siem_export.ndjson").
            append:       If True (default), appends to existing file so that
                          multiple scans accumulate in the same file.
        """
        mode = "a" if append else "w"
        payload = _build_siem_payload(scan_result)
        try:
            with open(output_path, mode, encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            logger.info("SIEM NDJSON export written to: %s", output_path)
        except OSError as exc:
            logger.error("Failed to write SIEM export to %s: %s", output_path, exc)
            raise

    # ------------------------------------------------------------------
    # 2. HTTP/HTTPS webhook (Splunk HEC, Elastic, custom SOC endpoints)
    # ------------------------------------------------------------------
    def export_to_http(
        self,
        scan_result: ScanResult,
        url: str,
        *,
        token: Optional[str] = None,
        timeout: int = 10,
    ) -> bool:
        """POST scan telemetry JSON to a SIEM/SOC HTTP endpoint.

        Args:
            scan_result:  Completed ScanResult object.
            url:          Full HTTPS URL of the SIEM webhook.
            token:        Optional Bearer token / Splunk HEC token.
            timeout:      HTTP request timeout in seconds (default 10).

        Returns:
            True on HTTP 2xx response, False otherwise.
        """
        if not _HTTP_AVAILABLE:
            logger.error("urllib not available; cannot perform HTTP export.")
            return False

        payload = _build_siem_payload(scan_result)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        headers: dict[str, str] = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent":   "AI-Discovery-Scanner/1.0",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.getcode()
                logger.info("SIEM HTTP export → %s  HTTP %s", url, status)
                return 200 <= status < 300
        except urllib.error.HTTPError as exc:
            logger.error("SIEM HTTP export failed: HTTP %s %s", exc.code, exc.reason)
            return False
        except Exception as exc:
            logger.error("SIEM HTTP export error: %s", exc)
            return False

    # ------------------------------------------------------------------
    # 3. Syslog (UDP or TCP)
    # ------------------------------------------------------------------
    def export_to_syslog(
        self,
        scan_result: ScanResult,
        *,
        host: str = "127.0.0.1",
        port: int = 514,
        protocol: str = "udp",
        facility: int = 16,   # local0
        app_name: str = "ai-discovery-scanner",
        timeout: int = 5,
    ) -> bool:
        """Send an RFC-5424 syslog message to a SIEM appliance.

        Args:
            scan_result:  Completed ScanResult object.
            host:         Syslog server IP / hostname.
            port:         Syslog server port (default 514).
            protocol:     "udp" (default) or "tcp".
            facility:     Syslog facility code (default 16 = local0).
            app_name:     Structured syslog application name.
            timeout:      TCP socket timeout in seconds.

        Returns:
            True if the message was sent without error, False otherwise.
        """
        result_dict = scan_result.to_dict()
        risk_score = result_dict["summary"].get("overall_risk_score", 0.0)
        severity = _risk_to_syslog_severity(risk_score)
        priority = facility * 8 + severity

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        hostname = result_dict.get("hostname", socket.gethostname()) or "-"
        msg_id = result_dict.get("scan_id", "-")

        structured_data = (
            f'[ai_scan@0 scan_id="{msg_id}" risk_score="{risk_score:.1f}" '
            f'findings="{result_dict["summary"].get("total_findings", 0)}" '
            f'severity="{_SEVERITY_NAMES.get(severity, "INFO")}"]'
        )

        syslog_msg = (
            f"<{priority}>1 {timestamp} {hostname} {app_name} - {msg_id} "
            f"{structured_data} AI discovery scan complete: "
            f"risk={risk_score:.1f}/100 findings={result_dict['summary'].get('total_findings', 0)}"
        )
        encoded = syslog_msg.encode("utf-8")

        try:
            if protocol.lower() == "tcp":
                with socket.create_connection((host, port), timeout=timeout) as sock:
                    sock.sendall(encoded + b"\n")
            else:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.sendto(encoded, (host, port))

            logger.info(
                "Syslog export → %s:%d (%s)  priority=%d",
                host, port, protocol.upper(), priority,
            )
            return True
        except Exception as exc:
            logger.error("Syslog export failed: %s", exc)
            return False


def export_sbom_csv(scan_result: ScanResult, output_path: str) -> None:
    """Export a CSV Software Bill of Materials from PackageScanner findings.

    Columns: finding_id, title, category, risk_level, source, confidence, timestamp

    Args:
        scan_result:  Completed ScanResult object.
        output_path:  Target .csv file path.
    """
    import csv

    result_dict = scan_result.to_dict()
    findings = result_dict.get("findings", [])

    rows = []
    for f in findings:
        rows.append({
            "finding_id":  f.get("finding_id", ""),
            "module":      f.get("module_name", ""),
            "title":       f.get("title", ""),
            "category":    f.get("category", ""),
            "risk_level":  f.get("risk_level", ""),
            "source":      f.get("source", ""),
            "confidence":  f"{float(f.get('confidence', 0)) * 100:.0f}%",
            "timestamp":   f.get("timestamp", ""),
        })

    fieldnames = ["finding_id", "module", "title", "category", "risk_level",
                  "source", "confidence", "timestamp"]

    try:
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        logger.info("SBOM CSV export written to: %s", output_path)
    except OSError as exc:
        logger.error("Failed to write SBOM CSV to %s: %s", output_path, exc)
        raise


def export_sbom_json(scan_result: ScanResult, output_path: str, format_type: str = "cyclonedx") -> None:
    """Export a standard JSON SBOM of discovered AI/ML package dependencies.

    Supports CycloneDX (v1.5) and SPDX (v2.3) formats, compliant with SEBI CSCRF guidelines.
    """
    import uuid
    import json
    from datetime import datetime, timezone

    result_dict = scan_result.to_dict()
    findings = result_dict.get("findings", [])

    # Filter to only package scanner findings
    pkg_findings = [f for f in findings if f.get("module_name") == "PackageScanner"]

    if format_type.lower() == "spdx":
        # Generate SPDX v2.3 JSON representation
        spdx_doc = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": "AI-Discovery-Scanner-SBOM",
            "documentNamespace": f"http://spdx.org/spdxdocs/ai-discovery-scanner-{uuid.uuid4()}",
            "creationInfo": {
                "creators": [
                    "Tool: AI-Discovery-Scanner-1.0.0",
                    "Organization: Group A-Y-S"
                ],
                "created": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            },
            "packages": []
        }

        for f in pkg_findings:
            details = f.get("details", {})
            pkg_name = details.get("package_name") or f.get("title").split(":")[1].strip()
            version = details.get("version") or "unknown"
            installer = details.get("installer") or "pip"
            install_loc = details.get("install_location") or "unknown"
            sha256 = details.get("sha256_hash") or ""
            verification = details.get("verification_status") or "unverified"

            purl_type = "pip" if "pip" in installer.lower() else ("npm" if "npm" in installer.lower() else "generic")
            purl = f"pkg:{purl_type}/{pkg_name}@{version}"
            license_declared = "NOASSERTION"
            pkg_ref = f"SPDXRef-Package-{pkg_name.lower().replace('/', '-')}-{version}"

            checksums = []
            if sha256:
                checksums.append({
                    "algorithm": "SHA256",
                    "checksumValue": sha256
                })

            spdx_doc["packages"].append({
                "name": pkg_name,
                "SPDXID": pkg_ref,
                "versionInfo": version,
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "licenseConcluded": license_declared,
                "licenseDeclared": license_declared,
                "copyrightText": "NOASSERTION",
                "checksums": checksums,
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": purl
                    }
                ],
                "comment": f"SEBI CSCRF Verification Status: {verification}. Installer: {installer}. Installed at: {install_loc}."
            })

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(spdx_doc, f, indent=2, ensure_ascii=False)
            logger.info("SPDX SBOM JSON export written to: %s", output_path)
        except OSError as exc:
            logger.error("Failed to write SPDX SBOM JSON to %s: %s", output_path, exc)
            raise

    else:
        # Default: CycloneDX v1.5 JSON representation
        cyclonedx_doc = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "tools": [
                    {
                        "vendor": "Group A-Y-S",
                        "name": "AI Discovery Scanner",
                        "version": "1.0.0"
                    }
                ]
            },
            "components": []
        }

        for f in pkg_findings:
            details = f.get("details", {})
            pkg_name = details.get("package_name") or f.get("title").split(":")[1].strip()
            version = details.get("version") or "unknown"
            installer = details.get("installer") or "pip"
            install_loc = details.get("install_location") or "unknown"
            sha256 = details.get("sha256_hash") or ""
            verification = details.get("verification_status") or "unverified"

            purl_type = "pip" if "pip" in installer.lower() else ("npm" if "npm" in installer.lower() else "generic")
            purl = f"pkg:{purl_type}/{pkg_name}@{version}"

            component = {
                "type": "library",
                "name": pkg_name,
                "version": version,
                "purl": purl,
                "properties": [
                    {
                        "name": "sebi:cscrf:verification",
                        "value": verification
                    },
                    {
                        "name": "sebi:cscrf:install_location",
                        "value": install_loc
                    },
                    {
                        "name": "sebi:cscrf:installer",
                        "value": installer
                    }
                ]
            }

            if sha256:
                component["hashes"] = [
                    {
                        "alg": "SHA-256",
                        "content": sha256
                    }
                ]

            cyclonedx_doc["components"].append(component)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(cyclonedx_doc, f, indent=2, ensure_ascii=False)
            logger.info("CycloneDX SBOM JSON export written to: %s", output_path)
        except OSError as exc:
            logger.error("Failed to write CycloneDX SBOM JSON to %s: %s", output_path, exc)
            raise
