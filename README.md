# 🔍 AI Discovery Scanner

A modular, cross-platform AI detection and audit system that scans host machines to identify AI frameworks, models, processes, runtimes, agents, and exposed API keys. It features a stunning, cyber-themed interactive dashboard, standalone CLI/GUI launchers, policy enforcement capabilities, and local network remote scanning.

> **Team:** Group A-Y-S  
> **Version:** v1.4.0 (Latest Release)  
> **License:** MIT  
> **Target OS:** Windows 10/11, macOS, Linux  

---

## ✨ Key Features

- **10 Scanner Modules** — System info, files, processes, packages, agents, runtimes, API keys, MCP configurations, copyleft licenses, and regulatory compliance.
- **Dual Executable Support** — Portable binaries for both **CLI** (`System Scanner.exe` with interactive menus) and **GUI** (`Client System Scanner.exe` with embedded browser using `pywebview`).
- **Heuristics & Rule-Based Classification** — Automatically classifies findings by confidence score, severity level, and specific risk vectors (e.g., DPDP Act, CERT-In guidelines, SEBI CSCRF).
- **Stunning Glassmorphic Dashboard (v1.4.0 UI)** — A premium cyber-themed dashboard with persistent theme toggling (Light/Dark), clickable executive metrics, sticky compliance tracking, and smooth transitions.
- **Custom Scan Configurations** — Support for scanning custom folders, target depths (Quick: 2, Normal: 10, Deep: 20, Custom, Unlimited), and configuration previewing.
- **Local Network Remote Scanning** — Spawn an HTTP scan server on a target machine, check consent-based remote scanning authorization, and view results remotely.
- **Automated Version Control** — Semantic versioning (SemVer) with automated Git pre-commit hooks and REST API versioning endpoints.
- **Hardened Error Handling** — Exception-hardened file traversal, graceful permissions handling, and support for terminal encoding variations.

---

## 🏗️ Architecture

```
                       UI CLIENTS (CLI Menu / GUI App / Web browser)
                                           │
                                           ▼
                                    Scan Controller
                                           │
                      ┌────────────────────┴────────────────────┐
                      ▼                                         ▼
               Discovery Engine                       Enforcement Engine
         (Parallel thread pool dispatch)         (Disable Copilot, terminate agents)
                      │
        ┌─────────────┼─────────────┐
        │             │             │
   Modules 01-04  Modules 05-07  Modules 08-10
   (Sys, File,    (Agent, Port,  (MCP, Copyleft,
   Proc, Pip)     API keys)      Regulatory)
        │             │             │
        └─────────────┼─────────────┘
                      ▼
            Classification Engine (Confidence & Severity)
                      │
                      ▼
               Report Generator
         (JSON / HTML Dashboard / Excel)
                      │
                      ▼
          History DB & Output Files (ai_scanner_history.db / report.json)
```

---

## 📁 Project Structure

The codebase is organized with the primary application source located inside the `System Scanner` folder:

```
System Scanner/
├── main.py                        # CLI entry point (interactive menu or scan flags)
├── gui.py                         # GUI entry point (runs native pywebview window)
├── requirements.txt               # Pinned Python dependencies
├── auto_version_bump.py           # Manual version bump script
├── bump_version.bat               # Windows batch wrapper for version bumping
├── setup_auto_version.py          # Git pre-commit hook installer
├── version_history.json           # Change log tracking version bumps
├── build_both_versions.py         # Python build script for PyInstaller
├── scanner/
│   ├── __init__.py                # Package descriptor
│   ├── models.py                  # Shared dataclasses (Finding, ScanResult, ModuleInfo)
│   ├── controller.py              # Scan Controller — orchestrates the full pipeline
│   ├── engine.py                  # Discovery Engine — ThreadPoolExecutor parallel dispatch
│   ├── classifier.py              # Classification Engine — rule-based categorization
│   ├── server.py                  # Local network HTTP server for remote scanning
│   ├── version_manager.py         # Core version control module
│   ├── enforcement.py             # Policy enforcement logic
│   ├── signature_verifier.py      # Module verification & signature utility
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── system_scanner.py      # MODULE 01: Host hardware & metadata
│   │   ├── file_scanner.py        # MODULE 02: AI model files on disk (.gguf, .safetensors, etc.)
│   │   ├── process_scanner.py     # MODULE 03: Running AI processes & daemons (ollama, vllm, etc.)
│   │   ├── package_scanner.py     # MODULE 04: Installed AI python/pip packages (torch, transformers)
│   │   ├── agent_scanner.py       # MODULE 05: AI agent code patterns (langchain, crewai, etc.)
│   │   ├── runtime_scanner.py     # MODULE 06: Active AI runtimes (ports & directories)
│   │   ├── api_scanner.py         # MODULE 07: Exposed AI API keys & credentials
│   │   ├── mcp_scanner.py         # MODULE 08: Model Context Protocol configs
│   │   ├── license_scanner.py     # MODULE 09: License compliance (AST copyleft detection)
│   │   └── compliance_scanner.py  # MODULE 10: Security compliance checks (DPDP, CERT-In, SEBI)
│   └── reporter/
│       ├── __init__.py
│       ├── report_generator.py    # JSON, HTML, and Excel report compiler
│       └── templates/
│           ├── dashboard.html.j2  # Cyber-themed findings dashboard
│           └── consent.html.j2    # Remote scan authorization portal
├── tests/                         # Unit tests (173 tests)
│   ├── test_agent_scanner.py
│   ├── test_api_scanner.py
│   ├── test_classifier.py
│   ├── test_compliance_scanner.py
│   ├── test_controller.py
│   ├── test_engine.py
│   ├── test_file_scanner.py
│   ├── test_license_scanner.py
│   ├── test_mcp_scanner.py
│   ├── test_package_scanner.py
│   ├── test_process_scanner.py
│   ├── test_runtime_scanner.py
│   ├── test_server.py
│   └── ... (22 unit test suites total)
└── dist/                          # Compiled standalone executables
    ├── System Scanner.exe         # Standalone CLI executable (10.98 MB)
    └── Client System Scanner.exe  # Standalone GUI executable (18.86 MB)
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10 or higher
- Windows 10/11, macOS, or Linux

### 2. Environment Setup

```bash
# Clone the repository
git clone https://github.com/Ajinkya-Furange-Patil/Group-A-Y-S.git
cd "Group-A-Y-S/System Scanner"

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Verify Installation
Ensure core dependencies are working correctly:
```bash
python -c "import psutil; import jinja2; import webview; print('All dependencies OK')"
```

---

## 📖 Execution Modes

### 1. Interactive CLI Menu
Run the main script without arguments to open a comprehensive interactive menu wizard:
```bash
python main.py
```
This launches the control panel menu:
```
======================================================================
    AI DISCOVERY SCANNER - Command Line Interface
    System Security & Compliance Analysis Tool
======================================================================

----------------------------------------------------------------------
MAIN MENU
----------------------------------------------------------------------
  [1] Run Quick Scan (Headless)
  [2] Run Full Scan (Headless)
  [3] Run Custom Scan (Configure Options)
  [4] Start Web UI Dashboard
  [5] View Last Scan Results
  [6] Export Last Scan (JSON)
  [7] Export Last Scan (HTML)
  [8] About / Help
  [0] Exit
----------------------------------------------------------------------
```

### 2. Standalone Desktop GUI
To open the borderless GUI windowed application (powered by `pywebview`, which automatically binds to a free random local port and wraps the interface):
```bash
python gui.py
```

### 3. Local Web UI Dashboard
Select option `[4]` from the CLI menu or start the scan server to access the dashboard in an external browser:
- Open your browser to `http://localhost:8000/`.
- Review consent parameters, select your options, and trigger scans interactively.

---

## ⚙️ Custom Scan Configurations

Select Option `[3]` in the interactive CLI menu to set custom parameters:
1. **Target Region:**
   - Full System Scan
   - Custom Folder (specify path, e.g., `C:\Projects\`)
   - GitHub Repository (future scope)
   - Google Drive / Cloud (future scope)
2. **Scan Depth:**
   - Quick Mode (2 levels — fast demo)
   - Normal (10 levels — recommended)
   - Deep Scan (20 levels — thorough analysis)
   - Custom Depth (user-defined number)
   - Unlimited Depth (0 levels — scans everything)

---

## 🌐 Local Network Remote Scanning

You can scan a target machine on the same local Wi-Fi or Ethernet network using the consent portal:

1. **On the target machine:**
   Run the scanner server. Select Option `[4]` on `main.py` or run:
   ```bash
   python main.py
   # Select Option 4
   ```
   *Note: In production executable mode, run `System Scanner.exe` and select Option 4.*
   The terminal will output the local network URL (e.g., `http://192.168.1.15:8000/`).

2. **From your machine:**
   - Open a browser and go to the Network Access URL (`http://192.168.1.15:8000/`).
   - Check the authorization consent box and click **Authorize & Run Scan**.
   - The scanner runs remotely in the background and auto-redirects you to the report once complete.

3. **Or use CLI / Curl to access API endpoints:**
   ```bash
   # Trigger scan remotely
   curl "http://192.168.1.15:8000/run-scan?quick=false"

   # Download the versioned reports via API
   curl -o report_v1_4_0.json "http://192.168.1.15:8000/api/export/json"
   curl -o report_v1_4_0.html "http://192.168.1.15:8000/api/export/html"
   curl -o report_v1_4_0.xlsx "http://192.168.1.15:8000/api/export/excel"
   ```

---

## 🔬 The 10 Scanner Modules

| # | Module | What It Detects | Key Technique |
|---|--------|----------------|---------------|
| 01 | **SystemScanner** | Hostname, OS, CPU, RAM, GPU, disk partitions, local IP | `platform`, `psutil`, `nvidia-smi` / `wmic` checks |
| 02 | **FileScanner** | AI model files (`.gguf`, `.safetensors`, `.pt`, `.pth`, `.onnx`, `.ckpt`, `.h5`) | Depth-limited `os.walk` traversal with speed exclusions |
| 03 | **ProcessScanner** | Running AI processes & daemons (`ollama`, `vllm`, `kiro`, `codex`, `antigravity`, `copilot`) | `psutil.process_iter()` with command-line regex parsing |
| 04 | **PackageScanner** | Installed python AI packages (`torch`, `tensorflow`, `transformers`, `langchain`, etc.) | `pip list --format=json` with fallback `importlib.metadata` |
| 05 | **AgentScanner** | AI agent code patterns (`from langchain`, `Agent(`, `Crew(`, `AssistantAgent(`) | Heuristic regex multi-file parsing |
| 06 | **RuntimeScanner** | Active AI runtime instances (ports `11434`, `8000`, `5000`, `8080` + `.ollama` folders) | Socket connect scans with port-to-process metadata mapping |
| 07 | **APIScanner** | Exposed credentials & API keys (OpenAI, Anthropic, Google, NVIDIA, AWS, GitHub) | Regex pattern matching in `.env`, `.yaml`, `.py`, `.json` files |
| 08 | **MCPScanner** | Model Context Protocol configurations & clients | Searches config files for compliance vectors |
| 09 | **LicenseScanner** | AST-based copyleft license detection and restrictive import analysis | Python Abstract Syntax Tree analysis for compliance verification |
| 10 | **ComplianceScanner** | Security posture audits against regulatory guidelines | Maps metadata findings to DPDP Act, CERT-In, and SEBI CSCRF |

---

## 🔄 Version Management System

The scanner features a **Semantic Versioning (SemVer)** automatic tracking system:
1. **Single Source of Truth:** Managed in [version_manager.py](file:///d:/College%20Work/Internship/Group%20A-Y-S/System%20Scanner/System%20Scanner/scanner/version_manager.py).
2. **Pre-commit Hook:** Automatically bumps patch versions on git commit. To install:
   ```bash
   python setup_auto_version.py install
   ```
3. **Manual Bumping:** Increment major, minor, or patch versions via:
   ```bash
   python auto_version_bump.py [patch|minor|major]
   ```
4. **Versioned Exports:** Exported filenames are automatically appended with the current version (e.g., `ai_scan_report_v1_4_0.xlsx`).

---

## 🎨 UI/UX Dashboard Enhancements (v1.4.0)

Version **v1.4.0** introduces professional design aesthetics and interactive features:
- **Theme Toggle Switch:** A modern checkbox toggle with Light/Dark labels and persistent `localStorage` theme state (`scanner-theme`).
- **Interactive Metrics Navigation:** Click on any summary metric card (AI Models, API Keys, etc.) to scroll smoothly to that module's section with a visual 2-second highlight pulse.
- **Sticky Compliance Sidebar:** The Module Compliance Panel remains sticky on the right, displaying execution times and statuses. Clicking on a module name scrolls you directly to its detailed card.
- **Improved Tables:** Altering row background styling, 2px borders, wider padding (12px 16px), and translation animations on hover.
- **Future Badges:** Google Drive and GitHub repository options are clearly marked with red "FUTURE" badges and styled with a disabled, non-interactable opacity state.

---

## 🧪 Running Tests

The test suite includes **173 unit tests** covering all modules, parsing utilities, endpoints, and exporters.

To execute tests:
```bash
python -m unittest discover -s tests
```

---

## 📊 Sample CLI Output

```
======================================================================
    AI DISCOVERY SCANNER - Command Line Interface
    System Security & Compliance Analysis Tool
======================================================================

Custom Scan Configuration:
----------------------------------------------------------------------
Target:    Full System Scan
Depth:     10 levels
Mode:      Full
----------------------------------------------------------------------

Scan Starting...

  [01] SystemScanner      : ✓ SUCCESS 0.451s  (2 findings)
  [02] FileScanner        : ✓ SUCCESS 3.234s  (3 findings)
  [03] ProcessScanner     : ✓ SUCCESS 0.089s  (1 findings)
  [04] PackageScanner     : ✓ SUCCESS 1.120s  (14 findings)
  [05] AgentScanner       : ✓ SUCCESS 1.890s  (5 findings)
  [06] RuntimeScanner     : ✓ SUCCESS 0.654s  (1 findings)
  [07] APIScanner         : ✓ SUCCESS 4.543s  (0 findings)
  [08] MCPScanner         : ✓ SUCCESS 0.231s  (0 findings)
  [09] LicenseScanner     : ✓ SUCCESS 1.450s  (2 findings)
  [10] ComplianceScanner  : ✓ SUCCESS 0.312s  (8 findings)

======================================================================
SCAN COMPLETE - SUMMARY
======================================================================
Hostname: AJINKYA-PATIL
OS: Windows 11 (10.0.22631)
Duration: 13.97 seconds
Modules Executed: 10
Findings: 36
Risk Score: 52.4/100
======================================================================
✓ Results saved to: report.json
✓ JSON report exported successfully
```

---

## 📦 Building Standalone Binaries (PyInstaller)

To compile self-contained executables for both CLI and GUI versions:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Build both versions using the build coordinator:
   ```bash
   python build_both_versions.py
   ```
   This will yield:
   - **`dist/System Scanner.exe`** (CLI, ~10.98 MB)
   - **`dist/Client System Scanner.exe`** (GUI, ~18.86 MB)

---

## ⚠️ Troubleshooting & Known Issues

- **Excel Export Fails / Disabled:** Excel export requires `openpyxl`. Install it via `pip install openpyxl`.
- **Antivirus Flags:** Standalone executables compiled via PyInstaller may trigger false positives. You can add them to exclusions or build directly from source.
- **Port Conflict (Port 8000):** If port 8000 is occupied, the GUI version will automatically find a free port. For the CLI version, make sure port 8000 is clear, or launch using Python directly and adjust [main.py](file:///d:/College%20Work/Internship/Group%20A-Y-S/System%20Scanner/System%20Scanner/main.py#L152).
- **Emoji Rendering in Command Prompt:** If console icons render incorrectly, run `chcp 65001` in your terminal prior to running the scanner.

---

## 👥 Team

- **Person A** — Lead / Backend Architect
- **Person B** — Module Developer
- **Person C** — UI / Report / Packaging

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
