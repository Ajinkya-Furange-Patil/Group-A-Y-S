# Design Document: License, Port, and Theme Enhancements

## Overview

This design specifies the implementation for three enhancements to the AI Discovery System Scanner:

1. **License Scanner Module (Module 09)**: A new scanner module that detects and classifies software licenses using taxonomy-based classification, AST-based Python code analysis, and restrictive import detection.

2. **Port-to-Process ID Mapping**: Enhancement to the Runtime Scanner (Module 06) to identify which processes are listening on monitored network ports using psutil with graceful permission error handling.

3. **UI Theme Synchronization**: Unification of theme storage keys across the Remote Authorization Portal (consent.html.j2) and Telemetry Dashboard (dashboard.html.j2) to enable consistent theme preferences.

## System Architecture

### Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                     ScanController                          │
│                 (Module Registration)                       │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ├──> Module 09: LicenseScanner
                    │    ├─> License Taxonomy Classifier
                    │    ├─> AST Parser (Docstring Analysis)
                    │    └─> Import Statement Analyzer
                    │
                    ├──> Module 06: RuntimeScanner (Enhanced)
                    │    ├─> Port Scanner
                    │    └─> Process Metadata Retriever (psutil)
                    │
                    └──> Reporter (Templates)
                         ├─> consent.html.j2 (Theme: "theme" key)
                         └─> dashboard.html.j2 (Theme: "theme" key)
```

## Design Components

### 1. License Scanner Module (Module 09)

#### 1.1 Module Structure

**File**: `scanner/modules/license_scanner.py`

The License Scanner follows the established scanner module pattern:

```python
class LicenseScanner:
    MODULE_NAME = "LicenseScanner"
    MODULE_NUMBER = 9
    
    def __init__(self, scan_folder: str | None = None, max_depth: int | None = None):
        self.scan_folder = scan_folder
        self.max_depth = max_depth
    
    def scan(self) -> list[Finding]:
        """Entry point called by Discovery Engine"""
        pass
```

#### 1.2 License Taxonomy Database

The taxonomy maps license types to risk levels and approval statuses:

```python
LICENSE_TAXONOMY = {
    "MIT": {
        "risk_level": RiskLevel.INFO,
        "status": "Approved",
        "description": "Permissive open source license"
    },
    "Apache 2.0": {
        "risk_level": RiskLevel.INFO,
        "status": "Approved",
        "description": "Permissive with patent grant"
    },
    "LGPL": {
        "risk_level": RiskLevel.MEDIUM,
        "status": "Moderate",
        "description": "Weak copyleft license"
    },
    "GPL": {
        "risk_level": RiskLevel.HIGH,
        "status": "Review / Banned",
        "description": "Strong copyleft license"
    },
    "AGPL": {
        "risk_level": RiskLevel.CRITICAL,
        "status": "Review / Banned",
        "description": "Network copyleft license"
    },
    "Polyform Shield": {
        "risk_level": RiskLevel.HIGH,
        "status": "Review / Banned",
        "description": "Commercial restriction license"
    },
    "Proprietary": {
        "risk_level": RiskLevel.MEDIUM,
        "status": "Review / Banned",
        "description": "Proprietary or closed source"
    }
}
```

#### 1.3 AST-Based Copyleft Detection

Uses Python's `ast` module to parse source files and detect license headers in module docstrings:

```python
def analyze_python_file(file_path: Path) -> list[Finding]:
    findings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source, filename=str(file_path))
        
        # Extract module-level docstring
        docstring = ast.get_docstring(tree)
        
        if docstring:
            # Check for GPL patterns
            if re.search(r'\bGPL\b|\bGeneral Public License\b', docstring, re.IGNORECASE):
                findings.append(create_license_finding(
                    file_path=file_path,
                    line_number=1,
                    license_type="GPL",
                    title="Code License: GPL Header",
                    docstring_snippet=docstring[:200],
                    confidence=0.90
                ))
            
            # Check for AGPL patterns
            if re.search(r'\bAGPL\b|\bAffero General Public License\b', docstring, re.IGNORECASE):
                findings.append(create_license_finding(
                    file_path=file_path,
                    line_number=1,
                    license_type="AGPL",
                    title="Code License: AGPL Header",
                    docstring_snippet=docstring[:200],
                    confidence=0.90
                ))
    
    except SyntaxError:
        logger.debug("Failed to parse %s (syntax error)", file_path)
    except Exception as e:
        logger.debug("Error analyzing %s: %s", file_path, e)
    
    return findings
```

#### 1.4 Restrictive Import Detection

Maintains a dictionary mapping restricted libraries to their license types:

```python
RESTRICTED_IMPORTS = {
    "PyQt5": {"license": "GPL", "risk": RiskLevel.HIGH},
    "PyQt6": {"license": "GPL", "risk": RiskLevel.HIGH},
    "mysql.connector": {"license": "GPL", "risk": RiskLevel.HIGH},
    "pygobject": {"license": "LGPL", "risk": RiskLevel.MEDIUM},
    "readline": {"license": "GPL", "risk": RiskLevel.HIGH},
}

def check_imports(tree: ast.AST, file_path: Path) -> list[Finding]:
    findings = []
    
    for node in ast.walk(tree):
        # Check direct imports: import PyQt5
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split('.')[0]
                if module_name in RESTRICTED_IMPORTS:
                    findings.append(create_import_finding(
                        file_path=file_path,
                        line_number=node.lineno,
                        module_name=module_name,
                        import_data=RESTRICTED_IMPORTS[module_name],
                        confidence=0.85
                    ))
        
        # Check from-imports: from PyQt5 import QtCore
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split('.')[0]
                if module_name in RESTRICTED_IMPORTS:
                    findings.append(create_import_finding(
                        file_path=file_path,
                        line_number=node.lineno,
                        module_name=module_name,
                        import_data=RESTRICTED_IMPORTS[module_name],
                        confidence=0.85
                    ))
    
    return findings
```

#### 1.5 Controller Integration

**File**: `scanner/controller.py` (modification)

Add License Scanner registration in the `_register_modules` method:

```python
# ── MODULE 09: License Scanner ───────────────────────────────
try:
    from scanner.modules.license_scanner import LicenseScanner
    self._engine.register_module(
        LicenseScanner(
            scan_folder=self._scan_folder, 
            max_depth=self._max_depth
        )
    )
    logger.info("Successfully registered MODULE 09: LicenseScanner")
except ImportError:
    logger.debug("MODULE 09: LicenseScanner not available (ImportError)")
except Exception as e:
    logger.warning("Failed to initialize MODULE 09: LicenseScanner: %s", e, exc_info=True)
```

### 2. Port-to-Process ID Mapping Enhancement

#### 2.1 Enhanced Process Metadata Retrieval

**File**: `scanner/modules/runtime_scanner.py` (modification)

Replace the existing `_find_process_for_port` function with enhanced version:

```python
def _find_process_for_port(port: int) -> dict[str, Any] | None:
    """Find process info listening on a local port using psutil.
    
    Implements two-tier strategy:
    1. Fast path: psutil.net_connections() - requires elevated permissions
    2. Fallback: Iterate through all processes - works with user permissions
    
    Returns:
        Dictionary with keys: process_id (int), process_name (str), 
        process_cmdline (list[str]), or None if not found
    """
    try:
        import psutil
    except ImportError:
        logger.debug("RuntimeScanner: psutil is not available")
        return None

    # Strategy 1: Fast path using net_connections (may require admin)
    try:
        conns = psutil.net_connections(kind="inet")
        for conn in conns:
            if (conn.laddr and 
                conn.laddr.port == port and 
                conn.status == "LISTEN"):
                
                if conn.pid is not None:
                    try:
                        p = psutil.Process(conn.pid)
                        return {
                            "process_id": conn.pid,
                            "process_name": p.name(),
                            "process_cmdline": p.cmdline(),
                        }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        return {
                            "process_id": conn.pid,
                            "process_name": "Unknown (Access Denied)",
                            "process_cmdline": [],
                        }
    except (psutil.AccessDenied, PermissionError) as e:
        logger.debug("RuntimeScanner: net_connections() denied (%s), trying fallback", e)
    except Exception as e:
        logger.debug("RuntimeScanner: net_connections() failed: %s", e)

    # Strategy 2: Fallback to process iteration
    try:
        for p in psutil.process_iter(["pid", "name"]):
            try:
                conns = p.connections(kind="inet")
                for conn in conns:
                    if (conn.laddr and 
                        conn.laddr.port == port and 
                        conn.status == "LISTEN"):
                        
                        try:
                            return {
                                "process_id": p.pid,
                                "process_name": p.name(),
                                "process_cmdline": p.cmdline(),
                            }
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            return {
                                "process_id": p.pid,
                                "process_name": "Unknown (Access Denied)",
                                "process_cmdline": [],
                            }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process terminated or access denied, skip it
                continue
            except Exception as e:
                logger.debug("RuntimeScanner: Error checking process %s: %s", p.pid, e)
                continue
    except Exception as e:
        logger.debug("RuntimeScanner: Process iteration failed: %s", e)

    return None
```

#### 2.2 Finding Enhancement

Update the port finding creation to include process metadata:

```python
# In the run() function, for each detected port:
details = {
    "port": port,
    "label": label,
    "host": "127.0.0.1",
}

# Attempt to find process info
process_info = _find_process_for_port(port)
if process_info:
    details["process_id"] = process_info["process_id"]
    details["process_name"] = process_info["process_name"]
    details["process_cmdline"] = process_info["process_cmdline"]

findings.append(
    Finding(
        module_name=MODULE_NAME,
        title=f"Active LLM Service Port: {port}",
        description=f"An active service was detected listening on port {port} ({label}).",
        source=f"127.0.0.1:{port}",
        category=FindingCategory.LLM_RUNTIME,
        risk_level=RiskLevel.MEDIUM,
        confidence=0.80,
        details=details,
    )
)
```

### 3. UI Theme Synchronization

#### 3.1 Consent Portal Theme Management

**File**: `scanner/reporter/templates/consent.html.j2` (modification)

Replace localStorage key `"hud-theme"` with `"theme"`:

**Current code (lines to change)**:
```javascript
// OLD: 
const savedTheme = localStorage.getItem('hud-theme');

// NEW:
const savedTheme = localStorage.getItem('theme');

// OLD:
localStorage.setItem('hud-theme', 'light');

// NEW:
localStorage.setItem('theme', 'light');

// OLD:
localStorage.setItem('hud-theme', 'dark');

// NEW:
localStorage.setItem('theme', 'dark');
```

**Location in file**: Search for all occurrences of `'hud-theme'` and replace with `'theme'`.

#### 3.2 Dashboard Theme Management

**File**: `scanner/reporter/templates/dashboard.html.j2` (verification)

Ensure the dashboard uses the same `'theme'` localStorage key. Search for theme-related JavaScript code and verify it matches:

```javascript
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'light') {
    body.classList.remove('dark-theme');
    themeBtn.textContent = '// THEME: LIGHT';
} else {
    body.classList.add('dark-theme');
    themeBtn.textContent = '// THEME: DARK';
}

function toggleTheme() {
    if (body.classList.contains('dark-theme')) {
        body.classList.remove('dark-theme');
        themeBtn.textContent = '// THEME: LIGHT';
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.add('dark-theme');
        themeBtn.textContent = '// THEME: DARK';
        localStorage.setItem('theme', 'dark');
    }
}
```

#### 3.3 Theme State Flow

```
User Action in Consent Portal
    │
    ├──> Toggle Theme Button Click
    │
    ├──> localStorage.setItem('theme', 'light' | 'dark')
    │
    └──> User navigates to Dashboard
         │
         └──> Dashboard loads
              │
              ├──> localStorage.getItem('theme')
              │
              └──> Apply theme class to body
```

## Data Models

### Finding Structure for License Scanner

```python
Finding(
    module_name="LicenseScanner",
    title="Code License: GPL Header" | "Restrictive Import: PyQt5",
    description="Detailed explanation of the license finding",
    source="<file_path>:<line_number>",
    category=FindingCategory.CONFIGURATION,
    risk_level=RiskLevel.HIGH | RiskLevel.MEDIUM | RiskLevel.INFO,
    details={
        "file_path": str,
        "line_number": int,
        "license_type": str,
        "status": str,  # "Approved", "Moderate", "Review / Banned"
        "imported_library": str,  # (for import findings only)
        "docstring_snippet": str,  # (for docstring findings only)
    },
    confidence=0.85 | 0.90
)
```

### Finding Structure for Enhanced Runtime Scanner

```python
Finding(
    module_name="RuntimeScanner",
    title="Active LLM Service Port: 11434",
    description="An active service was detected listening on port 11434 (Ollama).",
    source="127.0.0.1:11434",
    category=FindingCategory.LLM_RUNTIME,
    risk_level=RiskLevel.MEDIUM,
    details={
        "port": int,
        "label": str,
        "host": str,
        "process_id": int,  # NEW
        "process_name": str,  # NEW
        "process_cmdline": list[str],  # NEW
    },
    confidence=0.80
)
```

## Error Handling

### License Scanner Error Handling

1. **Import Errors**: Module fails gracefully if not available
2. **AST Parse Errors**: Log debug message and continue to next file
3. **File Access Errors**: Skip file and continue scanning
4. **Encoding Errors**: Attempt UTF-8, skip file if fails

### Runtime Scanner Error Handling

1. **psutil.AccessDenied**: Catch and attempt fallback strategy
2. **psutil.PermissionError**: Catch and attempt fallback strategy
3. **psutil.NoSuchProcess**: Skip process and continue iteration
4. **Missing psutil**: Return None from process lookup, continue with port finding without process info

### Theme Synchronization Error Handling

1. **Missing localStorage**: Default to dark theme
2. **Invalid theme value**: Default to dark theme
3. **localStorage read/write errors**: Fail silently, use default theme

## Testing Strategy

### License Scanner Testing

1. **Taxonomy Classification**: Verify each license type maps to correct risk level and status
2. **AST Docstring Detection**: Test GPL/AGPL pattern matching in various docstring formats
3. **Import Detection**: Test both `import` and `from ... import` statement patterns
4. **File Scanning**: Test recursion with depth limits
5. **Error Resilience**: Test with invalid Python files, permission-denied files

### Runtime Scanner Testing

1. **Process Lookup - Happy Path**: Test with known service on known port
2. **Process Lookup - Permission Denied**: Test net_connections() fallback
3. **Process Lookup - No Process**: Test port open but no process info available
4. **Metadata Serialization**: Verify process_id, process_name, process_cmdline in Finding.details

### Theme Synchronization Testing

1. **Cross-Page Persistence**: Set theme in consent portal, verify in dashboard
2. **Default Theme**: Clear localStorage, verify both pages default to dark
3. **Toggle Behavior**: Verify toggle button updates localStorage and UI
4. **Page Reload**: Verify theme persists after page reload

## Correctness Properties

### Property 1: License Taxonomy Consistency
**Description**: All license findings must have a status field matching the taxonomy definition.

**Formal Statement**:
```
∀ finding ∈ LicenseScanner.findings:
  finding.details["license_type"] ∈ LICENSE_TAXONOMY.keys() →
    finding.details["status"] = LICENSE_TAXONOMY[finding.details["license_type"]]["status"]
```

**Validation**: Every license finding includes a status field that matches the taxonomy.

### Property 2: AST Confidence Bound
**Description**: AST-based license detections must have confidence = 0.90.

**Formal Statement**:
```
∀ finding ∈ LicenseScanner.findings:
  "docstring_snippet" ∈ finding.details.keys() →
    finding.confidence = 0.90
```

**Validation**: All docstring-based findings have exactly 0.90 confidence.

### Property 3: Import Confidence Bound
**Description**: Import-based license detections must have confidence = 0.85.

**Formal Statement**:
```
∀ finding ∈ LicenseScanner.findings:
  "imported_library" ∈ finding.details.keys() →
    finding.confidence = 0.85
```

**Validation**: All import-based findings have exactly 0.85 confidence.

### Property 4: Process Metadata Completeness
**Description**: When process info is found, all three fields (process_id, process_name, process_cmdline) must be present.

**Formal Statement**:
```
∀ finding ∈ RuntimeScanner.findings:
  "process_id" ∈ finding.details.keys() →
    ("process_name" ∈ finding.details.keys() ∧
     "process_cmdline" ∈ finding.details.keys())
```

**Validation**: Process metadata is always complete or entirely absent.

### Property 5: Theme Key Consistency
**Description**: Both templates must use the same localStorage key for theme persistence.

**Formal Statement**:
```
localStorage_key(consent.html.j2) = localStorage_key(dashboard.html.j2) = "theme"
```

**Validation**: Both templates read and write to the same "theme" key.

### Property 6: Finding Category Consistency
**Description**: All license findings must use FindingCategory.CONFIGURATION.

**Formal Statement**:
```
∀ finding ∈ LicenseScanner.findings:
  finding.category = FindingCategory.CONFIGURATION
```

**Validation**: License scanner produces only CONFIGURATION category findings.

### Property 7: Port Finding Resilience
**Description**: RuntimeScanner must succeed even when process metadata cannot be retrieved.

**Formal Statement**:
```
∀ port ∈ open_ports:
  _find_process_for_port(port) = None →
    ∃ finding ∈ RuntimeScanner.findings: finding.details["port"] = port
```

**Validation**: Port findings are created regardless of process lookup success.

### Property 8: No Unhandled Permission Exceptions
**Description**: RuntimeScanner must catch all permission-related exceptions.

**Formal Statement**:
```
∀ exception ∈ {AccessDenied, PermissionError}:
  exception raised in _find_process_for_port() →
    exception is caught ∧ module_status ≠ "error"
```

**Validation**: Permission errors never propagate to module failure.

## Implementation Notes

### File Paths

- **License Scanner**: `scanner/modules/license_scanner.py` (new file)
- **Controller**: `scanner/controller.py` (modification at line ~145)
- **Runtime Scanner**: `scanner/modules/runtime_scanner.py` (modification of `_find_process_for_port` function)
- **Consent Portal**: `scanner/reporter/templates/consent.html.j2` (JavaScript modification)
- **Dashboard**: `scanner/reporter/templates/dashboard.html.j2` (verification, possible JavaScript modification)

### Dependencies

- **Python Standard Library**: `ast`, `re`, `pathlib`, `logging`
- **External**: `psutil` (already used in RuntimeScanner)

### Configuration

- **Scan Folder**: Passed from ScanController to LicenseScanner
- **Max Depth**: Passed from ScanController to LicenseScanner
- **Target Ports**: Defined in RuntimeScanner.PORT_MAP (no changes needed)

## Dashboard Integration

### License Finding Display

License findings will appear in the dashboard with:
- **Category Badge**: "Configuration"
- **Severity Badge**: Color-coded based on risk level (Critical/High/Medium/Info)
- **Filter Compatibility**: Findings with status "Approved" or "Moderate" appear under "Approved & Moderate" filter
- **Status Field**: Displayed in finding details metadata

### Process Metadata Display

Enhanced Runtime Scanner findings will show:
- **Process ID**: Integer process identifier
- **Process Name**: Executable name (e.g., "ollama", "python.exe")
- **Command Line**: Full command with arguments
- **Graceful Degradation**: When process info is unavailable, only port/label displayed

### Theme Synchronization

- User sets theme in consent portal → localStorage updated
- User navigates to dashboard → theme loaded from localStorage
- Theme persists across browser sessions
- Both interfaces start with dark theme if no preference saved

## Security Considerations

1. **File System Access**: License Scanner respects max_depth to prevent excessive recursion
2. **Process Inspection**: RuntimeScanner handles permission errors gracefully without requiring elevation
3. **Code Execution**: AST parsing is safe (no `eval` or `exec`)
4. **Cross-Site Storage**: localStorage is domain-scoped, no cross-origin issues

## Performance Considerations

1. **License Scanner**: Scans only Python files (`.py` extension filter)
2. **AST Parsing**: Faster than regex on full file content
3. **Process Lookup**: Fallback iteration only when fast path fails
4. **Theme Switching**: CSS class toggle is instant, no page reload required
