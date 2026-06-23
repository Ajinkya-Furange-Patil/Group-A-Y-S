"""
AI Discovery Scanner — GitHub Repository Downloader

Downloads a public GitHub repository as a ZIP archive (using GitHub's
public archive API) and extracts it to a temporary folder so the existing
ScanController can scan it with all 10 modules.

Flow:
    parse_github_url(url)           → (owner, repo)
    download_and_extract_repo(url)  → extracted_folder_path

Only Python stdlib is used — no external dependencies.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import time
import urllib.error
import urllib.request
import zipfile

logger = logging.getLogger(__name__)

# Base directory for temp repos — sits next to this file's package root
_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "temp_repos")
_BASE_DIR = os.path.normpath(_BASE_DIR)


def parse_github_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL.

    Supports:
        https://github.com/owner/repo
        https://github.com/owner/repo.git
        https://github.com/owner/repo/tree/branch
        github.com/owner/repo

    Args:
        url: The GitHub repository URL.

    Returns:
        A (owner, repo) tuple.

    Raises:
        ValueError: If the URL cannot be parsed as a GitHub repo URL.
    """
    url = url.strip().rstrip("/")

    # Strip scheme if missing
    if not url.startswith("http"):
        url = "https://" + url

    # Match github.com/owner/repo (with optional .git and sub-paths)
    pattern = r"https?://(?:www\.)?github\.com/([^/]+)/([^/\s?#]+)"
    match = re.match(pattern, url)
    if not match:
        raise ValueError(
            f"Could not parse GitHub URL: '{url}'. "
            "Expected format: https://github.com/owner/repo"
        )

    owner = match.group(1)
    repo = match.group(2)

    # Strip .git suffix if present
    if repo.endswith(".git"):
        repo = repo[:-4]

    logger.debug("Parsed GitHub URL → owner=%s, repo=%s", owner, repo)
    return owner, repo


def _download_zip(zip_url: str, dest_path: str) -> None:
    """Download a file from url to dest_path with a progress indicator.

    Args:
        zip_url:   Full URL of the ZIP archive.
        dest_path: Local file path to save the downloaded ZIP.

    Raises:
        urllib.error.HTTPError: If the server returns an HTTP error.
        urllib.error.URLError:  If the connection fails.
    """
    logger.info("Downloading: %s", zip_url)

    req = urllib.request.Request(
        zip_url,
        headers={
            "User-Agent": "AI-Discovery-Scanner/1.0 (github-repo-scan)",
            "Accept": "application/zip",
        },
    )

    with urllib.request.urlopen(req, timeout=60) as response:
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 65536  # 64 KB

        with open(dest_path, "wb") as out_file:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = (downloaded / total) * 100
                    logger.debug(
                        "Download progress: %.1f%% (%d / %d bytes)", pct, downloaded, total
                    )

    logger.info("Download complete: %s bytes saved to %s", downloaded, dest_path)


def download_and_extract_repo(github_url: str) -> str:
    """Download a GitHub repo and extract it to a temp folder.

    Tries the ``main`` branch first; if GitHub returns 404, falls back to
    the ``master`` branch.

    Args:
        github_url: Public GitHub repository URL, e.g.
                    ``https://github.com/owner/repo``

    Returns:
        Absolute path to the extracted repository folder, e.g.
        ``…/temp_repos/owner_repo_1234567890/owner-repo-main``

    Raises:
        ValueError:             If the URL cannot be parsed.
        urllib.error.HTTPError: If neither branch ZIP is available.
        zipfile.BadZipFile:     If the downloaded file is not a valid ZIP.
    """
    owner, repo = parse_github_url(github_url)

    # Ensure base temp dir exists
    os.makedirs(_BASE_DIR, exist_ok=True)

    # Unique session folder: owner_repo_<timestamp>
    timestamp = int(time.time())
    session_dir = os.path.join(_BASE_DIR, f"{owner}_{repo}_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)
    logger.info("Temp session directory: %s", session_dir)

    # Try main then master branch
    branches_to_try = ["main", "master"]
    zip_path = os.path.join(session_dir, "repo.zip")
    last_error: Exception | None = None

    for branch in branches_to_try:
        zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
        try:
            _download_zip(zip_url, zip_path)
            logger.info("Successfully downloaded branch '%s'", branch)
            last_error = None
            break
        except urllib.error.HTTPError as e:
            logger.warning("Branch '%s' not available (HTTP %s). Trying next...", branch, e.code)
            last_error = e
            # Remove partial file if any
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except urllib.error.URLError as e:
            logger.error("Network error downloading repo: %s", e)
            raise

    if last_error is not None:
        # Both branches failed — clean up and raise
        shutil.rmtree(session_dir, ignore_errors=True)
        raise last_error

    # Extract the ZIP archive
    logger.info("Extracting ZIP archive to: %s", session_dir)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(session_dir)
    except zipfile.BadZipFile:
        shutil.rmtree(session_dir, ignore_errors=True)
        raise

    # Remove the zip file — we only need the extracted contents
    os.remove(zip_path)

    # GitHub extracts to a sub-folder named owner-repo-branch/
    # Find that sub-folder
    extracted_contents = [
        d for d in os.listdir(session_dir)
        if os.path.isdir(os.path.join(session_dir, d))
    ]

    if len(extracted_contents) == 1:
        extracted_path = os.path.join(session_dir, extracted_contents[0])
    else:
        # Fall back to session_dir itself if structure is unexpected
        extracted_path = session_dir

    logger.info("Extracted repository path: %s", extracted_path)
    return extracted_path


def cleanup_temp_repos() -> None:
    """Remove the entire temp_repos directory.

    Called automatically via ``atexit`` when the application exits, so all
    downloaded repositories are cleaned up without user intervention.
    """
    if os.path.exists(_BASE_DIR):
        try:
            shutil.rmtree(_BASE_DIR, ignore_errors=True)
            logger.info("Cleaned up temp_repos directory: %s", _BASE_DIR)
        except Exception as e:
            logger.warning("Could not clean up temp_repos: %s", e)
    else:
        logger.debug("temp_repos directory not found, nothing to clean up.")
