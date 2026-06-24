"""
AI Discovery Scanner — JSON Exporter
"""

import json
import logging
from typing import Any
from scanner.models import ScanResult

logger = logging.getLogger(__name__)


def export_to_json(scan_result: ScanResult | dict, output_path: str) -> None:
    """Serialize the ScanResult to a JSON file.

    Args:
        scan_result: The ScanResult model populated by the controller, or a dictionary from JSON.
        output_path: Target file path.
    """
    try:
        if isinstance(scan_result, dict):
            result_dict = scan_result
        else:
            result_dict = scan_result.to_dict()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        logger.info("JSON report successfully exported to: %s", output_path)
    except Exception as e:
        logger.error("Failed to export JSON report to %s: %s", output_path, e)
        raise
