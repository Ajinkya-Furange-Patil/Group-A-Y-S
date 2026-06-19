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
        "--folder", "--path", "-p",
        type=str,
        default=None,
        help="Specific folder or directory to scan only",
    )
    parser.add_argument(
        "--depth", "-d",
        type=int,
        default=None,
        help="Custom depth level/limit for filesystem traversal walks",
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
    parser.add_argument(
        "--export-siem",
        type=str,
        default=None,
        metavar="FILE",
        help="Append scan telemetry to an NDJSON file for SIEM ingestion",
    )
    parser.add_argument(
        "--export-csv",
        type=str,
        default=None,
        metavar="FILE",
        help="Export findings as a CSV SBOM (e.g. --export-csv sbom.csv)",
    )
    parser.add_argument(
        "--export-excel",
        type=str,
        default=None,
        metavar="FILE",
        help="Export full report as an Excel workbook (e.g. --export-excel report.xlsx)",
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Skip writing this scan to the 180-day log retention database",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Show scan history trend from the 180-day retention database and exit",
    )
    return parser


def print_cyber_hud_report(result) -> None:
    """Print a highly styled cyberpunk HUD style findings report in the terminal."""
    import re
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GOLD = "\033[38;5;220m"
    AMBER = "\033[38;5;214m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"

    ansi_escape = re.compile(r'\x1b\[[0-9;]*[mK]')
    def get_visible_len(s: str) -> int:
        return len(ansi_escape.sub('', s))

    def print_hud_line(content_styled: str) -> None:
        visible_len = get_visible_len(content_styled)
        padding = 77 - visible_len
        pad_str = " " * max(0, padding)
        print(f"{BOLD}{GOLD}│{RESET}{content_styled}{pad_str}{BOLD}{GOLD}│{RESET}")

    # Top border
    print(f"\n{BOLD}{GOLD}┌" + "─" * 77 + f"┐{RESET}")
    
    # Header Info
    print_hud_line(f" Access to file: {BOLD}{GREEN}GRANTED{RESET}                   [|| ||| | ||]   {BOLD}{GOLD}/// FILE-5{RESET}")
    print_hud_line(f" User ID: {DIM}214-SYS{RESET}                             BASIC • AUDIT • DEVICE")
    print_hud_line(f" User restrictions: {BOLD}{GREEN}NONE{RESET}")
    
    # Separator
    print(f"{BOLD}{GOLD}├" + "─" * 77 + f"┤{RESET}")
    
    # Title
    print_hud_line(f"{' ' * 24}{BOLD}{GOLD}A I   D E T E C T I O N S   L O G{RESET}")
    
    # Separator
    print(f"{BOLD}{GOLD}├" + "─" * 77 + f"┤{RESET}")
    
    # Top Grid Dots
    print_hud_line(f"      {DIM}+                   +                   +                   +{RESET}")

    findings = result.findings
    if not findings:
        print_hud_line(f"{' ' * 17}{BOLD}{GREEN}NO RISK DETECTORS TRIGGERED IN THIS REGION{RESET}")
        print_hud_line(f"      {DIM}+                   +                   +                   +{RESET}")
    else:
        # Sort findings by risk score DESC
        sorted_findings = sorted(findings, key=lambda f: f.risk_level.numeric_score, reverse=True)
        for f in sorted_findings:
            # Color risk badge
            if f.risk_level.value == "critical":
                risk_badge = f"{BOLD}{RED}[CRITICAL]{RESET}"
            elif f.risk_level.value == "high":
                risk_badge = f"{BOLD}{AMBER}[  HIGH  ]{RESET}"
            elif f.risk_level.value == "medium":
                risk_badge = f"{BOLD}{YELLOW}[ MEDIUM ]{RESET}"
            elif f.risk_level.value == "low":
                risk_badge = f"{BOLD}{BLUE}[  LOW   ]{RESET}"
            else:
                risk_badge = f"{BOLD}{GREEN}[  INFO  ]{RESET}"
            
            # Category
            cat_str = f.category.value if hasattr(f.category, "value") else str(f.category)
            cat_styled = f"{CYAN}{cat_str[:12]:<12}{RESET}"
            
            # Title
            title_styled = f"{BOLD}{f.title[:30]:<30}{RESET}"
            
            # Print main finding line
            print_hud_line(f"  {BOLD}{GOLD}[{f.finding_id}]{RESET} {risk_badge} {cat_styled} | {title_styled}")
            
            # Print source line
            src_str = f.source
            
            # Split src_str into chunks of 61 characters to show the entire path
            max_chunk = 61
            chunks = [src_str[i:i+max_chunk] for i in range(0, len(src_str), max_chunk)]
            if not chunks:
                chunks = [""]
            
            # Print first chunk with "Source: " prefix
            print_hud_line(f"        {DIM}Source: {chunks[0]}")
            
            # Print subsequent chunks indented
            for chunk in chunks[1:]:
                print_hud_line(f"                {chunk}")
                
            print_hud_line(f"      {DIM}+                   +                   +                   +{RESET}")

    # Bottom Separator
    print(f"{BOLD}{GOLD}├" + "─" * 77 + f"┤{RESET}")
    
    # Footer Info
    print_hud_line(f" {BOLD}SUMMARY:{RESET} {len(findings)} files/processes flagged.")
    print_hud_line(f" {DIM}\\\\ DIAGONAL ACCENT SUB-GRID v1.0.0 \\\\{RESET}")
    
    # Bottom border
    print(f"{BOLD}{GOLD}└" + "─" * 77 + f"┘{RESET}")


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
            print("  [1] Run Full System Scan & Show HUD Telemetry (Recommended)")
            print("  [2] Run Quick Scan & Show HUD Telemetry (Faster)")
            print("  [3] Scan Specific Directory only")
            print("  [4] Exit")
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
                verbose = False
                folder = None
                depth = None

            args = InteractiveArgs()
            if not choice or choice == "1":
                args.scan = True
            elif choice == "2":
                args.scan = True
                args.quick = True
            elif choice == "3":
                args.scan = True
                try:
                    f_path = input(f"{BOLD}Enter absolute folder path to scan: {RESET}").strip()
                    if f_path:
                        args.folder = f_path
                    depth_in = input(f"{BOLD}Enter depth limit (default 5): {RESET}").strip()
                    if depth_in:
                        args.depth = int(depth_in)
                except ValueError:
                    print("Invalid depth. Defaulting to 5.")
                    args.depth = 5
                except (KeyboardInterrupt, EOFError):
                    print("\nExiting.")
                    sys.exit(0)
            elif choice == "4":
                print("Exiting.")
                sys.exit(0)
            else:
                print("Invalid option. Please choose again.")
                continue
        else:
            args = parser.parse_args()
            # If command-line args were provided but scan was not set
            if not args.scan:
                parser.print_help()
                sys.exit(0)

        # Setup logging
        setup_logging(verbose=args.verbose)
        logger = logging.getLogger("ai_scanner")

        # --history mode: show retention DB trend and exit
        if not interactive and hasattr(args, "history") and args.history:
            from scanner.reporter.log_retention import LogRetentionDB
            db = LogRetentionDB()
            trend = db.get_trend_summary(days=30)
            stats = db.get_stats()
            print(f"\n{BOLD}{AMBER}180-Day Log Retention Summary{RESET}")
            print(f"  DB path:       {stats['db_path']}")
            print(f"  Total scans:   {stats['total_scans']}")
            print(f"  Oldest record: {stats['oldest_record'] or 'N/A'}")
            print(f"  DB size:       {stats['db_size_bytes']:,} bytes")
            print(f"\n{BOLD}Last 30 days:{RESET}")
            print(f"  Scans:         {trend['scan_count']}")
            print(f"  Avg risk:      {trend['avg_risk']}")
            print(f"  Max risk:      {trend['max_risk']}")
            print(f"  Min risk:      {trend['min_risk']}")
            print(f"  Total findings:{trend['total_findings']}")
            db.close()
            sys.exit(0)
        print(f"\n{BOLD}{GOLD}🔍 AI DISCOVERY SCANNER{RESET} {DIM}v1.0.0{RESET}")
        print(f"{DIM}============================================================{RESET}")
        logger.info("Scan initiated...")

        # Run the scan
        controller = ScanController(quick=args.quick, scan_folder=args.folder, max_depth=args.depth)
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
                # Suppress printing raw JSON to terminal by default, as we now show a detailed HUD report
                generate_json_report(result, "report.json")
            if args.format in ["html", "both"]:
                # Auto-save HTML report as rendered_dashboard.html for preview
                generate_html_report(result, "rendered_dashboard.html")

        summary = result_dict.get("summary", {})

        # ── Developer C: SIEM / CSV / Log-Retention post-processing ──
        from scanner.reporter.exporter import SIEMExporter, export_sbom_csv
        from scanner.reporter.log_retention import LogRetentionDB

        # Always archive to 180-day retention DB (unless --no-db)
        no_db = getattr(args, "no_db", False)
        if not no_db:
            try:
                db = LogRetentionDB()
                db.store_scan(result)
                db.close()
                logger.info("Scan archived to 180-day retention database.")
            except Exception as db_err:
                logger.warning("Could not archive scan to retention DB: %s", db_err)

        # Optional: NDJSON SIEM export
        siem_file = getattr(args, "export_siem", None)
        if siem_file:
            try:
                exporter = SIEMExporter()
                exporter.export_to_file(result, siem_file)
                print(f"  {GREEN}SIEM export:{RESET}      {siem_file}")
            except Exception as siem_err:
                logger.warning("SIEM export failed: %s", siem_err)

        # Optional: CSV SBOM export
        csv_file = getattr(args, "export_csv", None)
        if csv_file:
            try:
                export_sbom_csv(result, csv_file)
                print(f"  {GREEN}SBOM CSV export:{RESET}  {csv_file}")
            except Exception as csv_err:
                logger.warning("CSV SBOM export failed: %s", csv_err)

        # Optional: Excel full report export
        excel_file = getattr(args, "export_excel", None)
        if excel_file:
            try:
                from scanner.reporter.excel_exporter import export_excel
                export_excel(result, excel_file)
                print(f"  {GREEN}Excel report:{RESET}     {excel_file}")
            except Exception as xl_err:
                logger.warning("Excel export failed: %s", xl_err)
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

        # Print the stunning cyberpunk HUD report preview
        print_cyber_hud_report(result)

        # Notify report location
        report_file = "rendered_dashboard.html"
        if args.output:
            report_file = f"{base_output}.html"
        print(f"\n{GREEN}✔ REPORT GENERATION COMPLETE{RESET}")
        print(f"  - HTML Dashboard: {report_file}")
        if args.output:
            print(f"  - Raw JSON Data:  {base_output}.json")

        if interactive:
            try:
                input(f"\n{BOLD}Press Enter to return to the main menu...{RESET}")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                sys.exit(0)

        if not interactive:
            break


if __name__ == "__main__":
    main()
