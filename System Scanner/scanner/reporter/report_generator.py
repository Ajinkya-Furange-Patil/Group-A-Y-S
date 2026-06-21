"""
AI Discovery Scanner — Report Generator

Handles output compilation in multiple formats:
  - JSON : Machine-readable structured output
  - HTML : Visual dashboard rendered via Jinja2 templates
"""

import json
import logging
import os
from jinja2 import Environment, FileSystemLoader
from scanner.models import ScanResult

logger = logging.getLogger(__name__)


def generate_json_report(scan_result: ScanResult, output_path: str) -> None:
    """Serialize the ScanResult to a JSON file.

    Args:
        scan_result: The ScanResult model populated by the controller.
        output_path: Target file path.
    """
    try:
        result_dict = scan_result.to_dict()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        logger.info("JSON report saved to: %s", output_path)
    except Exception as e:
        logger.error("Failed to write JSON report to %s: %s", output_path, e)
        raise


def generate_html_report(scan_result: ScanResult, output_path: str) -> None:
    """Render the ScanResult via dashboard.html.j2 and save as an HTML file.

    Args:
        scan_result: The ScanResult model populated by the controller.
        output_path: Target file path.
    """
    try:
        # Get path to templates folder relative to this script
        templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        
        # Set up Jinja2 environment
        from jinja2 import select_autoescape
        env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(['html', 'xml', 'j2'])
        )
        template = env.get_template("dashboard.html.j2")
        
        # Render the template
        rendered_html = template.render(result=scan_result)
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)
        logger.info("HTML report saved to: %s", output_path)
    except Exception as e:
        logger.error("Failed to render HTML report to %s: %s", output_path, e)
        raise
