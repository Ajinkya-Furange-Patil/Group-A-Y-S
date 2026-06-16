# 🔍 AI Discovery Scanner

A modular, cross-platform AI detection system designed to scan host machines and identify AI frameworks, models, processes, runtimes, agents, and API keys.

---

## 🏗️ Project Architecture & Flow

```
UI (CLI / HTML)
       ↓  trigger scan
Scan Controller
       ↓  dispatch modules
Discovery Engine ── [7 Scanner Modules run in parallel]
       ↓  raw findings
Classification Engine
       ↓  classified items (Confidence & Severity)
Report Generator ── JSON + HTML
       ↓  render dashboard
AI Discovery Dashboard (Glassmorphic Web UI)
```

The data flow is:
`UI ➔ Scan Controller ➔ Discovery Engine ➔ 7 Scanners (Parallel) ➔ Raw Findings ➔ Classification ➔ Report Generator ➔ Dashboard`

---

## 📅 Project Progress & Sprint Status

### **DAY 1 — Scaffold & Foundation (Completed)**
- [x] **Project Scaffolding**: Structured the core package directories and empty `__init__.py` files.
- [x] **Data Contract Definition**: Created `Finding`, `ScanResult`, and `ModuleInfo` models in `scanner/models.py`.
- [x] **CLI Setup**: Built `main.py` CLI parser supporting `--scan`, `--format`, `--output`, and `--verbose` arguments.
- [x] **Terminal Encoding Patch**: Reconfigured output streams to UTF-8 on startup to avoid encoding crashes when rendering emojis on Windows cmd/powershell.
- [x] **System Scanner Module (Module 01)**: Fully implemented by Person B to collect hardware specs, CPU/RAM percentages, storage partitions, IP addresses, and detect active GPUs.
- [x] **Jinja2 Dashboard Template**: Created `dashboard.html.j2` with glassmorphic cards, dynamic metrics summary, interactive finding disclosures, and client-side searching/filtering.

### **DAY 2 — Parallel Execution & Core Scanners (Next Up)**
- [ ] **Discovery Engine**: ThreadPoolExecutor-based parallel execution of registered scanners.
- [ ] **Classification Engine**: Rule-based categorization engine (Model, Runtime, Agent, Framework, Service, Config).
- [ ] **File Scanner (Module 02)**: Multi-threaded directory traversal detecting GGUF, Safetensors, PyTorch, ONNX, and CKPT models.
- [ ] **Process Scanner (Module 03)**: Introspecting active runtimes (Ollama, LM Studio, vLLM, custom python scripts).
- [ ] **Report Generator (JSON)**: Structured JSON compiler.

---

## 📁 Project Directory Layout

```
System Scanner/
├── main.py                    # CLI entry point with argparse & formatting
├── requirements.txt           # Project environment dependencies
├── scanner/
│   ├── __init__.py            # Core package descriptor
│   ├── models.py              # Shared dataclasses (Finding, ScanResult, ModuleInfo)
│   ├── controller.py          # Central scan controller orchestrating pipeline
│   ├── engine.py              # Parallel Discovery Engine (ThreadPool Dispatcher)
│   ├── classifier.py          # Classification Engine
│   ├── modules/               # 7 Scanner Modules
│   │   ├── __init__.py
│   │   └── system_scanner.py  # MODULE 01: Host hardware & metadata collector
│   └── reporter/
│       ├── __init__.py
│       └── templates/
│           └── dashboard.html.j2 # Jinja2 HTML report dashboard layout
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.8 or higher
- Windows, macOS, or Linux

### 2. Environment Setup
Clone the repository and install dependencies inside a virtual environment:

```bash
# Clone the repository
git clone https://github.com/Ajinkya-Furange-Patil/Group-A-Y-S.git
cd "Group-A-Y-S/System Scanner"

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Running the Scanner
To execute the scanner via the CLI:

```bash
# Print help menu and options
python main.py -h

# Perform a scan (stub mode for Day 1 modules)
python main.py --scan

# Perform a scan with verbose debug logging
python main.py --scan --verbose
```

### 4. Running the Frontend (HTML Dashboard)
To generate and view the visual dashboard locally:
```bash
# 1. Run a scan and compile findings to HTML
python main.py --scan --format html

# 2. Spin up a local server to bypass file protocol browser security
python -m http.server 8000
```
Once the server is running, navigate to [http://localhost:8000/report.html](http://localhost:8000/report.html) to interact with the dashboard.

---

## 🤝 Collaboration Workflow & Git Branching

To keep code integrated smoothly, use the following flow:

### 1. Synchronize main
Before working, pull the latest changes:
```bash
git checkout main
git pull origin main
```

### 2. Create a Feature Branch
Check out a branch named after your role/task:
```bash
git checkout -b feature/cli-and-template-wireframe # (Person C, Day 1 example)
```

### 3. Push and Create Pull Request
Once code has been local-tested:
```bash
git add .
git commit -m "Brief summary of changes"
git push -u origin feature/your-branch-name
```
Open a PR on the GitHub repository and ask for at least **1 approval** before merging into `main`.
