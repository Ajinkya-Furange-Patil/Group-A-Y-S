"""
AI Discovery Scanner — Local Network HTTP Server

Allows triggering and viewing system scans remotely over the local Wi-Fi/Ethernet network
upon receiving explicit web-based consent approval.
"""

from __future__ import annotations

import http.server
import json
import logging
import os
import platform
import socket
import urllib.parse
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


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
        logger.debug("%s - - %s", self.address_string(), format % args)

    def do_GET(self) -> None:
        """Handle incoming HTTP GET requests."""
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

                rendered_html = template.render(
                    hostname=hostname,
                    os_info=os_info,
                    ip_address=ip_address
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

        elif path == "/run-scan":
            query = urllib.parse.parse_qs(parsed_url.query)
            quick = query.get("quick", ["false"])[0].lower() == "true"
            folder = query.get("folder", [None])[0]
            depth_str = query.get("depth", [None])[0]

            depth = None
            if depth_str and depth_str.strip():
                try:
                    depth = int(depth_str)
                except ValueError:
                    pass

            try:
                from scanner.controller import ScanController
                from scanner.reporter import generate_json_report, generate_html_report

                # Perform scan directly inside the handler thread
                controller = ScanController(quick=quick, scan_folder=folder, max_depth=depth)
                result = controller.run_scan()

                # Generate reports on filesystem
                generate_json_report(result, "report.json")
                generate_html_report(result, "rendered_dashboard.html")

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status": "success"}')
            except Exception as e:
                logger.error("Server-initiated scan failed: %s", e, exc_info=True)
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
