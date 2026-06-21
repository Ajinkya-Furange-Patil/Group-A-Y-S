#!/usr/bin/env python3
"""
AI Discovery Scanner — UI Entry Point

This is the primary user interface for the AI Discovery Scanner.
It launches the local web server to display the interactive diagnostic dashboard.
"""

from __future__ import annotations

import logging
import sys

from scanner.server import ScanServer


def setup_logging() -> None:
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
    console_handler.setLevel(logging.INFO)
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


def main() -> None:
    """Main entry point for the AI Discovery Scanner."""
    # Reconfigure stdout/stderr to UTF-8
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    # Enable ANSI escape colors on Windows
    if sys.platform == "win32":
        import os
        os.system("")

    setup_logging()
    
    server = ScanServer(host="127.0.0.1", port=8000)
    server.start()

if __name__ == "__main__":
    main()
