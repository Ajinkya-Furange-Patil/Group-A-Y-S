# System Scanner - Quick Reference Card

**Version:** CLI 1.0.2 | GUI 1.0.0  
**Build Date:** June 22, 2026  

---

## 🚀 Quick Start

### CLI Version
```bash
# Run the executable
System Scanner.exe

# Main menu will appear - select option 1-8
```

### GUI Version
```bash
# Run the executable
Client System Scanner.exe

# Window opens automatically with dashboard
```

---

## 📋 CLI Menu Options

```
[1] Run Quick Scan (Headless)      - Fast 2-level scan
[2] Run Full Scan (Headless)       - Complete 10-level scan
[3] Run Custom Scan                - Configure everything
[4] Start Web UI Dashboard         - Browser interface
[5] View Last Scan Results         - Summary in terminal
[6] Export Last Scan (JSON)        - Save JSON report
[7] Export Last Scan (HTML)        - Save HTML report
[8] About / Help                   - Documentation
[0] Exit                           - Quit application
```

---

## ⚙️ Configuration Options (Both Versions)

### Target Region
| Option | Description | Status |
|--------|-------------|--------|
| **Full System** | Scan entire system | ✅ Available |
| **Custom Folder** | Specify directory path | ✅ Available |
| **GitHub Repo** | Clone & scan repository | 🔜 Future |
| **Google Drive** | Scan cloud storage | 🔜 Future |

### Scan Depth
| Option | Levels | Speed | CLI | GUI |
|--------|--------|-------|-----|-----|
| **Quick Mode** | 2 | Fastest | ✅ | ✅ |
| **Normal** | 10 | Balanced | ✅ | ✅ |
| **Deep Scan** | 20 | Thorough | ✅ | ❌ |
| **Custom** | 0-999 | Variable | ✅ | ✅ |
| **Unlimited** | 0 | Slowest | ✅ | ⚠️ |

---

## 📂 Output Files

| File | Description | When Created |
|------|-------------|--------------|
| `report.json` | Scan results (machine-readable) | After every scan |
| `report.html` | Dashboard export | On HTML export |
| `ai_scanner.log` | Detailed logs (CLI) | While running |
| `ai_scanner_gui.log` | GUI logs | While running |
| `ai_scanner_history.db` | Scan history database | First scan |

---

## 🎯 Common Tasks

### Task 1: Quick Security Check
```
CLI: [1] Quick Scan
GUI: Click "Start Scan" (default quick mode)
Time: 8-12 seconds
```

### Task 2: Full System Audit
```
CLI: [2] Full Scan
GUI: Select "Full System" + "Normal" depth
Time: 15-25 seconds
```

### Task 3: Scan Specific Folder
```
CLI: [3] Custom Scan → [2] Custom Folder
GUI: Select "Custom Folder" → Enter path
Enter: C:\Projects\MyApp
```

### Task 4: Deep Scan (CLI Only)
```
CLI: [3] Custom Scan → [3] Deep Scan
Depth: 20 levels
Time: 30-45 seconds
```

### Task 5: View Previous Results
```
CLI: [5] View Last Results
GUI: Check history section in dashboard
```

---

## 🔍 Scanner Modules

| # | Module | Detects |
|---|--------|---------|
| 01 | System | OS, hardware info |
| 02 | File | AI model files (.gguf, .safetensors) |
| 03 | Process | Running AI processes |
| 04 | Package | Python AI packages |
| 05 | Agent | AI framework scripts |
| 06 | Runtime | Open ports, services |
| 07 | API | Hardcoded API keys |
| 08 | MCP | Model Context Protocol |
| 09 | License | License compliance |
| 10 | Compliance | Security checks |

---

## 🎨 Risk Levels

| Level | Color | Action Required |
|-------|-------|----------------|
| 🔴 **Critical** | Red | Immediate attention |
| 🟠 **High** | Orange | Address soon |
| 🟡 **Medium** | Yellow | Monitor & plan |
| 🔵 **Low** | Blue | Low priority |
| ⚪ **Info** | White | Reference only |

---

## 🛠️ Troubleshooting

### Issue: Port 8000 in use
**Solution:** GUI auto-detects. CLI: Close other apps or use GUI.

### Issue: Scan takes too long
**Solution:** Use Quick Mode or cancel (Ctrl+C).

### Issue: No results found
**Solution:** Run as Administrator for full access.

### Issue: Antivirus blocks
**Solution:** Add to exclusions (false positive).

### Issue: Path doesn't exist
**Solution:** Check path spelling, use absolute paths.

---

## 💡 Tips & Tricks

### CLI Tips
- Press **Enter** after each result to return to menu
- Use **Ctrl+C** to cancel running scan
- Option **[4]** opens web UI without browser hassle
- Option **[8]** shows full help anytime

### GUI Tips
- Dashboard shows real-time progress
- Click module names to jump to findings
- Use filters to view specific severities
- Export before closing to save results

### Performance Tips
- Close unnecessary applications before scanning
- Quick Mode for routine checks
- Full/Deep Scan for audits
- Custom folder scan for projects

---

## 📏 File Sizes

| Version | Size | Includes |
|---------|------|----------|
| **CLI** | 10.97 MB | All modules + Web UI |
| **GUI** | 18.85 MB | CLI + pywebview |

---

## 🔄 Version Comparison

| Feature | CLI | GUI | Winner |
|---------|-----|-----|--------|
| File Size | 10.97 MB | 18.85 MB | CLI |
| User-Friendly | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | GUI |
| Automation | ⭐⭐⭐⭐⭐ | ⭐⭐ | CLI |
| Deep Scan | ✅ | ❌ | CLI |
| Visual | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | GUI |
| Flexibility | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | CLI |

---

## 📱 Use Cases

### CLI Best For:
- Developers & IT professionals
- Automation & scripting
- SSH/remote sessions
- CI/CD pipelines
- Command-line workflows

### GUI Best For:
- End users & non-technical staff
- Desktop application users
- Presentations & demos
- Visual analysis
- Point-and-click operation

---

## 🔐 Security Notes

- ✅ All scans are local (no internet)
- ✅ No data transmitted externally
- ✅ Reports stored locally only
- ✅ Safe to use on sensitive systems
- ⚠️ May require admin rights for full visibility

---

## 📞 Quick Help

### CLI
- Type **8** at menu for help
- Check `ai_scanner.log` for errors
- Use Option **[5]** to view last results

### GUI
- Click **?** icon (if available)
- Check `ai_scanner_gui.log` for errors
- Review dashboard history section

---

## 🚦 Status Indicators

### CLI Console
```
✓ = Success
✗ = Error/Failure
→ = Information
⚠️ = Warning
! = Attention
```

### GUI Dashboard
```
Green Badge = OK/Success
Red Badge = Critical/Error
Yellow Badge = Warning
Blue Badge = Info
```

---

## ⌨️ Keyboard Shortcuts

### CLI
- **0-8** = Menu selection
- **Y/N** = Yes/No prompts
- **Enter** = Confirm/Continue
- **Ctrl+C** = Cancel/Exit

### GUI
- **F5** = Refresh (browser)
- **Ctrl+W** = Close window
- **Ctrl+R** = Reload page

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `BUILD_COMPLETE_REPORT.md` | Technical build details |
| `QUICK_START_GUIDE.md` | User guide for both versions |
| `CLI_ENHANCED_OPTIONS.md` | CLI configuration guide |
| `FINAL_BUILD_SUMMARY.md` | Complete feature comparison |
| `QUICK_REFERENCE_CARD.md` | This card! |

---

## 🎓 Remember

1. **Quick Check?** → CLI Option [1] or GUI Quick Mode
2. **Full Audit?** → CLI Option [2] or GUI Full System
3. **Specific Folder?** → CLI Option [3] or GUI Custom Folder
4. **Need Help?** → CLI Option [8] or check docs
5. **Save Results?** → CLI Option [6]/[7] or GUI Export

---

## ✨ Quick Examples

### Example 1: Fast Check
```
CLI: [1] → Wait 10s → View results → [0] Exit
Time: < 1 minute
```

### Example 2: Project Scan
```
CLI: [3] → [2] → Enter "C:\MyProject" → [1] Normal → Y
Time: 15-30 seconds
```

### Example 3: Web Dashboard
```
CLI: [4] → Browser opens → Click "Start Scan"
GUI: Double-click exe → Click "Start Scan"
```

---

**Keep This Card Handy!**

Print or bookmark for quick reference while using the scanner.

---

**Created:** June 22, 2026  
**Version:** 1.0  
**Status:** Reference Guide
