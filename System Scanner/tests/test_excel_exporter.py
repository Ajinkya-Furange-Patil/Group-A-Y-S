"""
Unit tests for scanner.reporter.excel_exporter
"""

import os
import tempfile
import unittest
import zipfile

from scanner.models import (
    ScanResult, Finding, FindingCategory, RiskLevel, ModuleInfo
)
from scanner.reporter.excel_exporter import export_excel


def _make_result(n_findings: int = 4, scan_id: str = "xl-test-001") -> ScanResult:
    risk_levels = [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW, RiskLevel.INFO]
    categories  = [FindingCategory.AI_AGENT, FindingCategory.AI_MODEL,
                   FindingCategory.CONFIGURATION, FindingCategory.ML_FRAMEWORK]
    findings = [
        Finding(
            module_name=["AgentScanner","FileScanner","APIScanner","PackageScanner"][i % 4],
            title=f"Finding {i}",
            description=f"Description for finding {i} with <special> & chars",
            source=f"/path/to/file_{i}",
            category=categories[i % len(categories)],
            risk_level=risk_levels[i % len(risk_levels)],
            confidence=round(0.5 + i * 0.1, 2),
        )
        for i in range(n_findings)
    ]
    modules = [
        ModuleInfo(name="AgentScanner",  module_number=5, status="success", duration_sec=1.1, findings_count=1),
        ModuleInfo(name="FileScanner",   module_number=2, status="success", duration_sec=2.2, findings_count=1),
        ModuleInfo(name="APIScanner",    module_number=7, status="error",   duration_sec=0.5, findings_count=0),
        ModuleInfo(name="PackageScanner",module_number=4, status="success", duration_sec=0.9, findings_count=1),
    ]
    r = ScanResult(
        scan_id=scan_id,
        hostname="test-host",
        os_info="Windows 11 x64",
        findings=findings,
        modules=modules,
    )
    r.total_duration_sec = 4.7
    r.compute_summary()
    return r


class TestExportExcel(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        self.tmp.close()
        self.path = self.tmp.name

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    # ── File creation ─────────────────────────────────────────────────────

    def test_file_created(self):
        export_excel(_make_result(), self.path)
        self.assertTrue(os.path.exists(self.path))
        self.assertGreater(os.path.getsize(self.path), 0)

    def test_valid_zip(self):
        """An .xlsx must be a valid ZIP archive."""
        export_excel(_make_result(), self.path)
        self.assertTrue(zipfile.is_zipfile(self.path))

    # ── Required ZIP members ──────────────────────────────────────────────

    def test_required_zip_members(self):
        export_excel(_make_result(), self.path)
        with zipfile.ZipFile(self.path) as zf:
            names = zf.namelist()
        required = {
            "[Content_Types].xml",
            "_rels/.rels",
            "xl/workbook.xml",
            "xl/styles.xml",
            "xl/sharedStrings.xml",
            "xl/_rels/workbook.xml.rels",
            "xl/worksheets/sheet1.xml",
            "xl/worksheets/sheet2.xml",
            "xl/worksheets/sheet3.xml",
            "xl/worksheets/sheet4.xml",
            "xl/worksheets/sheet5.xml",
        }
        for member in required:
            self.assertIn(member, names, f"Missing: {member}")

    def test_five_sheets(self):
        export_excel(_make_result(), self.path)
        with zipfile.ZipFile(self.path) as zf:
            sheets = [n for n in zf.namelist() if n.startswith("xl/worksheets/sheet")]
        self.assertEqual(len(sheets), 5)

    # ── Content checks ────────────────────────────────────────────────────

    def test_workbook_xml_contains_sheet_names(self):
        export_excel(_make_result(), self.path)
        with zipfile.ZipFile(self.path) as zf:
            wb = zf.read("xl/workbook.xml").decode("utf-8")
        for name in ["Summary", "Findings", "Risk Breakdown", "By Category", "By Risk Level"]:
            self.assertIn(name, wb, f"Sheet name missing from workbook.xml: {name}")

    def test_shared_strings_contains_scan_id(self):
        r = _make_result(scan_id="sst-check-99")
        export_excel(r, self.path)
        with zipfile.ZipFile(self.path) as zf:
            sst = zf.read("xl/sharedStrings.xml").decode("utf-8")
        self.assertIn("sst-check-99", sst)

    def test_shared_strings_contains_hostname(self):
        export_excel(_make_result(), self.path)
        with zipfile.ZipFile(self.path) as zf:
            sst = zf.read("xl/sharedStrings.xml").decode("utf-8")
        self.assertIn("test-host", sst)

    def test_findings_sheet_has_all_rows(self):
        """Sheet2 (Findings) should have header + n_findings rows."""
        n = 6
        export_excel(_make_result(n_findings=n), self.path)
        with zipfile.ZipFile(self.path) as zf:
            sheet2 = zf.read("xl/worksheets/sheet2.xml").decode("utf-8")
        # Count <row> elements — header + n data rows = n+1
        row_count = sheet2.count('<row r=')
        self.assertEqual(row_count, n + 1)

    def test_xml_escaping_in_description(self):
        """Special XML chars in description must be escaped, not break XML."""
        export_excel(_make_result(), self.path)
        with zipfile.ZipFile(self.path) as zf:
            sheet2 = zf.read("xl/worksheets/sheet2.xml").decode("utf-8")
        # If escaping works the file is valid XML — just verify no raw < inside cell values
        # (our inline strings should use &lt;)
        import xml.etree.ElementTree as ET
        ET.fromstring(sheet2)   # raises if malformed

    def test_zero_findings(self):
        """Should produce a valid file even with no findings."""
        r = _make_result(n_findings=0)
        export_excel(r, self.path)
        self.assertTrue(zipfile.is_zipfile(self.path))

    def test_content_types_xml(self):
        export_excel(_make_result(), self.path)
        with zipfile.ZipFile(self.path) as zf:
            ct = zf.read("[Content_Types].xml").decode("utf-8")
        self.assertIn("spreadsheetml.sheet.main", ct)
        self.assertIn("spreadsheetml.worksheet", ct)
        self.assertIn("spreadsheetml.sharedStrings", ct)

    def test_styles_xml_has_bold_font(self):
        export_excel(_make_result(), self.path)
        with zipfile.ZipFile(self.path) as zf:
            styles = zf.read("xl/styles.xml").decode("utf-8")
        self.assertIn("<b/>", styles)

    # ── CLI integration ───────────────────────────────────────────────────

    def test_export_excel_importable_from_reporter(self):
        from scanner.reporter import export_excel as ee
        self.assertIsNotNone(ee)

    def test_multiple_exports_independent_sst(self):
        """Each call to export_excel must reset the shared-string table."""
        r1 = _make_result(scan_id="r1", n_findings=2)
        r2 = _make_result(scan_id="r2", n_findings=3)

        p2 = self.path.replace(".xlsx", "_2.xlsx")
        try:
            export_excel(r1, self.path)
            export_excel(r2, p2)
            # Both should be valid ZIPs
            self.assertTrue(zipfile.is_zipfile(self.path))
            self.assertTrue(zipfile.is_zipfile(p2))
            # r2 scan_id must NOT appear in r1's SST
            with zipfile.ZipFile(self.path) as zf:
                sst1 = zf.read("xl/sharedStrings.xml").decode("utf-8")
            self.assertNotIn("r2", sst1)
        finally:
            if os.path.exists(p2):
                os.remove(p2)


if __name__ == "__main__":
    unittest.main()
