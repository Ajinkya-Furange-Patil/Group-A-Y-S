"""
AI Discovery Scanner — 180-Day ICT Log Retention Database  (Developer C · Day 7)

Implements a lightweight SQLite-backed archive that:
  - Stores every completed scan summary and its findings.
  - Automatically purges records older than 180 days (CERT-In mandate).
  - Provides query helpers for history visualisation and trend analysis.

Database file: ai_scanner_history.db  (created next to main.py by default)

Usage:
    from scanner.reporter.log_retention import LogRetentionDB
    db = LogRetentionDB()                          # opens / creates DB
    db.store_scan(scan_result)                     # archive a scan
    rows = db.get_scan_history(days=30)            # last 30 days
    db.purge_old_records()                         # enforce 180-day window
    summary = db.get_trend_summary(days=30)        # risk trend dict
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from scanner.models import ScanResult

logger = logging.getLogger(__name__)

# Default retention window mandated by CERT-In ICT log rules
RETENTION_DAYS = 180

# Schema version — increment when columns change so callers can migrate
_SCHEMA_VERSION = 1


class LogRetentionDB:
    """SQLite-backed 180-day ICT log archive for AI Discovery Scanner.

    Creates two tables:
      scan_history  — one row per completed scan (summary-level data)
      scan_findings — individual findings linked to scan_history via scan_id

    All timestamps are stored as ISO-8601 UTC strings and as Unix epoch
    floats for easy range queries.
    """

    def __init__(self, db_path: str = "ai_scanner_history.db") -> None:
        """Open (or create) the retention database.

        Args:
            db_path: Path to the SQLite database file.
                     Defaults to "ai_scanner_history.db" in the current directory.
                     Pass ":memory:" for an in-memory database (useful for tests).
        """
        # Do NOT resolve ":memory:" — it is a special SQLite keyword
        if db_path == ":memory:":
            self._db_path = ":memory:"
        else:
            self._db_path = str(Path(db_path).resolve())
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_schema()
        logger.info("LogRetentionDB ready at: %s", self._db_path)

    # ------------------------------------------------------------------
    # Connection & schema
    # ------------------------------------------------------------------
    def _connect(self) -> None:
        self._conn = sqlite3.connect(
            self._db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")

    def _create_schema(self) -> None:
        assert self._conn is not None
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS schema_meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS scan_history (
                scan_id              TEXT PRIMARY KEY,
                scan_timestamp       TEXT NOT NULL,
                epoch_ts             REAL NOT NULL,
                hostname             TEXT,
                os_info              TEXT,
                total_duration_sec   REAL,
                total_findings       INTEGER,
                overall_risk_score   REAL,
                modules_run          INTEGER,
                modules_failed       INTEGER,
                findings_by_risk     TEXT,
                findings_by_category TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_scan_history_epoch
                ON scan_history (epoch_ts);

            CREATE TABLE IF NOT EXISTS scan_findings (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id         TEXT NOT NULL
                                REFERENCES scan_history(scan_id) ON DELETE CASCADE,
                finding_id      TEXT,
                module_name     TEXT,
                title           TEXT,
                category        TEXT,
                risk_level      TEXT,
                source          TEXT,
                confidence      REAL,
                timestamp_ts    TEXT,
                details_json    TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_scan_findings_scan_id
                ON scan_findings (scan_id);
        """)
        # Record schema version
        self._conn.execute(
            "INSERT OR IGNORE INTO schema_meta VALUES ('version', ?)",
            (str(_SCHEMA_VERSION),),
        )
        self._conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # Store a completed scan
    # ------------------------------------------------------------------
    def store_scan(self, scan_result: ScanResult) -> None:
        """Persist a completed scan to the archive.

        Also triggers automatic purge of records older than 180 days.

        Args:
            scan_result: The completed ScanResult from the controller.
        """
        assert self._conn is not None
        result_dict = scan_result.to_dict()
        summary = result_dict.get("summary", {})

        # Parse ISO timestamp; fall back to now if malformed
        try:
            dt = datetime.fromisoformat(result_dict["scan_timestamp"])
        except (ValueError, KeyError):
            dt = datetime.now(timezone.utc)
        epoch_ts = dt.timestamp()

        try:
            with self._conn:
                self._conn.execute(
                    """
                    INSERT OR REPLACE INTO scan_history (
                        scan_id, scan_timestamp, epoch_ts, hostname, os_info,
                        total_duration_sec, total_findings, overall_risk_score,
                        modules_run, modules_failed,
                        findings_by_risk, findings_by_category
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        result_dict["scan_id"],
                        result_dict["scan_timestamp"],
                        epoch_ts,
                        result_dict.get("hostname", ""),
                        result_dict.get("os_info", ""),
                        result_dict.get("total_duration_sec", 0.0),
                        summary.get("total_findings", 0),
                        summary.get("overall_risk_score", 0.0),
                        summary.get("modules_run", 0),
                        summary.get("modules_failed", 0),
                        json.dumps(summary.get("findings_by_risk", {})),
                        json.dumps(summary.get("findings_by_category", {})),
                    ),
                )

                # Store individual findings
                findings_rows = [
                    (
                        result_dict["scan_id"],
                        f.get("finding_id", ""),
                        f.get("module_name", ""),
                        f.get("title", ""),
                        f.get("category", ""),
                        f.get("risk_level", ""),
                        f.get("source", ""),
                        float(f.get("confidence", 0.0)),
                        f.get("timestamp", ""),
                        json.dumps(f.get("details", {})),
                    )
                    for f in result_dict.get("findings", [])
                ]
                if findings_rows:
                    self._conn.executemany(
                        """
                        INSERT INTO scan_findings
                            (scan_id, finding_id, module_name, title, category,
                             risk_level, source, confidence, timestamp_ts, details_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        findings_rows,
                    )

            logger.info(
                "Archived scan %s  (%d findings)",
                result_dict["scan_id"],
                summary.get("total_findings", 0),
            )
        except sqlite3.Error as exc:
            logger.error("Failed to store scan %s: %s", result_dict.get("scan_id"), exc)
            raise

        # Enforce retention window after every store
        self.purge_old_records()

    # ------------------------------------------------------------------
    # Retrieve scan history
    # ------------------------------------------------------------------
    def get_scan_history(self, days: int = RETENTION_DAYS) -> list[dict[str, Any]]:
        """Return scan summaries for the past N days (most recent first).

        Args:
            days: Number of days to look back (default 180).

        Returns:
            List of dicts, each representing one scan summary row.
        """
        assert self._conn is not None
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()
        cursor = self._conn.execute(
            """
            SELECT * FROM scan_history
            WHERE epoch_ts >= ?
            ORDER BY epoch_ts DESC
            """,
            (cutoff,),
        )
        rows = []
        for row in cursor.fetchall():
            d = dict(row)
            d["findings_by_risk"] = json.loads(d.get("findings_by_risk") or "{}")
            d["findings_by_category"] = json.loads(d.get("findings_by_category") or "{}")
            rows.append(d)
        return rows

    def get_scan_findings(self, scan_id: str) -> list[dict[str, Any]]:
        """Return all individual findings for a specific scan_id.

        Args:
            scan_id: The scan ID to look up.

        Returns:
            List of finding dicts.
        """
        assert self._conn is not None
        cursor = self._conn.execute(
            "SELECT * FROM scan_findings WHERE scan_id = ? ORDER BY id",
            (scan_id,),
        )
        rows = []
        for row in cursor.fetchall():
            d = dict(row)
            d["details"] = json.loads(d.pop("details_json", "{}"))
            rows.append(d)
        return rows

    def get_latest_scan(self) -> Optional[dict[str, Any]]:
        """Return the most recently stored scan summary, or None."""
        history = self.get_scan_history(days=RETENTION_DAYS)
        return history[0] if history else None

    # ------------------------------------------------------------------
    # Trend / analytics helpers
    # ------------------------------------------------------------------
    def get_trend_summary(self, days: int = 30) -> dict[str, Any]:
        """Compute a risk trend summary for the past N days.

        Returns a dict suitable for dashboard visualisation:
          {
            "period_days":   30,
            "scan_count":    12,
            "avg_risk":      54.2,
            "max_risk":      78.0,
            "min_risk":      22.1,
            "total_findings":391,
            "scans":         [{scan_id, scan_timestamp, overall_risk_score,
                               total_findings}, ...]   (oldest → newest)
          }
        """
        history = self.get_scan_history(days=days)
        if not history:
            return {
                "period_days": days,
                "scan_count": 0,
                "avg_risk": 0.0,
                "max_risk": 0.0,
                "min_risk": 0.0,
                "total_findings": 0,
                "scans": [],
            }

        scores = [h["overall_risk_score"] for h in history]
        total_findings = sum(h["total_findings"] for h in history)

        scans_asc = [
            {
                "scan_id":          h["scan_id"],
                "scan_timestamp":   h["scan_timestamp"],
                "overall_risk_score": h["overall_risk_score"],
                "total_findings":   h["total_findings"],
            }
            for h in reversed(history)
        ]

        return {
            "period_days":   days,
            "scan_count":    len(history),
            "avg_risk":      round(sum(scores) / len(scores), 1),
            "max_risk":      round(max(scores), 1),
            "min_risk":      round(min(scores), 1),
            "total_findings": total_findings,
            "scans":         scans_asc,
        }

    def get_stats(self) -> dict[str, Any]:
        """Return database-level statistics (total scans, oldest record, DB size)."""
        assert self._conn is not None
        total_cursor = self._conn.execute("SELECT COUNT(*) as cnt FROM scan_history")
        total = (total_cursor.fetchone() or {"cnt": 0})["cnt"]

        oldest_cursor = self._conn.execute(
            "SELECT MIN(scan_timestamp) as oldest FROM scan_history"
        )
        oldest = (oldest_cursor.fetchone() or {"oldest": None})["oldest"]

        try:
            import os
            db_size_bytes = os.path.getsize(self._db_path)
        except OSError:
            db_size_bytes = 0

        return {
            "total_scans":    total,
            "oldest_record":  oldest,
            "retention_days": RETENTION_DAYS,
            "db_path":        self._db_path,
            "db_size_bytes":  db_size_bytes,
        }

    # ------------------------------------------------------------------
    # Retention enforcement
    # ------------------------------------------------------------------
    def purge_old_records(self) -> int:
        """Delete scan records older than RETENTION_DAYS (180 days).

        Returns:
            Number of scan records deleted.
        """
        assert self._conn is not None
        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
        ).timestamp()
        try:
            with self._conn:
                cursor = self._conn.execute(
                    "DELETE FROM scan_history WHERE epoch_ts < ?", (cutoff,)
                )
                deleted = cursor.rowcount
            if deleted:
                logger.info(
                    "Purged %d scan record(s) older than %d days (CERT-In mandate).",
                    deleted,
                    RETENTION_DAYS,
                )
            return deleted
        except sqlite3.Error as exc:
            logger.error("Purge failed: %s", exc)
            return 0

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------
    def __enter__(self) -> "LogRetentionDB":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
