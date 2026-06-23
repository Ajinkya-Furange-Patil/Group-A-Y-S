"""
AI Discovery Scanner — Excel Report Exporter

Generates a fully-formatted multi-sheet .xlsx workbook from a ScanResult.
Uses only Python standard-library (zipfile + xml) — no openpyxl required.

Sheets produced:
  1. SBOM Report   — Software Bill of Materials findings
  2. CBOM Report   — Configuration Bill of Materials findings
  3. AI BOM Report — AI Bill of Materials findings

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

def _sheet_xml(rows_data: list[list[tuple]], col_widths: list[int] = None) -> bytes:
    """
    Build a worksheet XML blob.

    rows_data: list of rows; each row is a list of tuples representing cells.
      tuple format: (ctype, value) or (ctype, value, style_index)
      ctype: 's' = shared-string, 'n' = number, 'i' = inline-string,
             'h' = header, 'p' = percent number
    Returns UTF-8 bytes.
    """
    ws = ET.Element("worksheet",
                    xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main")
    
    if col_widths:
        cols_el = ET.SubElement(ws, "cols")
        for i, w in enumerate(col_widths):
            ET.SubElement(cols_el, "col", min=str(i + 1), max=str(i + 1), width=str(w), customWidth="1")

    sd = ET.SubElement(ws, "sheetData")

    for r_idx, row_cells in enumerate(rows_data):
        row_el = ET.SubElement(sd, "row", r=str(r_idx + 1))
        for c_idx, cell_data in enumerate(row_cells):
            ctype = cell_data[0]
            val = cell_data[1]
            style = cell_data[2] if len(cell_data) > 2 else None

            if val is None:
                val = ""
            
            if ctype == "h":
                row_el.append(_cell_s(r_idx, c_idx, str(val), style=style if style is not None else 1))
            elif ctype == "n":
                row_el.append(_cell_n(r_idx, c_idx, val, style=style if style is not None else 0))
            elif ctype == "p":
                row_el.append(_cell_n(r_idx, c_idx, round(float(val), 2), style=style if style is not None else 12))
            elif ctype == "i":
                row_el.append(_cell_inline(r_idx, c_idx, str(val), style=style if style is not None else 0))
            else:  # 's'
                row_el.append(_cell_s(r_idx, c_idx, str(val), style=style if style is not None else 0))

    tree = ET.ElementTree(ws)
    buf = io.BytesIO()
    tree.write(buf, xml_declaration=True, encoding="UTF-8")
    return buf.getvalue()


# ── Sheet data builders ───────────────────────────────────────────────────

def _build_summary_sheet(result_dict: dict) -> list[list[tuple]]:
    summary = result_dict.get("summary", {})
    rows = [
        [("s", f"AI Discovery Scanner — Scan Summary Report (v{result_dict.get('version', '1.1.0')})", 2)],
        [],
        [("h", "Field", 1), ("h", "Value", 1)],
        [("s", "Scan ID", 9),          ("s", result_dict.get("scan_id", ""), 0)],
        [("s", "Scan Timestamp", 9),   ("s", result_dict.get("scan_timestamp", ""), 0)],
        [("s", "Hostname", 9),         ("s", result_dict.get("hostname", ""), 0)],
        [("s", "Operating System", 9), ("s", result_dict.get("os_info", ""), 0)],
        [("s", "Scan Duration (s)", 9),("n", round(result_dict.get("total_duration_sec", 0), 3), 10)],
        [],
        [("s", "Summary Statistics", 3), ("s", "", 3)],
        [("s", "Total Findings", 9),   ("n", summary.get("total_findings", 0), 10)],
        [("s", "Overall Risk Score (0-100)", 9), ("n", summary.get("overall_risk_score", 0), 10)],
        [("s", "Modules Run", 9),      ("n", summary.get("modules_run", 0), 10)],
        [("s", "Modules Succeeded", 9),("n", summary.get("modules_succeeded", 0), 10)],
        [("s", "Modules Failed", 9),   ("n", summary.get("modules_failed", 0), 10)],
        [],
        [("h", "Module", 1), ("h", "Status", 1), ("h", "Duration (s)", 1), ("h", "Findings", 1)],
    ]
    for idx, mod in enumerate(result_dict.get("modules", [])):
        is_even = idx % 2 == 0
        rows.append([
            ("s", mod.get("name", ""), 0 if is_even else 4),
            ("s", mod.get("status", ""), 10 if is_even else 11),
            ("n", round(mod.get("duration_sec", 0), 3), 10 if is_even else 11),
            ("n", mod.get("findings_count", 0), 10 if is_even else 11),
        ])
    return rows


def _build_diagnostics_sheet(result_dict: dict) -> list[list[tuple]]:
    header = [("h", h, 1) for h in [
        "Diagnostic Check", "Value / Output", "Status", "Timestamp"
    ]]
    rows = [header]
    for idx, diag in enumerate(result_dict.get("diagnostics", [])):
        is_even = idx % 2 == 0
        status = diag.get("status", "PASS").upper()
        
        status_style = 10 if is_even else 11
        if status == "FAIL":
            status_style = 5
        elif status == "WARNING":
            status_style = 6
        elif status == "PASS":
            status_style = 8
            
        rows.append([
            ("s", diag.get("name", ""), 0 if is_even else 4),
            ("s", diag.get("value", ""), 0 if is_even else 4),
            ("s", status, status_style),
            ("s", diag.get("timestamp", ""), 10 if is_even else 11),
        ])
    return rows


def _build_findings_sheet(result_dict: dict) -> list[list[tuple]]:
    header = [("h", h, 1) for h in [
        "Finding ID", "Module", "Title", "Description",
        "Category", "Risk Level", "Source", "Confidence %", "Timestamp"
    ]]
    rows = [header]
    for idx, f in enumerate(result_dict.get("findings", [])):
        is_even = idx % 2 == 0
        rl = f.get("risk_level", "").lower()
        
        risk_style = 10 if is_even else 11
        if rl == "critical":
            risk_style = 5
        elif rl == "high":
            risk_style = 6
        elif rl == "medium":
            risk_style = 7
        elif rl in ("low", "info"):
            risk_style = 8

        conf_pct = round(float(f.get("confidence", 0)) * 100, 1)
        rows.append([
            ("s", f.get("finding_id", ""), 10 if is_even else 11),
            ("s", f.get("module_name", ""), 0 if is_even else 4),
            ("s", f.get("title", ""), 0 if is_even else 4),
            ("i", f.get("description", ""), 14 if is_even else 15),
            ("s", f.get("category", ""), 10 if is_even else 11),
            ("s", f.get("risk_level", "").upper(), risk_style),
            ("i", f.get("source", ""), 14 if is_even else 15),
            ("n", conf_pct, 10 if is_even else 11),
            ("s", f.get("timestamp", ""), 10 if is_even else 11),
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

    def get_level_style(score: int) -> int:
        if score >= 75:
            return 5
        elif score >= 50:
            return 6
        elif score >= 25:
            return 7
        return 8

    dim_level = lambda s: "CRITICAL" if s>=75 else "HIGH" if s>=50 else "MEDIUM" if s>=25 else "LOW"

    rows = [
        [("s", "5-Dimension Risk Breakdown", 2)],
        [],
        [("h", "Dimension", 1), ("h", "Weight", 1), ("h", "Score (0-100)", 1), ("h", "Level", 1)],
        [("s", "Security", 0),      ("s", "25%", 10),("n", sec_score, 10), ("s", dim_level(sec_score), get_level_style(sec_score))],
        [("s", "Data Privacy", 4),  ("s", "25%", 11),("n", priv_score, 11),("s", dim_level(priv_score), get_level_style(priv_score))],
        [("s", "Compliance", 0),    ("s", "25%", 10),("n", comp_score, 10),("s", dim_level(comp_score), get_level_style(comp_score))],
        [("s", "Supply Chain", 4),  ("s", "15%", 11),("n", sup_score, 11), ("s", dim_level(sup_score), get_level_style(sup_score))],
        [("s", "Operational", 0),   ("s", "10%", 10),("n", ops_score, 10), ("s", dim_level(ops_score), get_level_style(ops_score))],
        [],
        [("s", "Overall Risk Score", 9), ("n", round(risk_score, 1), 10), ("s", "", 0), ("s", "", 0)],
    ]
    return rows


def _build_by_category_sheet(result_dict: dict) -> list[list[tuple]]:
    by_cat = result_dict.get("summary", {}).get("findings_by_category", {})
    rows = [
        [("h", "Category", 1), ("h", "Finding Count", 1)],
    ]
    for idx, (cat, count) in enumerate(sorted(by_cat.items(), key=lambda x: -x[1])):
        is_even = idx % 2 == 0
        rows.append([
            ("s", cat, 0 if is_even else 4),
            ("n", count, 10 if is_even else 11)
        ])
    return rows


def _build_by_risk_sheet(result_dict: dict) -> list[list[tuple]]:
    by_risk = result_dict.get("summary", {}).get("findings_by_risk", {})
    order   = ["critical", "high", "medium", "low", "info"]
    rows    = [[("h", "Risk Level", 1), ("h", "Finding Count", 1)]]
    
    def get_risk_style(lvl: str) -> int:
        l = lvl.lower()
        if l == "critical": return 5
        if l == "high": return 6
        if l == "medium": return 7
        return 8

    for idx, level in enumerate(order):
        if level in by_risk:
            is_even = idx % 2 == 0
            rows.append([
                ("s", level.upper(), get_risk_style(level)),
                ("n", by_risk[level], 10 if is_even else 11)
            ])
    return rows


def _build_cbom_sheet(result_dict: dict) -> list[list[tuple]]:
    header = [("h", h, 1) for h in [
        "Finding ID", "Module", "Setting Name", "Description",
        "Value / Source", "Risk Level", "Confidence %", "Timestamp"
    ]]
    rows = [header]
    
    cbom_cats = ("Configuration", "System Info")
    findings = [f for f in result_dict.get("findings", []) if f.get("category") in cbom_cats]
    
    for idx, f in enumerate(findings):
        is_even = idx % 2 == 0
        rl = f.get("risk_level", "").lower()
        
        risk_style = 10 if is_even else 11
        if rl == "critical":
            risk_style = 5
        elif rl == "high":
            risk_style = 6
        elif rl == "medium":
            risk_style = 7
        elif rl in ("low", "info"):
            risk_style = 8

        conf_pct = round(float(f.get("confidence", 0)) * 100, 1)
        rows.append([
            ("s", f.get("finding_id", ""), 10 if is_even else 11),
            ("s", f.get("module_name", ""), 0 if is_even else 4),
            ("s", f.get("title", ""), 0 if is_even else 4),
            ("i", f.get("description", ""), 14 if is_even else 15),
            ("i", f.get("source", ""), 14 if is_even else 15),
            ("s", f.get("risk_level", "").upper(), risk_style),
            ("n", conf_pct, 10 if is_even else 11),
            ("s", f.get("timestamp", ""), 10 if is_even else 11),
        ])
    return rows


def _build_sbom_sheet(result_dict: dict) -> list[list[tuple]]:
    header = [("h", h, 1) for h in [
        "Finding ID", "Module", "Package / Library", "Description",
        "Location / Source", "Risk Level", "Confidence %", "Timestamp"
    ]]
    rows = [header]
    
    sbom_cats = ("ML Framework", "AI Service")
    findings = [f for f in result_dict.get("findings", []) if f.get("category") in sbom_cats]
    
    for idx, f in enumerate(findings):
        is_even = idx % 2 == 0
        rl = f.get("risk_level", "").lower()
        
        risk_style = 10 if is_even else 11
        if rl == "critical":
            risk_style = 5
        elif rl == "high":
            risk_style = 6
        elif rl == "medium":
            risk_style = 7
        elif rl in ("low", "info"):
            risk_style = 8

        conf_pct = round(float(f.get("confidence", 0)) * 100, 1)
        rows.append([
            ("s", f.get("finding_id", ""), 10 if is_even else 11),
            ("s", f.get("module_name", ""), 0 if is_even else 4),
            ("s", f.get("title", ""), 0 if is_even else 4),
            ("i", f.get("description", ""), 14 if is_even else 15),
            ("i", f.get("source", ""), 14 if is_even else 15),
            ("s", f.get("risk_level", "").upper(), risk_style),
            ("n", conf_pct, 10 if is_even else 11),
            ("s", f.get("timestamp", ""), 10 if is_even else 11),
        ])
    return rows


def _build_aibom_sheet(result_dict: dict) -> list[list[tuple]]:
    header = [("h", h, 1) for h in [
        "Finding ID", "Module", "AI Model / Agent / Runtime", "Description",
        "Type (Category)", "Location / Endpoint", "Risk Level", "Confidence %", "Timestamp"
    ]]
    rows = [header]
    
    aibom_cats = ("AI Model", "AI Agent", "LLM Runtime")
    findings = [f for f in result_dict.get("findings", []) if f.get("category") in aibom_cats]
    
    for idx, f in enumerate(findings):
        is_even = idx % 2 == 0
        rl = f.get("risk_level", "").lower()
        
        risk_style = 10 if is_even else 11
        if rl == "critical":
            risk_style = 5
        elif rl == "high":
            risk_style = 6
        elif rl == "medium":
            risk_style = 7
        elif rl in ("low", "info"):
            risk_style = 8

        conf_pct = round(float(f.get("confidence", 0)) * 100, 1)
        rows.append([
            ("s", f.get("finding_id", ""), 10 if is_even else 11),
            ("s", f.get("module_name", ""), 0 if is_even else 4),
            ("s", f.get("title", ""), 0 if is_even else 4),
            ("i", f.get("description", ""), 14 if is_even else 15),
            ("s", f.get("category", ""), 10 if is_even else 11),
            ("i", f.get("source", ""), 14 if is_even else 15),
            ("s", f.get("risk_level", "").upper(), risk_style),
            ("n", conf_pct, 10 if is_even else 11),
            ("s", f.get("timestamp", ""), 10 if is_even else 11),
        ])
    return rows


# ── XLSX static parts (styles, relationships, content-types) ─────────────

_STYLES_XML = b"""<?xml version='1.0' encoding='UTF-8'?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="8">
    <font><sz val="11"/><name val="Calibri"/><color rgb="FF000000"/></font>
    <font><b/><sz val="11"/><name val="Calibri"/><color rgb="FFFFFFFF"/></font>
    <font><b/><sz val="16"/><name val="Calibri"/><color rgb="FF1F4E79"/></font>
    <font><b/><sz val="11"/><name val="Calibri"/><color rgb="FF1F4E79"/></font>
    <font><b/><sz val="11"/><name val="Calibri"/><color rgb="FFC00000"/></font>
    <font><b/><sz val="11"/><name val="Calibri"/><color rgb="FFE36C0A"/></font>
    <font><b/><sz val="11"/><name val="Calibri"/><color rgb="FFB25E00"/></font>
    <font><b/><sz val="11"/><name val="Calibri"/><color rgb="FF385723"/></font>
  </fonts>
  <fills count="9">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF1F4E79"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFF2F2F2"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFCE4D6"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFF2CC"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFFFC4"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFE2EFDA"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFDDEBF7"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>
      <left style="thin"><color rgb="FFD9D9D9"/></left>
      <right style="thin"><color rgb="FFD9D9D9"/></right>
      <top style="thin"><color rgb="FFD9D9D9"/></top>
      <bottom style="thin"><color rgb="FFD9D9D9"/></bottom>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="16">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>
    <xf numFmtId="0" fontId="3" fillId="8" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>
    <xf numFmtId="0" fontId="0" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>
    <xf numFmtId="0" fontId="4" fillId="4" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="5" fillId="5" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="6" fillId="6" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="7" fillId="7" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="3" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1"/>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="9" fontId="0" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="9" fontId="0" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1"><alignment vertical="top" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="0" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"><alignment vertical="top" wrapText="1"/></xf>
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


def _workbook_rels_xml(num_sheets: int) -> str:
    rels = []
    for i in range(1, num_sheets + 1):
        rels.append(f'  <Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>')
    rels.append(f'  <Relationship Id="rId{num_sheets + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>')
    rels.append(f'  <Relationship Id="rId{num_sheets + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>')
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{"\n".join(rels)}
</Relationships>"""


def _content_types_xml(num_sheets: int) -> str:
    overrides = []
    for i in range(1, num_sheets + 1):
        overrides.append(f'  <Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml"               ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
{"\n".join(overrides)}
  <Override PartName="/xl/sharedStrings.xml"           ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
  <Override PartName="/xl/styles.xml"                  ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""


# ── Public API ────────────────────────────────────────────────────────────

def export_excel(scan_result: ScanResult | dict, output_path: str) -> None:
    """Write a multi-sheet .xlsx workbook for the given ScanResult.

    Produces 3 sheets:
      1. SBOM Report     — Software Bill of Materials findings
      2. CBOM Report     — Configuration Bill of Materials findings
      3. AI BOM Report   — AI Bill of Materials findings

    No third-party dependencies required (stdlib zipfile + xml only).

    Args:
        scan_result:  Completed ScanResult from the controller, or a dictionary from JSON.
        output_path:  Destination .xlsx file path.
    """
    _reset_sst()

    if isinstance(scan_result, dict):
        result_dict = scan_result
    else:
        result_dict = scan_result.to_dict()

    sheet_defs = [
        ("SBOM Report",   _build_sbom_sheet(result_dict), [15, 18, 28, 45, 40, 15, 15, 25]),
        ("CBOM Report",   _build_cbom_sheet(result_dict), [15, 18, 28, 45, 40, 15, 15, 25]),
        ("AI BOM Report", _build_aibom_sheet(result_dict), [15, 18, 28, 45, 18, 40, 15, 15, 25]),
    ]

    # Build all sheet XMLs first (populates shared-string table)
    sheet_xmls = [_sheet_xml(rows, col_widths) for _, rows, col_widths in sheet_defs]
    sheet_names = [name for name, _, _ in sheet_defs]

    try:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml",  _content_types_xml(len(sheet_defs)))
            zf.writestr("_rels/.rels",          _RELS_XML)
            zf.writestr("xl/workbook.xml",      _workbook_xml(sheet_names))
            zf.writestr("xl/styles.xml",        _STYLES_XML)
            zf.writestr("xl/_rels/workbook.xml.rels", _workbook_rels_xml(len(sheet_defs)))

            for i, xml_bytes in enumerate(sheet_xmls, start=1):
                zf.writestr(f"xl/worksheets/sheet{i}.xml", xml_bytes)

            zf.writestr("xl/sharedStrings.xml", _shared_strings_xml())

        logger.info("Excel report written to: %s  (%d findings, %d sheets)",
                    output_path, result_dict["summary"].get("total_findings", 0) if "summary" in result_dict else 0,
                    len(sheet_defs))
    except OSError as exc:
        logger.error("Failed to write Excel report to %s: %s", output_path, exc)
        raise
