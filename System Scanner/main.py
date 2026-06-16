#!/usr/bin/env python3
"""
AI Discovery Scanner — CLI Entry Point

Usage:
    python main.py --scan                     Run a full AI discovery scan
    python main.py --scan --format json       Output results as JSON
    python main.py --scan --output report     Save results to file (report.json / report.html)

This is the primary user interface for the AI Discovery Scanner.
Person C will expand this with argparse flags, progress bars, and
colored terminal output over Days 1–4.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from scanner.controller import ScanController


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the scanner.

    Args:
        verbose: If True, set log level to DEBUG. Otherwise, INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="ai_scanner",
        description="🔍 AI Discovery Scanner — Detect AI frameworks, models, "
        "agents, and runtimes on your machine.",
        epilog="Example: python main.py --scan --format json --output report",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Run a full AI discovery scan",
    )
    parser.add_argument(
        "--format",
        choices=["json", "html", "both"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (without extension). "
        "Example: --output report → report.json",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug logging",
    )
    return parser


def main() -> None:
    """Main entry point for the AI Discovery Scanner CLI."""
    parser = build_parser()
    args = parser.parse_args()

    # If no arguments provided, show help
    if not args.scan:
        parser.print_help()
        sys.exit(0)

    # Setup logging
    setup_logging(verbose=args.verbose)

    logger = logging.getLogger("ai_scanner")
    logger.info("AI Discovery Scanner v1.0.0")
    logger.info("Scan started...")

    # Run the scan
    controller = ScanController()
    result = controller.run_scan()

    # Output results
    result_dict = result.to_dict()

    if args.output:
        # Save to file
        output_path = f"{args.output}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        logger.info("Report saved to: %s", output_path)
    else:
        # Print to stdout
        print("\n" + json.dumps(result_dict, indent=2, ensure_ascii=False))

    # Print summary
    summary = result_dict.get("summary", {})
    print("\n" + "=" * 50)
    print("SCAN SUMMARY")
    print("=" * 50)
    print(f"  Host:            {result.hostname}")
    print(f"  OS:              {result.os_info}")
    print(f"  Total Findings:  {summary.get('total_findings', 0)}")
    print(f"  Modules Run:     {summary.get('modules_run', 0)}")
    print(f"  Modules OK:      {summary.get('modules_succeeded', 0)}")
    print(f"  Modules Failed:  {summary.get('modules_failed', 0)}")
    print(f"  Risk Score:      {summary.get('overall_risk_score', 0)}/100")
    print(f"  Duration:        {result.total_duration_sec:.2f}s")
    print("=" * 50)


if __name__ == "__main__":
    main()
