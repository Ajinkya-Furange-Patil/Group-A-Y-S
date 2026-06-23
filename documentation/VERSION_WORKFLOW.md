# Version Management Workflow

**Visual Guide to Automatic Versioning**

---

## 📊 Version Management Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VERSION MANAGEMENT SYSTEM                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Single Source   │
│    of Truth      │
│                  │
│  version_manager │◄───────┐
│      .py         │        │
│                  │        │
│ VERSION="1.2.1"  │        │
└────────┬─────────┘        │
         │                  │
         ├──────────────────┤
         ▼                  │
┌──────────────────┐        │
│  Auto-Generated  │        │
│     History      │        │
│                  │        │
│ version_history  │        │
│     .json        │        │
│                  │        │
│  [              │        │
│    {            │        │
│     "old": "1.2.0" │    │
│     "new": "1.2.1" │    │
│    }            │        │
│  ]              │        │
└──────────────────┘        │
                            │
┌───────────────────────────┴─────────────────────────────┐
│                   UPDATE METHODS                         │
└──────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Manual     │    │   Windows    │    │     Git      │
│   Python     │    │    Batch     │    │  Pre-Commit  │
│   Script     │    │    File      │    │    Hook      │
│              │    │              │    │              │
│ auto_version │    │ bump_version │    │  Automatic   │
│  _bump.py    │    │    .bat      │    │   on every   │
│              │    │              │    │   commit     │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                           ▼
                ┌──────────────────┐
                │  increment_      │
                │   version()      │
                │                  │
                │  - Parse version │
                │  - Increment     │
                │  - Update file   │
                │  - Log change    │
                └──────────────────┘
```

---

## 🔄 Manual Version Bump Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                   MANUAL BUMP WORKFLOW                       │
└─────────────────────────────────────────────────────────────┘

   Developer
       │
       ├─► Make code changes
       │
       ├─► Run bump script
       │   ┌────────────────────────────────────┐
       │   │ python auto_version_bump.py patch  │
       │   └────────────────────────────────────┘
       │            │
       │            ▼
       │   ┌─────────────────┐
       │   │  Read current   │
       │   │    version      │
       │   │   "1.2.1"       │
       │   └────────┬────────┘
       │            │
       │            ▼
       │   ┌─────────────────┐
       │   │  Increment      │
       │   │  based on type  │
       │   │                 │
       │   │  patch → 1.2.2  │
       │   │  minor → 1.3.0  │
       │   │  major → 2.0.0  │
       │   └────────┬────────┘
       │            │
       │            ▼
       │   ┌─────────────────┐
       │   │  Update         │
       │   │  version_       │
       │   │  manager.py     │
       │   └────────┬────────┘
       │            │
       │            ▼
       │   ┌─────────────────┐
       │   │  Log change to  │
       │   │  version_       │
       │   │  history.json   │
       │   └────────┬────────┘
       │            │
       │            ▼
       │   ┌─────────────────┐
       │   │  Display        │
       │   │  success        │
       │   │  message        │
       │   └─────────────────┘
       │
       ├─► Commit changes
       │
       └─► Build executables (optional)
```

---

## 🤖 Automatic Git Hook Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                  GIT HOOK AUTO-BUMP WORKFLOW                │
└─────────────────────────────────────────────────────────────┘

   Developer
       │
       ├─► One-time setup:
       │   python setup_auto_version.py install
       │
       │   ┌─────────────────────────────────┐
       │   │  Install pre-commit hook at:    │
       │   │  .git/hooks/pre-commit          │
       │   └─────────────────────────────────┘
       │
       │
   ┌───┴──────────────────────────────────────────────┐
   │              NORMAL WORKFLOW                      │
   └───┬──────────────────────────────────────────────┘
       │
       ├─► Make code changes
       │
       ├─► git add .
       │
       ├─► git commit -m "Fixed bug"
       │
       │   ┌────────────────────────────┐
       │   │  Pre-commit hook triggers  │
       │   └───────────┬────────────────┘
       │               │
       │               ▼
       │   ┌─────────────────────────┐
       │   │  Auto-increment patch   │
       │   │  1.2.1 → 1.2.2          │
       │   └───────────┬─────────────┘
       │               │
       │               ▼
       │   ┌─────────────────────────┐
       │   │  Stage version files:   │
       │   │  - version_manager.py   │
       │   │  - version_history.json │
       │   └───────────┬─────────────┘
       │               │
       │               ▼
       │   ┌─────────────────────────┐
       │   │  Print version change:  │
       │   │  [Auto Version]         │
       │   │  1.2.1 → 1.2.2          │
       │   └───────────┬─────────────┘
       │               │
       │               ▼
       │   ┌─────────────────────────┐
       │   │  Commit proceeds with   │
       │   │  updated version files  │
       │   └─────────────────────────┘
       │
       └─► Done! Version auto-bumped
```

---

## 🌐 Version Flow Through System

```
┌─────────────────────────────────────────────────────────────┐
│              VERSION PROPAGATION FLOW                        │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│ version_manager  │
│     .py          │
│                  │
│ VERSION="1.2.1"  │
└────────┬─────────┘
         │
         │ get_version()
         │
         ├────────────────────────────┐
         │                            │
         ▼                            ▼
┌─────────────────┐          ┌─────────────────┐
│   scanner/      │          │   scanner/      │
│   __init__.py   │          │   server.py     │
│                 │          │                 │
│ __version__ =   │          │ get_version()   │
│  get_version()  │          │                 │
└────────┬────────┘          └────────┬────────┘
         │                            │
         ├────────────┬───────────────┤
         │            │               │
         ▼            ▼               ▼
┌─────────────┐ ┌──────────┐ ┌──────────────┐
│  Console    │ │  Web UI  │ │  API         │
│  Output     │ │ Template │ │  Endpoints   │
│             │ │          │ │              │
│ "v1.2.1"    │ │ {{version}}│ │ /api/version│
└─────────────┘ └──────────┘ └──────────────┘
         │            │               │
         └────────────┴───────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │   OUTPUTS              │
         ├────────────────────────┤
         │ • report.json          │
         │   "version": "1.2.1"   │
         │                        │
         │ • report_v1_2_1.xlsx   │
         │   Header: "v1.2.1"     │
         │                        │
         │ • dashboard_v1_2_1.html│
         │   Footer: "v1.2.1"     │
         │                        │
         │ • ai_scanner.log       │
         │   "Scanner v1.2.1..."  │
         └────────────────────────┘
```

---

## 🎛️ Version Bump Type Selection

```
┌─────────────────────────────────────────────────────────────┐
│                 VERSION BUMP DECISION TREE                   │
└─────────────────────────────────────────────────────────────┘

            What type of change?
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
    Breaking              Compatible
     change?                change?
        │                       │
        ├─YES──►MAJOR       ┌───┴───┐
        │       (2.0.0)     │       │
        └─NO───┐            ▼       ▼
               │         New     Bug fix?
               │       feature?    │
               │          │        │
               │     ┌────┴───┐    │
               │     │        │    │
               └─────┼──YES───┼────┼──►PATCH
                     │        │    │   (1.2.2)
                     ▼        └─NO─┘
                   MINOR
                  (1.3.0)


EXAMPLES:

PATCH (1.2.1 → 1.2.2)
├─► Fixed ProcessScanner crash
├─► Updated documentation
├─► Minor UI tweaks
└─► Performance improvements

MINOR (1.2.1 → 1.3.0)
├─► Added PDF export
├─► New scanner module
├─► Enhanced API endpoints
└─► New features (compatible)

MAJOR (1.2.1 → 2.0.0)
├─► Changed API structure
├─► Removed deprecated features
├─► New CLI arguments
└─► Breaking changes
```

---

## 🔧 Version Manager Internal Flow

```
┌─────────────────────────────────────────────────────────────┐
│           increment_version() INTERNAL FLOW                  │
└─────────────────────────────────────────────────────────────┘

increment_version("patch")
        │
        ▼
┌───────────────────┐
│ 1. Parse VERSION  │
│    "1.2.1"        │
│    → [1, 2, 1]    │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 2. Increment      │
│    based on type  │
│                   │
│    patch: [1,2,2] │
│    minor: [1,3,0] │
│    major: [2,0,0] │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 3. Format new     │
│    version string │
│    "1.2.2"        │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 4. Read file      │
│    version_       │
│    manager.py     │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 5. Replace        │
│    VERSION line   │
│    "1.2.1" →      │
│    "1.2.2"        │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 6. Write file     │
│    back to disk   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 7. Log change to  │
│    history.json   │
│    {              │
│      old: "1.2.1" │
│      new: "1.2.2" │
│      type: "patch"│
│      time: "..."  │
│    }              │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 8. Return new     │
│    version        │
│    "1.2.2"        │
└───────────────────┘
```

---

## 📦 Build Process with Versioning

```
┌─────────────────────────────────────────────────────────────┐
│              BUILD PROCESS WITH VERSION                      │
└─────────────────────────────────────────────────────────────┘

python build_both_versions.py
        │
        ▼
┌──────────────────┐
│ 1. Import        │
│    get_version() │
│    → "1.2.1"     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 2. Build CLI     │
│    System        │
│    Scanner.exe   │
│                  │
│    Includes:     │
│    - version in  │
│      metadata    │
│    - version in  │
│      resources   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 3. Build GUI     │
│    Client System │
│    Scanner.exe   │
│                  │
│    Includes:     │
│    - version in  │
│      metadata    │
│    - version in  │
│      resources   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 4. Both exes     │
│    report        │
│    version v1.2.1│
│    when run      │
└──────────────────┘
```

---

## 🎯 Quick Reference

### Version Format
```
MAJOR.MINOR.PATCH
  1  .  2  .  1

1 = Breaking changes
2 = New features
1 = Bug fixes
```

### Bump Commands
```bash
# Patch (1.2.1 → 1.2.2)
python auto_version_bump.py patch

# Minor (1.2.1 → 1.3.0)
python auto_version_bump.py minor

# Major (1.2.1 → 2.0.0)
python auto_version_bump.py major
```

### Git Hook
```bash
# Install
python setup_auto_version.py install

# Uninstall
python setup_auto_version.py uninstall
```

### Check Version
```python
from scanner.version_manager import get_version
print(get_version())  # "1.2.1"
```

---

**For complete documentation, see:**
- `VERSION_MANAGEMENT.md` - Full guide
- `BACKEND_FEATURES_README.md` - Quick reference
- `IMPLEMENTATION_COMPLETE.md` - Summary
