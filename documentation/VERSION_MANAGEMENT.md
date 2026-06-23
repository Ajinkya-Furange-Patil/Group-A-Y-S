# Version Management System

**AI Discovery Scanner - Automatic Version Control**

---

## Overview

The AI Discovery Scanner includes an automated version management system that follows **Semantic Versioning (SemVer)** principles. The version number is automatically incremented based on the type of changes made.

**Current Version:** `1.2.0`

---

## Semantic Versioning Format

```
MAJOR.MINOR.PATCH
  │     │     │
  │     │     └── Bug fixes and patches (backwards-compatible)
  │     └──────── New features (backwards-compatible)
  └────────────── Breaking changes (not backwards-compatible)
```

### Version Increment Rules

| Change Type | Increment | Example | When to Use |
|-------------|-----------|---------|-------------|
| **PATCH** | x.x.1 | 1.0.0 → 1.0.1 | Bug fixes, small improvements, documentation updates |
| **MINOR** | x.1.0 | 1.0.0 → 1.1.0 | New features, new modules, non-breaking enhancements |
| **MAJOR** | 1.0.0 | 1.0.0 → 2.0.0 | Breaking API changes, major refactors, incompatible updates |

---

## Version Files

### Single Source of Truth

**File:** `System Scanner/scanner/version_manager.py`

```python
VERSION = "1.2.0"  # Auto-updated on changes

def get_version() -> str:
    """Return the application version number."""
    return VERSION
```

### Version History Log

**File:** `System Scanner/version_history.json`

Automatically maintained log of all version changes:

```json
[
  {
    "old_version": "1.1.0",
    "new_version": "1.2.0",
    "bump_type": "minor",
    "timestamp": "2026-06-22T14:30:00",
    "auto_updated": true
  }
]
```

---

## Manual Version Bumping

### Quick Version Bump (Windows)

```batch
REM Patch version (bug fixes)
bump_version.bat

REM Minor version (new features)
bump_version.bat minor

REM Major version (breaking changes)
bump_version.bat major
```

### Python Script

```bash
# Patch version (default)
python auto_version_bump.py

# Specific bump type
python auto_version_bump.py patch   # 1.0.0 -> 1.0.1
python auto_version_bump.py minor   # 1.0.0 -> 1.1.0
python auto_version_bump.py major   # 1.0.0 -> 2.0.0
```

---

## Automatic Version Bumping

### Git Pre-Commit Hook (Recommended)

Install automatic version bumping on every Git commit:

```bash
# Install the hook
python setup_auto_version.py install

# Now every commit auto-increments patch version
git commit -m "Fixed bug in ProcessScanner"
# Output: [Auto Version] 1.2.0 -> 1.2.1

# Uninstall if needed
python setup_auto_version.py uninstall
```

**How It Works:**
1. You make code changes
2. You run `git commit`
3. Pre-commit hook automatically bumps patch version
4. Version files are staged and included in commit
5. Commit proceeds with updated version

**Benefits:**
- Never forget to update version
- Every commit has a unique version
- Automatic version history tracking
- No manual intervention needed

---

## Version Display

### Where Version Appears

1. **Web Dashboard**
   - Footer: "AI Discovery Scanner v1.2.0"
   - Header display name
   
2. **Console Output**
   ```
   AI Discovery Scanner v1.2.0
   Starting scan...
   ```

3. **Exported Reports**
   - JSON: `"version": "1.2.0"`
   - Excel: Header "AI Discovery Scanner — Scan Summary Report (v1.2.0)"
   - HTML: Footer and metadata
   - Filenames: `ai_scan_report_v1_2_0.xlsx`

4. **API Endpoints**
   ```bash
   GET /api/version
   Response: {
     "version": "1.2.0",
     "version_string": "v1.2.0",
     "display_name": "AI Discovery Scanner v1.2.0",
     "api_version": "1.0",
     "build_date": "2026-06-22T14:30:00"
   }
   ```

5. **Log Files**
   ```
   2026-06-22 14:30:00 | INFO | AI Discovery Scanner v1.2.0 starting...
   ```

---

## Integration with Build System

### Version in Executables

When building with PyInstaller, the version is embedded:

```bash
# Build with current version
python build_both_versions.py

# Executables include version in metadata
System Scanner.exe         # v1.2.0
Client System Scanner.exe  # v1.2.0
```

### Version Check in Code

```python
from scanner.version_manager import get_version, get_version_info

# Simple version string
version = get_version()  # "1.2.0"

# Detailed version info
info = get_version_info()
# {
#   "version": "1.2.0",
#   "version_string": "v1.2.0",
#   "display_name": "AI Discovery Scanner v1.2.0",
#   "api_version": "1.0",
#   "build_date": "2026-06-22T14:30:00"
# }
```

---

## Workflow Examples

### Scenario 1: Bug Fix

```bash
# 1. Fix the bug in code
# 2. Bump patch version
python auto_version_bump.py patch
# Output: 1.2.0 -> 1.2.1

# 3. Commit changes
git add .
git commit -m "Fixed ProcessScanner crash on empty results"

# 4. Rebuild if distributing
python build_both_versions.py
```

### Scenario 2: New Feature

```bash
# 1. Implement new feature
# 2. Bump minor version
python auto_version_bump.py minor
# Output: 1.2.1 -> 1.3.0

# 3. Commit
git commit -m "Added PDF export functionality"

# 4. Rebuild
python build_both_versions.py
```

### Scenario 3: With Auto-Commit Hook

```bash
# 1. Install auto-version hook (once)
python setup_auto_version.py install

# 2. Make changes
# 3. Commit (version auto-bumps)
git commit -m "Updated API scanner patterns"
# Output: [Auto Version] 1.3.0 -> 1.3.1

# Done! Version updated automatically
```

---

## Version History Tracking

### View Version History

```python
import json
from pathlib import Path

history_file = Path("System Scanner/version_history.json")
history = json.loads(history_file.read_text())

for entry in history[-10:]:  # Last 10 changes
    print(f"{entry['old_version']} -> {entry['new_version']}")
    print(f"  Type: {entry['bump_type']}")
    print(f"  Time: {entry['timestamp']}")
    print()
```

### History Retention

- Automatically keeps last **50 version changes**
- Older entries are pruned
- Full history available in Git commits

---

## Best Practices

### When to Bump

✅ **DO bump version when:**
- Fixing bugs (patch)
- Adding features (minor)
- Changing APIs (major)
- Releasing to users
- Creating distribution builds

❌ **DON'T bump version for:**
- Work-in-progress commits (use feature branches)
- Documentation-only changes (optional)
- Internal refactoring without user impact (optional)

### Recommended Workflow

**Option A: Auto-Commit Hook (Best for Teams)**
```bash
python setup_auto_version.py install
# Now every commit auto-bumps patch
# Manual bump for minor/major only
```

**Option B: Manual Bumping (Best for Solo)**
```bash
# Bump when ready to release
python auto_version_bump.py minor
git commit -m "Release v1.3.0 with new features"
```

**Option C: Release Branches**
```bash
# Develop on feature branches (no version bump)
git checkout -b feature/pdf-export

# Bump version when merging to main
git checkout main
git merge feature/pdf-export
python auto_version_bump.py minor
git commit -m "Release v1.3.0"
```

---

## Troubleshooting

### Version Not Updating

**Issue:** Version shows old number after bump

**Solution:**
```bash
# Restart application/server
# Rebuild executables if using .exe
python build_both_versions.py
```

### Git Hook Not Working

**Issue:** Pre-commit hook doesn't run

**Solution:**
```bash
# Reinstall hook
python setup_auto_version.py uninstall
python setup_auto_version.py install

# Check hook is executable (Linux/Mac)
chmod +x .git/hooks/pre-commit
```

### Version Conflict

**Issue:** Multiple developers changing version

**Solution:**
```bash
# Use auto-commit hook to avoid conflicts
# Or coordinate version bumps on main branch only
```

---

## API Reference

### Functions

```python
# Get current version string
from scanner.version_manager import get_version
version = get_version()  # "1.2.0"

# Get detailed version info
from scanner.version_manager import get_version_info
info = get_version_info()
# Returns: dict with version, version_string, display_name, etc.

# Manually increment version
from scanner.version_manager import increment_version
new_version = increment_version("minor")  # "1.2.0" -> "1.3.0"
```

### REST API Endpoints

```bash
# Get version info
GET /api/version
Response: {
  "version": "1.2.0",
  "version_string": "v1.2.0",
  "display_name": "AI Discovery Scanner v1.2.0",
  "api_version": "1.0",
  "build_date": "2026-06-22T14:30:00"
}

# Download versioned reports
GET /api/export/json   # ai_scan_report_v1_2_0.json
GET /api/export/excel  # ai_scan_report_v1_2_0.xlsx
GET /api/export/html   # ai_scan_dashboard_v1_2_0.html
```

---

## Migration Guide

### Upgrading from Non-Versioned System

If you have an older scanner without version management:

```bash
# 1. Copy new version files
cp version_manager.py System\ Scanner/scanner/
cp auto_version_bump.py System\ Scanner/
cp setup_auto_version.py System\ Scanner/

# 2. Set initial version
# Edit scanner/version_manager.py
VERSION = "1.0.0"  # Set your current version

# 3. Install auto-bump (optional)
python setup_auto_version.py install

# 4. Rebuild
python build_both_versions.py
```

---

## Summary

✅ **Implemented Features:**
- Single source of truth for version
- Semantic versioning (MAJOR.MINOR.PATCH)
- Manual version bumping scripts
- Automatic Git pre-commit hook
- Version history logging
- API endpoints for version info
- Version in all reports and exports
- Version in executable metadata

✅ **Version Management Files:**
- `scanner/version_manager.py` - Core version module
- `auto_version_bump.py` - Manual bump script
- `bump_version.bat` - Windows batch wrapper
- `setup_auto_version.py` - Git hook installer
- `version_history.json` - Change log

---

**Current Version:** `1.2.0`  
**Last Updated:** June 22, 2026  
**Auto-Update:** Enabled via pre-commit hook
