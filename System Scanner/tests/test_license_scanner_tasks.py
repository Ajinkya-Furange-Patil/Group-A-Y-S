"""
Test file to verify tasks 2.1, 3.1, and 4.1 implementation
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner.modules.license_scanner import LICENSE_TAXONOMY, RESTRICTED_IMPORTS, scan_py_file_ast
from scanner.models import RiskLevel, FindingCategory


def test_task_2_1_license_taxonomy():
    """Verify Task 2.1: LICENSE_TAXONOMY dictionary with all seven license types"""
    print("Testing Task 2.1: LICENSE_TAXONOMY dictionary...")
    
    # Verify all seven license types exist
    expected_licenses = ["MIT", "Apache 2.0", "LGPL", "GPL", "AGPL", "Polyform Shield", "Proprietary"]
    assert set(LICENSE_TAXONOMY.keys()) == set(expected_licenses), "Missing or extra license types"
    
    # Verify MIT
    assert LICENSE_TAXONOMY["MIT"]["status"] == "Approved"
    assert LICENSE_TAXONOMY["MIT"]["risk_level"] == RiskLevel.INFO
    
    # Verify Apache 2.0
    assert LICENSE_TAXONOMY["Apache 2.0"]["status"] == "Approved"
    assert LICENSE_TAXONOMY["Apache 2.0"]["risk_level"] == RiskLevel.INFO
    
    # Verify LGPL
    assert LICENSE_TAXONOMY["LGPL"]["status"] == "Moderate"
    assert LICENSE_TAXONOMY["LGPL"]["risk_level"] == RiskLevel.MEDIUM
    
    # Verify GPL
    assert LICENSE_TAXONOMY["GPL"]["status"] == "Review / Banned"
    assert LICENSE_TAXONOMY["GPL"]["risk_level"] == RiskLevel.HIGH
    
    # Verify AGPL
    assert LICENSE_TAXONOMY["AGPL"]["status"] == "Review / Banned"
    assert LICENSE_TAXONOMY["AGPL"]["risk_level"] == RiskLevel.CRITICAL
    
    # Verify Polyform Shield
    assert LICENSE_TAXONOMY["Polyform Shield"]["status"] == "Review / Banned"
    assert LICENSE_TAXONOMY["Polyform Shield"]["risk_level"] == RiskLevel.HIGH
    
    # Verify Proprietary
    assert LICENSE_TAXONOMY["Proprietary"]["status"] == "Review / Banned"
    assert LICENSE_TAXONOMY["Proprietary"]["risk_level"] == RiskLevel.MEDIUM
    
    print("✓ Task 2.1 PASSED: All seven license types correctly defined")


def test_task_3_1_ast_parsing():
    """Verify Task 3.1: analyze_python_file function with AST parsing"""
    print("\nTesting Task 3.1: AST parsing function...")
    
    # Create a test file with GPL header
    test_file = Path(__file__).parent / "temp_test_gpl.py"
    test_file.write_text('''"""
This file is licensed under the GPL General Public License.
All rights reserved.
"""

def hello():
    pass
''')
    
    try:
        findings = scan_py_file_ast(test_file)
        
        # Verify GPL detection
        assert len(findings) > 0, "No findings from GPL docstring"
        gpl_finding = [f for f in findings if "GPL" in f.title][0]
        assert gpl_finding.confidence == 0.90, "Incorrect confidence for AST detection"
        assert gpl_finding.category == FindingCategory.CONFIGURATION
        assert "file_path" in gpl_finding.details
        assert "snippet" in gpl_finding.details
        
        print("✓ Task 3.1 PASSED: AST parsing correctly detects GPL headers")
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


def test_task_4_1_restricted_imports():
    """Verify Task 4.1: RESTRICTED_IMPORTS dictionary"""
    print("\nTesting Task 4.1: RESTRICTED_IMPORTS dictionary...")
    
    # Verify all five restricted libraries exist
    expected_imports = ["PyQt5", "PyQt6", "mysql.connector", "pygobject", "readline"]
    assert set(RESTRICTED_IMPORTS.keys()) == set(expected_imports), "Missing or extra restricted imports"
    
    # Verify structure is correct (dict with "license" and "risk" keys)
    for lib_name, lib_data in RESTRICTED_IMPORTS.items():
        assert isinstance(lib_data, dict), f"{lib_name} should have dict value"
        assert "license" in lib_data, f"{lib_name} missing 'license' key"
        assert "risk" in lib_data, f"{lib_name} missing 'risk' key"
    
    # Verify PyQt5
    assert RESTRICTED_IMPORTS["PyQt5"]["license"] == "GPL"
    assert RESTRICTED_IMPORTS["PyQt5"]["risk"] == RiskLevel.HIGH
    
    # Verify PyQt6
    assert RESTRICTED_IMPORTS["PyQt6"]["license"] == "GPL"
    assert RESTRICTED_IMPORTS["PyQt6"]["risk"] == RiskLevel.HIGH
    
    # Verify mysql.connector
    assert RESTRICTED_IMPORTS["mysql.connector"]["license"] == "GPL"
    assert RESTRICTED_IMPORTS["mysql.connector"]["risk"] == RiskLevel.HIGH
    
    # Verify pygobject
    assert RESTRICTED_IMPORTS["pygobject"]["license"] == "LGPL"
    assert RESTRICTED_IMPORTS["pygobject"]["risk"] == RiskLevel.MEDIUM
    
    # Verify readline
    assert RESTRICTED_IMPORTS["readline"]["license"] == "GPL"
    assert RESTRICTED_IMPORTS["readline"]["risk"] == RiskLevel.HIGH
    
    print("✓ Task 4.1 PASSED: All five restricted imports correctly defined")
    
    # Test import detection
    test_file = Path(__file__).parent / "temp_test_import.py"
    test_file.write_text('''import PyQt5
from mysql.connector import connect

def main():
    pass
''')
    
    try:
        findings = scan_py_file_ast(test_file)
        
        # Verify import detection
        import_findings = [f for f in findings if "Restrictive Import" in f.title]
        assert len(import_findings) >= 2, "Should detect both PyQt5 and mysql.connector"
        
        # Verify confidence is 0.85 for import detections
        for finding in import_findings:
            assert finding.confidence == 0.85, "Incorrect confidence for import detection"
            assert finding.category == FindingCategory.CONFIGURATION
        
        print("✓ Task 4.1 PASSED: Import detection works correctly")
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    print("=" * 60)
    print("Verification Tests for Tasks 2.1, 3.1, and 4.1")
    print("=" * 60)
    
    try:
        test_task_2_1_license_taxonomy()
        test_task_3_1_ast_parsing()
        test_task_4_1_restricted_imports()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nSummary:")
        print("  • Task 2.1: LICENSE_TAXONOMY - VERIFIED ✓")
        print("  • Task 3.1: AST Parsing - VERIFIED ✓")
        print("  • Task 4.1: RESTRICTED_IMPORTS - VERIFIED ✓")
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
