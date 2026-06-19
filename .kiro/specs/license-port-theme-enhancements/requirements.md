# Requirements Document

## Introduction

This document specifies the requirements for three critical enhancements to the AI Discovery System Scanner: (1) License Scanner Integration to detect and classify software licenses including copyleft restrictions, (2) Network Port PID Mapping to identify processes bound to specific network ports, and (3) UI Theme Synchronization to ensure consistent theme preferences across the Remote Authorization Portal and Telemetry Dashboard interfaces.

These enhancements address compliance, operational visibility, and user experience concerns in the system scanner's telemetry collection and reporting capabilities.

## Glossary

- **Scanner_Controller**: The central orchestrator module that registers and dispatches all scanner modules through the Discovery Engine
- **License_Scanner**: Module 09 scanner that performs license taxonomy classification and AST-based Python code analysis
- **Runtime_Scanner**: Module 06 scanner that identifies active LLM runtimes and network port listeners
- **Discovery_Engine**: The parallel module execution engine that runs all registered scanner modules
- **Finding**: A single discovered artifact containing metadata (title, description, risk level, category, source, details)
- **License_Taxonomy**: A classification database mapping license types (MIT, Apache 2.0, LGPL, GPL, AGPL, Polyform Shield, Proprietary) to risk levels and approval statuses
- **AST_Parser**: Python Abstract Syntax Tree parser used to analyze source code imports and docstring headers
- **Port_Monitor**: Component within Runtime Scanner that checks active network ports on localhost
- **Process_Metadata**: Dictionary containing process_id, process_name, and process_cmdline for a running process
- **Consent_Portal**: Remote Authorization Portal web interface (consent.html.j2 template)
- **Telemetry_Dashboard**: Main scan results dashboard interface (dashboard.html.j2 template)
- **Theme_State**: User preference for UI appearance stored as 'light' or 'dark' in browser localStorage
- **Target_Ports**: The set of network ports monitored by the scanner: 11434, 1234, 8000, 8080, 5000
- **Copyleft_License**: A license type (GPL, AGPL) requiring derivative works to use the same license, flagged as high-risk
- **psutil**: Python system and process utilities library providing cross-platform process and network connection information
- **Restrictive_Import**: Import of a Python library known to have copyleft or commercial restrictions (PyQt5, PyQt6, mysql.connector)

## Requirements

### Requirement 1: License Scanner Controller Registration

**User Story:** As a system administrator, I want the License Scanner to be automatically registered and executed during scans, so that license compliance findings appear in telemetry reports.

#### Acceptance Criteria

1. THE Scanner_Controller SHALL register License_Scanner as Module 09 during the module registration phase
2. WHEN the Scanner_Controller initializes License_Scanner, THE Scanner_Controller SHALL pass the scan_folder and max_depth parameters from the scan configuration
3. IF License_Scanner import fails, THEN THE Scanner_Controller SHALL log a warning message and continue with remaining modules
4. WHEN Discovery_Engine executes all modules, THE License_Scanner SHALL be included in the parallel execution set
5. THE License_Scanner SHALL return a list of Finding objects conforming to the Finding data model
6. FOR ALL Finding objects returned by License_Scanner, parsing the Finding and serializing to JSON SHALL preserve all metadata fields

### Requirement 2: License Taxonomy Classification

**User Story:** As a compliance officer, I want the scanner to classify licenses according to a defined taxonomy, so that I can identify approved, moderate, and banned licenses in our codebase.

#### Acceptance Criteria

1. THE License_Taxonomy SHALL map MIT licenses to RiskLevel.INFO with status "Approved"
2. THE License_Taxonomy SHALL map Apache 2.0 licenses to RiskLevel.INFO with status "Approved"
3. THE License_Taxonomy SHALL map LGPL licenses to RiskLevel.MEDIUM with status "Moderate"
4. THE License_Taxonomy SHALL map GPL licenses to RiskLevel.HIGH with status "Review / Banned"
5. THE License_Taxonomy SHALL map AGPL licenses to RiskLevel.CRITICAL with status "Review / Banned"
6. THE License_Taxonomy SHALL map Polyform Shield licenses to RiskLevel.HIGH with status "Review / Banned"
7. THE License_Taxonomy SHALL map Proprietary licenses to RiskLevel.MEDIUM with status "Review / Banned"
8. WHEN a license is detected, THE License_Scanner SHALL include the license name, status, and risk level in the Finding details dictionary

### Requirement 3: AST-Based Copyleft Detection

**User Story:** As a developer, I want the scanner to parse Python source files and detect GPL/AGPL headers, so that I can identify code with copyleft obligations before distribution.

#### Acceptance Criteria

1. WHEN a Python file contains a docstring, THE AST_Parser SHALL extract the module-level docstring content
2. IF the docstring matches a GPL keyword pattern, THEN THE License_Scanner SHALL create a Finding with title "Code License: GPL Header"
3. IF the docstring matches an AGPL keyword pattern, THEN THE License_Scanner SHALL create a Finding with title "Code License: AGPL Header"
4. THE License_Scanner SHALL include the file path, line number 1, detected license name, and docstring snippet in the Finding details
5. WHEN AST parsing fails for a file, THE License_Scanner SHALL log a debug message and continue scanning remaining files
6. THE License_Scanner SHALL set confidence to 0.90 for license detections from docstring headers

### Requirement 4: Restrictive Import Detection

**User Story:** As a compliance officer, I want the scanner to flag imports of libraries with restrictive licenses like PyQt5, so that I can assess license compatibility risks.

#### Acceptance Criteria

1. WHEN a Python file imports PyQt5, THE License_Scanner SHALL create a Finding with risk level RiskLevel.HIGH and license type "GPL"
2. WHEN a Python file imports PyQt6, THE License_Scanner SHALL create a Finding with risk level RiskLevel.HIGH and license type "GPL"
3. WHEN a Python file imports mysql.connector, THE License_Scanner SHALL create a Finding with risk level RiskLevel.HIGH and license type "GPL"
4. WHEN a Python file imports pygobject, THE License_Scanner SHALL create a Finding with risk level RiskLevel.MEDIUM and license type "LGPL"
5. WHEN a Python file imports readline, THE License_Scanner SHALL create a Finding with risk level RiskLevel.HIGH and license type "GPL"
6. THE License_Scanner SHALL extract the import statement line number from the AST node
7. THE License_Scanner SHALL include the imported library name, license type, file path, and line number in the Finding details
8. THE License_Scanner SHALL set confidence to 0.85 for restrictive import detections
9. THE License_Scanner SHALL match both direct imports (import PyQt5) and from-imports (from PyQt5 import QtCore)

### Requirement 5: Port to Process ID Mapping

**User Story:** As a system administrator, I want the scanner to identify which process is listening on each open port, so that I can correlate network services with running applications.

#### Acceptance Criteria

1. WHEN Runtime_Scanner detects an open port in Target_Ports, THE Runtime_Scanner SHALL attempt to find the process listening on that port using psutil
2. IF psutil.net_connections() succeeds, THE Runtime_Scanner SHALL use the connection list to find the process ID for the port
3. IF psutil.net_connections() raises AccessDenied or PermissionError, THEN THE Runtime_Scanner SHALL fall back to iterating over all processes with psutil.process_iter()
4. WHEN a process is found for a port, THE Runtime_Scanner SHALL retrieve the process ID, process name, and command line arguments
5. THE Runtime_Scanner SHALL store process_id, process_name, and process_cmdline in the Finding details dictionary
6. IF process information cannot be retrieved due to AccessDenied, THE Runtime_Scanner SHALL set process_name to "Unknown (Access Denied)" and process_cmdline to an empty list
7. THE Runtime_Scanner SHALL continue scanning remaining ports if process lookup fails for one port

### Requirement 6: Graceful Permission Error Handling

**User Story:** As a user running the scanner without administrator privileges, I want the scanner to handle permission errors gracefully, so that the scan completes successfully with partial process information.

#### Acceptance Criteria

1. WHEN psutil.net_connections() raises AccessDenied, THE Runtime_Scanner SHALL catch the exception and attempt the fallback method
2. WHEN psutil.net_connections() raises PermissionError, THE Runtime_Scanner SHALL catch the exception and attempt the fallback method
3. WHEN process_iter() encounters NoSuchProcess exception, THE Runtime_Scanner SHALL skip that process and continue iteration
4. WHEN process_iter() encounters AccessDenied exception, THE Runtime_Scanner SHALL skip that process and continue iteration
5. IF no process information can be retrieved, THE Runtime_Scanner SHALL still create a Finding for the open port without process metadata
6. THE Runtime_Scanner SHALL NOT raise unhandled exceptions due to permission constraints
7. THE Runtime_Scanner module status SHALL remain "success" even when process metadata cannot be retrieved for all ports

### Requirement 7: Process Metadata Enrichment for Target Ports

**User Story:** As a security analyst, I want detailed process information for all monitored ports, so that I can assess whether expected services are running.

#### Acceptance Criteria

1. WHEN port 11434 is open, THE Runtime_Scanner SHALL include process metadata in the Ollama Finding details
2. WHEN port 1234 is open, THE Runtime_Scanner SHALL include process metadata in the Finding details
3. WHEN port 8000 is open, THE Runtime_Scanner SHALL include process metadata in the Finding details
4. WHEN port 8080 is open, THE Runtime_Scanner SHALL include process metadata in the Finding details
5. WHEN port 5000 is open, THE Runtime_Scanner SHALL include process metadata in the Finding details
6. THE Process_Metadata dictionary SHALL contain keys "process_id", "process_name", and "process_cmdline"
7. THE process_cmdline value SHALL be a list of command-line argument strings

### Requirement 8: Theme Storage Key Unification

**User Story:** As a user, I want my theme preference to persist consistently across both the consent portal and dashboard, so that I don't have to set my theme preference twice.

#### Acceptance Criteria

1. THE Consent_Portal SHALL use the localStorage key "theme" for storing theme preferences
2. THE Consent_Portal SHALL NOT use the localStorage key "hud-theme"
3. WHEN Consent_Portal loads, THE Consent_Portal SHALL read the theme preference from localStorage.getItem('theme')
4. WHEN the user toggles the theme in Consent_Portal, THE Consent_Portal SHALL save the preference using localStorage.setItem('theme', value)
5. THE theme value stored SHALL be either "light" or "dark"
6. THE Telemetry_Dashboard SHALL use the same localStorage key "theme" for theme preference retrieval

### Requirement 9: Theme State Synchronization Across Interfaces

**User Story:** As a user, I want the theme I select in the authorization portal to automatically apply to the dashboard, so that the interface remains visually consistent.

#### Acceptance Criteria

1. WHEN the user sets theme to "dark" in Consent_Portal and navigates to Telemetry_Dashboard, THE Telemetry_Dashboard SHALL display in dark theme
2. WHEN the user sets theme to "light" in Consent_Portal and navigates to Telemetry_Dashboard, THE Telemetry_Dashboard SHALL display in light theme
3. IF no theme preference exists in localStorage, THE Consent_Portal SHALL default to dark theme
4. IF no theme preference exists in localStorage, THE Telemetry_Dashboard SHALL default to dark theme
5. WHEN theme is changed in either interface, THE Theme_State SHALL persist across browser page reloads
6. THE theme preference SHALL be stored in the same browser storage domain for both interfaces

### Requirement 10: Dashboard Filter Compatibility with License Findings

**User Story:** As a compliance officer, I want to filter license findings by approval status in the dashboard, so that I can focus on licenses requiring review.

#### Acceptance Criteria

1. WHEN License_Scanner creates a Finding with status "Approved", THE Finding SHALL be visible when the dashboard filter is set to "Approved & Moderate"
2. WHEN License_Scanner creates a Finding with status "Moderate", THE Finding SHALL be visible when the dashboard filter is set to "Approved & Moderate"
3. WHEN License_Scanner creates a Finding with status "Review / Banned", THE Finding SHALL be visible when the dashboard filter is set to "Review & Banned"
4. THE License_Scanner SHALL set the Finding category to FindingCategory.CONFIGURATION for all license-related findings
5. THE dashboard filtering mechanism SHALL correctly parse the "status" field from Finding details dictionary
