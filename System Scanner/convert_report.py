import re

with open('report.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Insert Jinja macros at the top
macros = """
{% macro get_risk_color(level) -%}
  {% if level|lower == 'critical' %}#d30d30
  {% elif level|lower == 'high' %}#e65c00
  {% elif level|lower == 'medium' %}#ffd200
  {% elif level|lower == 'low' %}#00ffcc
  {% else %}#00e5ff
  {% endif %}
{%- endmacro %}

{% macro render_finding_card(f) %}
<div class="finding-card risk-level-{{ f.risk_level|lower }}" data-category="{{ f.category }}" data-risk="{{ f.risk_level|lower }}">
  <div class="finding-header" onclick="toggleFinding(this)">
    <div class="finding-main-info">
      <div class="finding-icon-state"></div>
      <div class="finding-title">{{ f.title }}</div>
    </div>
    <div class="finding-meta">
      <div class="badge badge-category">{{ f.category }}</div>
      <div class="badge badge-severity badge-severity-{{ f.risk_level|lower }}">{{ f.risk_level|upper }}</div>
      <div class="expand-chevron">▼</div>
    </div>
  </div>
  <div class="finding-body">
    <div class="details-grid">
      <div class="details-label">ID</div><div class="details-val">{{ f.finding_id }}</div>
      <div class="details-label">Module</div><div class="details-val">{{ f.module_name }}</div>
      <div class="details-label">Description</div><div class="details-val">{{ f.description }}</div>
      <div class="details-label">Source</div><div class="details-val"><span class="details-val-source">{{ f.source }}</span></div>
      
      {% if f.details %}
        <div class="details-code">
          {% for k, v in f.details.items() %}
            {{ k }}: {{ v }}<br>
          {% endfor %}
        </div>
      {% endif %}
    </div>
    
    <div class="confidence-wrapper">
      <div class="confidence-lbl">CONFIDENCE</div>
      <div class="confidence-track">
        <div class="confidence-bar" style="width: {{ "%.0f"|format(f.confidence * 100) }}%;"></div>
      </div>
      <div class="confidence-lbl" style="min-width: unset;">{{ "%.0f"|format(f.confidence * 100) }}%</div>
    </div>
  </div>
</div>
{% endmacro %}
"""

text = re.sub(r'<!-- ═══════════════ JINJA2 MACROS DEFINED AT TOP FOR SCOPING ═══════════════ -->', macros, text)

# 2. Replace cover page stats
text = re.sub(r'<div class="print-cover-item-value">AD-.*</div>', '<div class="print-cover-item-value">{{ result.scan_id }}</div>', text)
text = re.sub(r'<div class="print-cover-item-value">2026-06-.*</div>', '<div class="print-cover-item-value">{{ result.scan_timestamp }}</div>', text)
text = re.sub(r'<div class="print-cover-item-value">DESKTOP-.*</div>', '<div class="print-cover-item-value">{{ result.hostname }}</div>', text)
text = re.sub(r'<div class="print-cover-item-value">Windows.*</div>', '<div class="print-cover-item-value">{{ result.os_info }}</div>', text)
text = re.sub(r'<div class="print-cover-item-value">103</div>', '<div class="print-cover-item-value">{{ result.summary.total_findings }}</div>', text)
text = re.sub(r'<div class="print-cover-item-value">33.58s</div>', '<div class="print-cover-item-value">{{ "%.2f"|format(result.total_duration_sec) }}s</div>', text)

# 3. Replace summary metrics
text = re.sub(r'<div class="metric-val">103</div>', '<div class="metric-val">{{ result.summary.total_findings }}</div>', text)
text = re.sub(r'<div class="metric-val">7</div>', '<div class="metric-val">{{ result.summary.modules_run }}</div>', text)
text = re.sub(r'<div class="metric-val">33.58s</div>', '<div class="metric-val">{{ "%.2f"|format(result.total_duration_sec) }}s</div>', text)
text = re.sub(r'<div class="gauge-value">50.0</div>', '<div class="gauge-value">{{ "%.1f"|format(result.summary.overall_risk_score) }}</div>', text)

# 4. Replace finding list with Jinja loop
# The findings are wrapped in <div class="findings-container" id="findings-list">
findings_start = text.find('<div class="findings-container" id="findings-list">')
findings_end = text.find('</div>\n\n          <!-- Right Column: Sidebar Telemetry -->', findings_start)

findings_html = """<div class="findings-container" id="findings-list">
            {% set grouped_findings = {} %}
            {% for f in result.findings %}
              {% set m = f.module_name %}
              {% if m not in grouped_findings %}
                {% set _ = grouped_findings.update({m: []}) %}
              {% endif %}
              {% set _ = grouped_findings[m].append(f) %}
            {% endfor %}

            {% for m, m_findings in grouped_findings.items() %}
            <div class="module-section" id="module-{{ m|replace(' ', '-')|lower }}">
              <div class="module-section-title">
                <span class="title-txt">MODULE: {{ m }}</span>
                <span class="module-badge">{{ m_findings|length }} FINDINGS</span>
              </div>
              <div class="findings-list-wrapper">
                {% for f in m_findings %}
                  {{ render_finding_card(f) }}
                {% endfor %}
              </div>
            </div>
            {% endfor %}
"""

text = text[:findings_start] + findings_html + text[findings_end:]

# 5. Sidebar telemetry
sidebar_start = text.find('<div class="sidebar-panel">')
sidebar_end = text.find('</div>\n        </div>\n      </div>', sidebar_start)

sidebar_html = """<div class="sidebar-panel">
            <div class="hud-panel" style="padding: 16px;">
              <div class="hud-corner c-tl"></div><div class="hud-corner c-tr"></div><div class="hud-corner c-bl"></div><div class="hud-corner c-br"></div>
              <div class="hud-header-tab" style="left: 15px;">MODULE COMPLIANCE</div>
              
              <div style="display:flex; flex-direction:column; gap:8px; margin-top: 10px;">
                {% for mod in result.modules %}
                <div class="module-row" onclick="scrollToModule('{{ mod.name|replace(' ', '-')|lower }}')" style="cursor: pointer;">
                  <div class="module-title-box">
                    <span class="module-index">{{ loop.index }}</span>
                    <span class="module-name-lbl">{{ mod.name }}</span>
                  </div>
                  <div class="module-telemetry">
                    <span class="module-time">{{ "%.3f"|format(mod.duration_sec) }}s</span>
                    {% if mod.status == 'success' %}
                      <span class="module-status-indicator status-ok">OK</span>
                    {% elif mod.status == 'error' %}
                      <span class="module-status-indicator status-fail">ERR</span>
                    {% else %}
                      <span class="module-status-indicator status-skip">SKIP</span>
                    {% endif %}
                    {% if mod.findings_count > 0 %}
                      <span class="sidebar-findings-counter">{{ mod.findings_count }}</span>
                    {% endif %}
                  </div>
                </div>
                {% endfor %}
              </div>
            </div>
"""

text = text[:sidebar_start] + sidebar_html + text[sidebar_end:]

# 6. Add PDF and Excel export buttons
filter_tabs_idx = text.find('<div class="filter-tabs" id="filter-tabs">')
export_bar_html = """
        <!-- Export Bar -->
        <div class="export-bar" style="display: flex; gap: 8px; margin-bottom: 15px;">
          <button class="export-btn export-btn-excel" onclick="window.location.href='/api/export/excel'" title="Download full report as Excel workbook (.xlsx)">
            📊 Excel
          </button>
          <button class="export-btn" onclick="openPdfModal()" title="Configure and generate a formatted PDF report">
            🖨 PDF Report
          </button>
        </div>
"""
text = text[:filter_tabs_idx] + export_bar_html + text[filter_tabs_idx:]

with open('scanner/reporter/templates/dashboard.html.j2', 'w', encoding='utf-8') as f:
    f.write(text)

print("Template conversion successful.")
