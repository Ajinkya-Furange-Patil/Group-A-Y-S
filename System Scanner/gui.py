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
    webview.create_window(
        title="AI Discovery Scanner",
        url=url,
        width=1280,
        height=800,
        min_size=(1024, 768),
        resizable=True,
        text_select=True,
        confirm_close=False,
    )
    
    # Start webview loop (blocks until the window is closed)
    webview.start()
    logger.info("Client GUI closed.")


if __name__ == "__main__":
    main()
