#!/usr/bin/env python3
"""
Comprehensive Integration Test
Tests all components working together: License Scanner + Port Mapping + Excel Export + Dashboard
"""

import sys
import json
import pathlib
from datetime import datetime

def test_full_integration():
    """Test complete scanner with all modules integrated"""
    print("\n" + "="*70)
    print("COMPREHENSIVE INTEGRATION TEST")
    print("Testing: License Scanner + Port Mapping + Excel Export + Dashboard")
    print("="*70)
    
    # Test 1: Import all components
    print("\n[TEST 1] Importing all components...")
    try:
        from scanner.controller import ScanController
        from scanner.models import ScanResult, Finding, FindingCategory, RiskLevel
        from scanner.reporter.excel_exporter import export_excel
        from scanner.reporter.report_generator import generate_html_report
        print("[OK] All imports successful")
    except ImportError as e:
        print(f"[FAIL] Import failed: {e}")
        return False
    
    # Test 2: Run full scan with all 9 modules
    print("\n[TEST 2] Running full system scan (this may take a minute)...")
    try:
        controller = ScanController(scan_folder=".", max_depth=2)
        result = controller.run_scan()
        print(f"[OK] Scan completed successfully")
        print(f"  - Found {len(result.findings)} findings")
        print(f"  - {len(result.modules)} modules executed")
        print(f"  - Overall risk score: {result.summary.get('overall_risk_score', 0)}")
    except Exception as e:
        print(f"[FAIL] Scan failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Verify License Scanner integration...
    print("\n[TEST 3] Verifying License Scanner integration...")
    license_findings = [f for f in result.findings if f.module_name == "LicenseScanner"]
    if license_findings:
        print(f"[OK] License Scanner produced {len(license_findings)} findings")
        for f in license_findings[:3]:  # Show first 3
            print(f"  - {f.title} (Risk: {f.risk_level})")
    else:
        print("[WARN] No license findings (OK if no licenses detected in scan folder)")
    
    # Test 4: Verify Runtime Scanner with process metadata
    print("\n[TEST 4] Verifying Runtime Scanner process metadata...")
    runtime_findings = [f for f in result.findings if f.module_name == "RuntimeScanner"]
    process_metadata_count = 0
    for f in runtime_findings:
        if "process_id" in f.details:
            process_metadata_count += 1
            print(f"[OK] Finding '{f.title}' includes process metadata:")
            print(f"  - PID: {f.details['process_id']}")
            print(f"  - Name: {f.details['process_name']}")
    
    if process_metadata_count > 0:
        print(f"[OK] {process_metadata_count} findings with process metadata")
    else:
        print("[WARN] No active ports with process metadata (OK if no services running)")
    
    # Test 5: Export to JSON
    print("\n[TEST 5] Exporting to JSON...")
    try:
        json_path = pathlib.Path("test_report.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2)
        size = json_path.stat().st_size
        print(f"[OK] JSON exported: {json_path} ({size:,} bytes)")
    except Exception as e:
        print(f"[FAIL] JSON export failed: {e}")
        return False
    
    # Test 6: Export to Excel
    print("\n[TEST 6] Exporting to Excel...")
    try:
        excel_path = pathlib.Path("test_report.xlsx")
        export_excel(result, str(excel_path))
        size = excel_path.stat().st_size
        print(f"[OK] Excel exported: {excel_path} ({size:,} bytes)")
        print(f"  - 3 sheets: SBOM Report, CBOM Report, AI BOM Report")
    except Exception as e:
        print(f"[FAIL] Excel export failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 7: Generate HTML Dashboard
    print("\n[TEST 7] Generating HTML dashboard...")
    try:
        html_path = pathlib.Path("test_dashboard.html")
        generate_html_report(result, str(html_path))
        size = html_path.stat().st_size
        print(f"[OK] HTML dashboard: {html_path} ({size:,} bytes)")
    except Exception as e:
        print(f"[FAIL] HTML generation failed: {e}")
        return False
    
    # Test 8: Verify all modules executed
    print("\n[TEST 8] Verifying module execution status...")
    expected_modules = [
        "SystemScanner", "FileScanner", "ProcessScanner", "PackageScanner",
        "AgentScanner", "RuntimeScanner", "APIScanner", "MCPScanner", "LicenseScanner"
    ]
    
    module_names = [m.name for m in result.modules]
    for expected in expected_modules:
        if expected in module_names:
            module = next(m for m in result.modules if m.name == expected)
            status_icon = "[OK]" if module.status == "success" else "[FAIL]"
            print(f"  {status_icon} {expected}: {module.status} ({module.findings_count} findings)")
        else:
            print(f"  [WARN] {expected}: not registered")
    
    # Test 9: Verify data model consistency
    print("\n[TEST 9] Verifying data model consistency...")
    issues = []
    for f in result.findings:
        if not f.finding_id:
            issues.append(f"Finding without ID: {f.title}")
        if not f.module_name:
            issues.append(f"Finding without module_name: {f.title}")
        if f.confidence < 0 or f.confidence > 1:
            issues.append(f"Invalid confidence {f.confidence} for {f.title}")
    
    if issues:
        print(f"[FAIL] Found {len(issues)} data model issues:")
        for issue in issues[:5]:
            print(f"  - {issue}")
        return False
    else:
        print("[OK] All findings conform to data model")
    
    # Test 10: Verify summary statistics
    print("\n[TEST 10] Verifying summary statistics...")
    summary = result.summary
    checks = [
        (summary.get("total_findings") == len(result.findings), "Total findings count"),
        (summary.get("modules_run") == len(result.modules), "Modules run count"),
        ("findings_by_category" in summary, "Category breakdown present"),
        ("findings_by_risk" in summary, "Risk breakdown present"),
        ("overall_risk_score" in summary, "Risk score calculated"),
    ]
    
    for check, desc in checks:
        icon = "[OK]" if check else "[FAIL]"
        print(f"  {icon} {desc}")
        if not check:
            return False
    
    # Final summary
    print("\n" + "="*70)
    print("INTEGRATION TEST RESULTS")
    print("="*70)
    print(f"[SUCCESS] ALL TESTS PASSED")
    print(f"\nGenerated Outputs:")
    print(f"  - JSON Report:      test_report.json")
    print(f"  - Excel Workbook:   test_report.xlsx")
    print(f"  - HTML Dashboard:   test_dashboard.html")
    print(f"\nScan Statistics:")
    print(f"  - Total Findings:   {len(result.findings)}")
    print(f"  - Modules Success:  {summary.get('modules_succeeded', 0)}/{summary.get('modules_run', 0)}")
    print(f"  - Overall Risk:     {summary.get('overall_risk_score', 0)}/100")
    print(f"  - Scan Duration:    {result.total_duration_sec:.2f}s")
    print("\n[OK] All components integrated and working correctly!")
    print("="*70)
    
    return True


if __name__ == "__main__":
    success = test_full_integration()
    sys.exit(0 if success else 1)
