#!/usr/bin/env python3
"""
AI Discovery Scanner — Client GUI Application

Starts the local scanning service on a loopback interface and wraps it in a
borderless, premium desktop UI window using pywebview.
"""

import logging
import os
import socket
import sys
import threading
import time
import webview

from scanner.server import ScanServer


def setup_gui_logging() -> None:
    """Setup logging for the GUI client."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler (if console is open or for debugging)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    root_logger.addHandler(console_handler)

    # File handler
    log_file = "ai_scanner_gui.log"
    try:
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
        )
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not initialize log file: {e}", file=sys.stderr)


def find_free_port() -> int:
    """Find an available port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_server_in_thread(port: int) -> ScanServer:
    """Start the ScanServer in a background thread."""
    # Bind only to 127.0.0.1 for local privacy on the client GUI
    server = ScanServer(host="127.0.0.1", port=port)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    return server


class GUI_API:
    def __init__(self, port: int, window=None):
        self.port = port
        self.window = window

    def download_report(self, file_type: str) -> dict:
        """
        Triggered from JavaScript inside PyWebView GUI.
        file_type: 'json' or 'excel' or 'html'
        """
        try:
            import webbrowser
            print(f"\n[GUI API] download_report called with file_type={file_type!r}")
            logging.info("GUI API: download_report called with file_type=%s", file_type)
            
            url = f"http://127.0.0.1:{self.port}/api/export/{file_type}"
            webbrowser.open(url)
            return {"status": "success", "path": "Browser Download"}
        except Exception as e:
            print(f"[GUI API] ERROR in download_report: {e}")
            logging.error("GUI API error in download_report", exc_info=True)
            return {"status": "error", "message": str(e)}

    def save_base64_file(self, base64_data: str, default_filename: str, file_type_desc: str) -> dict:
        """
        Save a base64 encoded data string sent from JS (e.g. PDF).
        """
        try:
            import base64
            import webbrowser
            import urllib.parse
            print(f"\n[GUI API] save_base64_file called for {default_filename!r}")
            logging.info("GUI API: save_base64_file called for %s", default_filename)
            
            # URL-decode the base64 data first to convert %2B, %2F, %3D back to +, /, =
            base64_data = urllib.parse.unquote(base64_data)
            
            # Remove header if present (e.g. data:application/pdf;base64,...)
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]
                
            file_bytes = base64.b64decode(base64_data)
            print(f"[GUI API] Decoded base64 data: {len(file_bytes)} bytes")
            
            # Save it to client_report.pdf in current working directory
            with open("client_report.pdf", "wb") as f:
                f.write(file_bytes)
            print("[GUI API] Saved base64 file to client_report.pdf")
            
            url = f"http://127.0.0.1:{self.port}/api/download-client-pdf"
            webbrowser.open(url)
            return {"status": "success", "path": "Browser Download"}
            
        except Exception as e:
            print(f"[GUI API] ERROR in save_base64_file: {e}")
            logging.error("GUI API error in save_base64_file", exc_info=True)
            return {"status": "error", "message": str(e)}


def main() -> None:
    """Launch the client GUI version of the scanner."""
    # Change CWD to the executable's folder to ensure local reports and logs
    # are written in the same directory as the executable.
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))

    setup_gui_logging()
    logger = logging.getLogger("ai_scanner_gui")
    logger.info("Starting AI Discovery Client GUI...")

    # Find a free local port
    try:
        port = find_free_port()
        logger.info("Local HTTP Server starting on port %d...", port)
    except Exception as e:
        logger.error("Failed to acquire local port: %s", e)
        # Fallback to standard port
        port = 8000

    # Start the server backend
    try:
        start_server_in_thread(port)
        # Give the server thread a brief moment to boot up
        time.sleep(0.5)
    except Exception as e:
        logger.critical("Failed to start background scanner server: %s", e)
        sys.exit(1)

    # Launch pywebview window
    url = f"http://127.0.0.1:{port}/"
    logger.info("Opening desktop window pointing to %s", url)

    # Initialize the borderless window with comfortable dimensions
    api = GUI_API(port=port)
    window = webview.create_window(
        title="AI Discovery Scanner",
        url=url,
        width=1280,
        height=800,
        min_size=(1024, 768),
        resizable=True,
        text_select=True,
        confirm_close=False,
        js_api=api
    )
    api.window = window
    
    # Start webview loop (blocks until the window is closed)
    webview.start(gui='edgechromium')
    logger.info("Client GUI closed.")


if __name__ == "__main__":
    main()
