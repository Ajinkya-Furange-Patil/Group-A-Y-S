# Implementation Plan: License, Port, and Theme Enhancements

## Overview

This implementation plan breaks down the three enhancements into discrete coding tasks:
1. License Scanner Module (Module 09) with taxonomy classification, AST-based detection, and restrictive import detection
2. Port-to-Process ID mapping enhancement for Runtime Scanner
3. UI Theme synchronization across consent portal and dashboard templates

Each task builds incrementally to ensure early validation of core functionality.

## Tasks

- [x] 1. Create License Scanner module structure and controller registration
  - Create `scanner/modules/license_scanner.py` with LicenseScanner class
  - Define MODULE_NAME, MODULE_NUMBER constants
  - Implement `__init__` method with scan_folder and max_depth parameters
  - Implement skeleton `scan()` method returning empty list
  - Add License Scanner registration in `scanner/controller.py` at MODULE 09 section
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [ ] 2. Implement license taxonomy database and classification logic
  - [x] 2.1 Define LICENSE_TAXONOMY dictionary with all seven license types
    - Map MIT and Apache 2.0 to RiskLevel.INFO with "Approved" status
    - Map LGPL to RiskLevel.MEDIUM with "Moderate" status
    - Map GPL to RiskLevel.HIGH with "Review / Banned" status
    - Map AGPL to RiskLevel.CRITICAL with "Review / Banned" status
    - Map Polyform Shield to RiskLevel.HIGH with "Review / Banned" status
    - Map Proprietary to RiskLevel.MEDIUM with "Review / Banned" status
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_
  
  - [ ]* 2.2 Write property test for taxonomy consistency
    - **Property 1: License Taxonomy Consistency**
    - **Validates: Requirements 2.1-2.8**
    - Generate random license findings with taxonomy license types
    - Verify status field matches taxonomy definition

- [ ] 3. Implement AST-based copyleft detection
  - [x] 3.1 Create `analyze_python_file` function with AST parsing
    - Parse Python files using ast.parse()
    - Extract module-level docstring using ast.get_docstring()
    - Implement GPL keyword pattern detection with regex
    - Implement AGPL keyword pattern detection with regex
    - Create Finding objects with title "Code License: GPL Header" or "Code License: AGPL Header"
    - Include file_path, line_number (1), license_type, and docstring_snippet in details
    - Set confidence to 0.90 for docstring-based detections
    - Handle SyntaxError and continue to next file on parse failure
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  
  - [ ]* 3.2 Write property test for AST confidence bound
    - **Property 2: AST Confidence Bound**
    - **Validates: Requirements 3.6**
    - Generate Python files with GPL/AGPL docstrings
    - Verify all docstring-based findings have confidence = 0.90

  - [ ]* 3.3 Write unit tests for AST parsing edge cases
    - Test files with no docstrings
    - Test files with syntax errors
    - Test files with encoding issues
    - Test GPL/AGPL variations in docstrings
    - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [ ] 4. Implement restrictive import detection
  - [x] 4.1 Define RESTRICTED_IMPORTS dictionary
    - Map PyQt5 to GPL with RiskLevel.HIGH
    - Map PyQt6 to GPL with RiskLevel.HIGH
    - Map mysql.connector to GPL with RiskLevel.HIGH
    - Map pygobject to LGPL with RiskLevel.MEDIUM
    - Map readline to GPL with RiskLevel.HIGH
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [-] 4.2 Create `check_imports` function with AST walker
    - Use ast.walk() to traverse AST nodes
    - Detect ast.Import nodes (direct imports like "import PyQt5")
    - Detect ast.ImportFrom nodes (from-imports like "from PyQt5 import QtCore")
    - Extract line numbers from AST node.lineno
    - Create Finding objects with imported_library, license_type, file_path, line_number in details
    - Set confidence to 0.85 for import-based detections
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9_
  
  - [ ]* 4.3 Write property test for import confidence bound
    - **Property 3: Import Confidence Bound**
    - **Validates: Requirements 4.8**
    - Generate Python files with restrictive imports
    - Verify all import-based findings have confidence = 0.85
  
  - [ ]* 4.4 Write unit tests for import detection patterns
    - Test direct import statements (import PyQt5)
    - Test from-import statements (from PyQt5 import QtCore)
    - Test nested imports (from PyQt5.QtCore import QObject)
    - Test multiple imports on one line
    - _Requirements: 4.9_

- [ ] 5. Integrate file scanning and Finding creation in License Scanner
  - [~] 5.1 Implement directory traversal in `scan()` method
    - Use pathlib.Path to walk scan_folder or current directory
    - Respect max_depth parameter for recursion limit
    - Filter for .py files only
    - Call analyze_python_file() and check_imports() for each Python file
    - Aggregate all findings from both functions
    - Set category to FindingCategory.CONFIGURATION for all findings
    - Return list of Finding objects
    - _Requirements: 1.5, 10.4_
  
  - [ ]* 5.2 Write property test for finding category consistency
    - **Property 6: Finding Category Consistency**
    - **Validates: Requirements 10.4**
    - Run license scanner on test directory
    - Verify all findings have category = FindingCategory.CONFIGURATION
  
  - [ ]* 5.3 Write integration test for license scanner end-to-end
    - Create test directory with various license scenarios
    - Run LicenseScanner.scan()
    - Verify findings include expected licenses, imports, and docstrings
    - Verify Finding.to_dict() serialization preserves all fields
    - _Requirements: 1.5, 1.6_

- [~] 6. Checkpoint - Ensure License Scanner tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Enhance Runtime Scanner with process metadata retrieval
  - [~] 7.1 Replace `_find_process_for_port` function implementation
    - Import psutil at function level with ImportError handling
    - Implement fast path using psutil.net_connections(kind="inet")
    - Check for conn.laddr.port match and conn.status == "LISTEN"
    - Retrieve process_id, process_name, and process_cmdline for matching connections
    - Catch psutil.AccessDenied and psutil.PermissionError exceptions
    - Implement fallback using psutil.process_iter() on permission errors
    - Iterate through all processes and check p.connections(kind="inet")
    - Handle psutil.NoSuchProcess and psutil.AccessDenied per-process
    - Return dictionary with process_id (int), process_name (str), process_cmdline (list[str])
    - Return None if process cannot be found or psutil unavailable
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_
  
  - [ ]* 7.2 Write property test for process metadata completeness
    - **Property 4: Process Metadata Completeness**
    - **Validates: Requirements 5.4, 7.6, 7.7**
    - Create mock port with known process
    - Verify findings with process_id always have process_name and process_cmdline
  
  - [ ]* 7.3 Write property test for port finding resilience
    - **Property 7: Port Finding Resilience**
    - **Validates: Requirements 5.5, 6.5, 6.7**
    - Mock _find_process_for_port to return None
    - Verify RuntimeScanner still creates port findings
    - Verify module_status = "success"

- [ ] 8. Update Runtime Scanner port findings to include process metadata
  - [~] 8.1 Modify port Finding creation in `run()` method
    - For each detected open port in PORT_MAP, call _find_process_for_port(port)
    - Add process_id, process_name, process_cmdline to details dictionary when available
    - Ensure findings are created even when process_info is None
    - Update Ollama-specific findings to include process metadata
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_
  
  - [ ]* 8.2 Write property test for no unhandled permission exceptions
    - **Property 8: No Unhandled Permission Exceptions**
    - **Validates: Requirements 6.1, 6.2, 6.6, 6.7**
    - Mock psutil methods to raise AccessDenied and PermissionError
    - Verify RuntimeScanner.run() completes with status "success"
    - Verify no exceptions propagate to caller
  
  - [ ]* 8.3 Write integration test for enhanced Runtime Scanner
    - Start a test server on a known port
    - Run RuntimeScanner.scan()
    - Verify finding includes process_id, process_name, process_cmdline
    - Stop test server and verify cleanup
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [~] 9. Checkpoint - Ensure Runtime Scanner tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Synchronize theme storage key in consent portal template
  - [~] 10.1 Update consent.html.j2 localStorage key from "hud-theme" to "theme"
    - Find all occurrences of localStorage.getItem('hud-theme') and replace with localStorage.getItem('theme')
    - Find all occurrences of localStorage.setItem('hud-theme', ...) and replace with localStorage.setItem('theme', ...)
    - Verify theme toggle button updates localStorage with correct key
    - Verify theme initialization on page load reads from correct key
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [ ]* 10.2 Write manual test plan for theme synchronization
    - Document steps to verify theme persists from consent portal to dashboard
    - Document steps to verify default dark theme when no preference exists
    - Document steps to verify theme persists across page reloads
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ] 11. Verify dashboard template uses consistent theme key
  - [~] 11.1 Review dashboard.html.j2 theme implementation
    - Search for all localStorage theme-related calls
    - Verify localStorage.getItem('theme') is used consistently
    - Verify localStorage.setItem('theme', ...) is used consistently
    - Ensure theme toggle function matches consent portal pattern
    - If using different key, update to use 'theme'
    - _Requirements: 8.6, 9.1, 9.2, 9.5, 9.6_
  
  - [ ]* 11.2 Write property test for theme key consistency
    - **Property 5: Theme Key Consistency**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.6**
    - Parse both template files for localStorage key usage
    - Verify both templates use "theme" key exclusively
    - Verify no "hud-theme" references remain

- [ ] 12. Verify dashboard filter compatibility with license findings
  - [~] 12.1 Test license findings in dashboard filter system
    - Start the scanner application
    - Run a scan that produces license findings
    - Open the dashboard and locate license findings
    - Verify findings with status "Approved" appear under "Approved & Moderate" filter
    - Verify findings with status "Moderate" appear under "Approved & Moderate" filter
    - Verify findings with status "Review / Banned" appear under "Review & Banned" filter
    - Verify category badge shows "Configuration"
    - Verify severity badges display correct colors (Critical/High/Medium/Info)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [~] 13. Final checkpoint - Integration verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Integration tests verify end-to-end functionality
- The implementation uses Python as the base language
- All scanner modules follow the established pattern in the codebase
- UI changes are minimal JavaScript modifications in Jinja2 templates

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1", "3.1", "4.1"] },
    { "id": 2, "tasks": ["2.2", "3.2", "3.3", "4.2"] },
    { "id": 3, "tasks": ["4.3", "4.4", "5.1"] },
    { "id": 4, "tasks": ["5.2", "5.3"] },
    { "id": 5, "tasks": ["7.1"] },
    { "id": 6, "tasks": ["7.2", "7.3", "8.1"] },
    { "id": 7, "tasks": ["8.2", "8.3"] },
    { "id": 8, "tasks": ["10.1", "11.1"] },
    { "id": 9, "tasks": ["10.2", "11.2", "12.1"] }
  ]
}
```
