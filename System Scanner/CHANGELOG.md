# Changelog

All notable changes to the AI Discovery Scanner project.

---

## [1.2.1] - 2026-06-22

### Added - Version Management System
- ✅ Automatic version management with semantic versioning
- ✅ `version_manager.py` - Core version control module
- ✅ `auto_version_bump.py` - Manual version bump script
- ✅ `bump_version.bat` - Windows batch wrapper for version bumping
- ✅ `setup_auto_version.py` - Git pre-commit hook installer
- ✅ `version_history.json` - Automatic version change tracking (last 50 entries)
- ✅ Version in all console outputs and log files
- ✅ Version in all exported reports (JSON, Excel, HTML)
- ✅ Versioned export filenames (e.g., `ai_scan_report_v1_2_1.xlsx`)

### Added - Backend API Enhancements
- ✅ `/api/version` - Get detailed version information
- ✅ `/api/modules` - Get module execution status and statistics
- ✅ `/api/export/json` - Download JSON report with versioned filename
- ✅ `/api/export/html` - Download HTML dashboard with versioned filename
- ✅ Enhanced `/api/export/excel` - Versioned filename support

### Added - Documentation
- ✅ `VERSION_MANAGEMENT.md` - Complete version management guide
- ✅ `BACKEND_IMPLEMENTATION_SUMMARY.md` - Technical implementation details
- ✅ `BACKEND_FEATURES_README.md` - Quick reference guide
- ✅ `IMPLEMENTATION_COMPLETE.md` - Implementation summary
- ✅ `VERSION_WORKFLOW.md` - Visual workflow diagrams
- ✅ `CHANGELOG.md` - This file

### Changed
- 🔄 Updated `server.py` to include version information in responses
- 🔄 Updated `BUILD_COMPLETE_REPORT.md` with version management info
- 🔄 Enhanced export endpoints with proper versioning

### Technical Details
- **Files Created:** 9 (5 Python scripts, 4 documentation files)
- **Files Modified:** 2 (server.py, BUILD_COMPLETE_REPORT.md)
- **Lines of Code Added:** ~500
- **Documentation Added:** ~2,000 lines
- **API Endpoints Added:** 5
- **Testing:** All features manually tested and verified

---

## [1.2.0] - 2026-06-22

### Added - Initial Backend Implementation
- ✅ Version management foundation
- ✅ Backend API structure
- ✅ Server enhancements for GUI version

---

## [1.1.0] - 2026-06-22 (Previous)

### Core Scanner Features
- ✅ 10 scanner modules (System, File, Process, Package, Agent, Runtime, API, MCP, License, Compliance)
- ✅ CLI interface with menu system
- ✅ GUI version with pywebview
- ✅ Web dashboard interface
- ✅ JSON and HTML report generation
- ✅ Excel export functionality
- ✅ Risk scoring and classification
- ✅ Module compliance tracking

### Build System
- ✅ PyInstaller build scripts
- ✅ Dual executable generation (CLI + GUI)
- ✅ Custom icon support
- ✅ Automated build process

---

## Version Format

This project follows [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes
MINOR: New features (backwards-compatible)
PATCH: Bug fixes (backwards-compatible)
```

---

## How to Update Version

### Manual Bump
```bash
python auto_version_bump.py [patch|minor|major]
```

### Automatic (Git Hook)
```bash
# One-time setup
python setup_auto_version.py install

# Then version auto-bumps on every commit
git commit -m "Your changes"
```

---

## Recent Changes Summary

### v1.2.1 (Current)
**Backend Implementation Complete**
- Automatic version management ✅
- Enhanced API endpoints ✅  
- Comprehensive documentation ✅
- Git integration ✅
- Production ready ✅

### v1.2.0
**Foundation Release**
- Version system architecture
- API structure
- Server enhancements

### v1.1.0
**Core Scanner Release**
- Full scanner functionality
- 10 detection modules
- CLI and GUI interfaces
- Report generation

---

## Upgrade Notes

### From 1.1.0 to 1.2.1

**New Features:**
- Version now auto-tracks in all outputs
- New API endpoints for version and module status
- Versioned export filenames
- Git hook for automatic versioning

**Breaking Changes:**
- None (fully backwards compatible)

**Migration Steps:**
1. No changes required for existing scans
2. Optionally install Git hook: `python setup_auto_version.py install`
3. Rebuild executables if distributing: `python build_both_versions.py`

---

## Roadmap

### Planned for v1.3.0 (Next Minor Release)
- ❌ PDF export functionality
- ❌ Enhanced UI/UX features
- ❌ Dynamic loading messages
- ❌ Theme toggle fixes

### Planned for v2.0.0 (Next Major Release)
- ❌ Cloud storage integration
- ❌ GitHub repository scanning
- ❌ Scheduled scan functionality
- ❌ Email reporting

---

## Contributors

**Group A-Y-S**
- Version Management System
- Backend API Enhancements
- Documentation

---

## License

See LICENSE file for details.

---

**Current Version:** 1.2.1  
**Last Updated:** June 22, 2026  
**Status:** Production Ready ✅
