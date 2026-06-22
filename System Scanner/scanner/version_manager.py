"""
AI Discovery Scanner — Version Manager

Defines and exposes the application version number as a single source of truth.
Automatically increments patch version on changes.
"""

import os
import json
from pathlib import Path
from datetime import datetime

VERSION = "1.4.0"  # Auto-updated on changes

def get_version() -> str:
    """Return the application version number."""
    return VERSION


def increment_version(bump_type: str = "patch") -> str:
    """
    Increment the version number based on semantic versioning.
    
    Args:
        bump_type: Type of version bump - "major", "minor", or "patch" (default)
    
    Returns:
        New version string
    """
    major, minor, patch = map(int, VERSION.split("."))
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    new_version = f"{major}.{minor}.{patch}"
    
    # Update the version in this file
    version_file = Path(__file__)
    content = version_file.read_text(encoding="utf-8")
    content = content.replace(f'VERSION = "{VERSION}"', f'VERSION = "{new_version}"')
    version_file.write_text(content, encoding="utf-8")
    
    # Log version change
    _log_version_change(VERSION, new_version, bump_type)
    
    return new_version


def _log_version_change(old_version: str, new_version: str, bump_type: str) -> None:
    """Log version changes to version_history.json"""
    history_file = Path(__file__).parent.parent / "version_history.json"
    
    history = []
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text(encoding="utf-8"))
        except:
            history = []
    
    history.append({
        "old_version": old_version,
        "new_version": new_version,
        "bump_type": bump_type,
        "timestamp": datetime.now().isoformat(),
        "auto_updated": True
    })
    
    # Keep only last 50 entries
    history = history[-50:]
    
    history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")


def get_version_info() -> dict:
    """Get detailed version information including build metadata."""
    return {
        "version": VERSION,
        "version_string": f"v{VERSION}",
        "display_name": f"AI Discovery Scanner v{VERSION}",
        "api_version": "1.0",
        "build_date": datetime.now().isoformat(),
    }
