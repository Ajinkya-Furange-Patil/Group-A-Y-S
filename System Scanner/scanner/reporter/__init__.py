"""
Reporter Package

Handles report generation in multiple formats:
  - JSON  : Machine-readable structured output
  - HTML  : Visual dashboard via Jinja2 templates
"""

from scanner.reporter.report_generator import generate_json_report, generate_html_report
