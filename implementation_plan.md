# AI Discovery Scanner — 5-Day Sprint Implementation Plan

> **Team:** 3 people × 6–8 hrs/day = **90–120 total engineering hours**
> **Target:** A fully working, packaged AI Discovery Scanner (Python CLI + HTML Dashboard + EXE)
> **Repo:** [Group-A-Y-S](https://github.com/Ajinkya-Furange-Patil/Group-A-Y-S)

---

## 👥 Team Roles & Responsibilities

| Role                                    | Focus Area                                                                        | Why This Split                                                                                                                                             |
| --------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Person A** — Lead / Backend Architect | Project scaffold, Scan Controller, Classification Engine, Integration             | Someone must own the "backbone" that all modules plug into — the controller, data models, and aggregation logic. This keeps the interface contract stable. |
| **Person B** — Module Developer         | All 7 Scanner Modules (System, File, Process, Package, Agent, Runtime, API)       | The scanners are the most numerous and parallelizable pieces of work. A focused developer can crank them out quickly using a shared module interface.      |
| **Person C** — UI / Report / Packaging  | Report Generator (JSON + HTML), Jinja2 Templates, Dashboard, CLI, PyInstaller EXE | User-facing output and packaging require a different mindset (design, UX, cross-platform testing). Keeping this separate avoids bottlenecks.               |

---

## 📐 Architecture Reference

```
UI (CLI / HTML / EXE)
       ↓  trigger scan
Scan Controller
       ↓  dispatch modules
Discovery Engine ── [Module 01..07 run in parallel]
       ↓  raw findings
Classification Engine
       ↓  classified items
Report Generator ── JSON + HTML
       ↓  render dashboard
AI Discovery Dashboard
```

**Tech Stack Justification:**

| Tool                 | Why                                                     |
| -------------------- | ------------------------------------------------------- |
| Python 3.x           | Cross-platform, rich stdlib, easy packaging             |
| `psutil`             | Best-in-class process/system introspection              |
| `pathlib` / `os`     | Idiomatic file traversal                                |
| `dataclasses`        | Lightweight, type-safe data models without ORM overhead |
| `concurrent.futures` | Built-in parallel execution; safe ThreadPoolExecutor    |
| `json`               | Universal output format for integrations                |
| `jinja2`             | Production-grade HTML templating                        |
| `PyInstaller`        | Single-file EXE with no Python runtime needed           |
| `logging`            | Structured runtime diagnostics                          |

---

## 📁 Target Project Structure

```
System Scanner/
├── scanner/
│   ├── __init__.py
│   ├── models.py              # Shared dataclasses (Finding, ScanResult)
│   ├── controller.py          # Scan Controller — orchestrates all modules
│   ├── engine.py              # Discovery Engine — parallel dispatch
│   ├── classifier.py          # Classification Engine
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── system_scanner.py  # MODULE 01
│   │   ├── file_scanner.py    # MODULE 02
│   │   ├── process_scanner.py # MODULE 03
│   │   ├── package_scanner.py # MODULE 04
│   │   ├── agent_scanner.py   # MODULE 05
│   │   ├── runtime_scanner.py # MODULE 06
│   │   └── api_scanner.py     # MODULE 07
│   └── reporter/
│       ├── __init__.py
│       ├── report_generator.py
│       └── templates/
│           └── dashboard.html.j2
├── main.py                    # CLI entry point
├── requirements.txt
├── README.md
├── ai_discovery_scanner_architecture_white.html
└── dist/                      # PyInstaller output (Day 5)
```

---

## 🗓️ Day-by-Day Sprint Plan

---

### 📅 DAY 1 — Foundation & Setup

**Goal:** Every team member can run code. Scaffold is in place. Data contracts are frozen.

| #   | Person | Task                                                                                                  | File(s)                             | Hours | Why                                                                                  |
| --- | ------ | ----------------------------------------------------------------------------------------------------- | ----------------------------------- | ----- | ------------------------------------------------------------------------------------ |
| 1   | **A**  | Create repo folder structure, `requirements.txt`, `__init__.py` files                                 | All `scanner/` dirs                 | 1h    | Must exist before anyone else writes code                                            |
| 2   | **A**  | Define shared data models: `Finding`, `ScanResult`, `RiskLevel` dataclasses                           | `scanner/models.py`                 | 2h    | The "contract" every module must conform to; if this changes later everything breaks |
| 3   | **A**  | Build skeleton `controller.py` with stub `run_scan()` that calls engine and returns `ScanResult`      | `scanner/controller.py`             | 2h    | Person B needs this interface to write modules against                               |
| 4   | **B**  | Set up dev environment: `python -m venv venv`, `pip install -r requirements.txt`, verify psutil works | Local env                           | 1h    | No code is usable until environment is verified                                      |
| 5   | **B**  | Write `MODULE 01 — SystemScanner`: hostname, OS, CPU, RAM, IP via `platform` + `psutil` + `socket`    | `scanner/modules/system_scanner.py` | 3h    | Simplest module — good way to learn the `Finding` interface                          |
| 6   | **C**  | Set up `main.py` skeleton CLI with `argparse`: `--scan`, `--output`, `--format` flags                 | `main.py`                           | 2h    | CLI is needed by Day 3 for end-to-end testing                                        |
| 7   | **C**  | Research Jinja2 templating, draft HTML dashboard wireframe structure                                  | `scanner/reporter/templates/`       | 2h    | Template design takes more time than people think; must start early                  |

**Day 1 Deliverable:** Runnable skeleton. `python main.py --scan` prints "Scan started…" and returns a stub `ScanResult`. All teammates can run this.

**Git Workflow Day 1:**

```bash
# Person A
git checkout -b feature/scaffold-and-models
# After work:
git push -u origin feature/scaffold-and-models
# Open PR → main, teammates review

# Person B
git checkout -b feature/module-system-scanner

# Person C
git checkout -b feature/cli-and-template-wireframe
```

---

### 📅 DAY 2 — Core Scanner Modules (High-Value Ones)

**Goal:** Modules 02, 03, 04, 05 are working and returning real findings on a test machine.

| #   | Person | Task                                                                                                                                                                      | File(s)                                        | Hours | Why                                                                                              |
| --- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- | ----- | ------------------------------------------------------------------------------------------------ |
| 1   | **A**  | Build `engine.py` — `ThreadPoolExecutor`-based parallel dispatcher; collects results from all modules                                                                     | `scanner/engine.py`                            | 3h    | Core of the "parallel" claim in the architecture; without this modules run serially              |
| 2   | **A**  | Build `classifier.py` — rule-based classification: maps raw findings → categories (AI Model, LLM Runtime, Agent, Framework, Service, Config) with confidence levels       | `scanner/classifier.py`                        | 3h    | Classification is the "intelligence" layer; needs full attention to get right                    |
| 3   | **B**  | Write `MODULE 02 — FileScanner`: Walk `~`, Downloads, `%USERPROFILE%/.cache/huggingface`, `~/.ollama` for `.gguf`, `.safetensors`, `.pt`, `.pth`, `.onnx`, `.ckpt`, `.h5` | `scanner/modules/file_scanner.py`              | 4h    | Most impactful module — model files are the biggest finding; path variations across OS need care |
| 4   | **B**  | Write `MODULE 03 — ProcessScanner`: Use `psutil.process_iter()` to find `ollama`, `lmstudio`, `llama.cpp`, `vllm`, `python` (with AI-related cmdline args)                | `scanner/modules/process_scanner.py`           | 2h    | Real-time detection of running AI services is a strong demo point                                |
| 5   | **C**  | Build `report_generator.py`: `generate_json_report(scan_result)` that writes structured JSON to file                                                                      | `scanner/reporter/report_generator.py`         | 2h    | JSON report is the foundation; HTML report is built on top of it                                 |
| 6   | **C**  | Start Jinja2 HTML dashboard template: header, metrics summary (counts), findings table                                                                                    | `scanner/reporter/templates/dashboard.html.j2` | 4h    | HTML report is the visually impressive deliverable — needs ample design time                     |

**Day 2 Deliverable:** Running `python main.py --scan --format json` produces a real JSON report with system info, model files found on the test machine, and running AI processes.

---

### 📅 DAY 3 — Remaining Modules + Integration

**Goal:** All 7 modules integrated and end-to-end pipeline works. First complete scan runs.

| #   | Person | Task                                                                                                                                                                                      | File(s)                                        | Hours | Why                                                                                   |
| --- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- | ----- | ------------------------------------------------------------------------------------- |
| 1   | **A**  | Wire up everything in `controller.py`: call engine, pass all module results through classifier, build final `ScanResult`                                                                  | `scanner/controller.py`                        | 3h    | Integration is always harder than individual parts; needs the most experienced person |
| 2   | **A**  | Add comprehensive `logging` throughout controller, engine, classifier — file + console handlers                                                                                           | All core files                                 | 2h    | Debugging scan failures requires logs; required for professional delivery             |
| 3   | **B**  | Write `MODULE 04 — PackageScanner`: Run `pip list --format=json`, parse for `torch`, `tensorflow`, `transformers`, `langchain`, `crewai`, `autogen`, `llama-index`, `openai`, `anthropic` | `scanner/modules/package_scanner.py`           | 2h    | pip list is the most reliable way to detect installed AI frameworks                   |
| 4   | **B**  | Write `MODULE 05 — AgentScanner`: Walk Python project files (`.py`) in CWD + home dir; regex search for `from langchain`, `Agent(`, `Crew(`, `AssistantAgent(`, `from crewai`             | `scanner/modules/agent_scanner.py`             | 3h    | Code-level scanning is complex — needs thoughtful regex to avoid false positives      |
| 5   | **B**  | Write `MODULE 06 — RuntimeScanner`: Check ports `11434`, `8000`, `5000`, `8080` with `socket.connect_ex`; check dirs `.ollama`, `lmstudio` in home                                        | `scanner/modules/runtime_scanner.py`           | 2h    | Port + folder check = two-pronged confirmation; reduces false positives               |
| 6   | **C**  | Write `MODULE 07 — APIScanner`: Search `.env`, `*.yaml`, `*.json` files in project dirs for `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `COHERE_API_KEY`                     | `scanner/modules/api_scanner.py`               | 2h    | API key detection is a security/audit concern — high value for the demo               |
| 7   | **C**  | Complete HTML dashboard template: risk score meter, per-module sections, styled findings cards                                                                                            | `scanner/reporter/templates/dashboard.html.j2` | 3h    | The visual wow factor comes from the HTML report — invest here                        |

**Day 3 Deliverable:** Full end-to-end pipeline. `python main.py --scan` runs all 7 modules in parallel, classifies findings, and outputs both JSON and HTML reports. All three team members test on their own machines.

---

### 📅 DAY 4 — Polish, Error Handling, CLI & Cross-Platform

**Goal:** The tool handles edge cases gracefully. Works on Windows AND Linux/Mac. CLI is user-friendly.

| #   | Person | Task                                                                                                                                                             | File(s)                                      | Hours | Why                                                                                  |
| --- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- | ----- | ------------------------------------------------------------------------------------ |
| 1   | **A**  | Add error handling in engine: modules that crash should log the error and continue (never fail the whole scan)                                                   | `scanner/engine.py`, all modules             | 2h    | In production, one bad scanner should never kill the whole scan                      |
| 2   | **A**  | Add OS-aware path resolution in all modules (Windows `USERPROFILE` vs Linux `HOME`, path separators)                                                             | `scanner/modules/*.py`                       | 3h    | Windows uses different paths; `pathlib.Path.home()` normalizes this                  |
| 3   | **A**  | Write `tests/` folder: at least one unit test per module with a mock filesystem / process list                                                                   | `tests/`                                     | 2h    | Verifies correctness without needing actual AI software installed; needed for CI     |
| 4   | **B**  | Harden all module outputs: handle `PermissionError` on restricted paths, `FileNotFoundError`, process access denied                                              | All module files                             | 2h    | Scanners will hit system-protected directories; uncaught exceptions = bad UX         |
| 5   | **B**  | Add performance timing to each module: record how long each scanner took in `ScanResult`                                                                         | `scanner/models.py`, all modules             | 1h    | Performance data lets the user see "which scanner is slow" — useful for demo         |
| 6   | **B**  | Add a `--quick` flag mode: file scanner only scans top-level home dirs (not recursive full scan)                                                                 | `scanner/modules/file_scanner.py`, `main.py` | 2h    | Full recursive scan can take minutes on large drives; quick mode is demo-friendly    |
| 7   | **C**  | Polish CLI output: progress bar (using `print` with `\r` or `rich` library), colored terminal output, summary table at end                                       | `main.py`                                    | 3h    | The first impression of the tool is the CLI; it must look professional               |
| 8   | **C**  | Finalize HTML report: add `<style>` with the same design language as `ai_discovery_scanner_architecture_white.html` (glassmorphism, Inter font, gradient header) | `dashboard.html.j2`                          | 3h    | Visual consistency between architecture doc and the output report = polished product |

**Day 4 Deliverable:** The tool runs cleanly without crashing on a fresh machine. Error states are handled. CLI looks professional. HTML report looks stunning.

---

### 📅 DAY 5 — Packaging, README, Demo Prep & Final QA

**Goal:** Deliverable EXE, complete documentation, and a live demo-ready walkthrough.

| #   | Person  | Task                                                                                                                                           | File(s)                                                      | Hours | Why                                                                             |
| --- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ----- | ------------------------------------------------------------------------------- |
| 1   | **A**   | Final integration test: full scan on Windows + one team member tests on Linux/Mac                                                              | All                                                          | 2h    | Cross-platform parity is the final gate before packaging                        |
| 2   | **A**   | Build PyInstaller EXE: `pyinstaller --onefile --name ai_scanner main.py --add-data "scanner/reporter/templates/*;scanner/reporter/templates/"` | `dist/ai_scanner.exe`                                        | 2h    | Single EXE is the deployment target; `--add-data` needed for Jinja2 templates   |
| 3   | **A**   | Test EXE on a machine with no Python installed                                                                                                 | `dist/`                                                      | 1h    | This is the ultimate test; finds hidden import issues that `pyinstaller` misses |
| 4   | **B**   | Write full `requirements.txt` with pinned versions; test `pip install -r requirements.txt` from scratch                                        | `requirements.txt`                                           | 1h    | Reproducibility; any contributor must be able to set up in < 5 minutes          |
| 5   | **B**   | Record a sample scan output: run the scanner, save the JSON report and HTML report as examples in `examples/` folder                           | `examples/sample_report.json`, `examples/sample_report.html` | 2h    | Reviewers and interviewers who don't want to run the code can still see output  |
| 6   | **B**   | Final code review: check naming conventions, remove dead code, add docstrings to all public functions                                          | All `.py` files                                              | 2h    | Clean code is evaluated; docstrings are the minimum professional standard       |
| 7   | **C**   | Complete and finalize `README.md`: add usage examples, screenshots of CLI and HTML report, description of all 7 modules, contribution guide    | `README.md`                                                  | 2h    | The README is what evaluators see first — it must be excellent                  |
| 8   | **C**   | Prepare a 5-minute demo script: show CLI scan, open HTML report in browser, walk through findings, explain architecture diagram                | `DEMO.md`                                                    | 2h    | A working demo with a rehearsed script is 10x more impressive than code alone   |
| 9   | **All** | Final git merge: all feature branches → `main`, tag release `v1.0`, push                                                                       | GitHub                                                       | 1h    | Clean repo history and a tagged release signals professionalism                 |

**Day 5 Deliverable:** `dist/ai_scanner.exe` runs on a fresh Windows machine. README is presentation-ready. HTML report is visually impressive. `v1.0` tag is on GitHub.

---

## ⏱️ Hour Budget Summary

| Day       | Person A | Person B | Person C | Day Total |
| --------- | -------- | -------- | -------- | --------- |
| Day 1     | 5h       | 4h       | 4h       | **13h**   |
| Day 2     | 6h       | 6h       | 6h       | **18h**   |
| Day 3     | 5h       | 7h       | 5h       | **17h**   |
| Day 4     | 7h       | 5h       | 6h       | **18h**   |
| Day 5     | 5h       | 5h       | 4h       | **14h**   |
| **Total** | **28h**  | **27h**  | **25h**  | **80h**   |

> Remaining ~10–40h buffer (from the 90–120h budget) is for debugging, code reviews, merge conflicts, meetings, and scope creep.

---

## 🎯 Definition of Done (DoD)

A task is **Done** when:

- [ ] Code is written and manually tested
- [ ] No uncaught exceptions on the happy path
- [ ] Function/class has at least a one-line docstring
- [ ] Changes are committed to the feature branch
- [ ] PR is opened and at least one teammate has reviewed it

The **project** is **Done** when:

- [ ] `python main.py --scan` completes without error and produces JSON + HTML output
- [ ] `dist/ai_scanner.exe` runs on a clean Windows machine
- [ ] All 7 modules report at least one finding on a developer machine
- [ ] README has usage instructions and screenshots
- [ ] GitHub has a `v1.0` tag

---

## ⚠️ Risks & Mitigations

| Risk                                                      | Likelihood | Impact | Mitigation                                                         |
| --------------------------------------------------------- | ---------- | ------ | ------------------------------------------------------------------ |
| File scanner is too slow (recursing entire drive)         | High       | Medium | `--quick` mode + configurable depth limit                          |
| PyInstaller can't find Jinja2 templates                   | Medium     | High   | Use `--add-data` flag + runtime path resolver                      |
| PermissionError on system directories                     | High       | Low    | Wrap all file/process I/O in `try/except`                          |
| Module interface changes mid-sprint (breaks other's work) | Medium     | High   | Freeze `models.py` by end of Day 1; no breaking changes after that |
| Agent scanner produces false positives                    | Medium     | Medium | Require ≥2 pattern matches before flagging a file                  |

---

## 📋 Daily Standup Template

Each morning (15 min max):

```
1. What did I complete yesterday?
2. What am I doing today?
3. Any blockers?
```

Use GitHub Issues or a shared Notion page to track blockers.

---

## 🔁 Git Branching Strategy

```
main
├── feature/scaffold-and-models          (A, Day 1)
├── feature/module-system-scanner        (B, Day 1)
├── feature/cli-and-template-wireframe   (C, Day 1)
├── feature/engine-and-classifier        (A, Day 2)
├── feature/modules-file-process         (B, Day 2)
├── feature/report-generator             (C, Day 2)
├── feature/integration                  (A, Day 3)
├── feature/modules-pkg-agent-runtime    (B, Day 3)
├── feature/api-scanner-html-report      (C, Day 3)
├── feature/error-handling-os-compat     (A, Day 4)
├── feature/module-hardening             (B, Day 4)
├── feature/cli-polish-html-final        (C, Day 4)
└── release/v1.0                         (All, Day 5)
```

**PR Rule:** No direct push to `main`. Every branch requires at least **1 approval** before merge.
