# AI Discovery Scanner

A powerful, standalone discovery agent designed to aggressively map AI infrastructure footprint. The scanner operates natively across Windows, Linux, and macOS environments, checking running processes, registries, package managers, and executing comprehensive heuristic risk analysis against Indian regulatory guidelines (DPDP Act, CERT-In, SEBI CSCRF).

## Deployment Options

The scanner provides two primary operational modes designed for diverse enterprise IT environments:

### 1. Local Network Service (Interactive Dashboard Mode)
Designed for IT administrators performing localized spot-checks. This mode spins up a local web server displaying a secure consent portal. Upon authorization, the scanner initiates, rendering a live tracking UI before generating an interactive diagnostic dashboard.

**Command:**
```bash
python main.py --host 127.0.0.1 --port 8000
```
- Wait for the console log `🚀 AI DISCOVERY SCANNER SERVER ACTIVE`.
- Navigate to `http://127.0.0.1:8000/` in any modern web browser.
- Network Access: To expose the interface securely to a local intranet, bind to the host's actual IP (e.g. `--host 192.168.1.100`).

### 2. Background CLI Daemon (Automated Telemetry Mode)
Optimized for deployment via enterprise endpoint management (MDM) suites like Microsoft Intune or Jamf. This mode runs completely headless, enforcing hard CPU and RAM bounds to preserve system responsiveness, generating a JSON payload or HTML dashboard quietly in the background.

**Command:**
```bash
python main.py --scan --quick --cpu-limit 80 --ram-limit 20
```
- `--scan`: Immediately triggers the scanning telemetry engine.
- `--quick`: Bypasses deep-filesystem crawls, keeping execution under 30 seconds.
- `--cpu-limit 80`: Instantly aborts the threadpool if the scanner exceeds 80% CPU overhead.
- `--ram-limit 20`: Instantly aborts the threadpool if the scanner exceeds 20% of total host RAM.

## Compilation & Packaging

To eliminate external Python environment requirements, package the scanner using `PyInstaller`.

### Windows Execution
Run the provided PyInstaller specification file:
```bash
python -m PyInstaller --clean ai_scanner.spec
```
The compiled, portable executable will be placed in `dist/ai_scanner.exe`.

### Cross-Platform Environments (Linux/macOS)
Since PyInstaller compiles to the native host architecture, we've provided an automated build script:
```bash
python build_release.py
```
*Note: Due to system architecture constraints, the script must be run on a macOS host to yield a `.app`/mac binary, and on a Linux host to yield an ELF Linux binary.*

## Reports & Retention

All generated data is natively exported as:
- **HTML Dashboard** (`rendered_dashboard.html` / `report.html`)
- **JSON Telemetry Payload** (`report.json`)
- **Excel SBOM/AIBOM Sheets** (`test_report.xlsx`)

In compliance with CERT-In 180-day retention policies, every scan execution hashes its findings and archives them locally in `ai_scanner_history.db`.
