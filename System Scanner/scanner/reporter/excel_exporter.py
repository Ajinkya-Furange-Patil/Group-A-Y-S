"""
AI Discovery Scanner — Excel Report Exporter

Generates a fully-formatted multi-sheet .xlsx workbook from a ScanResult.
Uses only Python standard-library (zipfile + xml) — no openpyxl required.

Sheets produced:
  1. Summary       — scan metadata, risk score, module results
  2. Findings      — one row per finding with all fields
  3. Risk Breakdown — 5-dimension scores
  4. By Category   — finding counts per category
  5. By Risk Level — finding counts per risk level

Usage:
    from scanner.reporter.excel_exporter import export_excel
    export_excel(scan_result, "ai_scan_report.xlsx")
"""

from __future__ import annotations

import io
import logging
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

from scanner.models import ScanResult

logger = logging.getLogger(__name__)

# ── XLSX shared-strings index (avoids duplicating string data) ────────────
_SST: list[str] = []
_SST_MAP: dict[str, int] = {}


def _si(text: str) -> int:
    """Return shared-string index for a cell string value."""
    if text not in _SST_MAP:
        _SST_MAP[text] = len(_SST)
        _SST.append(text)
    return _SST_MAP[text]


def _reset_sst() -> None:
    global _SST, _SST_MAP
    _SST = []
    _SST_MAP = {}


# ── Cell address helpers ──────────────────────────────────────────────────

def _col_letter(n: int) -> str:
    """Convert 0-based column index to Excel column letter (0→A, 25→Z, 26→AA)."""
    result = ""
    n += 1
    while n:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result


def _cell_ref(row: int, col: int) -> str:
    """Return Excel cell reference like A1 (both 0-based)."""
    return f"{_col_letter(col)}{row + 1}"


# ── Low-level cell builders ───────────────────────────────────────────────

def _cell_s(row: int, col: int, text: str, style: int = 0) -> ET.Element:
    """Shared-string cell."""
    c = ET.Element("c", r=_cell_ref(row, col), t="s", s=str(style))
    ET.SubElement(c, "v").text = str(_si(str(text)))
    return c


def _cell_n(row: int, col: int, value: float | int, style: int = 0) -> ET.Element:
    """Numeric cell."""
    c = ET.Element("c", r=_cell_ref(row, col), s=str(style))
    ET.SubElement(c, "v").text = str(value)
    return c


def _cell_inline(row: int, col: int, text: str, style: int = 0) -> ET.Element:
    """Inline string cell (used for long / special-char values)."""
    c = ET.Element("c", r=_cell_ref(row, col), t="inlineStr", s=str(style))
    is_ = ET.SubElement(c, "is")
    ET.SubElement(is_, "t").text = str(text)
    return c


# ── Sheet builder helpers ─────────────────────────────────────────────────

def _sheet_xml(rows_data: list[list[tuple[str, Any]]]) -> bytes:
    """
    Build a worksheet XML blob.

    rows_data: list of rows; each row is a list of (type, value) tuples.
      type: 's' = shared-string, 'n' = number, 'i' = inline-string,
            'h' = header (bold style=1), 'p' = percent number
    Returns UTF-8 bytes.
    """
    ws = ET.Element("worksheet",
                    xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main")
    sd = ET.SubElement(ws, "sheetData")

    for r_idx, row_cells in enumerate(rows_data):
        row_el = ET.SubElement(sd, "row", r=str(r_idx + 1))
        for c_idx, (ctype, val) in enumerate(row_cells):
            if val is None:
                val = ""
            if ctype == "h":
                row_el.append(_cell_s(r_idx, c_idx, str(val), style=1))
            elif ctype == "n":
                row_el.append(_cell_n(r_idx, c_idx, val, style=0))
            elif ctype == "p":
                row_el.append(_cell_n(r_idx, c_idx, round(float(val), 2), style=2))
            elif ctype == "i":
                row_el.append(_cell_inline(r_idx, c_idx, str(val), style=0))
            else:  # 's'
                row_el.append(_cell_s(r_idx, c_idx, str(val), style=0))

    tree = ET.ElementTree(ws)
    buf = io.BytesIO()
    tree.write(buf, xml_declaration=True, encoding="UTF-8")
    return buf.getvalue()


# ── Sheet data builders ───────────────────────────────────────────────────

def _build_summary_sheet(result_dict: dict) -> list[list[tuple]]:
    summary = result_dict.get("summary", {})
    rows = [
        [("h", "AI Discovery Scanner — Scan Summary Report")],
        [],
        [("h", "Field"), ("h", "Value")],
        [("s", "Scan ID"),          ("s", result_dict.get("scan_id", ""))],
        [("s", "Scan Timestamp"),   ("s", result_dict.get("scan_timestamp", ""))],
        [("s", "Hostname"),         ("s", result_dict.get("hostname", ""))],
        [("s", "Operating System"), ("s", result_dict.get("os_info", ""))],
        [("s", "Scan Duration (s)"),("n", round(result_dict.get("total_duration_sec", 0), 3))],
        [],
        [("h", "Summary Statistics"), ("h", "")],
        [("s", "Total Findings"),   ("n", summary.get("total_findings", 0))],
        [("s", "Overall Risk Score (0-100)"), ("n", summary.get("overall_risk_score", 0))],
        [("s", "Modules Run"),      ("n", summary.get("modules_run", 0))],
        [("s", "Modules Succeeded"),("n", summary.get("modules_succeeded", 0))],
        [("s", "Modules Failed"),   ("n", summary.get("modules_failed", 0))],
        [],
        [("h", "Module"), ("h", "Status"), ("h", "Duration (s)"), ("h", "Findings")],
    ]
    for mod in result_dict.get("modules", []):
        rows.append([
            ("s", mod.get("name", "")),
            ("s", mod.get("status", "")),
            ("n", round(mod.get("duration_sec", 0), 3)),
            ("n", mod.get("findings_count", 0)),
        ])
    return rows


def _build_findings_sheet(result_dict: dict) -> list[list[tuple]]:
    header = [("h", h) for h in [
        "Finding ID", "Module", "Title", "Description",
        "Category", "Risk Level", "Source", "Confidence %", "Timestamp"
    ]]
    rows = [header]
    for f in result_dict.get("findings", []):
        conf_pct = round(float(f.get("confidence", 0)) * 100, 1)
        rows.append([
            ("s", f.get("finding_id", "")),
            ("s", f.get("module_name", "")),
            ("s", f.get("title", "")),
            ("i", f.get("description", "")),
            ("s", f.get("category", "")),
            ("s", f.get("risk_level", "").upper()),
            ("i", f.get("source", "")),
            ("n", conf_pct),
            ("s", f.get("timestamp", "")),
        ])
    return rows


def _build_risk_breakdown_sheet(result_dict: dict) -> list[list[tuple]]:
    summary = result_dict.get("summary", {})
    risk_score = float(summary.get("overall_risk_score", 0))
    findings = result_dict.get("findings", [])
    total = max(len(findings), 1)

    by_risk = summary.get("findings_by_risk", {})
    critical = int(by_risk.get("critical", 0))
    high     = int(by_risk.get("high", 0))
    medium   = int(by_risk.get("medium", 0))

    by_cat = summary.get("findings_by_category", {})
    agents  = by_cat.get("AI Agent", 0)
    models  = by_cat.get("AI Model", 0)
    pkgs    = by_cat.get("ML Framework", 0)
    configs = by_cat.get("Configuration", 0)
    runtimes = sum(v for k, v in by_cat.items()
                   if k not in ("AI Agent","AI Model","ML Framework","Configuration","System Info"))

    sec_score  = min(max((critical * 100 + high * 75) // total, 0), 100)
    priv_score = min(max((configs * 85 + agents * 55) // total, 0), 100)
    comp_score = min(max(int(risk_score * 0.8), 0), 100)
    sup_score  = min(max((models * 60 + pkgs * 40) // total, 0), 100)
    ops_score  = min(max((runtimes * 50 + medium * 25) // total, 0), 100)

    rows = [
        [("h", "5-Dimension Risk Breakdown")],
        [],
        [("h", "Dimension"), ("h", "Weight"), ("h", "Score (0-100)"), ("h", "Level")],
    ]
    dims = [
        ("Security",     "25%", sec_score),
        ("Data Privacy", "25%", priv_score),
        ("Compliance",   "25%", comp_score),
        ("Supply Chain", "15%", sup_score),
        ("Operational",  "10%", ops_score),
    ]
    for name, weight, score in dims:
        level = "CRITICAL" if score >= 75 else "HIGH" if score >= 50 else "MEDIUM" if score >= 25 else "LOW"
        rows.append([("s", name), ("s", weight), ("n", score), ("s", level)])
    rows += [
        [],
        [("h", "Overall Risk Score"), ("n", round(risk_score, 1)), ("s", ""), ("s", "")],
    ]
    return rows


def _build_by_category_sheet(result_dict: dict) -> list[list[tuple]]:
    by_cat = result_dict.get("summary", {}).get("findings_by_category", {})
    rows = [
        [("h", "Category"), ("h", "Finding Count")],
    ]
    for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
        rows.append([("s", cat), ("n", count)])
    return rows


def _build_by_risk_sheet(result_dict: dict) -> list[list[tuple]]:
    by_risk = result_dict.get("summary", {}).get("findings_by_risk", {})
    order   = ["critical", "high", "medium", "low", "info"]
    rows    = [[("h", "Risk Level"), ("h", "Finding Count")]]
    for level in order:
        if level in by_risk:
            rows.append([("s", level.upper()), ("n", by_risk[level])])
    return rows


# ── XLSX static parts (styles, relationships, content-types) ─────────────

_STYLES_XML = b"""<?xml version='1.0' encoding='UTF-8'?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><sz val="11"/><name val="Calibri"/><b/></font>
  </fonts>
  <fills count="2">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
  </fills>
  <borders count="1">
    <border><left/><right/><top/><bottom/><diagonal/></border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="3">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="9" fontId="0" fillId="0" borderId="0" xfId="0"/>
  </cellXfs>
</styleSheet>"""

_WORKBOOK_RELS_XML = """<?xml version='1.0' encoding='UTF-8'?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet3.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet4.xml"/>
  <Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet5.xml"/>
  <Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
  <Relationship Id="rId7" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

_CONTENT_TYPES_XML = """<?xml version='1.0' encoding='UTF-8'?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml"               ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml"       ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml"       ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet3.xml"       ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet4.xml"       ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet5.xml"       ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/sharedStrings.xml"           ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
  <Override PartName="/xl/styles.xml"                  ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""

_RELS_XML = """<?xml version='1.0' encoding='UTF-8'?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""


def _workbook_xml(sheet_names: list[str]) -> bytes:
    wb = ET.Element("workbook",
                    xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main",
                    **{"xmlns:r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"})
    sheets_el = ET.SubElement(wb, "sheets")
    for i, name in enumerate(sheet_names, start=1):
        ET.SubElement(sheets_el, "sheet",
                      name=name, sheetId=str(i),
                      **{"r:id": f"rId{i}"})
    buf = io.BytesIO()
    ET.ElementTree(wb).write(buf, xml_declaration=True, encoding="UTF-8")
    return buf.getvalue()


def _shared_strings_xml() -> bytes:
    root = ET.Element(
        "sst",
        xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        count=str(len(_SST)),
        uniqueCount=str(len(_SST)),
    )
    for s in _SST:
        si = ET.SubElement(root, "si")
        t = ET.SubElement(si, "t")
        t.text = s
        # Preserve leading/trailing whitespace
        if s != s.strip():
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    buf = io.BytesIO()
    ET.ElementTree(root).write(buf, xml_declaration=True, encoding="UTF-8")
    return buf.getvalue()


# ── Public API ────────────────────────────────────────────────────────────

def export_excel(scan_result: ScanResult, output_path: str) -> None:
    """Write a multi-sheet .xlsx workbook for the given ScanResult.

    Produces 5 sheets:
      1. Summary        — scan metadata + module results
      2. Findings       — one row per finding
      3. Risk Breakdown — 5-dimension scores
      4. By Category    — findings grouped by category
      5. By Risk Level  — findings grouped by risk level

    No third-party dependencies required (stdlib zipfile + xml only).

    Args:
        scan_result:  Completed ScanResult from the controller.
        output_path:  Destination .xlsx file path.
    """
    _reset_sst()

    result_dict = scan_result.to_dict()

    sheet_defs = [
        ("Summary",        _build_summary_sheet(result_dict)),
        ("Findings",       _build_findings_sheet(result_dict)),
        ("Risk Breakdown", _build_risk_breakdown_sheet(result_dict)),
        ("By Category",    _build_by_category_sheet(result_dict)),
        ("By Risk Level",  _build_by_risk_sheet(result_dict)),
    ]

    # Build all sheet XMLs first (populates shared-string table)
    sheet_xmls = [_sheet_xml(rows) for _, rows in sheet_defs]
    sheet_names = [name for name, _ in sheet_defs]

    try:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml",  _CONTENT_TYPES_XML)
            zf.writestr("_rels/.rels",          _RELS_XML)
            zf.writestr("xl/workbook.xml",      _workbook_xml(sheet_names))
            zf.writestr("xl/styles.xml",        _STYLES_XML)
            zf.writestr("xl/_rels/workbook.xml.rels", _WORKBOOK_RELS_XML)

            for i, xml_bytes in enumerate(sheet_xmls, start=1):
                zf.writestr(f"xl/worksheets/sheet{i}.xml", xml_bytes)

            zf.writestr("xl/sharedStrings.xml", _shared_strings_xml())

        logger.info("Excel report written to: %s  (%d findings, %d sheets)",
                    output_path, result_dict["summary"].get("total_findings", 0),
                    len(sheet_defs))
    except OSError as exc:
        logger.error("Failed to write Excel report to %s: %s", output_path, exc)
        raise
