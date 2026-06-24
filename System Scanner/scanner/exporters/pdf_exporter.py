"""
AI Discovery Scanner — PDF Exporter
"""

import os
import tempfile
import logging
from pathlib import Path
from scanner.models import ScanResult
from scanner.reporter.report_generator import generate_html_report

logger = logging.getLogger(__name__)


def export_to_pdf(scan_result: ScanResult | dict, output_path: str) -> None:
    """Render ScanResult as PDF using weasyprint if available.

    Falls back to generating a beautifully formatted text report if weasyprint is not installed.

    Args:
        scan_result: The ScanResult model populated by the controller, or a dictionary from JSON.
        output_path: Target PDF file path (or text file path on fallback).
    """
    try:
        import weasyprint
        has_weasyprint = True
    except ImportError:
        has_weasyprint = False

    # Standardize result data to dictionary and ScanResult object
    if isinstance(scan_result, dict):
        result_dict = scan_result
        # Try to reconstruct a model if we need to render via Jinja template which expects result.summary etc.
        from _open_dashboard import load_from_json
        # Create a temp file to pass data
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp.close()
            with open(tmp.name, "w", encoding="utf-8") as f:
                import json
                json.dump(result_dict, f)
            scan_obj = load_from_json(Path(tmp.name))
            os.unlink(tmp.name)
    else:
        scan_obj = scan_result
        result_dict = scan_obj.to_dict()

    if has_weasyprint:
        try:
            # Generate a temporary HTML file
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
                temp_html_path = tmp.name
            
            # Write dashboard HTML to the temporary file
            generate_html_report(scan_obj, temp_html_path)
            
            # Compile HTML to PDF using weasyprint
            logger.info("Compiling HTML report to PDF using weasyprint...")
            weasyprint.HTML(temp_html_path).write_pdf(output_path)
            logger.info("PDF report successfully exported to: %s", output_path)
            
            # Clean up the temporary HTML file
            if os.path.exists(temp_html_path):
                os.unlink(temp_html_path)
        except Exception as e:
            logger.error("Failed to compile PDF with weasyprint: %s", e)
            raise
    else:
        logger.warning("weasyprint is not installed. PDF export will fall back to a structured text report.")
        try:
            summary = result_dict.get("summary", {})
            
            content = []
            content.append("=" * 80)
            content.append(f"AI DISCOVERY SCANNER - EXECUTIVE REPORT (v{result_dict.get('version', '1.1.0')})")
            content.append("=" * 80)
            content.append(f"Scan ID:        {result_dict.get('scan_id', '')}")
            content.append(f"Timestamp:      {result_dict.get('scan_timestamp', '')}")
            content.append(f"Hostname:       {result_dict.get('hostname', '')}")
            content.append(f"OS Info:        {result_dict.get('os_info', '')}")
            content.append(f"Duration (s):   {result_dict.get('total_duration_sec', 0.0)}")
            content.append("-" * 80)
            content.append("SUMMARY STATISTICS")
            content.append(f"  Total Findings:      {summary.get('total_findings', 0)}")
            content.append(f"  Overall Risk Score:  {summary.get('overall_risk_score', 0)}")
            content.append(f"  Modules Run:         {summary.get('modules_run', 0)}")
            content.append(f"  Modules Succeeded:   {summary.get('modules_succeeded', 0)}")
            content.append(f"  Modules Failed:      {summary.get('modules_failed', 0)}")
            content.append("-" * 80)
            
            content.append("FINDINGS BY CATEGORY:")
            for cat, count in summary.get("findings_by_category", {}).items():
                content.append(f"  - {cat}: {count}")
            content.append("-" * 80)

            content.append("FINDINGS BY RISK LEVEL:")
            for risk, count in summary.get("findings_by_risk", {}).items():
                content.append(f"  - {risk.upper()}: {count}")
            content.append("-" * 80)

            content.append("MODULE DETAILS:")
            for m in result_dict.get("modules", []):
                content.append(f"  - {m.get('name')}: status={m.get('status')}, findings={m.get('findings_count')}, duration={m.get('duration_sec')}s")
            content.append("-" * 80)
            
            content.append("ALL SCAN FINDINGS:")
            for f in result_dict.get("findings", []):
                content.append(f"  [{f.get('finding_id', '')}] {f.get('risk_level', '').upper()} - {f.get('title', '')}")
                content.append(f"    Module:      {f.get('module_name', '')}")
                content.append(f"    Category:    {f.get('category', '')}")
                content.append(f"    Description: {f.get('description', '')}")
                content.append(f"    Source:      {f.get('source', '')}")
                content.append(f"    Confidence:  {float(f.get('confidence', 0)) * 100:.0f}%")
                content.append(f"    Timestamp:   {f.get('timestamp', '')}")
                content.append("    " + "." * 70)
            
            content.append("=" * 80)
            text_report = "\n".join(content)
            
            # Save the text report to the output path
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text_report)
            logger.info("PDF fallback text report successfully exported to: %s", output_path)
        except Exception as e:
            logger.error("Failed to generate PDF fallback text report: %s", e)
            raise
