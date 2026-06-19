"""
Reporter Package

Handles report generation in multiple formats:
  - JSON        : Machine-readable structured output
  - HTML        : Visual dashboard via Jinja2 templates
  - SIEM/SOC    : Syslog / HTTP / NDJSON exporters
  - CSV         : SBOM export
  - Log Archive : 180-day SQLite retention database
"""

from scanner.reporter.report_generator import generate_json_report, generate_html_report
from scanner.reporter.exporter import SIEMExporter, export_sbom_csv, export_sbom_json
from scanner.reporter.log_retention import LogRetentionDB

__all__ = [
    "generate_json_report",
    "generate_html_report",
    "SIEMExporter",
    "export_sbom_csv",
    "export_sbom_json",
    "LogRetentionDB",
]
