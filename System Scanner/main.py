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
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Clear existing handlers to prevent duplicate logging
    root_logger.handlers = []

    # Console Handler: level controlled by verbose flag
    console_level = logging.DEBUG if verbose else logging.INFO
    console_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File Handler: always log DEBUG details for thorough diagnostics
    log_file = "ai_scanner.log"
    try:
        file_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not initialize log file '{log_file}': {e}", file=sys.stderr)


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
        "--quick",
        action="store_true",
        help="Enable quick scan mode (file scanner only scans top-level home dirs)",
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
        "--server",
        action="store_true",
        help="Start local HTTP server for remote scan authorization and viewing",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host address to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug logging",
    )
    return parser


def main() -> None:
    """Main entry point for the AI Discovery Scanner."""
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
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"

    interactive = (len(sys.argv) == 1)
    parser = build_parser()

    while True:
        if interactive:
            print(f"\n{BOLD}{GOLD}🔍 AI DISCOVERY SCANNER{RESET} {DIM}v1.0.0{RESET}")
            print(f"{DIM}============================================================{RESET}")
            print("Choose an option:")
            print("  [1] Run Full Scan & Open HTML Dashboard (Recommended)")
            print("  [2] Run Quick Scan & Open HTML Dashboard (Faster)")
            print("  [3] Exit")
            print(f"{DIM}============================================================{RESET}")
            try:
                choice = input(f"{BOLD}Select an option [1]: {RESET}").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                sys.exit(0)

            # Create standard args namespace for interactive options
            class InteractiveArgs:
                scan = False
                quick = False
                format = "both"
                output = "report"
                server = False
                port = 8000
                host = "0.0.0.0"
                verbose = False

            args = InteractiveArgs()
            if not choice or choice == "1":
                args.scan = True
            elif choice == "2":
                args.scan = True
                args.quick = True
            elif choice == "3":
                print("Exiting.")
                sys.exit(0)
            else:
                print("Invalid option. Please choose again.")
                continue
        else:
            args = parser.parse_args()
            # If command-line args were provided but neither scan nor server was set
            if not args.scan and not args.server:
                parser.print_help()
                sys.exit(0)

        # Setup logging
        setup_logging(verbose=args.verbose)
        logger = logging.getLogger("ai_scanner")

        if args.server:
            from scanner.server import ScanServer
            server = ScanServer(host=args.host, port=args.port)
            if interactive:
                import webbrowser
                webbrowser.open(f"http://localhost:{args.port}/")
            server.start()
            if not interactive:
                sys.exit(0)
            continue

        print(f"\n{BOLD}{GOLD}🔍 AI DISCOVERY SCANNER{RESET} {DIM}v1.0.0{RESET}")
        print(f"{DIM}============================================================{RESET}")
        logger.info("Scan initiated...")

        # Run the scan
        controller = ScanController(quick=args.quick)
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
                # Auto-save HTML report as rendered_dashboard.html for preview
                generate_html_report(result, "rendered_dashboard.html")

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
        print(f"  {BOLD}Scan Duration:{RESET}    {result.duration_formatted}")
        print(f"  {BOLD}Scanners Run:{RESET}     {summary.get('modules_run', 0)}")
        print(f"  {BOLD}Scanners OK:{RESET}      {GREEN}{summary.get('modules_succeeded', 0)}{RESET}")
        print(f"  {BOLD}Scanners Failed:{RESET}  {RED if summary.get('modules_failed', 0) > 0 else RESET}{summary.get('modules_failed', 0)}{RESET}")
        print(f"{BOLD}{AMBER}╟──────────────────────────────────────────────────────────╢{RESET}")
        print(f"{BOLD}{AMBER}║ MODULE RESULTS:                                          ║{RESET}")
        print(f"{BOLD}{AMBER}╟──────────────────────────────────────────────────────────╢{RESET}")
        for mod in result.modules:
            status_char = f"{GREEN}✓ SUCCESS{RESET}" if mod.status == "success" else (f"{RED}✗ FAILED{RESET}" if mod.status == "error" else f"{YELLOW}! SKIPPED{RESET}")
            duration_str = f"{mod.duration_sec:.3f}s"
            findings_str = f"({mod.findings_count} findings)" if mod.findings_count > 0 else ""
            print(f"  [{mod.module_number:02d}] {mod.name:<18} : {status_char:<18} {duration_str:<8} {DIM}{findings_str}{RESET}")
        print(f"{BOLD}{AMBER}╚══════════════════════════════════════════════════════════╝{RESET}")

        # Auto-open dashboard in browser if run interactively (no arguments passed)
        if interactive and args.scan:
            import webbrowser
            from pathlib import Path
            
            report_file = "report.html"
            if args.output:
                base_output = args.output
                if base_output.lower().endswith(".json"):
                    base_output = base_output[:-5]
                elif base_output.lower().endswith(".html"):
                    base_output = base_output[:-5]
                report_file = f"{base_output}.html"
            else:
                report_file = "rendered_dashboard.html"

            report_path = Path(report_file).absolute()
            if report_path.exists():
                print(f"\n{GREEN}Opening HTML Dashboard in your browser...{RESET}")
                webbrowser.open(report_path.as_uri())
            else:
                print(f"\n{RED}Error: Could not find HTML report at {report_path}{RESET}")
            
            try:
                input(f"\n{BOLD}Press Enter to return to the main menu...{RESET}")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                sys.exit(0)

        if not interactive:
            break


if __name__ == "__main__":
    main()
