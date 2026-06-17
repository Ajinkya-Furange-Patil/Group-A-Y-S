# Local Network Web Service for Remote AI Scanning

This implementation plan describes the design and code adjustments to expose the AI Discovery Scanner as a local network service. This allows two machines on the same Wi-Fi network to collaborate: the scanner runs on the friend's laptop (server), and the scan is authorized and viewed via a web browser from either machine.

---

## User Review Required

> [!IMPORTANT]
> The server will bind to all network interfaces (`0.0.0.0`) by default when started with `--server`. This makes it accessible to any device on the same local Wi-Fi/Ethernet network at `http://<ip-address>:8000`.
> To prevent unauthorized scans:
> 1. A consent page will be shown to any client accessing the URL.
> 2. The scan will only run after checking a consent box and clicking "Authorize & Run Scan".
> 3. No external Python packages are introduced; we rely entirely on the standard Python standard library (`http.server` and `socketserver`) for maximum compatibility and ease of deployment.

---

## Open Questions

> [!NOTE]
> 1. Do we need any password/token authentication for the web interface, or is the explicit consent checkbox on the page sufficient for your testing needs?
> 2. Should we support downloading the JSON report directly from the web UI? (Currently proposing adding a link to download `report.json`).

---

## Proposed Changes

### CLI Entrypoint

#### [MODIFY] [main.py](file:///d:/College%20Work/Internship/Group%20A-Y-S/System%20Scanner/System%20Scanner/main.py)
- Update `build_parser()` to add server arguments:
  - `--server`: Action flag to start the scanner web server.
  - `--port`: The port to run the server on (default: `8000`).
  - `--host`: The host address to bind the server to (default: `0.0.0.0`).
- Update `main()` to check if `args.server` is passed. If so, call the server initialization function instead of running the scan directly from the CLI.

---

### Web Server Module

#### [NEW] [server.py](file:///d:/College%20Work/Internship/Group%20A-Y-S/System%20Scanner/System%20Scanner/scanner/server.py)
- Create a new `ScanServer` orchestrator class that starts a standard library `http.server.ThreadingHTTPServer` (to support multiple requests concurrently).
- Create a custom HTTP request handler `ScanHTTPRequestHandler` that handles the following paths:
  - `GET /`: Serve a beautiful, responsive HTML authorization page (`consent.html.j2`) showing host hostname, OS, IP address, and details of what will be scanned.
  - `POST /run-scan` or `GET /run-scan`: Run the scan controller in Python directly, writing `report.json` and `rendered_dashboard.html`, and returning a JSON success status.
  - `GET /report`: Serve the generated `rendered_dashboard.html` report.
  - `GET /api/results`: Serve the raw `report.json` results.
- Implement helper function `get_local_ip()` to print the exact IP address and command line instruction for the user to visit (e.g., `http://192.168.1.15:8000`).

---

### Templates

#### [NEW] [consent.html.j2](file:///d:/College%20Work/Internship/Group%20A-Y-S/System%20Scanner/System%20Scanner/scanner/reporter/templates/consent.html.j2)
- Create a template for the consent and authorization page.
- Apply a premium cyber-dark theme styling consistent with the main dashboard.
- Display a checklist of the scanner modules:
  - System Details, Files Scanner, Processes, Installed Packages, Agents, Runtimes, and API Keys.
- Add checkbox consent validation so the scan button remains disabled until consent is checked.
- Include a "Quick Scan (Recommended)" toggle to let users run in quick mode.
- Use JavaScript to send an AJAX request to `/run-scan` and display a premium loading spinner with text updates (e.g., "Initializing Scan...", "Walking Directory Trees...", "Writing Reports...") before redirecting to `/report`.

---

## Verification Plan

### Automated Tests
- Create a new test file `tests/test_server.py` to test:
  - HTTP Server initialization.
  - GET requests to `/` rendering the consent page.
  - GET/POST requests to `/run-scan` triggering the controller (mocked) and returning success.
  - Serving `/report` and `/api/results`.
- Run all unit tests:
  `.\venv\Scripts\python -m unittest discover -s tests`

### Manual Verification
- Start the server on the host machine:
  `.\venv\Scripts\python main.py --server`
- Verify that it outputs the correct local IP (e.g., `http://192.168.x.x:8000`).
- Connect from a second device (or another browser window) to `http://<local-ip>:8000`.
- Verify the consent checkbox disables/enables the scan trigger.
- Trigger a quick scan and check that the progress screen animates correctly, then successfully redirects to the dashboard displaying all scanned system information.
