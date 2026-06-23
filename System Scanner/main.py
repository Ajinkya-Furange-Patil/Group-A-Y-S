#!/usr/bin/env python3
"""
AI Discovery Scanner — CLI Entry Point

This is the command-line interface for the AI Discovery Scanner.
It provides menu options to run scans, start the web UI, or export reports.
"""

from __future__ import annotations

import atexit
import logging
import sys
import os
import threading
import time
import webbrowser

from scanner.server import ScanServer
from scanner.controller import ScanController
from scanner.repo_scanner import download_and_extract_repo, cleanup_temp_repos

# Ensure temp repos are cleaned up on any exit path
atexit.register(cleanup_temp_repos)

# Global variable to store last scan result for exports
_last_scan_result = None


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the scanner."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    root_logger.handlers = []

    # Console Handler
    console_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File Handler
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


def print_banner():
    """Print the application banner."""
    print("\n" + "=" * 70)
    print("    AI DISCOVERY SCANNER - Command Line Interface")
    print("    System Security & Compliance Analysis Tool")
    print("=" * 70 + "\n")


def print_menu():
    """Print the main menu options."""
    print("\n" + "-" * 70)
    print("MAIN MENU")
    print("-" * 70)
    print("  [1] Run Quick Scan (Headless)")
    print("  [2] Run Full Scan (Headless)")
    print("  [3] Run Custom Scan (Configure Options)")
    print("  [4] Start Web UI Dashboard")
    print("  [5] View Last Scan Results")
    print("  [6] Export Last Scan (JSON)")
    print("  [7] Export Last Scan (HTML)")
    print("  [8] About / Help")
    print("  [0] Exit")
    print("-" * 70)


def run_scan(quick: bool = False, scan_folder: str = None, max_depth: int = None, repo_mode: bool = False) -> None:
    """Run a headless scan and display results."""
    global _last_scan_result
    
    scan_type = "Quick" if quick else "Full"
    if scan_folder or max_depth:
        scan_type = "Custom"
    
    print(f"\n{scan_type} Scan Starting...\n")
    
    if scan_folder:
        print(f"→ Target Folder: {scan_folder}")
    if max_depth is not None:
        print(f"→ Max Depth: {max_depth} levels")
    print()
    
    try:
        controller = ScanController(quick=quick, scan_folder=scan_folder, max_depth=max_depth, repo_mode=repo_mode)
        result = controller.run_scan()
        
        # Store result for exports
        _last_scan_result = result
        
        # Display summary
        print("\n" + "=" * 70)
        print("SCAN COMPLETE - SUMMARY")
        print("=" * 70)
        print(f"Hostname: {result.hostname}")
        print(f"OS: {result.os_info}")
        print(f"Duration: {result.total_duration_sec:.2f} seconds")
        print(f"Modules Executed: {len(result.modules)}")
        print(f"Findings: {len(result.findings)}")
        print(f"Risk Score: {result.summary.get('overall_risk_score', 0.0)}/100")
        print("=" * 70)
        
        # Show severity breakdown
        summary = result.summary
        print(f"\nSeverity Breakdown:")
        print(f"  Critical: {summary.get('critical_count', 0)}")
        print(f"  High:     {summary.get('high_count', 0)}")
        print(f"  Medium:   {summary.get('medium_count', 0)}")
        print(f"  Low:      {summary.get('low_count', 0)}")
        print(f"  Info:     {summary.get('info_count', 0)}")
        
        # Export results
        print(f"\n✓ Results saved to: report.json")
        
        # Save JSON report
        try:
            from scanner.reporter import generate_json_report
            generate_json_report(result, "report.json")
            print(f"✓ JSON report exported successfully")
        except Exception as e:
            print(f"✗ Failed to export JSON: {e}")
        
        print()
        
    except Exception as e:
        print(f"\n✗ Scan failed: {e}")
        logging.error("Scan failed", exc_info=True)


def start_web_ui():
    """Start the web server and open browser."""
    print("\nStarting Web UI Dashboard...")
    print("→ Server will run on: http://127.0.0.1:8000")
    print("→ Press Ctrl+C to stop the server\n")
    
    # Start server in background thread
    server = ScanServer(host="127.0.0.1", port=8000)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    
    # Wait a moment for server to start
    time.sleep(1)
    
    # Try to open browser
    try:
        webbrowser.open("http://127.0.0.1:8000")
        print("✓ Browser opened automatically")
    except Exception:
        print("! Could not open browser automatically")
        print("  Please open: http://127.0.0.1:8000 in your browser")
    
    print("\nServer is running. Press Ctrl+C to stop...")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")


def run_custom_scan():
    """Configure and run a custom scan with user-specified options."""
    print("\n" + "=" * 70)
    print("CUSTOM SCAN CONFIGURATION")
    print("=" * 70)
    
    # Target Region Selection
    print("\nTarget Region:")
    print("  [1] Full System Scan (Default)")
    print("  [2] Custom Folder")
    print("  [3] GitHub Repository (Future Scope)")
    print("  [4] Google Drive / Cloud Storage (Future Scope)")
    
    region_choice = input("\nSelect target region [1-4] (default: 1): ").strip() or "1"
    
    scan_folder = None
    if region_choice == "2":
        print("\n→ Custom Folder Selected")
        scan_folder = input("  Enter folder path (e.g., C:\\Projects\\): ").strip()
        if not scan_folder:
            print("✗ No folder path provided, using current directory")
            scan_folder = None
        elif not os.path.exists(scan_folder):
            print(f"⚠️  Warning: Path '{scan_folder}' does not exist")
            confirm = input("  Continue anyway? [y/N]: ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("✗ Scan cancelled")
                return
    elif region_choice == "3":
        print("\n→ GitHub Repository Scan")
        github_url = input("  Enter GitHub URL (e.g. https://github.com/owner/repo): ").strip()
        if not github_url:
            print("✗ No URL provided, returning to menu.")
            return
        if "github.com" not in github_url:
            print("✗ URL must be a GitHub URL containing 'github.com'.")
            return

        print(f"\n⬇ Downloading repository from: {github_url}")
        try:
            extracted_path = download_and_extract_repo(github_url)
            print(f"✓ Repository extracted to: {extracted_path}")
        except Exception as e:
            print(f"✗ Failed to download repository: {e}")
            return

        # Run all 10 modules on the extracted folder with full depth
        run_scan(quick=False, scan_folder=extracted_path, max_depth=10, repo_mode=True)
        return
    elif region_choice == "4":
        print("\n⚠️  Google Drive / Cloud Storage scanning is not yet implemented")
        print("This feature will allow scanning cloud-based directories")
        print("Expected in future release")
        input("\nPress Enter to return to menu...")
        return
    
    # Scan Depth Configuration
    print("\n" + "-" * 70)
    print("Scan Depth Level:")
    print("  [1] Normal (10 levels) - Recommended")
    print("  [2] Quick Mode (2 levels) - Faster")
    print("  [3] Deep Scan (20 levels) - Thorough")
    print("  [4] Custom Depth")
    
    depth_choice = input("\nSelect depth level [1-4] (default: 1): ").strip() or "1"
    
    max_depth = None
    quick_mode = False
    
    if depth_choice == "1":
        max_depth = 10
        print("→ Using Normal depth (10 levels)")
    elif depth_choice == "2":
        max_depth = 2
        quick_mode = True
        print("→ Using Quick mode (2 levels)")
    elif depth_choice == "3":
        max_depth = 20
        print("→ Using Deep scan (20 levels)")
    elif depth_choice == "4":
        depth_input = input("  Enter custom depth (0 for unlimited): ").strip()
        try:
            max_depth = int(depth_input)
            if max_depth < 0:
                max_depth = 10
                print(f"✗ Invalid depth, using default (10)")
            elif max_depth == 0:
                max_depth = None
                print("→ Using unlimited depth (may take very long)")
            else:
                print(f"→ Using custom depth ({max_depth} levels)")
        except ValueError:
            max_depth = 10
            print(f"✗ Invalid input, using default (10)")
    
    # Confirmation
    print("\n" + "=" * 70)
    print("SCAN CONFIGURATION SUMMARY")
    print("=" * 70)
    print(f"Target:    {scan_folder or 'Full System'}")
    print(f"Depth:     {max_depth if max_depth is not None else 'Unlimited'} levels")
    print(f"Mode:      {'Quick' if quick_mode else 'Full'}")
    print("=" * 70)
    
    confirm = input("\nProceed with scan? [Y/n]: ").strip().lower()
    if confirm in ['n', 'no']:
        print("✗ Scan cancelled")
        return
    
    # Run the scan
    run_scan(quick=quick_mode, scan_folder=scan_folder, max_depth=max_depth)


def view_last_results():
    """Display the last scan results summary."""
    print("\nLast Scan Results:")
    print("-" * 70)
    
    import json
    from pathlib import Path
    
    report_path = Path("report.json")
    
    if not report_path.exists():
        print("✗ No previous scan results found.")
        print("  Run a scan first (option 1 or 2)")
        return
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Hostname: {data.get('hostname', 'Unknown')}")
        print(f"OS: {data.get('os_info', 'Unknown')}")
        print(f"Scan Time: {data.get('timestamp', 'Unknown')}")
        print(f"Duration: {data.get('total_duration_sec', 0):.2f} seconds")
        print(f"Findings: {len(data.get('findings', []))}")
        
        summary = data.get('summary', {})
        print(f"\nRisk Score: {summary.get('overall_risk_score', 0)}/100")
        print(f"\nSeverity Breakdown:")
        print(f"  Critical: {summary.get('critical_count', 0)}")
        print(f"  High:     {summary.get('high_count', 0)}")
        print(f"  Medium:   {summary.get('medium_count', 0)}")
        print(f"  Low:      {summary.get('low_count', 0)}")
        print(f"  Info:     {summary.get('info_count', 0)}")
        
        print(f"\nModules Executed: {len(data.get('modules', []))}")
        for mod in data.get('modules', []):
            status_icon = "✓" if mod.get('status') == 'success' else "✗"
            print(f"  {status_icon} {mod.get('name', 'Unknown')} - {mod.get('duration_sec', 0):.3f}s")
        
    except Exception as e:
        print(f"✗ Failed to read results: {e}")


def export_json():
    """Export last scan results to JSON."""
    print("\nExporting to JSON...")
    
    from pathlib import Path
    report_path = Path("report.json")
    
    if report_path.exists():
        print(f"✓ JSON report already exists: {report_path.absolute()}")
        print(f"  Size: {report_path.stat().st_size / 1024:.2f} KB")
    else:
        print("✗ No scan results found. Run a scan first.")


def export_html():
    """Export last scan results to HTML."""
    global _last_scan_result
    
    print("\nExporting to HTML...")
    
    from pathlib import Path
    
    # Check if we have a scan result in memory
    if _last_scan_result is not None:
        # Use the in-memory result
        try:
            from scanner.reporter import generate_html_report
            generate_html_report(_last_scan_result, "report.html")
            
            html_path = Path("report.html")
            print(f"✓ HTML report exported: {html_path.absolute()}")
            print(f"  Size: {html_path.stat().st_size / 1024:.2f} KB")
            return
        except Exception as e:
            print(f"✗ Failed to export HTML: {e}")
            logging.error("HTML export failed", exc_info=True)
            return
    
    # Fallback: Try to load from JSON
    import json
    json_path = Path("report.json")
    
    if not json_path.exists():
        print("✗ No scan results found. Run a scan first.")
        return
    
    print("⚠ No scan result in memory. HTML export requires running a fresh scan.")
    print("  Please run option [1] or [2] first to generate a new scan.")



def show_help():
    """Display help information."""
    print("\n" + "=" * 70)
    print("ABOUT AI DISCOVERY SCANNER")
    print("=" * 70)
    print("\nThe AI Discovery Scanner is a comprehensive security analysis tool")
    print("that detects and catalogs AI-related components in your system.")
    print("\nFeatures:")
    print("  • 10 specialized scanner modules")
    print("  • Risk scoring and compliance checking")
    print("  • Multiple export formats (JSON, HTML)")
    print("  • Web-based dashboard interface")
    print("  • Customizable scan depth and target folders")
    print("\nScan Modes:")
    print("  • Quick Scan: Faster, 2-level depth, current directory")
    print("  • Full Scan: Comprehensive, 10-level depth, full system")
    print("  • Custom Scan: Configure folder path and depth level")
    print("  • Web UI: Interactive visual dashboard with all options")
    print("\nConfiguration Options:")
    print("  • Target Region:")
    print("    - Full System Scan (default)")
    print("    - Custom Folder (specify path)")
    print("    - GitHub Repository (future - clone and scan repos)")
    print("    - Google Drive / Cloud (future - scan cloud storage)")
    print("\n  • Scan Depth:")
    print("    - Quick Mode: 2 levels")
    print("    - Normal: 10 levels (recommended)")
    print("    - Deep Scan: 20 levels")
    print("    - Custom: User-defined depth")
    print("    - Unlimited: 0 (may take very long)")
    print("\nOutput Files:")
    print("  • report.json - Machine-readable scan results")
    print("  • report.html - Human-readable dashboard export")
    print("  • ai_scanner.log - Detailed execution logs")
    print("\nUsage Examples:")
    print("  1. Quick security check: Option [1]")
    print("  2. Full system audit: Option [2]")
    print("  3. Scan specific folder: Option [3] → Custom Folder")
    print("  4. Interactive analysis: Option [4] → Web UI")
    print("\nFor more information, visit the documentation or README file.")
    print("=" * 70)


def main() -> None:
    """Main entry point for the CLI Scanner."""
    # Reconfigure stdout/stderr to UTF-8
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    # Enable ANSI escape colors on Windows
    if sys.platform == "win32":
        os.system("")

    setup_logging()
    
    print_banner()
    
    while True:
        try:
            print_menu()
            choice = input("\nSelect option [0-8]: ").strip()
            
            if choice == "1":
                run_scan(quick=True)
            elif choice == "2":
                run_scan(quick=False)
            elif choice == "3":
                run_custom_scan()
            elif choice == "4":
                start_web_ui()
            elif choice == "5":
                view_last_results()
            elif choice == "6":
                export_json()
            elif choice == "7":
                export_html()
            elif choice == "8":
                show_help()
            elif choice == "0":
                print("\nExiting AI Discovery Scanner...")
                print("Thank you for using the scanner!\n")
                sys.exit(0)
            else:
                print("\n✗ Invalid option. Please select 0-8.")
            
            input("\nPress Enter to continue...")
            
        except KeyboardInterrupt:
            print("\n\nExiting AI Discovery Scanner...")
            print("Thank you for using the scanner!\n")
            sys.exit(0)
        except Exception as e:
            print(f"\n✗ Error: {e}")
            logging.error("Menu error", exc_info=True)
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
