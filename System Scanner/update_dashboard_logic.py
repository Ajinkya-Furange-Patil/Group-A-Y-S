import re

with open('scanner/reporter/templates/dashboard.html.j2', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update finding details logic to render tables
old_details = '''      {% if f.details %}
        <div class="details-code">
          {% for k, v in f.details.items() %}
            {{ k }}: {{ v }}<br>
          {% endfor %}
        </div>
      {% endif %}'''

new_details = '''      {% if f.details %}
        <div class="details-code">
          {% for k, v in f.details.items() %}
            {% if k == "registry_entries" and v is iterable and v is not string and v|length > 0 %}
              <div class="details-label" style="margin-top: 10px; margin-bottom: 5px;">Registry Entries</div>
              <table class="metadata-table">
                <thead>
                  <tr>
                    <th>Hive</th>
                    <th>Key Path</th>
                    <th>Value Name</th>
                    <th>Interpretation</th>
                  </tr>
                </thead>
                <tbody>
                  {% for entry in v %}
                  <tr>
                    <td>{{ entry.get("hive", "") }}</td>
                    <td style="word-break: break-all;">{{ entry.get("key_path", "") }}</td>
                    <td>{{ entry.get("value_name", "") }}</td>
                    <td>{{ entry.get("interpretation", "") }}</td>
                  </tr>
                  {% endfor %}
                </tbody>
              </table>
            {% elif v is mapping %}
              <strong>{{ k }}:</strong>
              <table class="metadata-table" style="margin-top: 4px; margin-bottom: 8px;">
                <tbody>
                {% for sub_k, sub_v in v.items() %}
                  <tr>
                    <td style="width: 30%;"><strong>{{ sub_k }}</strong></td>
                    <td>{{ sub_v }}</td>
                  </tr>
                {% endfor %}
                </tbody>
              </table>
            {% else %}
              <strong>{{ k }}:</strong> {{ v }}<br>
            {% endif %}
          {% endfor %}
        </div>
      {% endif %}'''

text = text.replace(old_details, new_details)

# 2. Add scrollToModule to script tag
script_add = '''
    function scrollToModule(moduleId) {
      const el = document.getElementById('module-' + moduleId);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Add a highlight effect
        el.style.transition = 'background-color 0.5s';
        const oldBg = el.style.backgroundColor;
        el.style.backgroundColor = 'rgba(211, 13, 48, 0.1)';
        setTimeout(() => {
          el.style.backgroundColor = oldBg;
        }, 1500);
      }
    }
'''
text = text.replace('function toggleFinding(header) {', script_add + '\n    function toggleFinding(header) {')

# 3. Add PDF Modal & Logic
pdf_html = '''
  <!-- PDF GENERATION MODAL (CORPORATE LIGHT THEME) -->
  <div id="pdfModal" class="pdf-modal-overlay" style="display: none;">
    <div class="pdf-modal-content">
      <div class="pdf-modal-header">
        <h3>CONFIGURE PDF EXPORT</h3>
        <button class="pdf-modal-close" onclick="closePdfModal()">×</button>
      </div>
      <div class="pdf-modal-body">
        <p>Generating a clean, professional corporate report. Select options below:</p>
        <div style="margin-top: 15px;">
          <label style="display:flex; align-items:center; gap:8px;">
            <input type="checkbox" id="pdfIncludeLogs" checked> Include detailed telemetry logs
          </label>
          <label style="display:flex; align-items:center; gap:8px; margin-top: 10px;">
            <input type="checkbox" id="pdfExcludeInfo"> Exclude INFO-level findings
          </label>
        </div>
      </div>
      <div class="pdf-modal-footer">
        <button class="export-btn" style="background: var(--text-muted);" onclick="closePdfModal()">Cancel</button>
        <button class="export-btn" id="generatePdfBtn" onclick="generateCorporatePdf()">Generate PDF</button>
      </div>
    </div>
  </div>
'''

# Find the end of body to insert the modal and html2pdf library
body_end = text.find('</body>')
text = text[:body_end] + pdf_html + '''
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
''' + text[body_end:]

# Add script for PDF
pdf_script = '''
    function openPdfModal() {
      document.getElementById('pdfModal').style.display = 'flex';
    }
    function closePdfModal() {
      document.getElementById('pdfModal').style.display = 'none';
    }
    
    function generateCorporatePdf() {
      const btn = document.getElementById('generatePdfBtn');
      btn.textContent = "Generating...";
      btn.disabled = true;
      
      const excludeInfo = document.getElementById('pdfExcludeInfo').checked;
      
      // Temporarily switch body to light theme for corporate print
      const wasDark = document.body.classList.contains('dark-theme');
      document.body.classList.remove('dark-theme');
      
      // We will clone the dashboard view to format it cleanly for print
      const dashboard = document.getElementById('dashboard-view');
      const clone = dashboard.cloneNode(true);
      
      // Clean up the clone for a corporate look
      clone.style.background = "#ffffff";
      clone.style.color = "#000000";
      clone.querySelector('.header').style.background = "#ffffff";
      clone.querySelector('.header-title h1').style.color = "#333333";
      clone.querySelector('.header-title h1').style.textShadow = "none";
      clone.querySelector('.header-title p').style.color = "#666666";
      
      // Remove export bar from PDF
      const exportBar = clone.querySelector('.export-bar');
      if (exportBar) exportBar.remove();
      
      // If exclude INFO, remove them
      if (excludeInfo) {
        const infos = clone.querySelectorAll('.risk-level-info');
        infos.forEach(el => el.remove());
      }
      
      // Force all finding cards to be open so details are visible in PDF
      clone.querySelectorAll('.finding-card').forEach(card => card.classList.add('open'));
      
      const opt = {
        margin:       0.5,
        filename:     'AI_Scanner_Corporate_Report.pdf',
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2 },
        jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
      };
      
      html2pdf().set(opt).from(clone).save().then(() => {
        closePdfModal();
        btn.textContent = "Generate PDF";
        btn.disabled = false;
        if(wasDark) document.body.classList.add('dark-theme');
      });
    }
'''
text = text.replace('function applyFilters() {', pdf_script + '\n    function applyFilters() {')

# Add PDF Modal CSS and table css
css_add = '''
    /* PDF Modal & Tables */
    .pdf-modal-overlay {
      position: fixed; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(0,0,0,0.7); z-index: 9999;
      display: flex; align-items: center; justify-content: center;
    }
    .pdf-modal-content {
      background: var(--bg-panel); border: 2px solid var(--hud-red);
      width: 400px; padding: 20px; box-shadow: 0 0 20px rgba(255,0,60,0.3);
      font-family: var(--font-sans); color: var(--text-main);
    }
    .pdf-modal-header { display: flex; justify-content: space-between; font-weight: bold; font-family: var(--font-mono); color: var(--hud-red); margin-bottom: 15px;}
    .pdf-modal-close { background: transparent; border: none; color: var(--text-main); font-size: 1.2rem; cursor: pointer; }
    .pdf-modal-footer { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
    
    .metadata-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.8rem;
      margin-top: 10px;
    }
    .metadata-table th, .metadata-table td {
      border: 1px solid var(--border-subtle);
      padding: 6px;
      text-align: left;
    }
    .metadata-table th {
      background: rgba(211, 13, 48, 0.05);
      color: var(--hud-red);
      font-family: var(--font-mono);
      text-transform: uppercase;
    }
'''
text = text.replace('/* ═══════════════ HEADER PANEL ═══════════════ */', css_add + '\n    /* ═══════════════ HEADER PANEL ═══════════════ */')

# Add time human readable formatting script
# Wait, scan_timestamp is rendered by Jinja! The user wants the timestamp to be human readable IST.
text = text.replace('{{ result.scan_timestamp }}', '<span id="humanReadableTimestamp">{{ result.scan_timestamp }}</span>')
timestamp_js = '''
    // Format timestamp for Indian timezone
    const tsEl = document.getElementById('humanReadableTimestamp');
    if (tsEl) {
      const rawIso = tsEl.textContent;
      const d = new Date(rawIso);
      if (!isNaN(d)) {
        tsEl.textContent = d.toLocaleString('en-IN', {
          day: '2-digit', month: 'long', year: 'numeric',
          hour: '2-digit', minute: '2-digit', second: '2-digit',
          timeZoneName: 'short', timeZone: 'Asia/Kolkata'
        });
      }
    }
'''
text = text.replace('/* ═══════════════ AUTH PORTAL LOGIC ═══════════════ */', timestamp_js + '\n    /* ═══════════════ AUTH PORTAL LOGIC ═══════════════ */')


with open('scanner/reporter/templates/dashboard.html.j2', 'w', encoding='utf-8') as f:
    f.write(text)

print('dashboard.html.j2 updated with tables, PDF modal, and scroll feature!')
