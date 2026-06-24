"""
AI Discovery Scanner — Excel Exporter
"""

import logging
from scanner.models import ScanResult
from scanner.reporter.excel_exporter import export_excel as original_export_excel

logger = logging.getLogger(__name__)


def export_to_excel(scan_result: ScanResult | dict, output_path: str) -> None:
    """Generate a multi-sheet Excel workbook from ScanResult.

    Args:
        scan_result: Completed ScanResult from the controller, or a dictionary from JSON.
        output_path: Destination .xlsx file path.
    """
    try:
        original_export_excel(scan_result, output_path)
        logger.info("Excel report successfully exported to: %s", output_path)
    except Exception as e:
        logger.error("Failed to export Excel report to %s: %s", output_path, e)
        raise
