import json
import logging
import os

logger = logging.getLogger(__name__)

STATUS_FILE = "scan_status.json"

def update_scan_status(status: str, progress: int) -> None:
    """Write scan phase and progress percentage to scan_status.json."""
    try:
        data = {"status": status, "progress": progress}
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        logger.debug("Updated scan status: %s (%d%%)", status, progress)
    except Exception as e:
        logger.error("Failed to write scan_status.json: %s", e)

def get_scan_status() -> dict:
    """Read current scan status from scan_status.json."""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error("Failed to read scan_status.json: %s", e)
    return {"status": "Exploring File System...", "progress": 10}

