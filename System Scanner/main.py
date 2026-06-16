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
    # Reconfigure stdout/stderr to UTF-8 on systems like Windows where the default code page lacks emoji support
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    # Enable ANSI escape colors on Windows
    if sys.platform == "win32":
        import os
        os.system("")

    # ANSI styles
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GOLD = "\033[38;5;220m"
    AMBER = "\033[38;5;214m"

    parser = build_parser()
    args = parser.parse_args()

    # If no arguments provided, show help
    if not args.scan:
        parser.print_help()
        sys.exit(0)

    # Setup logging
    setup_logging(verbose=args.verbose)

    logger = logging.getLogger("ai_scanner")
    print(f"\n{BOLD}{GOLD}🔍 AI DISCOVERY SCANNER{RESET} {DIM}v1.0.0{RESET}")
    print(f"{DIM}============================================================{RESET}")
    logger.info("Scan initiated...")

    # Run the scan
    controller = ScanController()
    result = controller.run_scan()

    # Output results
    result_dict = result.to_dict()
    from scanner.reporter import generate_json_report, generate_html_report

    if args.output:
        # Save to file (strip extension if user provided it to avoid double extensions like report.json.json)
        base_output = args.output
        if base_output.lower().endswith(".json"):
            base_output = base_output[:-5]
        elif base_output.lower().endswith(".html"):
            base_output = base_output[:-5]

        if args.format in ["json", "both"]:
            generate_json_report(result, f"{base_output}.json")
        if args.format in ["html", "both"]:
            generate_html_report(result, f"{base_output}.html")
    else:
        # Default behavior when --output is not provided
        if args.format in ["json", "both"]:
            print("\n" + json.dumps(result_dict, indent=2, ensure_ascii=False))
        if args.format in ["html", "both"]:
            # Auto-save HTML report as report.html for preview
            generate_html_report(result, "report.html")

    # Print summary
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    AMBER = "\033[38;5;214m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"

    summary = result_dict.get("summary", {})
    
    # Select risk color based on score
    risk_score = summary.get("overall_risk_score", 0.0)
    if risk_score >= 75:
        risk_color = RED + BOLD
    elif risk_score >= 50:
        risk_color = YELLOW + BOLD
    elif risk_score >= 25:
        risk_color = BLUE + BOLD
    else:
        risk_color = GREEN + BOLD

    print(f"\n{BOLD}{AMBER}╔══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{AMBER}║                    SCAN RESULT SUMMARY                   ║{RESET}")
    print(f"{BOLD}{AMBER}╚══════════════════════════════════════════════════════════╝{RESET}")
    print(f"  {BOLD}Target Host:{RESET}      {result.hostname}")
    print(f"  {BOLD}Operating System:{RESET} {result.os_info}")
    print(f"  {BOLD}Total Findings:{RESET}   {summary.get('total_findings', 0)}")
    print(f"  {BOLD}Risk Score:{RESET}       {risk_color}{risk_score}/100{RESET}")
    print(f"  {BOLD}Scan Duration:{RESET}    {result.total_duration_sec:.2f} seconds")
    print(f"  {BOLD}Scanners Run:{RESET}     {summary.get('modules_run', 0)}")
    print(f"  {BOLD}Scanners OK:{RESET}      {GREEN}{summary.get('modules_succeeded', 0)}{RESET}")
    print(f"  {BOLD}Scanners Failed:{RESET}  {RED if summary.get('modules_failed', 0) > 0 else RESET}{summary.get('modules_failed', 0)}{RESET}")
    print(f"{BOLD}{AMBER}╟──────────────────────────────────────────────────────────╢{RESET}")
    print(f"{BOLD}{AMBER}║ MODULE RESULTS:                                          ║{RESET}")
    print(f"{BOLD}{AMBER}╟──────────────────────────────────────────────────────────╢{RESET}")
    for mod in result.modules:
        status_char = f"{GREEN}✓ SUCCESS{RESET}" if mod.status == "success" else (f"{RED}✗ FAILED{RESET}" if mod.status == "error" else f"{YELLOW}! SKIPPED{RESET}")
        findings_str = f"({mod.findings_count} findings)" if mod.findings_count > 0 else ""
        print(f"  [{mod.module_number:02d}] {mod.name:<18} : {status_char:<18} {DIM}{findings_str}{RESET}")
    print(f"{BOLD}{AMBER}╚══════════════════════════════════════════════════════════╝{RESET}")


if __name__ == "__main__":
    main()
