"""
Regenerate rendered_dashboard.html from the latest report.json (or demo data),
then open it in the default browser.
"""
import sys
import os
import json
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scanner.reporter.report_generator import generate_html_report
from scanner.models import (
    ScanResult, Finding, FindingCategory, RiskLevel, ModuleInfo
)

OUTPUT = Path(__file__).parent / "rendered_dashboard.html"
REPORT_JSON = Path(__file__).parent / "report.json"


def load_from_json(path: Path) -> ScanResult:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    findings = []
    for fd in data.get("findings", []):
        try:
            cat = FindingCategory(fd.get("category", "Unknown"))
        except ValueError:
            cat = FindingCategory.UNKNOWN
        try:
            risk = RiskLevel(fd.get("risk_level", "info"))
        except ValueError:
            risk = RiskLevel.INFO
        findings.append(Finding(
            finding_id=fd.get("finding_id", ""),
            module_name=fd.get("module_name", ""),
            title=fd.get("title", ""),
            description=fd.get("description", ""),
            source=fd.get("source", ""),
            category=cat,
            risk_level=risk,
            details=fd.get("details", {}),
            confidence=float(fd.get("confidence", 0)),
            timestamp=fd.get("timestamp", ""),
        ))

    modules = []
    for md in data.get("modules", []):
        modules.append(ModuleInfo(
            name=md.get("name", ""),
            module_number=md.get("module_number", 0),
            status=md.get("status", "success"),
            duration_sec=float(md.get("duration_sec", 0)),
            findings_count=int(md.get("findings_count", 0)),
            error_message=md.get("error_message"),
        ))

    result = ScanResult(
        scan_id=data.get("scan_id", ""),
        scan_timestamp=data.get("scan_timestamp", ""),
        hostname=data.get("hostname", ""),
        os_info=data.get("os_info", ""),
        total_duration_sec=float(data.get("total_duration_sec", 0)),
        findings=findings,
        modules=modules,
    )
    result.compute_summary()
    return result


def demo_result() -> ScanResult:
    """Minimal demo result when no report.json exists."""
    findings = [
        Finding(module_name="AgentScanner", title="GitHub Copilot CLI",
                description="AI coding assistant detected via npm global package",
                source="C:/Users/ADMIN/AppData/Roaming/npm/gh",
                category=FindingCategory.AI_AGENT, risk_level=RiskLevel.HIGH, confidence=0.95),
        Finding(module_name="APIScanner", title="OpenAI API Key Exposed",
                description="OPENAI_API_KEY found in environment variables",
                source=".env / System Environment", category=FindingCategory.CONFIGURATION,
                risk_level=RiskLevel.CRITICAL, confidence=0.99),
        Finding(module_name="FileScanner", title="llama3.Q4_K_M.gguf",
                description="Local LLM model weight file found on disk",
                source="C:/models/llama3.Q4_K_M.gguf", category=FindingCategory.AI_MODEL,
                risk_level=RiskLevel.MEDIUM, confidence=0.92),
        Finding(module_name="PackageScanner", title="torch==2.3.0",
                description="PyTorch ML framework installed in Python environment",
                source="pip: torch 2.3.0", category=FindingCategory.ML_FRAMEWORK,
                risk_level=RiskLevel.LOW, confidence=0.88),
        Finding(module_name="RuntimeScanner", title="Ollama LLM Server",
                description="Ollama inference server listening on port 11434",
                source="localhost:11434", category=FindingCategory.LLM_RUNTIME,
                risk_level=RiskLevel.HIGH, confidence=0.97),
        Finding(module_name="AgentScanner", title="LangChain Agent Framework",
                description="LangChain agent orchestration scripts detected",
                source="C:/projects/ai_bot/agent.py", category=FindingCategory.AI_AGENT,
                risk_level=RiskLevel.MEDIUM, confidence=0.85),
        Finding(module_name="APIScanner", title="Anthropic API Key",
                description="ANTHROPIC_API_KEY detected in shell profile",
                source="~/.bashrc", category=FindingCategory.CONFIGURATION,
                risk_level=RiskLevel.CRITICAL, confidence=0.98),
        Finding(module_name="SystemScanner", title="Windows 11 x64",
                description="Host system information collected",
                source="System", category=FindingCategory.SYSTEM_INFO,
                risk_level=RiskLevel.INFO, confidence=1.0),
    ]
    modules = [
        ModuleInfo(name="SystemScanner",  module_number=1, status="success", duration_sec=0.71, findings_count=1),
        ModuleInfo(name="FileScanner",    module_number=2, status="success", duration_sec=5.37, findings_count=1),
        ModuleInfo(name="ProcessScanner", module_number=3, status="success", duration_sec=0.05, findings_count=0),
        ModuleInfo(name="PackageScanner", module_number=4, status="success", duration_sec=1.73, findings_count=1),
        ModuleInfo(name="AgentScanner",   module_number=5, status="success", duration_sec=40.2, findings_count=2),
        ModuleInfo(name="RuntimeScanner", module_number=6, status="success", duration_sec=1.54, findings_count=1),
        ModuleInfo(name="APIScanner",     module_number=7, status="success", duration_sec=12.2, findings_count=2),
    ]
    result = ScanResult(
        scan_id="demo-2026-001",
        scan_timestamp="2026-06-19T10:30:00.000000",
        hostname="DEMO-WORKSTATION",
        os_info="Windows 11 (x64)",
        total_duration_sec=61.82,
        findings=findings,
        modules=modules,
    )
    result.compute_summary()
    return result


if __name__ == "__main__":
    if REPORT_JSON.exists():
        print(f"Loading real scan data from {REPORT_JSON.name} ...")
        result = load_from_json(REPORT_JSON)
        print(f"  {len(result.findings)} findings  |  risk score: {result.summary['overall_risk_score']}")
    else:
        print("No report.json found — using demo data.")
        result = demo_result()
        print(f"  {len(result.findings)} demo findings  |  risk score: {result.summary['overall_risk_score']}")

    print(f"Rendering dashboard → {OUTPUT.name} ...", end=" ", flush=True)
    generate_html_report(result, str(OUTPUT))
    size = OUTPUT.stat().st_size
    print(f"done  ({size:,} bytes)")

    print("Opening in browser ...")
    webbrowser.open(OUTPUT.as_uri())
    print("Dashboard opened.")
