"""
AI Discovery Scanner — Local Network HTTP Server

Allows triggering and viewing system scans remotely over the local Wi-Fi/Ethernet network
upon receiving explicit web-based consent approval.
"""

from __future__ import annotations

import atexit
import http.server
import json
import logging
import os
import platform
import socket
import urllib.parse
from jinja2 import Environment, FileSystemLoader
from scanner.status_tracker import update_scan_status
from scanner.version_manager import get_version, get_version_info
from scanner.repo_scanner import download_and_extract_repo, cleanup_temp_repos

import threading

# Register temp repo cleanup when server process exits
atexit.register(cleanup_temp_repos)

logger = logging.getLogger(__name__)

_scan_thread = None
_scan_lock = threading.Lock()


def _run_scan_background(quick: bool, folder: str | None, depth: int | None) -> None:
    global _scan_thread
    with _scan_lock:
        try:
            from scanner.controller import ScanController
            from scanner.reporter import generate_json_report, generate_html_report

            # Ensure we start progress tracking
            update_scan_status("Exploring File System...", 10)
            controller = ScanController(quick=quick, scan_folder=folder, max_depth=depth)
            result = controller.run_scan()

            # Generate reports on filesystem
            generate_json_report(result, "report.json")
            generate_html_report(result, "rendered_dashboard.html")

            # Update status to complete
            update_scan_status("Complete", 100)
        except Exception as e:
            logger.error("Background scan failed: %s", e, exc_info=True)
            update_scan_status(f"Error: {e}", 100)


def _run_repo_scan_background(github_url: str) -> None:
<<<<<<< HEAD
    global _scan_thread
    with _scan_lock:
        try:
            from scanner.repo_scanner import run_repo_scan
            from scanner.reporter import generate_repo_html_report
            import json

            # Update status
            update_scan_status("Downloading Repository...", 15)
            report_data = run_repo_scan(github_url)
            if report_data:
                # Save JSON and HTML report
                with open("report.json", "w", encoding="utf-8") as f:
                    json.dump(report_data, f, indent=2)
                
                generate_repo_html_report(report_data, "rendered_dashboard.html")
                update_scan_status("Complete", 100)
            else:
                update_scan_status("Error: Scan Failed", 100)
        except Exception as e:
            logger.error("Background repository scan failed: %s", e, exc_info=True)
=======
    """Background thread: download repo ZIP → extract → run full scan."""
    global _scan_thread
    with _scan_lock:
        try:
            from scanner.controller import ScanController
            from scanner.reporter import generate_json_report, generate_html_report

            update_scan_status("Downloading GitHub Repository...", 5)
            logger.info("Starting GitHub repo scan: %s", github_url)

            # Download and extract the repo
            extracted_path = download_and_extract_repo(github_url)
            logger.info("Repo extracted to: %s", extracted_path)

            update_scan_status("Scanning Repository Files...", 15)

            # Run all 10 modules on the extracted folder
            controller = ScanController(quick=False, scan_folder=extracted_path, max_depth=10, repo_mode=True)
            result = controller.run_scan()

            # Tag the result so dashboard knows it's a repo scan
            result.hostname = f"GitHub: {github_url.rstrip('/').split('/')[-1]}"

            generate_json_report(result, "report.json")
            generate_html_report(result, "rendered_dashboard.html")

            update_scan_status("Complete", 100)
            logger.info("GitHub repo scan complete.")
        except ValueError as e:
            logger.error("Invalid GitHub URL: %s", e)
            update_scan_status(f"Error: {e}", 100)
        except Exception as e:
            logger.error("GitHub repo scan failed: %s", e, exc_info=True)
>>>>>>> 0216ea5cd9da6e34b7bb5fe5dd3cb97986c49dfe
            update_scan_status(f"Error: {e}", 100)


def get_local_ip() -> str:
    """Detect the local IP address of this host on the network."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not need to be reachable or send packet
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def safe_print(msg: str) -> None:
    """Print a message handling character encoding errors gracefully on restricted terminals."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            # Fallback to ascii representation or strip emojis
            print(msg.encode("ascii", errors="replace").decode("ascii"))
        except Exception as e:
            logger.debug("Failed to fallback print message: %s", e)


class ScanHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP Request Handler for the AI Discovery Scan Server."""

    def log_message(self, format: str, *args: any) -> None:
        """Override standard logging to redirect requests to python logging system."""
        # Use info so requests print to the console under standard settings
        logger.info("%s - - %s", self.address_string(), format % args)

    def do_GET(self) -> None:
        """Handle incoming HTTP GET requests."""
        global _scan_thread
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            try:
                # Resolve template folder relative to current scanner root
                scanner_dir = os.path.dirname(os.path.abspath(__file__))
                templates_dir = os.path.join(scanner_dir, "reporter", "templates")
                
                from jinja2 import select_autoescape
                env = Environment(
                    loader=FileSystemLoader(templates_dir),
                    autoescape=select_autoescape(['html', 'xml', 'j2'])
                )
                template = env.get_template("consent.html.j2")

                hostname = socket.gethostname()
                system = platform.system()
                release = platform.release()
                os_info = f"{system} {release}" if system else "Unknown OS"
                ip_address = get_local_ip()
                version_info = get_version_info()

                rendered_html = template.render(
                    hostname=hostname,
                    os_info=os_info,
                    ip_address=ip_address,
                    version=version_info["version"],
                    version_string=version_info["version_string"],
                    display_name=version_info["display_name"]
                )
                self.wfile.write(rendered_html.encode("utf-8"))
            except Exception as e:
                logger.error("Consent page render failed: %s", e, exc_info=True)
                self.wfile.write(f"Error rendering authorization template: {e}".encode("utf-8"))

        elif path == "/report":
            dashboard_path = "rendered_dashboard.html"
            if os.path.exists(dashboard_path):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                try:
                    with open(dashboard_path, "r", encoding="utf-8") as f:
                        self.wfile.write(f.read().encode("utf-8"))
                except Exception as e:
                    logger.error("Error reading dashboard report: %s", e)
                    self.wfile.write(f"Error reading dashboard file: {e}".encode("utf-8"))
            else:
                self.send_response(302)
                self.send_header("Location", "/")
                self.end_headers()
        elif path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            status_path = "scan_status.json"
            
            is_running = _scan_thread is not None and _scan_thread.is_alive()
            
            status_data = {"status": "Complete", "progress": 100}
            if os.path.exists(status_path):
                try:
                    with open(status_path, "r", encoding="utf-8") as f:
                        status_data = json.load(f)
                except Exception as e:
                    logger.error("Error reading scan_status.json: %s", e)
            
            status_data["running"] = is_running
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
        
        elif path == "/api/version":
            """Get version information"""
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            version_info = get_version_info()
            self.wfile.write(json.dumps(version_info).encode("utf-8"))
        
        elif path == "/api/modules":
            """Get module execution status from last scan"""
            report_path = "report.json"
            if os.path.exists(report_path):
                try:
                    with open(report_path, "r", encoding="utf-8") as f:
                        report_data = json.load(f)
                    
                    modules = report_data.get("modules", [])
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "modules": modules,
                        "total_count": len(modules),
                        "success_count": sum(1 for m in modules if m.get("status") == "success"),
                        "failure_count": sum(1 for m in modules if m.get("status") != "success")
                    }).encode("utf-8"))
                except Exception as e:
                    logger.error("Error reading modules from report: %s", e)
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Failed to read module data"}).encode("utf-8"))
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "No scan results found"}')

        elif path == "/api/results":
            report_path = "report.json"
            if os.path.exists(report_path):
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                try:
                    with open(report_path, "r", encoding="utf-8") as f:
                        self.wfile.write(f.read().encode("utf-8"))
                except Exception as e:
                    logger.error("Error reading report.json: %s", e)
                    self.wfile.write(b'{"error": "Failed to read report.json"}')
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "No scan results found"}')

        elif path == "/api/export/excel":
            print("\n[SERVER API] /api/export/excel requested")
            logger.info("Server API: /api/export/excel requested")
            report_path = "report.json"
            if os.path.exists(report_path):
                try:
                    import tempfile
                    from scanner.exporters.excel_exporter import export_to_excel
                    
                    print("[SERVER API] Reading report.json and generating excel workbook in temp file...")
                    with open(report_path, "r", encoding="utf-8") as f:
                        report_data = json.load(f)
                        
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                        tmp_name = tmp.name
                        
                    export_to_excel(report_data, tmp_name)
                    
                    with open(tmp_name, "rb") as f:
                        excel_data = f.read()
                        
                    os.unlink(tmp_name)
                    
                    # Include version in filename
                    version = get_version().replace(".", "_")
                    filename = f"ai_scan_report_v{version}.xlsx"
                    
                    print(f"[SERVER API] Generated Excel workbook ({len(excel_data)} bytes), sending attachment...")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                    self.end_headers()
                    self.wfile.write(excel_data)
                    print("[SERVER API] SUCCESS: Sent Excel workbook.")
                except PermissionError as e:
                    logger.error("Excel export permission error: %s", e, exc_info=True)
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Cannot write to destination folder. Check permissions."}).encode("utf-8"))
                except OSError as e:
                    import errno
                    logger.error("Excel export OS error: %s", e, exc_info=True)
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    if e.errno == errno.ENOSPC:
                        err_msg = "Insufficient disk space for export."
                    else:
                        err_msg = f"Export failed: {e.strerror or str(e)}"
                    self.wfile.write(json.dumps({"error": err_msg}).encode("utf-8"))
                except (ImportError, ModuleNotFoundError) as e:
                    logger.error("Excel export missing dependencies error: %s", e, exc_info=True)
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Excel export requires additional libraries. Please install dependencies."}).encode("utf-8"))
                except Exception as e:
                    logger.error("Error generating Excel report: %s", e, exc_info=True)
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Failed to generate Excel: {e}"}).encode("utf-8"))
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "No scan results found to export"}')

        elif path == "/api/export/pdf":
            print("\n[SERVER API] /api/export/pdf requested")
            logger.info("Server API: /api/export/pdf requested")
            report_path = "report.json"
            if os.path.exists(report_path):
                try:
                    import tempfile
                    from scanner.exporters.pdf_exporter import export_to_pdf
                    
                    print("[SERVER API] Reading report.json and generating pdf report in temp file...")
                    with open(report_path, "r", encoding="utf-8") as f:
                        report_data = json.load(f)
                        
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp_name = tmp.name
                        
                    export_to_pdf(report_data, tmp_name)
                    
                    with open(tmp_name, "rb") as f:
                        pdf_data = f.read()
                        
                    os.unlink(tmp_name)
                    
                    # Include version in filename
                    version = get_version().replace(".", "_")
                    filename = f"ai_scan_report_v{version}.pdf"
                    
                    print(f"[SERVER API] Generated PDF report ({len(pdf_data)} bytes), sending attachment...")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/pdf")
                    self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                    self.end_headers()
                    self.wfile.write(pdf_data)
                    print("[SERVER API] SUCCESS: Sent PDF report.")
                except PermissionError as e:
                    logger.error("PDF export permission error: %s", e, exc_info=True)
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Cannot write to destination folder. Check permissions."}).encode("utf-8"))
                except OSError as e:
                    import errno
                    logger.error("PDF export OS error: %s", e, exc_info=True)
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    if e.errno == errno.ENOSPC:
                        err_msg = "Insufficient disk space for export."
                    else:
                        err_msg = f"Export failed: {e.strerror or str(e)}"
                    self.wfile.write(json.dumps({"error": err_msg}).encode("utf-8"))
                except Exception as e:
                    logger.error("Error generating PDF report: %s", e, exc_info=True)
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Failed to generate PDF: {e}"}).encode("utf-8"))
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "No scan results found to export"}')

        elif path == "/api/download-client-pdf":
            client_pdf_path = "client_report.pdf"
            if os.path.exists(client_pdf_path):
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                version = get_version().replace(".", "_")
                filename = f"ai_scan_report_v{version}.pdf"
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.end_headers()
                try:
                    with open(client_pdf_path, "rb") as f:
                        self.wfile.write(f.read())
                except Exception as e:
                    logger.error("Error reading client_report.pdf: %s", e)
                    self.wfile.write(b"Error reading file")
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "Client PDF report not found"}')
        
        elif path == "/api/export/json":
            """Download JSON report with versioned filename"""
            print("\n[SERVER API] /api/export/json requested")
            logger.info("Server API: /api/export/json requested")
            report_path = "report.json"
            if os.path.exists(report_path):
                try:
                    with open(report_path, "rb") as f:
                        json_data = f.read()
                    
                    # Include version in filename
                    version = get_version().replace(".", "_")
                    filename = f"ai_scan_report_v{version}.json"
                    
                    print(f"[SERVER API] Found report.json ({len(json_data)} bytes), sending JSON report...")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                    self.end_headers()
                    self.wfile.write(json_data)
                    print("[SERVER API] SUCCESS: Sent JSON report.")
                except Exception as e:
                    logger.error("Error downloading JSON report: %s", e)
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Failed to download JSON: {e}"}).encode("utf-8"))
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "No scan results found to export"}')
        
        elif path in ("/static/jspdf.umd.min.js", "/static/html2pdf.bundle.min.js"):
            filename = os.path.basename(path)
            scanner_dir = os.path.dirname(os.path.abspath(__file__))
            js_path = os.path.join(scanner_dir, "reporter", "templates", filename)
            if os.path.exists(js_path):
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
                self.end_headers()
                try:
                    with open(js_path, "rb") as f:
                        self.wfile.write(f.read())
                except Exception as e:
                    logger.error("Error reading static JS file %s: %s", filename, e)
                    self.wfile.write(b"Error reading file")
            else:
                self.send_response(404)
                self.end_headers()

        elif path == "/api/export/html":
            """Download HTML report with versioned filename"""
            print("\n[SERVER API] /api/export/html requested")
            logger.info("Server API: /api/export/html requested")
            html_path = "rendered_dashboard.html"
            if os.path.exists(html_path):
                try:
                    with open(html_path, "rb") as f:
                        html_data = f.read()
                    
                    # Include version in filename
                    version = get_version().replace(".", "_")
                    filename = f"ai_scan_dashboard_v{version}.html"
                    
                    print(f"[SERVER API] Found rendered_dashboard.html ({len(html_data)} bytes), sending HTML...")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                    self.end_headers()
                    self.wfile.write(html_data)
                    print("[SERVER API] SUCCESS: Sent HTML report.")
                except Exception as e:
                    logger.error("Error downloading HTML report: %s", e)
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Failed to download HTML: {e}"}).encode("utf-8"))
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "No scan results found to export"}')

        elif path == "/repo-scan":
            query = urllib.parse.parse_qs(parsed_url.query)
            github_url = query.get("url", [""])[0].strip()

            if not github_url:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": "Missing 'url' parameter"}).encode("utf-8"))
                return

            # Basic GitHub URL validation
            if "github.com" not in github_url:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": "URL must be a GitHub repository URL (github.com)"}).encode("utf-8"))
                return

            has_previous = False

            try:
                if _scan_thread is None or not _scan_thread.is_alive():
                    update_scan_status("Starting scan...", 5)
                    _scan_thread = threading.Thread(
                        target=_run_repo_scan_background,
                        args=(github_url,),
                        daemon=True
                    )
                    _scan_thread.start()
                    status_msg = "started"
                else:
                    status_msg = "already_running"

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": status_msg, "has_previous": has_previous}).encode("utf-8"))
            except Exception as e:
                logger.error("Repo scan start failed: %s", e, exc_info=True)
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode("utf-8"))

        elif path == "/run-scan":
            query = urllib.parse.parse_qs(parsed_url.query)
            quick = query.get("quick", ["false"])[0].lower() == "true"
            folder = query.get("folder", [None])[0]
            depth_str = query.get("depth", [None])[0]
            github_url = query.get("github_url", [None])[0]

            depth = None
            if depth_str and depth_str.strip():
                try:
                    depth = int(depth_str)
                except ValueError:
                    pass

            # Check if there is a previous scan report
            has_previous = os.path.exists("rendered_dashboard.html") and os.path.exists("report.json")

            status_msg = "success"

            try:
                if _scan_thread is None or not _scan_thread.is_alive():
<<<<<<< HEAD
                    update_scan_status("Starting scan...", 5)
                    _scan_thread = threading.Thread(
                        target=_run_scan_background,
                        args=(quick, folder, depth),
                        daemon=True
                    )
=======
                    if github_url:
                        _scan_thread = threading.Thread(
                            target=_run_repo_scan_background,
                            args=(github_url,),
                            daemon=True
                        )
                    else:
                        _scan_thread = threading.Thread(
                            target=_run_scan_background,
                            args=(quick, folder, depth),
                            daemon=True
                        )
>>>>>>> 0e4bd6ab40e404e826ccffd35618d50fc5dff11e
                    _scan_thread.start()
                else:
                    status_msg = "already_running"

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                response = {
                    "status": status_msg,
                    "has_previous": has_previous
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))
            except Exception as e:
                logger.error("Server-initiated background scan start failed: %s", e, exc_info=True)
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode("utf-8"))

        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"404 Not Found")


class ScanServer:
    """Orchestrator for the Threading Scan HTTPServer."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        self.host = host
        self.port = port
        self.server: http.server.ThreadingHTTPServer | None = None

    def start(self) -> None:
        """Start listening for network requests."""
        try:
            self.server = http.server.ThreadingHTTPServer((self.host, self.port), ScanHTTPRequestHandler)
            local_ip = get_local_ip()
            
            # Clean startup display matching the CLI styling
            RESET = "\033[0m"
            BOLD = "\033[1m"
            GOLD = "\033[38;5;220m"
            AMBER = "\033[38;5;214m"
            DIM = "\033[2m"

            safe_print(f"\n{BOLD}{GOLD}🚀 AI DISCOVERY SCANNER SERVER ACTIVE{RESET}")
            safe_print(f"{DIM}============================================================{RESET}")
            safe_print(f"  {BOLD}Local Access:{RESET}      http://localhost:{self.port}/")
            safe_print(f"  {BOLD}Network Access:{RESET}    http://{local_ip}:{self.port}/")
            safe_print(f"  {BOLD}Host Interface:{RESET}    {self.host}")
            safe_print(f"{DIM}============================================================{RESET}")
            safe_print("Press Ctrl+C to terminate the host server.\n")

            self.server.serve_forever()
        except KeyboardInterrupt:
            safe_print("\nShutting down host server gracefully...")
        except Exception as e:
            logger.critical("Failed to launch HTTP Server: %s", e)
            safe_print(f"\nError: Port {self.port} may be in use, or host {self.host} is invalid: {e}")
            raise
        finally:
            if self.server:
                self.server.server_close()
                logger.info("Server port %d closed.", self.port)
