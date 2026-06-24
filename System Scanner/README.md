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

## Remote GitHub Repository Scanning

The scanner supports remote scanning of public GitHub repositories. It parses the URL, downloads the ZIP archive (trying the `main` branch first, and falling back to the `master` branch on HTTP 404), extracts the files, runs the core scanner modules, and generates custom visual reports.

### Operational Guide (CLI)
1. Run:
   ```bash
   python main.py
   ```
2. Select Option `[3] Run Custom Scan`.
3. Select Target Option `[2] GitHub Repository` (Option 3 in the sub-menu).
4. Enter a public GitHub repository URL (e.g., `https://github.com/openai/openai-python`).
5. Review AIBOM summary metrics and find saved outputs `report.json` and `report.html` in the workspace directory.

### Operational Guide (Web UI)
1. Start the server via CLI option `[4] Start Web UI Dashboard`.
2. Connect to `http://127.0.0.1:8000/`.
3. In the **Target Region** dropdown, select **Remote Github Repositories**.
4. Enter the public GitHub URL in the textbox.
5. Authorize and click **Authorize & Run Scan**.
6. The dashboard will redirect to a dedicated Repository Telemetry Dashboard displaying the confidence gauge dial, detected languages, frameworks, models, and interactive collapsible code findings.
