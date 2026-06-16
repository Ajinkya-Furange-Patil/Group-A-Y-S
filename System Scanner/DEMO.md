# 🎬 AI Discovery Scanner — 5-Minute Demo Script

This script outlines a professional 5-minute presentation walkthrough of the **AI Discovery Scanner** CLI tool and HTML dashboard, showcasing its design aesthetics, parallel execution engine, classification rules, and security credentials masking.

---

## ⏱️ Timeline Overview

| Timestamp | Duration | Section | Focus Point |
|---|---|---|---|
| **0:00 - 1:00** | 60s | **Introduction & Architecture** | Core value prop, architecture diagram, and parallel execution logic. |
| **1:00 - 2:00** | 60s | **CLI Walkthrough** | Running the CLI scan, explaining progress logs, and highlighting the terminal summary. |
| **2:00 - 3:30** | 90s | **HTML Dashboard QA** | Opening the report, toggling dark/light themes, expanding details, and searching. |
| **3:30 - 4:30** | 60s | **Security & Masking** | Displaying API key scan rules (Module 07) and masked results. |
| **4:30 - 5:00** | 30s | **QA & Conclusion** | Deployment targets (EXE) and summary statistics. |

---

## 🎤 Step-by-Step Presentation Guide

### 📍 Step 1: Introduction & Architecture (60s)
1. **Action**: Display the [README.md](file:///c:/Users/ADMIN/OneDrive/Desktop/AI%20scanner/Group-A-Y-S/README.md) or open the architecture flow in your browser.
2. **Talk Track**:
   > *"Good morning/afternoon. Today I am demonstrating the **AI Discovery Scanner** — a lightweight, modular security and asset audit tool designed to search host machines and identify AI frameworks, models, processes, active runtimes, agents, and configurations.*
   > 
   > *The system flow starts at the CLI trigger, which registers all modules with the Scan Controller. These scanners are dispatched in parallel via our Discovery Engine using a thread pool. Raw findings are then passed to the Classification Engine to assign severity levels and categories, which are compiled into machine-readable JSON and glassmorphic HTML dashboards."*

---

### 📍 Step 2: The CLI Scanner Demo (60s)
1. **Action**: Open a terminal window and run:
   ```bash
   python main.py --scan
   ```
2. **Visual Highlights**: Point out the bold startup header, the live `[OK]` status updates from `SystemScanner` and `APIScanner`, and the colored Unicode summary grid.
3. **Talk Track**:
   > *"Let's trigger a live audit scan. By running `python main.py --scan`, the scanner prints our bold v1.0.0 header and starts processing modules in parallel. Within a fraction of a second, the scan completes, outputting our **Scan Result Summary** block.*
   > 
   > *Here we see the target host, OS, duration, and a status list of individual scanners. The ANSI colors let the user instantly check scanner health (Green for SUCCESS, Red for FAIL) and visualizes the aggregate Risk Score."*

---

### 📍 Step 3: Interactive HTML Dashboard (90s)
1. **Action**: Generate the HTML dashboard and open it in a browser:
   ```bash
   python main.py --scan --format html
   ```
   Open `report.html` in your browser.
2. **Visual Highlights**:
   - Toggle the **LIGHT / DARK** button in the header.
   - Type `"Host"` in the search input to filter finding lists.
   - Click a finding card to expand and show details.
3. **Talk Track**:
   > *"By running the scan with `--format html`, the tool renders a glassmorphic dashboard (`report.html`). It defaults to a Warm Champagne Ivory theme, ideal for professional presentations.*
   > 
   > *With the header action, we can dynamically toggle a Dark Gold glassmorphic theme. Both views utilize satin gradients, double frosted card borders (`rgba(255,255,255,0.75)`), and soft drop shadows.*
   > 
   > *The findings section supports full client-side search and dropdown filters for Categories and Risk Levels. Users can click any card header to toggle details and reveal raw JSON metadata fields."*

---

### 📍 Step 4: Security & Credentials Masking (60s)
1. **Action**: Create a temporary test `.env` file (e.g., write `OPENAI_API_KEY="sk-proj-1234567890abcdef1234567890abcdef12345678"` inside it) and re-run:
   ```bash
   python main.py --scan
   ```
2. **Visual Highlights**: Show the `APIScanner` finding card highlighting a `CRITICAL` risk level. Expand it to show that the API key value is masked (`sk-proj-...5678`).
3. **Talk Track**:
   > *"One of our core modules is the **API Scanner (Module 07)**. It audits settings files (`.env`, `.json`, `.yaml`) for exposed AI credentials. *
   > 
   > *When it detects an API key, it assigns a `CRITICAL` severity rating. To maintain security, the engine automatically masks the key before exporting the report, revealing only safe prefixes and trailing digits."*

---

### 📍 Step 5: Wrap-up & Packaging (30s)
1. **Talk Track**:
   > *"The entire codebase is structured to run with minimal dependencies. This makes the project highly portable and allows us to compile the scanner into a single, self-contained executable (`.exe`) file on Day 5 using PyInstaller.*
   > 
   > *Thank you for your time. I am open to any questions!"*
