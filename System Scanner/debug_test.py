"""Debug test to see what's happening with the import detection"""
import pathlib
import tempfile
from scanner.modules import license_scanner

with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = pathlib.Path(temp_dir)
    file_path = temp_path / "imports_script.py"
    
    # Script with GPL PyQt5 import
    code_content = '''
import sys
from PyQt5.QtWidgets import QApplication
import mysql.connector

def main():
    pass
'''
    file_path.write_text(code_content, encoding="utf-8")
    
    findings = license_scanner.scan_py_file_ast(file_path)
    
    print(f"Found {len(findings)} findings:")
    for i, f in enumerate(findings, 1):
        print(f"\n{i}. {f.title}")
        print(f"   Source: {f.source}")
        print(f"   Details: {f.details}")
