import json
import logging

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
