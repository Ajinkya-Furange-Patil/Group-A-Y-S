"""
Quick test to verify check_imports function implementation
"""
import ast
import pathlib
import tempfile
from scanner.modules.license_scanner import check_imports, RESTRICTED_IMPORTS

# Test code with various import patterns
test_code = """
import PyQt5
import PyQt6
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget
import mysql.connector
from mysql.connector import connect
import pygobject
import readline
import os  # Should not be flagged
from pathlib import Path  # Should not be flagged
"""

def test_check_imports():
    """Test the check_imports function with various import patterns"""
    # Parse test code
    tree = ast.parse(test_code)
    
    # Create a temporary file path for testing
    temp_file = pathlib.Path(tempfile.gettempdir()) / "test_imports.py"
    
    # Call check_imports
    findings = check_imports(tree, temp_file)
    
    print(f"\n{'='*60}")
    print(f"CHECK_IMPORTS FUNCTION TEST RESULTS")
    print(f"{'='*60}\n")
    
    print(f"Total findings detected: {len(findings)}")
    print(f"\nExpected restricted imports:")
    for lib in RESTRICTED_IMPORTS.keys():
        print(f"  - {lib}: {RESTRICTED_IMPORTS[lib]}")
    
    print(f"\n{'-'*60}")
    print(f"DETECTED FINDINGS:")
    print(f"{'-'*60}\n")
    
    for i, finding in enumerate(findings, 1):
        print(f"{i}. {finding.title}")
        print(f"   Line: {finding.details['line_number']}")
        print(f"   Library: {finding.details['imported_library']}")
        print(f"   License: {finding.details['license_type']}")
        print(f"   Risk Level: {finding.risk_level}")
        print(f"   Confidence: {finding.confidence}")
        print(f"   Category: {finding.category}")
        print()
    
    # Verify key requirements
    print(f"{'-'*60}")
    print(f"REQUIREMENT VERIFICATION:")
    print(f"{'-'*60}\n")
    
    # Check that all findings have confidence = 0.85
    confidence_check = all(f.confidence == 0.85 for f in findings)
    print(f"✓ All findings have confidence = 0.85: {confidence_check}")
    
    # Check that all findings have imported_library in details
    imported_lib_check = all('imported_library' in f.details for f in findings)
    print(f"✓ All findings have 'imported_library' in details: {imported_lib_check}")
    
    # Check that all findings have line_number in details
    line_num_check = all('line_number' in f.details for f in findings)
    print(f"✓ All findings have 'line_number' in details: {line_num_check}")
    
    # Check that all findings have license_type in details
    license_check = all('license_type' in f.details for f in findings)
    print(f"✓ All findings have 'license_type' in details: {license_check}")
    
    # Check that all findings have file_path in details
    filepath_check = all('file_path' in f.details for f in findings)
    print(f"✓ All findings have 'file_path' in details: {filepath_check}")
    
    # Check that we detected expected imports (should be at least 5 restricted imports)
    count_check = len(findings) >= 5
    print(f"✓ Detected at least 5 restricted imports: {count_check} (found {len(findings)})")
    
    print(f"\n{'='*60}")
    if all([confidence_check, imported_lib_check, line_num_check, 
            license_check, filepath_check, count_check]):
        print("✅ ALL CHECKS PASSED - Task 4.2 implementation verified!")
    else:
        print("❌ SOME CHECKS FAILED - Review implementation")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    test_check_imports()
