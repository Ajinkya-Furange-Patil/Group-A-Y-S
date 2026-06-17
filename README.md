# 🔍 AI Discovery Scanner

A modular, cross-platform AI detection system that scans host machines to identify AI frameworks, models, processes, runtimes, agents, and exposed API keys — with a visual cyber-themed dashboard and local network remote scanning capability.

> **Team:** Group A-Y-S  
> **Version:** v1.0.0  
> **License:** MIT

---

## ✨ Key Features

- **7 Parallel Scanner Modules** — System info, files, processes, packages, agents, runtimes, and API keys
- **Threaded Discovery Engine** — All modules execute concurrently via `ThreadPoolExecutor`
- **Rule-Based Classification Engine** — Categorizes findings with confidence scores and risk levels
- **Interactive HTML Dashboard** — Glassmorphic cyber-themed report with dark/light themes
- **Local Network Remote Scanning** — Start an HTTP server, scan a friend's machine over Wi-Fi with consent
- **Quick Scan Mode** — Depth-limited scanning for fast demo runs
- **Exception Hardened** — Gracefully handles restricted paths, access denied, and encoding errors
- **Single-File EXE** — Packagable via PyInstaller for deployment without Python

---

## 🏗️ Architecture

```
UI (CLI / HTML / Network Server)
       ↓  trigger scan
Scan Controller
       ↓  dispatch modules
Discovery Engine ── [7 Scanner Modules run in parallel]
       ↓  raw findings
Classification Engine
       ↓  classified items (Confidence & Severity)
Report Generator ── JSON + HTML
       ↓  render dashboard
AI Discovery Dashboard (Cyber-Themed Web UI)
```

---

## 📁 Project Structure

```
System Scanner/
├── main.py                        # CLI entry point (--scan, --server, --quick, etc.)
├── requirements.txt               # Pinned Python dependencies
├── scanner/
│   ├── __init__.py                # Package descriptor (v1.0.0)
│   ├── models.py                  # Shared dataclasses (Finding, ScanResult, ModuleInfo)
│   ├── controller.py              # Scan Controller — orchestrates the full pipeline
│   ├── engine.py                  # Discovery Engine — ThreadPoolExecutor parallel dispatch
│   ├── classifier.py              # Classification Engine — rule-based categorization
│   ├── server.py                  # Local network HTTP server for remote scanning
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── system_scanner.py      # MODULE 01: Host hardware & metadata
│   │   ├── file_scanner.py        # MODULE 02: AI model files on disk
│   │   ├── process_scanner.py     # MODULE 03: Running AI processes
│   │   ├── package_scanner.py     # MODULE 04: Installed AI pip packages
│   │   ├── agent_scanner.py       # MODULE 05: AI agent code patterns
│   │   ├── runtime_scanner.py     # MODULE 06: Active AI runtimes (ports & folders)
│   │   └── api_scanner.py         # MODULE 07: Exposed AI API keys & credentials
│   └── reporter/
│       ├── __init__.py
│       ├── report_generator.py    # JSON & HTML report compiler
│       └── templates/
│           ├── dashboard.html.j2  # Cyber-themed findings dashboard
│           └── consent.html.j2    # Remote scan authorization portal
├── tests/                         # Unit tests (47 tests)
│   ├── test_agent_scanner.py
│   ├── test_api_scanner.py
│   ├── test_classifier.py
│   ├── test_controller.py
│   ├── test_engine.py
│   ├── test_file_scanner.py
│   ├── test_package_scanner.py
│   ├── test_process_scanner.py
│   ├── test_runtime_scanner.py
│   └── test_server.py
├── examples/                      # Sample scan outputs for review
│   ├── sample_report.json
│   └── sample_report.html
└── dist/                          # PyInstaller output (ai_scanner.exe)
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

```bash
python -c "import psutil; import jinja2; print('All dependencies OK')"
```

---

## 📖 Usage Examples

### Run a Full Scan (JSON output to terminal)

```bash
python main.py --scan
```

### Run a Full Scan with JSON + HTML Reports

```bash
python main.py --scan --format both --output report
```
This generates `report.json` and `report.html` in the current directory.

### Quick Scan Mode (Fast Demo)

```bash
python main.py --scan --quick --format both
```
Limits directory traversal depth for instant results (~1 second for file scanning).

### Verbose Debug Logging

```bash
python main.py --scan --verbose
```

### All CLI Options

```
usage: ai_scanner [-h] [--scan] [--quick] [--format {json,html,both}]
                  [--output OUTPUT] [--server] [--port PORT] [--host HOST]
                  [--verbose]

🔍 AI Discovery Scanner — Detect AI frameworks, models, agents, and
runtimes on your machine.

options:
  -h, --help            Show this help message and exit
  --scan                Run a full AI discovery scan
  --quick               Enable quick scan mode (top-level dirs only)
  --format {json,html,both}
                        Output format (default: json)
  --output OUTPUT       Output file path (without extension)
  --server              Start local HTTP server for remote scanning
  --port PORT           Server port (default: 8000)
  --host HOST           Server bind address (default: 0.0.0.0)
  --verbose, -v         Enable verbose/debug logging
```

---

## 🌐 Local Network Remote Scanning

Scan a friend's machine over the same Wi-Fi network with consent-based authorization:

### On the target machine (friend's laptop):

```bash
python main.py --server --port 8000
```

Output:
```
🚀 AI DISCOVERY SCANNER SERVER ACTIVE
============================================================
  Local Access:      http://localhost:8000/
  Network Access:    http://192.168.1.15:8000/
  Host Interface:    0.0.0.0
============================================================
```

### From your machine:

1. Open a browser and navigate to the **Network Access** URL (e.g., `http://192.168.1.15:8000/`)
2. Review the scan scope and check the consent box
3. Click **Authorize & Run Scan**
4. The dashboard auto-redirects after scanning is complete

Or use CLI:
```bash
# Trigger scan remotely
curl "http://192.168.1.15:8000/run-scan?quick=false"

# Download the HTML report
curl -o friend_dashboard.html "http://192.168.1.15:8000/report"

# Download the JSON results
curl -o friend_report.json "http://192.168.1.15:8000/api/results"
```

---

## 🔬 The 7 Scanner Modules

| # | Module | What It Detects | Key Technique |
|---|--------|----------------|---------------|
| 01 | **SystemScanner** | Hostname, OS, CPU, RAM, GPU, disk partitions, IP | `platform`, `psutil`, `nvidia-smi` / `wmic` |
| 02 | **FileScanner** | `.gguf`, `.safetensors`, `.pt`, `.pth`, `.onnx`, `.ckpt`, `.h5` model files | Depth-limited `os.walk` with exclusion pruning |
| 03 | **ProcessScanner** | Running `ollama`, `lmstudio`, `llama.cpp`, `vllm`, AI python scripts | `psutil.process_iter()` with cmdline inspection |
| 04 | **PackageScanner** | `torch`, `tensorflow`, `transformers`, `langchain`, `openai`, `anthropic`, etc. | `pip list --format=json` + `importlib.metadata` fallback |
| 05 | **AgentScanner** | `from langchain`, `Agent(`, `Crew(`, `AssistantAgent(`, AI import patterns in `.py` files | Regex code scanning across project directories |
| 06 | **RuntimeScanner** | Ports `11434`, `8000`, `5000`, `8080` + `.ollama`, `lmstudio` directories | `socket.connect_ex()` + directory existence checks |
| 07 | **APIScanner** | OpenAI, Anthropic, Google, NVIDIA, Cloudflare, HuggingFace, AWS, GitHub tokens in `.env`, `.yaml`, `.py`, `.json` files | Pattern-based regex with masking for secure reporting |

---

## 🧪 Running Tests

The project includes **47 unit tests** covering all modules, the engine, classifier, controller, and HTTP server.

```bash
python -m unittest discover -s tests
```

Expected output:
```
Ran 47 tests in 15.xxx s

OK
```

---

## 📊 Sample CLI Output

```
🔍 AI DISCOVERY SCANNER v1.0.0
============================================================

╔══════════════════════════════════════════════════════════╗
║                    SCAN RESULT SUMMARY                   ║
╚══════════════════════════════════════════════════════════╝
  Target Host:      AJINKYA-PATIL
  Operating System: Windows 11 (x64)
  Total Findings:   47
  Risk Score:       63.3/100
  Scan Duration:    1m 40.56s
  Scanners Run:     7
  Scanners OK:      7
  Scanners Failed:  0
╟──────────────────────────────────────────────────────────╢
║ MODULE RESULTS:                                          ║
╟──────────────────────────────────────────────────────────╢
  [01] SystemScanner      : ✓ SUCCESS 0.706s   (2 findings)
  [02] FileScanner        : ✓ SUCCESS 5.370s   (2 findings)
  [03] ProcessScanner     : ✓ SUCCESS 0.053s
  [04] PackageScanner     : ✓ SUCCESS 1.733s
  [05] AgentScanner       : ✓ SUCCESS 40.242s  (10 findings)
  [06] RuntimeScanner     : ✓ SUCCESS 1.544s   (1 findings)
  [07] APIScanner         : ✓ SUCCESS 100.219s (32 findings)
╚══════════════════════════════════════════════════════════╝
```

---

## 📦 Building the EXE (PyInstaller)

To produce a single standalone executable that runs without Python installed:

```bash
pip install pyinstaller
pyinstaller --onefile --name ai_scanner main.py \
    --add-data "scanner/reporter/templates/*;scanner/reporter/templates/"
```

The output EXE will be in `dist/ai_scanner.exe`.

Test it:
```bash
dist\ai_scanner.exe --scan --format both --output report
```

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Commit** your changes: `git commit -m "Add your feature"`
4. **Push** to the branch: `git push origin feature/your-feature`
5. **Open** a Pull Request with at least **1 approval** before merging

### Code Standards
- All public functions must have docstrings
- Use `pathlib.Path` for cross-platform path handling
- Wrap filesystem/process I/O in `try/except` (PermissionError, FileNotFoundError, OSError)
- Run `python -m unittest discover -s tests` before pushing

---

## ⚠️ Known Issues & Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: psutil` | venv not activated | Run `pip install -r requirements.txt` inside the venv |
| `ModuleNotFoundError: scanner` | Running from wrong directory | `cd` into `System Scanner/` (where `scanner/` folder lives) |
| Emoji rendering broken in cmd | Default cp1252 encoding | Use PowerShell or Windows Terminal, or run `chcp 65001` first |
| GPU finding missing | No GPU or drivers not installed | Expected — SystemScanner still reports host info |
| Port 8000 in use (server mode) | Another service on the port | Use `--port 8080` or another free port |

---

## 👥 Team

| Member | Role | Focus |
|--------|------|-------|
| **Person A** | Lead / Backend Architect | Controller, Engine, Classifier, Integration |
| **Person B** | Module Developer | All 7 Scanner Modules |
| **Person C** | UI / Report / Packaging | Dashboard, CLI, Server, README, PyInstaller |

---

## 📄 License

This project is licensed under the MIT License.
