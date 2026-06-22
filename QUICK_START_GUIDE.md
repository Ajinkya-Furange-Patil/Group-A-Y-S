# System Scanner - Quick Start Guide

## Choose Your Version

### 🖥️ Client System Scanner.exe (Recommended for Most Users)
**Best for:** End users, non-technical staff, presentations

✅ Easy to use - just double-click  
✅ No browser required - opens in its own window  
✅ Clean, professional interface  
✅ Best user experience  

**How to use:**
1. Double-click `Client System Scanner.exe`
2. Wait for the window to open (3-5 seconds)
3. Click "Start Scan" button
4. View results in the dashboard

---

### ⌨️ System Scanner.exe (For Developers & Automation)
**Best for:** Developers, IT professionals, automation

✅ Command-line interface  
✅ Detailed console output  
✅ Scriptable and automatable  
✅ Smaller file size  

**How to use:**
1. Double-click `System Scanner.exe` or run from terminal
2. Wait for "Server started" message
3. Open your browser to: http://localhost:8000
4. Click "Start Scan" button
5. View results in the browser

---

## First Time Setup

### No Installation Required! ✅

Both versions are **portable executables** - no installation needed.

1. Download the .exe file you want
2. Save it anywhere (Desktop, Documents, USB drive, etc.)
3. Double-click to run
4. That's it!

### System Requirements

- **OS:** Windows 10 or Windows 11
- **RAM:** 2 GB minimum (4 GB recommended)
- **Disk:** 50 MB free space
- **Permissions:** User-level (no admin required)

---

## Common Tasks

### Run a Basic Scan

1. **Start the scanner:**
   - GUI: Double-click `Client System Scanner.exe`
   - CLI: Double-click `System Scanner.exe`, then open browser

2. **Click "Start Scan"** button

3. **Wait** for scan to complete (usually 10-30 seconds)

4. **Review Results** in the dashboard

### Export Results

**JSON Export:**
- Click "Export JSON" button
- File saved as `report.json` in scanner directory

**HTML Export:**
- Click "Export HTML" button  
- File saved as `report.html` in scanner directory

**Excel Export (requires openpyxl):**
- Click "Export Excel" button
- File saved as `report.xlsx` in scanner directory

### View Scan History

The scanner automatically maintains a SQLite database of all scans:
- Database file: `ai_scanner_history.db`
- View in dashboard: History section shows recent scans
- Access directly: Use any SQLite browser

### Read Logs

**CLI Version:**
- Log file: `ai_scanner.log`
- Shows detailed scan progress and any errors
- View in any text editor

**GUI Version:**
- Log file: `ai_scanner_gui.log`
- Shows application startup and errors
- View in any text editor

---

## Dashboard Features

### Main Sections

1. **System Overview**
   - Hostname and OS information
   - Risk score and severity breakdown
   - Scan duration and module count

2. **Findings Tab**
   - All detected AI agents, files, processes
   - Filterable by severity and category
   - Click to expand details

3. **Risk Analysis Tab**
   - Risk dimensions breakdown
   - Attack surface analysis
   - Compliance status

4. **Module Compliance**
   - Right sidebar panel
   - Shows which modules ran
   - Execution time and status

5. **Threat Vectors Tab**
   - Potential security threats
   - Diagnostic information
   - Mitigation recommendations

---

## Understanding Scan Results

### Risk Levels

| Level | Color | Meaning |
|-------|-------|---------|
| 🔴 **Critical** | Red | Immediate attention required |
| 🟠 **High** | Orange | Should be addressed soon |
| 🟡 **Medium** | Yellow | Monitor and plan remediation |
| 🔵 **Low** | Blue | Informational, low priority |
| ⚪ **Info** | White | Reference information only |

### Common Findings

1. **AI Agents Detected**
   - Running AI processes (Copilot, Kiro, etc.)
   - AI-related services
   - Verdict: Review for approval

2. **AI Model Files**
   - .gguf, .safetensors, .bin files
   - Large model files
   - Verdict: Check licensing and usage

3. **Python AI Packages**
   - langchain, crewai, autogen, etc.
   - Framework installations
   - Verdict: Verify business justification

4. **API Keys / Credentials**
   - Hardcoded API keys
   - Secret tokens in code
   - Verdict: Rotate immediately (Critical)

5. **Open Ports**
   - Services listening on network
   - Process IDs mapped to ports
   - Verdict: Review firewall rules

---

## Troubleshooting

### "Port 8000 already in use" (CLI version)

**Solution 1:** Close other applications using port 8000
- Stop any local web servers
- Check for other scanner instances

**Solution 2:** GUI version auto-detects free ports
- Use `Client System Scanner.exe` instead
- It automatically finds an available port

### Window doesn't open (GUI version)

**Cause:** Antivirus may be blocking execution

**Solution:**
1. Add exception in your antivirus
2. Right-click → "Run as Administrator" (if needed)
3. Check `ai_scanner_gui.log` for errors

### Scan takes too long

**Normal scan time:** 10-30 seconds  
**Large systems:** Up to 2 minutes

**To speed up:**
- Close unnecessary applications
- Reduce scan depth (modify config)
- Use "Quick Scan" mode (if available)

### Missing findings / Incomplete results

**Possible causes:**
1. Insufficient permissions
   - Some processes require admin rights to scan
   - Re-run as Administrator if needed

2. Antivirus interference
   - May block process enumeration
   - Add scanner to exclusions

3. Module failed
   - Check Module Compliance panel
   - Review logs for error messages

### Antivirus false positive

**Why this happens:**
- PyInstaller executables are sometimes flagged
- This is a known false positive

**Solutions:**
1. Add to antivirus exclusions
2. Verify file hash (if provided)
3. Build from source to verify

---

## Advanced Usage

### Command-Line Options (CLI version)

Currently, the CLI version runs with default settings. To customize:

1. Edit `main.py` before building
2. Or use the Python source directly:
   ```bash
   python main.py --quick --depth 3
   ```

### Custom Scan Folders

To scan specific directories:

1. **Via Python source:**
   ```python
   from scanner.controller import ScanController
   controller = ScanController(scan_folder="C:\\Projects", max_depth=5)
   result = controller.run_scan()
   ```

2. **Via build:** Modify `main.py` to accept command-line arguments

### Automation & Integration

**Scheduled Scans:**
1. Use Windows Task Scheduler
2. Schedule `System Scanner.exe` to run
3. Parse output `report.json` for monitoring

**CI/CD Integration:**
```bash
# Run scanner
"System Scanner.exe"

# Wait for scan to complete
timeout /t 60

# Parse results
python parse_report.py report.json
```

**SIEM Integration:**
- Scanner supports syslog output (check logs)
- Parse JSON reports for security events
- Monitor for high/critical findings

---

## Best Practices

### For Security Teams

1. **Baseline Scan:** Run initial scan to establish baseline
2. **Regular Scans:** Schedule weekly or monthly scans
3. **Compare Results:** Track changes over time
4. **Investigate Critical:** Address critical findings immediately
5. **Document:** Keep scan reports for compliance

### For Developers

1. **Pre-Commit:** Run scan before code commits
2. **API Keys:** Never commit credentials (scanner detects them)
3. **Model Files:** Store large models outside repository
4. **Compliance:** Check license scanner results

### For Management

1. **Risk Reporting:** Use overall risk score for KPIs
2. **Compliance:** Track licensing and compliance findings
3. **Trend Analysis:** Compare scans over time
4. **Governance:** Set policies based on findings

---

## Getting Help

### Log Files

Always check logs first:
- **CLI:** `ai_scanner.log`
- **GUI:** `ai_scanner_gui.log`

### Common Log Messages

```
✅ "Scan Complete" - Success
⚠️ "Module failed" - Check that module specifically
❌ "Permission denied" - Run as Administrator
🔍 "No findings" - System is clean (or scan incomplete)
```

### Report Issues

When reporting issues, include:
1. Scanner version (CLI or GUI)
2. Operating system version
3. Log file contents
4. Screenshot of error (if GUI)
5. Steps to reproduce

---

## FAQ

**Q: Do I need admin rights to run the scanner?**  
A: No, user-level permissions are sufficient for most scans. Admin rights may reveal additional processes.

**Q: Does the scanner send data to the internet?**  
A: No, all scanning is local. No data is transmitted.

**Q: Can I run both versions at the same time?**  
A: Yes, they use different ports (GUI auto-detects, CLI uses 8000).

**Q: How often should I run scans?**  
A: Weekly for development environments, monthly for production.

**Q: Can I customize what the scanner looks for?**  
A: Yes, modify the source code and rebuild, or configure via Python API.

**Q: Is my data safe?**  
A: Yes, all scans are local and reports are stored on your machine only.

**Q: Can I scan network drives?**  
A: Yes, specify the network path in scan_folder parameter.

**Q: Does it work on Linux/Mac?**  
A: These builds are Windows-only. Rebuild from source for Linux/Mac.

---

## Quick Reference Card

### GUI Version (Client System Scanner.exe)
```
1. Double-click to start
2. Click "Start Scan"
3. View dashboard results
4. Click "Export" buttons to save
```

### CLI Version (System Scanner.exe)
```
1. Double-click to start server
2. Open browser: http://localhost:8000
3. Click "Start Scan"
4. View dashboard in browser
5. Reports saved in scanner folder
```

### Output Files
```
report.json                 - JSON format results
report.html                 - HTML dashboard export
ai_scanner_history.db       - Scan history database
ai_scanner.log              - Detailed log file
```

---

## Updates & Versions

**Current Version:** 1.0.0  
**Build Date:** June 22, 2026  
**Python Version:** 3.14.3  
**PyInstaller:** 6.21.0

### Checking for Updates

Currently no auto-update mechanism. Check for new releases manually.

### Release Notes

**Version 1.0.0 (Initial Release)**
- ✅ 10 scanner modules
- ✅ CLI and GUI versions
- ✅ HTML/JSON export
- ✅ Module compliance panel
- ✅ Risk heuristics engine
- ✅ Scan history database

---

## Support

For additional support:
1. Check `BUILD_COMPLETE_REPORT.md` for technical details
2. Review source code in `System Scanner/` folder
3. Consult `DEMO.md` for feature demonstrations
4. Contact your IT department or system administrator

---

**Remember:** The scanner is a discovery and analysis tool. Always review findings with your security team before taking action.

🎯 **Goal:** Help you understand and manage AI usage in your environment!
