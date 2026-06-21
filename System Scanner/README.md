# AI Discovery Scanner

A powerful, standalone discovery agent designed to aggressively map AI infrastructure footprint. The scanner operates natively across Windows, Linux, and macOS environments, checking running processes, registries, package managers, and executing comprehensive heuristic risk analysis against Indian regulatory guidelines (DPDP Act, CERT-In, SEBI CSCRF).

## Deployment Options

The scanner provides a primary operational mode designed for interactive use:

### Local Network Service (Interactive Dashboard Mode)
Designed for IT administrators performing localized spot-checks. This mode spins up a local web server displaying a secure consent portal. Upon authorization, the scanner initiates, rendering a live tracking UI before generating an interactive diagnostic dashboard.

**Command:**
```bash
python main.py
```
- Wait for the console log `🚀 AI DISCOVERY SCANNER SERVER ACTIVE`.
- Navigate to `http://127.0.0.1:8000/` in any modern web browser.

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
