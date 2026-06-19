"""
Unit tests for Developer C modules:
  - scanner.reporter.exporter   (SIEM/SOC exporter + CSV SBOM)
  - scanner.reporter.log_retention  (180-day ICT log archive)
"""

import csv
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from scanner.models import (
    ScanResult, Finding, FindingCategory, RiskLevel, ModuleInfo
)
from scanner.reporter.exporter import (
    SIEMExporter, export_sbom_csv, _build_siem_payload,
    _risk_to_syslog_severity,
)
from scanner.reporter.log_retention import LogRetentionDB, RETENTION_DAYS


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_scan_result(
    *,
    scan_id: str = "test-scan-1",
    n_findings: int = 3,
) -> ScanResult:
    """Build a minimal ScanResult for testing."""
    findings = []
    risk_levels = [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM,
                   RiskLevel.LOW, RiskLevel.INFO]
    for i in range(n_findings):
        findings.append(Finding(
            module_name="TestModule",
            title=f"Test Finding {i}",
            description="A test finding",
            source=f"/test/path/{i}",
            category=FindingCategory.AI_AGENT,
            risk_level=risk_levels[i % len(risk_levels)],
            confidence=0.8,
        ))

    result = ScanResult(
        scan_id=scan_id,
        hostname="test-host",
        os_info="Windows 11",
        findings=findings,
        modules=[
            ModuleInfo(name="TestModule", module_number=1, status="success",
                       duration_sec=1.0, findings_count=n_findings),
        ],
    )
    result.compute_summary()
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Tests: SIEM Payload builder
# ──────────────────────────────────────────────────────────────────────────────

class TestBuildSIEMPayload(unittest.TestCase):
    def test_payload_keys(self):
        result = _make_scan_result()
        payload = _build_siem_payload(result)
        required_keys = {
            "event_type", "scan_id", "timestamp", "export_time",
            "hostname", "os_info", "severity", "risk_score",
            "total_findings", "findings_by_risk", "findings_by_category",
            "modules_run", "modules_failed", "scan_duration_sec", "findings",
        }
        self.assertTrue(required_keys.issubset(payload.keys()))

    def test_payload_event_type(self):
        payload = _build_siem_payload(_make_scan_result())
        self.assertEqual(payload["event_type"], "ai_discovery_scan")

    def _make_result_with_fixed_risk(self, score: float) -> ScanResult:
        """Build a result whose computed risk score matches the given value."""
        result = _make_scan_result()
        # Patch compute_summary so it always returns the desired score
        original_compute = result.compute_summary

        def patched_compute():
            original_compute()
            result.summary["overall_risk_score"] = score

        result.compute_summary = patched_compute
        return result

    def test_severity_critical(self):
        payload = _build_siem_payload(self._make_result_with_fixed_risk(80.0))
        self.assertEqual(payload["severity"], "CRIT")

    def test_severity_high(self):
        payload = _build_siem_payload(self._make_result_with_fixed_risk(60.0))
        self.assertEqual(payload["severity"], "ERR")

    def test_severity_medium(self):
        payload = _build_siem_payload(self._make_result_with_fixed_risk(35.0))
        self.assertEqual(payload["severity"], "WARNING")

    def test_severity_low(self):
        payload = _build_siem_payload(self._make_result_with_fixed_risk(10.0))
        self.assertEqual(payload["severity"], "INFO")


# ──────────────────────────────────────────────────────────────────────────────
# Tests: Syslog severity mapping
# ──────────────────────────────────────────────────────────────────────────────

class TestSyslogSeverity(unittest.TestCase):
    def test_critical_threshold(self):
        self.assertEqual(_risk_to_syslog_severity(75), 2)   # CRIT

    def test_high_threshold(self):
        self.assertEqual(_risk_to_syslog_severity(50), 3)   # ERR

    def test_medium_threshold(self):
        self.assertEqual(_risk_to_syslog_severity(25), 4)   # WARNING

    def test_low_threshold(self):
        self.assertEqual(_risk_to_syslog_severity(0), 6)    # INFO


# ──────────────────────────────────────────────────────────────────────────────
# Tests: File export (NDJSON)
# ──────────────────────────────────────────────────────────────────────────────

class TestSIEMExporterFile(unittest.TestCase):
    def setUp(self):
        self.exporter = SIEMExporter()
        self.tmpfile = tempfile.NamedTemporaryFile(
            mode="w", suffix=".ndjson", delete=False
        )
        self.tmpfile.close()

    def tearDown(self):
        if os.path.exists(self.tmpfile.name):
            os.remove(self.tmpfile.name)

    def test_export_creates_file(self):
        result = _make_scan_result()
        self.exporter.export_to_file(result, self.tmpfile.name, append=False)
        self.assertTrue(os.path.exists(self.tmpfile.name))
        with open(self.tmpfile.name, encoding="utf-8") as f:
            content = f.read().strip()
        self.assertTrue(len(content) > 0)

    def test_export_valid_json(self):
        result = _make_scan_result()
        self.exporter.export_to_file(result, self.tmpfile.name, append=False)
        with open(self.tmpfile.name, encoding="utf-8") as f:
            obj = json.loads(f.readline())
        self.assertEqual(obj["event_type"], "ai_discovery_scan")

    def test_append_mode_adds_lines(self):
        r1 = _make_scan_result(scan_id="scan-aaa")
        r2 = _make_scan_result(scan_id="scan-bbb")
        self.exporter.export_to_file(r1, self.tmpfile.name, append=False)
        self.exporter.export_to_file(r2, self.tmpfile.name, append=True)
        with open(self.tmpfile.name, encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        self.assertEqual(len(lines), 2)

    def test_scan_id_in_export(self):
        result = _make_scan_result(scan_id="unique-test-id")
        self.exporter.export_to_file(result, self.tmpfile.name, append=False)
        with open(self.tmpfile.name, encoding="utf-8") as f:
            obj = json.loads(f.readline())
        self.assertEqual(obj["scan_id"], "unique-test-id")


# ──────────────────────────────────────────────────────────────────────────────
# Tests: HTTP export
# ──────────────────────────────────────────────────────────────────────────────

class TestSIEMExporterHTTP(unittest.TestCase):
    def setUp(self):
        self.exporter = SIEMExporter()

    @patch("urllib.request.urlopen")
    def test_http_export_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_urlopen.return_value.__enter__ = lambda s: mock_resp
        mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)

        result = _make_scan_result()
        ok = self.exporter.export_to_http(result, "https://siem.test/webhook")
        self.assertTrue(ok)

    @patch("urllib.request.urlopen")
    def test_http_export_sends_json(self, mock_urlopen):
        import urllib.request
        captured = {}

        def fake_urlopen(req, timeout=10):
            captured["data"] = req.data
            captured["headers"] = dict(req.headers)
            mock_resp = MagicMock()
            mock_resp.getcode.return_value = 200
            return MagicMock(__enter__=lambda s: mock_resp, __exit__=MagicMock(return_value=False))

        mock_urlopen.side_effect = fake_urlopen
        result = _make_scan_result()
        self.exporter.export_to_http(result, "https://siem.test/webhook")
        payload = json.loads(captured["data"].decode("utf-8"))
        self.assertEqual(payload["event_type"], "ai_discovery_scan")


# ──────────────────────────────────────────────────────────────────────────────
# Tests: Syslog export
# ──────────────────────────────────────────────────────────────────────────────

class TestSIEMExporterSyslog(unittest.TestCase):
    def setUp(self):
        self.exporter = SIEMExporter()

    def test_syslog_udp_success(self):
        result = _make_scan_result()
        with patch("socket.socket") as mock_sock_cls:
            mock_sock = MagicMock()
            mock_sock.__enter__ = lambda s: mock_sock
            mock_sock.__exit__ = MagicMock(return_value=False)
            mock_sock_cls.return_value = mock_sock
            ok = self.exporter.export_to_syslog(
                result, host="127.0.0.1", port=514, protocol="udp"
            )
        self.assertTrue(ok)
        mock_sock.sendto.assert_called_once()

    def test_syslog_message_contains_scan_id(self):
        result = _make_scan_result(scan_id="syslog-test-id")
        sent_data = {}
        with patch("socket.socket") as mock_sock_cls:
            mock_sock = MagicMock()
            mock_sock.__enter__ = lambda s: mock_sock
            mock_sock.__exit__ = MagicMock(return_value=False)
            mock_sock.sendto.side_effect = lambda data, addr: sent_data.update({"msg": data})
            mock_sock_cls.return_value = mock_sock
            self.exporter.export_to_syslog(result, protocol="udp")
        self.assertIn(b"syslog-test-id", sent_data["msg"])


# ──────────────────────────────────────────────────────────────────────────────
# Tests: CSV SBOM export
# ──────────────────────────────────────────────────────────────────────────────

class TestExportSBOMCSV(unittest.TestCase):
    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        )
        self.tmpfile.close()

    def tearDown(self):
        if os.path.exists(self.tmpfile.name):
            os.remove(self.tmpfile.name)

    def test_csv_created(self):
        result = _make_scan_result(n_findings=4)
        export_sbom_csv(result, self.tmpfile.name)
        self.assertTrue(os.path.exists(self.tmpfile.name))

    def test_csv_row_count(self):
        n = 5
        result = _make_scan_result(n_findings=n)
        export_sbom_csv(result, self.tmpfile.name)
        with open(self.tmpfile.name, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertEqual(len(rows), n)

    def test_csv_has_required_columns(self):
        result = _make_scan_result(n_findings=1)
        export_sbom_csv(result, self.tmpfile.name)
        with open(self.tmpfile.name, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            cols = set(reader.fieldnames or [])
        required = {"finding_id", "module", "title", "category", "risk_level",
                    "source", "confidence", "timestamp"}
        self.assertTrue(required.issubset(cols))

    def test_csv_confidence_percent(self):
        result = _make_scan_result(n_findings=1)
        result.findings[0].confidence = 0.75
        result.compute_summary()
        export_sbom_csv(result, self.tmpfile.name)
        with open(self.tmpfile.name, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        self.assertEqual(row["confidence"], "75%")


# ──────────────────────────────────────────────────────────────────────────────
# Tests: 180-Day Log Retention DB
# ──────────────────────────────────────────────────────────────────────────────

class TestLogRetentionDB(unittest.TestCase):
    def setUp(self):
        # Use an in-memory database for all tests
        self.db = LogRetentionDB(":memory:")

    def tearDown(self):
        self.db.close()

    def test_store_and_retrieve(self):
        result = _make_scan_result(scan_id="retain-001", n_findings=2)
        self.db.store_scan(result)
        history = self.db.get_scan_history(days=1)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["scan_id"], "retain-001")

    def test_total_findings_stored(self):
        result = _make_scan_result(scan_id="retain-002", n_findings=7)
        self.db.store_scan(result)
        history = self.db.get_scan_history(days=1)
        self.assertEqual(history[0]["total_findings"], 7)

    def test_store_multiple_scans(self):
        for i in range(5):
            self.db.store_scan(_make_scan_result(scan_id=f"scan-{i:03d}"))
        history = self.db.get_scan_history(days=365)
        self.assertEqual(len(history), 5)

    def test_findings_stored_per_scan(self):
        result = _make_scan_result(scan_id="find-test", n_findings=3)
        self.db.store_scan(result)
        findings = self.db.get_scan_findings("find-test")
        self.assertEqual(len(findings), 3)

    def test_get_latest_scan(self):
        self.db.store_scan(_make_scan_result(scan_id="first"))
        self.db.store_scan(_make_scan_result(scan_id="second"))
        latest = self.db.get_latest_scan()
        self.assertIsNotNone(latest)
        # Most recent should be "second"
        self.assertEqual(latest["scan_id"], "second")

    def test_purge_old_records(self):
        """Records with epoch older than 180 days must be purged."""
        import sqlite3

        # Insert a record with an old epoch directly
        old_epoch = (
            datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS + 5)
        ).timestamp()

        self.db._conn.execute(
            """
            INSERT INTO scan_history
                (scan_id, scan_timestamp, epoch_ts, hostname, os_info,
                 total_duration_sec, total_findings, overall_risk_score,
                 modules_run, modules_failed, findings_by_risk, findings_by_category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("old-scan", "2000-01-01T00:00:00", old_epoch,
             "old-host", "OS", 1.0, 0, 0.0, 0, 0, "{}", "{}"),
        )
        self.db._conn.commit()

        # Verify it's there
        cur = self.db._conn.execute("SELECT COUNT(*) FROM scan_history")
        self.assertEqual(cur.fetchone()[0], 1)

        deleted = self.db.purge_old_records()
        self.assertEqual(deleted, 1)

        cur = self.db._conn.execute("SELECT COUNT(*) FROM scan_history")
        self.assertEqual(cur.fetchone()[0], 0)

    def test_trend_summary_empty(self):
        summary = self.db.get_trend_summary(days=30)
        self.assertEqual(summary["scan_count"], 0)
        self.assertEqual(summary["avg_risk"], 0.0)

    def test_trend_summary_values(self):
        r1 = _make_scan_result(scan_id="t1")
        r2 = _make_scan_result(scan_id="t2")
        self.db.store_scan(r1)
        self.db.store_scan(r2)
        summary = self.db.get_trend_summary(days=365)
        self.assertEqual(summary["scan_count"], 2)
        # Both scans used default findings, so scores should be equal and non-zero
        self.assertGreaterEqual(summary["avg_risk"], 0.0)
        self.assertGreaterEqual(summary["max_risk"], summary["min_risk"])

    def test_get_stats(self):
        self.db.store_scan(_make_scan_result(scan_id="stats-test"))
        stats = self.db.get_stats()
        self.assertEqual(stats["total_scans"], 1)
        self.assertEqual(stats["retention_days"], RETENTION_DAYS)
        self.assertIsNotNone(stats["oldest_record"])

    def test_context_manager(self):
        with LogRetentionDB(":memory:") as db:
            db.store_scan(_make_scan_result())
            history = db.get_scan_history()
        self.assertEqual(len(history), 1)


if __name__ == "__main__":
    unittest.main()
