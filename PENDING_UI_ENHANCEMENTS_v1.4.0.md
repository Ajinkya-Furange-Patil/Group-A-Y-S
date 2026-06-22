# Pending UI Enhancements - v1.4.0

**Date:** June 22, 2026  
**Version Target:** 1.4.0  
**Status:** Requirements Documented - Ready for Implementation

---

## 📋 Requirements Summary

### 1. ✅ GitHub & Google Drive Input Placeholders
**Location:** Consent page (authorization screen)  
**Status:** Need to add  
**Details:**
- Add "Remote GitHub Repositories" option (disabled/placeholder)
- Add "Google Drive & Cloud" option (disabled/placeholder)
- Mark as "Future Feature" with tooltip

### 2. ✅ Better Theme Toggle Styling
**Location:** Both consent.html and dashboard.html  
**Current:** Basic button  
**Required:**
- Modern toggle switch design
- Smooth sliding animation
- Better visual feedback
- Consistent across both pages

### 3. ✅ Executive Metric Attribution - Clickable Modules
**Location:** Dashboard metrics section  
**Current:** Static metrics display  
**Required:**
- Make each metric card clickable
- Clicking redirects to related findings section
- Smooth scroll animation
- Highlight target section briefly

### 4. ✅ Dynamic Version Display
**Location:** Footer and headers  
**Current:** Static "SCANNER CORE v1.0"  
**Required:**
- Use actual version from backend ({{ version }})
- Update to show v1.4.0
- Sync with version_manager.py

### 5. ✅ Improved Table Styling
**Location:** All tables in details section  
**Current:** Borders present but could be better  
**Required:**
- More visible borders (2px instead of 1px)
- Better cell padding
- Alternating row colors
- Better hover effects

### 6. ✅ Module Compliance Panel Repositioning
**Location:** Dashboard layout  
**Current:** Below "SUSPECTED DETECTION VECTORS"  
**Required:**
- Move to right side of "SUSPECTED DETECTION VECTORS"
- Create two-column layout
- Left: Detection vectors
- Right: Module compliance

### 7. ✅ Clickable Module Names in Compliance Panel
**Location:** Module Compliance Panel  
**Current:** Static module names  
**Required:**
- Make module names clickable
- Redirect to corresponding MODULE section
- Smooth scroll to target
- Highlight target module section

---

## 🎨 Design Specifications

### Theme Toggle Button

**Current Design:**
```html
<button>DARK MODE</button>
```

**New Design:**
```html
<div class="theme-toggle-container">
  <span class="theme-label">Light</span>
  <div class="toggle-switch">
    <input type="checkbox" id="theme-checkbox" />
    <label for="theme-checkbox" class="toggle-label">
      <span class="toggle-slider"></span>
    </label>
  </div>
  <span class="theme-label">Dark</span>
</div>
```

**CSS Specifications:**
- Toggle width: 50px
- Toggle height: 24px
- Slider: circular, smooth transition
- Colors: Red accent (#d30d30)
- Animation: 300ms ease-in-out

---

### GitHub & Google Drive Options

**HTML Structure:**
```html
<div class="diagnostic-grid">
  ...existing options...
  
  <!-- New options with disabled state -->
  <div class="diagnostic-item disabled" title="Feature coming soon">
    🔗 Remote Github Repositories
    <span class="future-badge">FUTURE</span>
  </div>
  
  <div class="diagnostic-item disabled" title="Feature coming soon">
    ☁️ Google Drive & Cloud
    <span class="future-badge">FUTURE</span>
  </div>
</div>
```

**CSS:**
```css
.diagnostic-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  position: relative;
}

.future-badge {
  position: absolute;
  top: 5px;
  right: 5px;
  background: var(--hud-red);
  color: white;
  font-size: 0.6rem;
  padding: 2px 6px;
  border-radius: 3px;
}
```

---

### Clickable Metrics

**JavaScript Implementation:**
```javascript
// Make metric cards clickable
document.querySelectorAll('.metric-card').forEach(card => {
  const metricType = card.getAttribute('data-metric-type');
  card.style.cursor = 'pointer';
  
  card.addEventListener('click', () => {
    const targetSection = document.getElementById(`module-${metricType}`);
    if (targetSection) {
      targetSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Highlight briefly
      targetSection.classList.add('highlight-pulse');
      setTimeout(() => {
        targetSection.classList.remove('highlight-pulse');
      }, 2000);
    }
  });
});
```

**CSS for Highlight:**
```css
@keyframes pulse {
  0%, 100% { background: var(--hud-panel-bg); }
  50% { background: var(--hud-red-dim); }
}

.highlight-pulse {
  animation: pulse 2s ease-in-out;
}
```

---

### Module Compliance Repositioning

**Current Layout:**
```
+----------------------------------+
|   SUSPECTED DETECTION VECTORS    |
|                                  |
|   (All findings here)            |
|                                  |
+----------------------------------+
|   MODULE COMPLIANCE              |
|   (Below everything)             |
+----------------------------------+
```

**New Layout:**
```
+-------------------------+----------+
|  SUSPECTED DETECTION    | MODULE  |
|  VECTORS               | COMPLI-  |
|                         | ANCE    |
|  (Findings here)        |         |
|                         | (Panel) |
|                         |         |
+-------------------------+----------+
    70% width              30% width
```

**CSS Implementation:**
```css
.findings-with-compliance {
  display: grid;
  grid-template-columns: 70% 30%;
  gap: 28px;
  align-items: start;
}

.module-compliance-panel {
  position: sticky;
  top: 20px;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
}
```

---

### Clickable Module Names

**JavaScript:**
```javascript
// Make module names in compliance panel clickable
document.querySelectorAll('.module-row').forEach(row => {
  const moduleName = row.querySelector('.module-name-lbl').textContent;
  const moduleId = moduleName.toLowerCase().replace(/\s+/g, '-');
  
  row.style.cursor = 'pointer';
  row.addEventListener('click', () => {
    const targetModule = document.getElementById(`module-${moduleId}`);
    if (targetModule) {
      targetModule.scrollIntoView({ behavior: 'smooth', block: 'start' });
      targetModule.classList.add('highlight-pulse');
      setTimeout(() => {
        targetModule.classList.remove('highlight-pulse');
      }, 2000);
    }
  });
});
```

---

### Improved Table Styling

**Enhanced CSS:**
```css
.metadata-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
  margin-top: 10px;
  background: var(--hud-panel-bg);
  border: 2px solid var(--hud-border-dim); /* Increased from 1px */
}

.metadata-table th, .metadata-table td {
  border: 2px solid var(--hud-border-dim); /* Increased from 1px */
  padding: 12px 16px; /* Increased from 10px 14px */
  text-align: left;
  line-height: 1.6;
}

.metadata-table tbody tr:nth-child(even) {
  background: var(--hud-red-dim); /* Alternating rows */
}

.metadata-table tbody tr:hover {
  background: var(--hud-panel-bg-hover);
  transform: translateX(2px);
  transition: all 200ms ease;
}
```

---

### Dynamic Version Display

**Template Changes:**
```jinja2
<!-- Footer -->
<footer class="footer">
  // SYSTEM SCANNED BY AI DISCOVERY AGENT — v{{ version }} — TELEMETRY ATTRIBUTION REPORT SECURE //
</footer>

<!-- Sidebar -->
<div class="scanner-version">
  SCANNER CORE v{{ version }}
</div>
```

**Ensure version is passed:**
```python
# In server.py or report_generator.py
from scanner.version_manager import get_version

template.render(
    result=result,
    version=get_version(),  # Pass dynamic version
    ...
)
```

---

## 📂 Files to Modify

### 1. `scanner/reporter/templates/consent.html.j2`
- [ ] Add GitHub/Google Drive options (disabled)
- [ ] Implement better theme toggle
- [ ] Add version display
- [ ] Update CSS for new elements

### 2. `scanner/reporter/templates/dashboard.html.j2`
- [ ] Implement better theme toggle
- [ ] Make metric cards clickable
- [ ] Reposition module compliance panel (grid layout)
- [ ] Make module names clickable
- [ ] Improve table styling (2px borders)
- [ ] Add dynamic version display
- [ ] Add JavaScript for click handlers
- [ ] Add highlight pulse animation

### 3. `scanner/server.py`
- [ ] Ensure version is passed to templates

### 4. `scanner/reporter/report_generator.py`
- [ ] Pass version to dashboard template

---

## 🧪 Testing Checklist

### Theme Toggle
- [ ] Toggle switches between light and dark
- [ ] Smooth animation
- [ ] Consistent across both pages
- [ ] State persists on reload

### GitHub/Google Drive
- [ ] Options visible but disabled
- [ ] "FUTURE" badge shown
- [ ] Tooltip on hover
- [ ] Cannot be clicked

### Clickable Metrics
- [ ] Each metric card is clickable
- [ ] Scrolls to correct section
- [ ] Smooth scroll animation
- [ ] Highlight pulse works

### Module Compliance
- [ ] Panel positioned on right side
- [ ] Sticky scrolling works
- [ ] Module names clickable
- [ ] Redirects to correct MODULE section
- [ ] Highlight pulse works

### Tables
- [ ] 2px borders visible
- [ ] Alternating row colors
- [ ] Hover effects work
- [ ] Better padding

### Version Display
- [ ] Shows correct version (1.4.0)
- [ ] Dynamic, not static
- [ ] Consistent across all locations

---

## 🎯 Implementation Priority

### Phase 1 (High Priority)
1. ✅ Dynamic version display
2. ✅ Module compliance repositioning
3. ✅ Clickable modules in compliance panel

### Phase 2 (Medium Priority)
4. ✅ Better theme toggle styling
5. ✅ Improved table styling
6. ✅ Clickable metric cards

### Phase 3 (Low Priority)
7. ✅ GitHub/Google Drive placeholders

---

## 📝 Implementation Notes

### Grid Layout for Compliance Panel

**Before:**
```html
<div class="findings-container">
  <!-- All findings -->
</div>
<div class="sidebar-panel">
  <div class="module-compliance-panel">
    <!-- Module compliance -->
  </div>
</div>
```

**After:**
```html
<div class="findings-with-compliance">
  <div class="findings-container">
    <!-- All findings (70% width) -->
  </div>
  <div class="sidebar-panel">
    <div class="module-compliance-panel">
      <!-- Module compliance (30% width, sticky) -->
    </div>
  </div>
</div>
```

### Module ID Generation

For clickable modules to work, module sections need IDs:
```html
<div class="module-section" id="module-systemscanner">
  <div class="module-section-title">
    MODULE: SystemScanner
  </div>
  <!-- Findings -->
</div>
```

JavaScript uses this ID:
```javascript
const moduleId = 'systemscanner'; // Lowercase, no spaces
document.getElementById(`module-${moduleId}`);
```

---

## ⚠️ Breaking Changes

None - All changes are additive or styling improvements.

---

## 📊 Estimated Impact

**Files Modified:** 4  
**CSS Changes:** ~150 lines  
**JavaScript Added:** ~80 lines  
**HTML Changes:** ~50 lines  
**Total Changes:** ~280 lines

**Testing Time:** 30-45 minutes  
**Implementation Time:** 2-3 hours

---

## ✅ Success Criteria

- [ ] All 7 requirements implemented
- [ ] No regressions in existing features
- [ ] Responsive on different screen sizes
- [ ] Smooth animations (no janky transitions)
- [ ] Cross-browser compatible
- [ ] Accessible (keyboard navigation works)

---

**Status:** Ready for implementation phase  
**Version Target:** 1.4.0  
**Priority:** High

---

**Note:** This is a comprehensive specification document. Implementation can be done in phases based on priority.
