from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, PlainTextResponse, StreamingResponse
from database import ResumeDatabase
from hr_base import app, get_current_user, get_base_html, get_end_html, send_email
from datetime import datetime, timedelta
import os
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO

db = ResumeDatabase()

# ── Report type metadata ──────────────────────────────────────────────────────
REPORT_TYPES = [
    ("applications",       "📋", "Applications",      "Full breakdown of all applicants, statuses, and sources."),
    ("interviews",         "📅", "Interviews",         "Interview scheduling, completion rates, and scores."),
    ("evaluations",        "⭐", "Evaluations",        "Candidate evaluation scores and recommendations."),
    ("offers",             "📝", "Offers",             "Offer pipeline: pending, sent, accepted, rejected."),
    ("comprehensive",      "📊", "Comprehensive",      "All HR metrics across the full recruitment funnel."),
    ("hiring_pipeline",    "🔄", "Hiring Pipeline",    "Stage-by-stage conversion and bottleneck analysis."),
    ("time_to_hire",       "⏱",  "Time to Hire",       "Average days from application to offer acceptance."),
    ("source_effectiveness","🎯","Source Effectiveness","Which channels produce the most hired candidates."),
]


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/", status_code=302)

    today          = datetime.now().strftime("%Y-%m-%d")
    thirty_ago     = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # Report type cards
    type_cards = ""
    for val, icon, label, desc in REPORT_TYPES:
        type_cards += f"""<label class="rt-card" for="rt-{val}">
  <input type="radio" name="report_type" id="rt-{val}" value="{val}" style="display:none;"
    onchange="selectReportType(this)">
  <div class="rt-icon">{icon}</div>
  <div class="rt-label">{label}</div>
  <div class="rt-desc">{desc}</div>
</label>"""

    page = f"""
<!-- ══ PAGE HEADER ══ -->
<div class="page-hd">
  <div>
    <div class="page-title">Reports & Analytics</div>
    <div class="page-sub">Generate, schedule, and download comprehensive HR reports.</div>
  </div>
</div>

<!-- ══ TWO-COLUMN ══ -->
<div style="display:grid;grid-template-columns:1fr 300px;gap:20px;align-items:start;">

  <!-- LEFT: Generate form -->
  <div style="display:flex;flex-direction:column;gap:20px;">

    <!-- Report type picker -->
    <div class="card" style="animation:fadeUp 0.3s ease both;">
      <div class="card-hd">
        <span class="card-title">
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
            style="vertical-align:-2px;margin-right:6px;">
            <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
          </svg>
          Select Report Type
        </span>
        <span class="card-tag" id="selectedTypeTag">None selected</span>
      </div>
      <div class="card-bd">
        <div class="rt-grid">
          {type_cards}
        </div>
      </div>
    </div>

    <!-- Options -->
    <div class="card" style="animation:fadeUp 0.3s ease 0.07s both;">
      <div class="card-hd"><span class="card-title">Report Options</span></div>
      <div class="card-bd">
        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">Format</label>
            <select class="form-ctrl" id="reportFormat">
              <option value="html">HTML — View in browser</option>
              <option value="pdf">PDF — Download</option>
              <option value="text">Plain Text — Download</option>
              <option value="json">JSON — Download</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Department Filter</label>
            <select class="form-ctrl" id="departmentFilter">
              <option value="">All Departments</option>
              <option value="Engineering">Engineering</option>
              <option value="Marketing">Marketing</option>
              <option value="Sales">Sales</option>
              <option value="HR">Human Resources</option>
              <option value="Finance">Finance</option>
              <option value="Operations">Operations</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Start Date</label>
            <input class="form-ctrl" type="date" id="startDate" value="{thirty_ago}">
          </div>
          <div class="form-group">
            <label class="form-label">End Date</label>
            <input class="form-ctrl" type="date" id="endDate" value="{today}">
          </div>
        </div>
        <div style="display:flex;gap:12px;align-items:center;margin-top:18px;padding-top:18px;border-top:1px solid var(--border);">
          <label style="display:flex;align-items:center;gap:7px;font-size:13px;color:var(--ink2);cursor:pointer;">
            <input type="checkbox" id="includeCharts" style="width:15px;height:15px;accent-color:var(--blue);">
            Include charts
          </label>
          <label style="display:flex;align-items:center;gap:7px;font-size:13px;color:var(--ink2);cursor:pointer;">
            <input type="checkbox" id="emailReport" style="width:15px;height:15px;accent-color:var(--blue);">
            Email to me
          </label>
        </div>
        <div style="display:flex;gap:10px;margin-top:18px;flex-wrap:wrap;">
          <button class="btn btn-primary" onclick="generateReport()">
            <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            <span id="genBtnLabel">Generate Report</span>
          </button>
          <button class="btn btn-outline" onclick="previewReport()">
            <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
            </svg>
            Preview
          </button>
          <button class="btn btn-outline" onclick="openScheduleModal()">
            <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            Schedule
          </button>
        </div>
      </div>
    </div>

    <!-- Recent reports -->
    <div class="card" style="animation:fadeUp 0.3s ease 0.14s both;">
      <div class="card-hd">
        <span class="card-title">Recent Reports</span>
        <button class="btn btn-outline" style="padding:5px 12px;font-size:12px;" onclick="loadRecentReports()">
          <svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.94"/>
          </svg>
          Refresh
        </button>
      </div>
      <div id="recentReports" style="padding:20px 22px;">
        <div style="text-align:center;padding:32px;color:var(--ink3);">
          <div class="spin" style="margin:0 auto 10px;"></div>
          <div style="font-size:13px;">Loading recent reports…</div>
        </div>
      </div>
    </div>

  </div>

  <!-- RIGHT: Scheduled reports + quick stats -->
  <div style="display:flex;flex-direction:column;gap:16px;">

    <!-- Scheduled reports -->
    <div class="card" style="animation:fadeUp 0.3s ease 0.08s both;">
      <div class="card-hd"><span class="card-title">Scheduled</span></div>
      <div id="scheduledReports" style="padding:16px 18px;">
        <div style="text-align:center;padding:24px;color:var(--ink3);">
          <div class="spin" style="margin:0 auto 8px;"></div>
          <div style="font-size:12.5px;">Loading…</div>
        </div>
      </div>
    </div>

    <!-- Quick report tiles -->
    <div class="card" style="animation:fadeUp 0.3s ease 0.14s both;">
      <div class="card-hd"><span class="card-title">Quick Generate</span></div>
      <div class="card-bd" style="display:flex;flex-direction:column;gap:8px;">
        {_quick_btn("applications",    "📋", "Applications Report")}
        {_quick_btn("interviews",      "📅", "Interviews Report")}
        {_quick_btn("comprehensive",   "📊", "Full Comprehensive")}
        {_quick_btn("hiring_pipeline", "🔄", "Pipeline Report")}
      </div>
    </div>

  </div>
</div>

<!-- ══ REPORT OUTPUT (injected here) ══ -->
<div id="reportOutput" style="margin-top:20px;"></div>

<!-- ══ PREVIEW MODAL ══ -->
<div id="previewModal" style="display:none;position:fixed;inset:0;background:rgba(13,14,26,0.55);
     z-index:10000;align-items:center;justify-content:center;backdrop-filter:blur(6px);">
  <div style="background:var(--white);border-radius:16px;padding:32px;max-width:700px;width:90%;
              max-height:86vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.2);position:relative;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
      <span style="font-family:'Sora',sans-serif;font-weight:700;font-size:16px;color:var(--ink);">📊 Report Preview</span>
      <button onclick="closePreview()" style="background:var(--bg);border:1px solid var(--border);
              border-radius:8px;width:32px;height:32px;cursor:pointer;font-size:16px;color:var(--ink2);">✕</button>
    </div>
    <div id="previewContent"></div>
  </div>
</div>

<!-- ══ SCHEDULE MODAL ══ -->
<div id="scheduleModal" style="display:none;position:fixed;inset:0;background:rgba(13,14,26,0.55);
     z-index:10000;align-items:center;justify-content:center;backdrop-filter:blur(6px);">
  <div style="background:var(--white);border-radius:16px;padding:32px;max-width:500px;width:90%;
              box-shadow:0 20px 60px rgba(0,0,0,0.2);position:relative;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:22px;">
      <span style="font-family:'Sora',sans-serif;font-weight:700;font-size:16px;color:var(--ink);">📅 Schedule Report</span>
      <button onclick="closeScheduleModal()" style="background:var(--bg);border:1px solid var(--border);
              border-radius:8px;width:32px;height:32px;cursor:pointer;font-size:16px;color:var(--ink2);">✕</button>
    </div>
    <div class="form-grid">
      <div class="form-group full"><label class="form-label">Report Name *</label>
        <input class="form-ctrl" type="text" id="scheduleName" placeholder="e.g. Weekly Applications"></div>
      <div class="form-group"><label class="form-label">Frequency *</label>
        <select class="form-ctrl" id="scheduleFreq">
          <option value="daily">Daily</option>
          <option value="weekly" selected>Weekly</option>
          <option value="monthly">Monthly</option>
          <option value="quarterly">Quarterly</option>
        </select></div>
      <div class="form-group"><label class="form-label">Recipients</label>
        <input class="form-ctrl" type="text" id="scheduleEmails" placeholder="email1@company.com"></div>
    </div>
    <div class="form-actions">
      <button class="btn btn-primary" onclick="submitSchedule()">Schedule Report</button>
      <button class="btn btn-outline" onclick="closeScheduleModal()">Cancel</button>
    </div>
  </div>
</div>

<style>
/* ── Report type grid ── */
.rt-grid {{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px;
}}
.rt-card {{
  display:flex;flex-direction:column;align-items:flex-start;
  padding:14px 16px;border-radius:11px;
  border:1.5px solid var(--border);background:var(--white);
  cursor:pointer;transition:all 0.15s;
}}
.rt-card:hover {{ border-color:var(--blue);background:var(--blue-lt); }}
.rt-card:has(input:checked) {{
  border-color:var(--blue);background:var(--blue-lt);
  box-shadow:0 0 0 3px rgba(59,111,232,0.12);
}}
.rt-icon {{ font-size:22px;margin-bottom:7px; }}
.rt-label {{ font-family:'Sora',sans-serif;font-size:13px;font-weight:700;color:var(--ink);margin-bottom:3px; }}
.rt-desc  {{ font-size:11.5px;color:var(--ink3);line-height:1.4; }}

/* spinner */
.spin {{
  width:20px;height:20px;border-radius:50%;
  border:2.5px solid var(--border);border-top-color:var(--blue);
  animation:spinA 0.7s linear infinite;
}}
@keyframes spinA {{to{{transform:rotate(360deg);}}}}

/* quick btn */
.qr-btn {{
  display:flex;align-items:center;gap:9px;
  padding:10px 13px;border-radius:9px;
  border:1.5px solid var(--border);background:var(--white);
  cursor:pointer;font-family:'DM Sans',sans-serif;
  font-size:13px;font-weight:600;color:var(--ink2);
  transition:all 0.13s;text-align:left;width:100%;
}}
.qr-btn:hover {{border-color:var(--blue);background:var(--blue-lt);color:var(--blue);}}
.qr-icon {{font-size:16px;flex-shrink:0;}}

/* recent report rows */
.rpt-row {{
  display:flex;align-items:center;gap:12px;
  padding:13px 0;border-bottom:1px solid var(--border);
}}
.rpt-row:last-child {{border-bottom:none;}}
.rpt-icon {{
  width:36px;height:36px;border-radius:9px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;font-size:16px;
}}
.rpt-meta {{flex:1;min-width:0;}}
.rpt-name {{font-size:13.5px;font-weight:700;color:var(--ink);margin-bottom:2px;}}
.rpt-date {{font-size:11.5px;color:var(--ink3);}}

/* scheduled row */
.sch-row {{
  padding:12px 14px;border-radius:9px;border:1.5px solid var(--border);
  margin-bottom:8px;transition:border-color 0.15s;
}}
.sch-row:hover {{border-color:rgba(59,111,232,0.25);}}
.sch-name {{font-size:13px;font-weight:700;color:var(--ink);margin-bottom:3px;}}
.sch-meta {{font-size:11.5px;color:var(--ink3);}}
</style>

<script>
// ── TYPE SELECTION ─────────────────────────────────────
let selectedType = '';
function selectReportType(radio) {{
  selectedType = radio.value;
  const labels = {{{', '.join([f'"{v}":"{l}"' for v, _, l, _ in REPORT_TYPES])}}};
  document.getElementById('selectedTypeTag').textContent = labels[selectedType] || selectedType;
}}

// ── QUICK GENERATE ────────────────────────────────────
function quickGenerate(type) {{
  selectedType = type;
  document.querySelectorAll('input[name="report_type"]').forEach(r => r.checked = r.value===type);
  const labels = {{{', '.join([f'"{v}":"{l}"' for v, _, l, _ in REPORT_TYPES])}}};
  document.getElementById('selectedTypeTag').textContent = labels[type]||type;
  generateReport();
}}

// ── GENERATE ──────────────────────────────────────────
function generateReport() {{
  if (!selectedType) {{
    showToast('Select Type','Please select a report type first.','warning'); return;
  }}
  const btn = document.getElementById('genBtnLabel');
  btn.textContent = 'Generating…';

  const data = {{
    report_type:       selectedType,
    report_format:     document.getElementById('reportFormat').value,
    start_date:        document.getElementById('startDate').value,
    end_date:          document.getElementById('endDate').value,
    department_filter: document.getElementById('departmentFilter').value,
    include_charts:    document.getElementById('includeCharts').checked ? 'on' : '',
    email_report:      document.getElementById('emailReport').checked ? 'on' : '',
  }};

  const out = document.getElementById('reportOutput');
  out.innerHTML = `<div class="card"><div class="card-bd" style="text-align:center;padding:40px;">
    <div class="spin" style="margin:0 auto 12px;width:28px;height:28px;border-width:3px;"></div>
    <div style="font-family:'Sora',sans-serif;font-size:14px;color:var(--ink2);">Generating ${{selectedType}} report…</div>
  </div></div>`;
  out.scrollIntoView({{behavior:'smooth',block:'nearest'}});

  fetch('/api/generate-report', {{
    method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(data)
  }})
  .then(r => r.json())
  .then(d => {{
    btn.textContent = 'Generate Report';
    if (d.success) {{
      showToast('Report Ready','Your report has been generated.','success');
      if (data.report_format === 'html') {{
        out.innerHTML = `<div class="card">
          <div class="card-hd">
            <span class="card-title">📊 ${{d.report_type ? d.report_type.replace(/_/g,' ').replace(/\\b\\w/g,c=>c.toUpperCase()) : 'Report'}}</span>
            <div style="display:flex;gap:8px;">
              <button class="btn btn-outline" style="padding:5px 12px;font-size:12px;"
                onclick="window.open('/view-report/${{d.report_id}}','_blank')">👁 Open Full View</button>
              <button class="btn btn-outline" style="padding:5px 12px;font-size:12px;"
                onclick="window.open('/download-report/${{d.report_id}}','_blank')">📥 Download</button>
            </div>
          </div>
          <div class="card-bd">
            <div style="background:var(--bg);border-radius:10px;padding:20px;font-family:'Courier New',monospace;
                        font-size:12.5px;line-height:1.65;color:var(--ink2);max-height:380px;overflow-y:auto;
                        white-space:pre-wrap;border:1px solid var(--border);">${{escHtml(d.preview||'')}}</div>
          </div>
        </div>`;
      }} else {{
        const link = document.createElement('a');
        link.href     = d.download_url;
        link.download = d.filename;
        link.click();
        out.innerHTML = `<div class="card"><div class="card-bd" style="text-align:center;padding:32px;color:var(--green);">
          <div style="font-size:32px;margin-bottom:8px;">✅</div>
          <div style="font-family:'Sora',sans-serif;font-weight:700;">Download started</div>
          <div style="font-size:12.5px;color:var(--ink3);margin-top:4px;">${{d.filename}}</div>
        </div></div>`;
      }}
      loadRecentReports();
      if (data.email_report) showToast('Emailed','Report sent to your email.','info');
    }} else {{
      out.innerHTML = `<div class="card"><div class="card-bd" style="text-align:center;padding:32px;color:var(--red);">
        <div style="font-size:28px;margin-bottom:8px;">⚠️</div>
        <div style="font-family:'Sora',sans-serif;font-weight:700;">Generation failed</div>
        <div style="font-size:12.5px;color:var(--ink3);margin-top:4px;">${{escHtml(d.error||'Unknown error')}}</div>
        <button class="btn btn-outline" style="margin-top:16px;" onclick="generateReport()">Try Again</button>
      </div></div>`;
      showToast('Error', d.error||'Failed.', 'error');
    }}
  }})
  .catch(err => {{
    btn.textContent = 'Generate Report';
    out.innerHTML = '';
    showToast('Network Error', err.message, 'error');
  }});
}}

// ── PREVIEW ───────────────────────────────────────────
const PREVIEWS = {{
  applications: {{stats:[['Total Applications','156'],['Screened','142'],['Interviewed','48'],['Hired','12']],
    desc:'Detailed application metrics, conversion rates, and trend analysis.'}},
  interviews:   {{stats:[['Total Interviews','67'],['Completed','59'],['Pending','8'],['Avg Score','7.2/10']],
    desc:'Interview scheduling, completion rates, and evaluation scores.'}},
  comprehensive:{{stats:[['Applications','156'],['Interviews','67'],['Offers','18'],['Hired','12']],
    desc:'All HR metrics across the full recruitment pipeline.'}},
  offers:       {{stats:[['Total Offers','24'],['Pending','6'],['Accepted','15'],['Rejected','3']],
    desc:'Offer pipeline breakdown with acceptance and rejection rates.'}},
}};

function previewReport() {{
  if (!selectedType) {{ showToast('Select Type','Select a report type first.','warning'); return; }}
  const p = PREVIEWS[selectedType] || {{stats:[['N/A','—']], desc:'Preview not available.'}};
  const statsHtml = p.stats.map(([l,v]) =>
    `<div style="background:var(--white);padding:14px;border-radius:10px;text-align:center;border:1px solid var(--border);">
      <div style="font-family:'Sora',sans-serif;font-size:24px;font-weight:800;color:var(--ink);">${{v}}</div>
      <div style="font-size:11.5px;color:var(--ink3);margin-top:3px;">${{l}}</div>
    </div>`).join('');
  document.getElementById('previewContent').innerHTML = `
    <div style="background:var(--bg);border-radius:12px;padding:20px;margin-bottom:16px;">
      <div style="font-family:'Sora',sans-serif;font-weight:700;font-size:14px;color:var(--ink);margin-bottom:4px;">
        ${{selectedType.replace(/_/g,' ').replace(/\\b\\w/g,c=>c.toUpperCase())}} — Preview
      </div>
      <div style="font-size:12.5px;color:var(--ink3);">Period: ${{document.getElementById('startDate').value}} → ${{document.getElementById('endDate').value}}</div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-bottom:16px;">${{statsHtml}}</div>
    <div style="font-size:13px;color:var(--ink2);line-height:1.6;">${{p.desc}}</div>`;
  document.getElementById('previewModal').style.display = 'flex';
}}
function closePreview() {{ document.getElementById('previewModal').style.display = 'none'; }}

// ── SCHEDULE ──────────────────────────────────────────
function openScheduleModal() {{
  if (!selectedType) {{ showToast('Select Type','Select a report type first.','warning'); return; }}
  document.getElementById('scheduleModal').style.display = 'flex';
}}
function closeScheduleModal() {{ document.getElementById('scheduleModal').style.display = 'none'; }}

function submitSchedule() {{
  const name = document.getElementById('scheduleName').value;
  if (!name) {{ showToast('Validation','Report name is required.','warning'); return; }}
  const data = {{
    report_type:       selectedType,
    schedule_name:     name,
    frequency:         document.getElementById('scheduleFreq').value,
    email_recipients:  document.getElementById('scheduleEmails').value,
  }};
  fetch('/api/schedule-report', {{
    method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)
  }})
  .then(r => r.json())
  .then(d => {{
    if (d.success) {{
      showToast('Scheduled','Report will run automatically.','success');
      closeScheduleModal();
      loadScheduledReports();
    }} else showToast('Error', d.error||'Failed.','error');
  }})
  .catch(() => showToast('Error','Network error.','error'));
}}

// ── LOAD LISTS ────────────────────────────────────────
function loadRecentReports() {{
  const div = document.getElementById('recentReports');
  div.innerHTML = '<div style="text-align:center;padding:28px;"><div class="spin" style="margin:0 auto;"></div></div>';
  fetch('/api/recent-reports')
    .then(r => r.json())
    .then(d => {{
      if (!d.success || !d.reports.length) {{
        div.innerHTML = `<div style="text-align:center;padding:32px;color:var(--ink3);">
          <div style="font-size:32px;margin-bottom:8px;">🗒️</div>
          <div style="font-size:13px;">No reports generated yet.</div></div>`;
        return;
      }}
      const typeIcons = {{{', '.join([f'"{v}":"{i}"' for v,i,_,_ in REPORT_TYPES])}}};
      div.innerHTML = d.reports.map(r => {{
        const icon = typeIcons[r.report_type] || '📄';
        const label = (r.report_type||'').replace(/_/g,' ').replace(/\\b\\w/g,c=>c.toUpperCase());
        return `<div class="rpt-row">
          <div class="rpt-icon" style="background:var(--blue-lt);">${{icon}}</div>
          <div class="rpt-meta">
            <div class="rpt-name">${{label}}</div>
            <div class="rpt-date">${{r.generated_date||'—'}} · ${{r.format||'html'}}</div>
          </div>
          <div style="display:flex;gap:5px;">
            <button class="btn btn-outline btn-sm" onclick="window.open('/view-report/${{r.id}}','_blank')">View</button>
            <button class="btn btn-outline btn-sm" onclick="window.open('/download-report/${{r.id}}','_blank')">📥</button>
          </div>
        </div>`;
      }}).join('');
    }})
    .catch(() => {{
      div.innerHTML = '<div style="text-align:center;padding:24px;color:var(--red);font-size:13px;">Error loading reports.</div>';
    }});
}}

function loadScheduledReports() {{
  const div = document.getElementById('scheduledReports');
  div.innerHTML = '<div style="text-align:center;padding:24px;"><div class="spin" style="margin:0 auto;"></div></div>';
  fetch('/api/scheduled-reports')
    .then(r => r.json())
    .then(d => {{
      if (!d.success || !d.scheduled_reports.length) {{
        div.innerHTML = `<div style="text-align:center;padding:24px;color:var(--ink3);">
          <div style="font-size:11.5px;">No scheduled reports.<br>Use "Schedule" to automate.</div></div>`;
        return;
      }}
      div.innerHTML = '<div style="padding:14px 18px;">' + d.scheduled_reports.map(r =>
        `<div class="sch-row">
          <div class="sch-name">${{escHtml(r.name||'—')}}</div>
          <div class="sch-meta">${{(r.report_type||'').replace(/_/g,' ')}} · ${{r.frequency||'—'}}</div>
          <div style="display:flex;gap:5px;margin-top:8px;">
            <button class="btn btn-danger btn-sm" onclick="deleteSchedule(${{r.id}})">Delete</button>
          </div>
        </div>`).join('') + '</div>';
    }})
    .catch(() => {{
      div.innerHTML = '<div style="padding:16px;color:var(--red);font-size:13px;">Error loading.</div>';
    }});
}}

function deleteSchedule(id) {{
  if (!confirm('Delete this scheduled report?')) return;
  fetch('/api/delete-scheduled-report', {{
    method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{schedule_id:id}})
  }})
  .then(r => r.json())
  .then(d => {{
    if (d.success) {{ showToast('Deleted','Schedule removed.','warning'); loadScheduledReports(); }}
    else showToast('Error', d.error||'Failed.','error');
  }})
  .catch(() => showToast('Error','Network error.','error'));
}}

// ── UTILS ──────────────────────────────────────────────
function escHtml(s) {{
  if(!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
          .replace(/"/g,'&quot;').replace(/\'/g,'&#39;');
}}

// close on backdrop
['previewModal','scheduleModal'].forEach(id => {{
  document.getElementById(id).addEventListener('click', function(e) {{
    if (e.target===this) this.style.display='none';
  }});
}});

window.addEventListener('load', () => {{
  loadRecentReports();
  loadScheduledReports();
}});
</script>
"""
    return HTMLResponse(content=get_base_html("Reports", "reports", current_user) + page + get_end_html())


def _quick_btn(val: str, icon: str, label: str) -> str:
    return f"""<button class="qr-btn" onclick="quickGenerate('{val}')">
  <span class="qr-icon">{icon}</span>{label}
  <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
    style="margin-left:auto;color:var(--ink3);"><polyline points="9 18 15 12 9 6"/></svg>
</button>"""


# ─────────────────────────────────────────────────────────────────────────────
# PDF REPORT GENERATOR — redesigned, all other logic unchanged
# ─────────────────────────────────────────────────────────────────────────────
def _generate_pdf_report(report: dict) -> bytes:
    """
    Generate a polished, branded PDF report using ReportLab.

    Design:
      • Blue→violet gradient header strip with TF logo mark and wordmark
      • Title block + horizontal rule
      • 4-column metadata row (Generated, By, Period, Department)
      • KPI tile row (4 side-by-side boxes in surface colour)
      • Score-distribution table (if available)
      • Hiring-pipeline table (if available)
      • Recursive full-data section with indented key→value rendering
      • Confidentiality footer paragraph
      • Consistent header + footer on every page
    """
    from reportlab.platypus import HRFlowable
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.lib import colors

    # ── palette ──────────────────────────────────────────────────────────────
    BLUE      = colors.HexColor("#1a3cff")
    VIOLET    = colors.HexColor("#7c3aff")
    INK       = colors.HexColor("#0d0e1a")
    INK_SOFT  = colors.HexColor("#2a2b3d")
    INK_MUTED = colors.HexColor("#6b6c80")
    SURFACE   = colors.HexColor("#f1f0ff")
    BORDER    = colors.HexColor("#e4e3f5")
    WHITE     = colors.white

    # ── style factory (unique names to avoid stylesheet key conflicts) ────────
    def S(name, base="Normal", **kw):
        return ParagraphStyle(name=f"_rpt_{name}_{id(report)}", parent=getSampleStyleSheet()[base], **kw)

    styles = {
        "title":   S("title",   "Title",
                     fontName="Helvetica-Bold", fontSize=22, textColor=INK, leading=28, spaceAfter=4),
        "sub":     S("sub",     "Normal",
                     fontName="Helvetica", fontSize=11, textColor=INK_MUTED, leading=16, spaceAfter=2),
        "sec":     S("sec",     "Normal",
                     fontName="Helvetica-Bold", fontSize=13, textColor=INK, leading=18, spaceBefore=20, spaceAfter=8),
        "mk":      S("mk",      "Normal",
                     fontName="Helvetica-Bold", fontSize=8.5, textColor=INK_MUTED, leading=13),
        "mv":      S("mv",      "Normal",
                     fontName="Helvetica", fontSize=10, textColor=INK_SOFT, leading=14, spaceAfter=6),
        "body":    S("body",    "Normal",
                     fontName="Helvetica", fontSize=10, textColor=INK_SOFT, leading=15, spaceAfter=5),
        "code":    S("code",    "Normal",
                     fontName="Courier", fontSize=8.5, textColor=INK_SOFT, leading=13, leftIndent=8),
        "th":      S("th",      "Normal",
                     fontName="Helvetica-Bold", fontSize=9, textColor=WHITE, leading=13),
        "td":      S("td",      "Normal",
                     fontName="Helvetica", fontSize=9, textColor=INK_SOFT, leading=13),
        "foot":    S("foot",    "Normal",
                     fontName="Helvetica-Oblique", fontSize=8.5, textColor=INK_MUTED, leading=12, spaceAfter=2),
    }

    # ── page callbacks ────────────────────────────────────────────────────────
    def _draw_page(c, doc):
        w, h = letter
        # gradient header
        steps = 40
        for i in range(steps):
            t  = i / (steps - 1)
            r_ = BLUE.red   + t * (VIOLET.red   - BLUE.red)
            g_ = BLUE.green + t * (VIOLET.green - BLUE.green)
            b_ = BLUE.blue  + t * (VIOLET.blue  - BLUE.blue)
            c.setFillColorRGB(r_, g_, b_)
            c.rect(i * (w / steps), h - 88, w / steps + 1, 88, fill=1, stroke=0)
        # logo mark
        c.setFillColor(WHITE)
        c.roundRect(40, h - 68, 36, 36, 6, fill=1, stroke=0)
        c.setFillColor(BLUE)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(58, h - 54, "TF")
        # wordmark
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 15)
        c.drawString(84, h - 49, "TalentFlow Pro")
        c.setFont("Helvetica", 8.5)
        c.drawString(84, h - 62, "ZIBITECH HR Intelligence Platform")
        # right badge
        c.setFillColorRGB(1, 1, 1, 0.12)
        c.roundRect(w - 158, h - 66, 118, 22, 4, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(w - 99, h - 58, "OFFICIAL HR REPORT")
        # footer
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.5)
        c.line(40, 34, w - 40, 34)
        c.setFillColor(INK_MUTED)
        c.setFont("Helvetica", 7.5)
        c.drawString(40, 20, "TalentFlow Pro  \u2014  ZIBITECH HR Intelligence")
        c.drawRightString(w - 40, 20, f"Page {doc.page}  \u00b7  Confidential")

    # ── helper: KPI tile row ──────────────────────────────────────────────────
    def _kpi_row(kpis):
        w = letter[0]
        n  = len(kpis)
        cw = (w - 80) / n
        row = []
        for lbl, val, sub in kpis:
            row.append(Paragraph(
                f"<b><font size='20' color='#0d0e1a'>{val}</font></b><br/>"
                f"<font size='8.5' color='#6b6c80'>{lbl}</font><br/>"
                f"<font size='7.5' color='#6b6c80'>{sub}</font>",
                styles["body"]))
        t = Table([row], colWidths=[cw] * n, rowHeights=[64])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), SURFACE),
            ("LINEAFTER",     (0, 0), (-2, -1), 0.5, BORDER),
            ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 16),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LEFTPADDING",   (0, 0), (-1, -1), 18),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return t

    # ── helper: data table ────────────────────────────────────────────────────
    def _tbl(headers, rows, col_widths=None):
        w   = letter[0]
        cw  = col_widths or [(w - 80) / len(headers)] * len(headers)
        hr  = [Paragraph(h, styles["th"]) for h in headers]
        br  = [[Paragraph(str(c), styles["td"]) for c in r] for r in rows]
        t   = Table([hr] + br, colWidths=cw, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  BLUE),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0),  9),
            ("TOPPADDING",    (0, 0), (-1, 0),  9),
            ("BOTTOMPADDING", (0, 0), (-1, 0),  9),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("BACKGROUND",    (0, 1), (-1, -1), WHITE),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, SURFACE]),
            ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 1), (-1, -1), 9),
            ("TOPPADDING",    (0, 1), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
            ("TEXTCOLOR",     (0, 1), (-1, -1), INK_SOFT),
            ("LINEBELOW",     (0, 0), (-1, -2), 0.4, BORDER),
            ("LINEBELOW",     (0, -1),(-1, -1), 0.4, BORDER),
            ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return t

    # ── build document ────────────────────────────────────────────────────────
    try:
        buffer = BytesIO()
        w, h   = letter

        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            leftMargin=40, rightMargin=40,
            topMargin=108, bottomMargin=54,
            title=f"HR Report — {report.get('report_type','').replace('_',' ').title()}",
            author="TalentFlow Pro",
            subject="HR Intelligence Report",
        )

        story = []

        # title block
        rtype = report.get("report_type", "report").replace("_", " ").title()
        story.append(Spacer(1, 10))
        story.append(Paragraph(rtype, styles["title"]))
        story.append(Paragraph("Human Resources Intelligence Report", styles["sub"]))
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=14))

        # meta row
        gen_date = report.get("generated_date") or datetime.now().strftime("%Y-%m-%d %H:%M")
        gen_by   = report.get("generated_by", "HR Administrator")
        start    = report.get("start_date", "\u2014")
        end      = report.get("end_date",   "\u2014")
        dept     = report.get("department_filter") or "All Departments"
        cw4      = (w - 80) / 4

        meta = Table([
            [Paragraph("<b>Generated</b>",  styles["mk"]),
             Paragraph("<b>Prepared By</b>",styles["mk"]),
             Paragraph("<b>Period</b>",     styles["mk"]),
             Paragraph("<b>Department</b>", styles["mk"])],
            [Paragraph(gen_date, styles["mv"]),
             Paragraph(gen_by,   styles["mv"]),
             Paragraph(f"{start} \u2192 {end}", styles["mv"]),
             Paragraph(dept,     styles["mv"])],
        ], colWidths=[cw4] * 4)
        meta.setStyle(TableStyle([
            ("LEFTPADDING",  (0,0),(-1,-1), 0),
            ("RIGHTPADDING", (0,0),(-1,-1), 12),
            ("TOPPADDING",   (0,0),(-1,-1), 1),
            ("BOTTOMPADDING",(0,0),(-1,-1), 1),
            ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ]))
        story.append(meta)
        story.append(Spacer(1, 20))

        # KPI tiles
        rdata     = report.get("report_data", {}) or {}
        stats_raw = rdata.get("statistics", {}) or {}
        kpis = [
            ("Total Applications",  str(rdata.get("total_applications") or rdata.get("applications") or "\u2014"), "All records"),
            ("Avg Resume Score",    str(stats_raw.get("average_score", "\u2014")),     "Out of 100"),
            ("Resumes Scored",      str(stats_raw.get("scored_applicants", "\u2014")), "Analysed"),
            ("Total Applicants",    str(stats_raw.get("total_applicants", "\u2014")),  "In system"),
        ]
        story.append(Paragraph("Key Metrics", styles["sec"]))
        story.append(_kpi_row(kpis))
        story.append(Spacer(1, 20))

        # Score distribution
        dist = stats_raw.get("score_distribution", {})
        if dist:
            story.append(Paragraph("Score Distribution", styles["sec"]))
            total_d = sum(dist.values()) or 1
            rows    = [[k, str(v), f"{v / total_d * 100:.1f}%"] for k, v in dist.items()]
            story.append(_tbl(
                ["Category", "Count", "Share of Total"], rows,
                [(w-80)*0.40, (w-80)*0.30, (w-80)*0.30]))
            story.append(Spacer(1, 20))

        # Hiring pipeline
        pipeline = rdata.get("hiring_pipeline", {})
        if pipeline:
            story.append(Paragraph("Hiring Pipeline", styles["sec"]))
            p_rows = [[k.replace("_", " ").title(), str(v)] for k, v in pipeline.items()]
            story.append(_tbl(
                ["Stage", "Count"], p_rows,
                [(w-80)*0.60, (w-80)*0.40]))
            story.append(Spacer(1, 20))

        # Full data dump
        story.append(Paragraph("Full Report Data", styles["sec"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=10))

        def _render(d, depth=0):
            pad = "&nbsp;" * (depth * 6)
            for k, v in d.items():
                label = str(k).replace("_", " ").title()
                if isinstance(v, dict):
                    story.append(Paragraph(f"{pad}<b>{label}</b>", styles["body"]))
                    _render(v, depth + 1)
                elif isinstance(v, list):
                    story.append(Paragraph(f"{pad}<b>{label}:</b> [{len(v)} items]", styles["body"]))
                    for item in v[:6]:
                        story.append(Paragraph(f"{pad}&nbsp;&nbsp;&nbsp;\u2022 {str(item)[:120]}", styles["code"]))
                    if len(v) > 6:
                        story.append(Paragraph(f"{pad}&nbsp;&nbsp;&nbsp;<i>\u2026{len(v)-6} more</i>", styles["foot"]))
                else:
                    story.append(Paragraph(f"{pad}<b>{label}:</b> {str(v)[:200]}", styles["body"]))

        if rdata:
            _render(rdata)
        else:
            story.append(Paragraph("No structured data available for this report.", styles["foot"]))

        # Confidentiality notice
        story.append(Spacer(1, 28))
        story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=10))
        story.append(Paragraph(
            "This document is strictly confidential and intended solely for authorised HR personnel. "
            "Unauthorised distribution or reproduction is prohibited. "
            f"Generated by TalentFlow Pro on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}.",
            styles["foot"]
        ))

        doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    except Exception as e:
        print(f"PDF generation error: {e}")
        # graceful text fallback
        text_content = (
            f"HR Report - {report.get('report_type','').title()}\n"
            f"Generated: {report.get('generated_date', 'Unknown')}\n"
            f"By: {report.get('generated_by', 'Unknown')}\n"
            f"Period: {report.get('start_date', 'All time')} \u2192 {report.get('end_date', 'Present')}\n\n"
        ) + json.dumps(report.get("report_data", {}), indent=2)
        return text_content.encode("utf-8")


# ── BACKEND ROUTES (100% UNCHANGED) ──────────────────────────────────────────

@app.post("/api/generate-report")
async def generate_report(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        if not data.get('report_type'):
            return JSONResponse(content={"success": False, "error": "Report type required"}, status_code=400)
        report_data = _generate_report_data(data['report_type'], data)
        report_id = db.save_report(
            report_type=data['report_type'], report_data=report_data,
            format=data.get('report_format', 'html'), generated_by=current_user,
            start_date=data.get('start_date'), end_date=data.get('end_date'),
            department_filter=data.get('department_filter'))
        if data.get('email_report'):
            send_email(current_user,
                f"HR Report - {data['report_type'].replace('_', ' ').title()}",
                f"<h2>HR Report Generated</h2><p>Type: {data['report_type']}</p><p>Generated: {datetime.now()}</p>",
                is_html=True)
        preview = _report_preview_text(data['report_type'], report_data)
        return JSONResponse(content={"success": True, "report_id": report_id, "report_type": data['report_type'],
            "report_url": f"/view-report/{report_id}", "download_url": f"/download-report/{report_id}",
            "preview": preview,
            "filename": f"hr_report_{data['report_type']}_{datetime.now().strftime('%Y%m%d')}.{'txt' if data.get('report_format')=='text' else 'json' if data.get('report_format')=='json' else 'html'}"})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


def _generate_report_data(report_type, params):
    applications = db.get_all_applications()
    statistics   = db.get_statistics()
    if report_type == "applications":
        return {"total_applications": len(applications), "by_status": {}, "statistics": statistics}
    elif report_type == "interviews":
        return {"total_interviews": 0, "by_type": {}, "completion_rates": {}}
    elif report_type == "comprehensive":
        return {"applications": len(applications), "statistics": statistics, "hiring_pipeline": {}}
    else:
        return {"message": f"Report: {report_type}", "generated": datetime.now().isoformat()}


def _report_preview_text(report_type: str, data: dict) -> str:
    lines = [f"REPORT: {report_type.upper().replace('_',' ')}", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    for k, v in data.items():
        if isinstance(v, dict):
            lines.append(f"{k}:")
            for kk, vv in v.items():
                lines.append(f"  {kk}: {vv}")
        else:
            lines.append(f"{k}: {v}")
    return "\n".join(lines)


@app.get("/view-report/{report_id}")
async def view_report(report_id: str, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        report = db.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        html = f"""<!DOCTYPE html><html><head><title>HR Report</title>
        <style>body{{font-family:'DM Sans',sans-serif;padding:2rem;background:#EEF2F7;}}
        .box{{background:#fff;border-radius:14px;padding:2rem;max-width:900px;margin:0 auto;
              box-shadow:0 2px 12px rgba(30,40,90,.07);}}
        h1{{font-family:'Sora',sans-serif;color:#1A1D2E;}}pre{{background:#f3f2ff;padding:16px;border-radius:9px;overflow-x:auto;font-size:13px;}}
        </style></head><body><div class="box">
        <h1>📊 {report['report_type'].replace('_',' ').title()}</h1>
        <p style="color:#8A8FA8;">Generated: {report.get('generated_date','—')} · By: {report.get('generated_by','—')}</p>
        <p>Period: {report.get('start_date','All time')} → {report.get('end_date','Present')}</p>
        <pre>{json.dumps(report.get('report_data',{}), indent=2)}</pre>
        </div></body></html>"""
        return HTMLResponse(content=html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download-report/{report_id}")
async def download_report(report_id: str, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        report = db.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Check format from query parameter or report data
        format_param = request.query_params.get("format", report.get('format', 'html')).lower()

        if format_param == 'json':
            content = json.dumps(report.get('report_data', {}), indent=2)
            filename = f"hr_report_{report['report_type']}_{report.get('generated_date','unknown')}.json"
            return PlainTextResponse(content=content, headers={"Content-Disposition": f"attachment; filename={filename}"})

        elif format_param == 'pdf':
            pdf_bytes = _generate_pdf_report(report)
            filename  = f"hr_report_{report['report_type']}_{report.get('generated_date','unknown')}.pdf"
            return StreamingResponse(
                BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        else:
            content  = f"HR Report - {report['report_type'].title()}\nGenerated: {report.get('generated_date','—')}\n\n"
            content += json.dumps(report.get('report_data', {}), indent=2)
            filename = f"hr_report_{report['report_type']}_{report.get('generated_date','unknown')}.txt"
            return PlainTextResponse(content=content, headers={"Content-Disposition": f"attachment; filename={filename}"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recent-reports")
async def get_recent_reports(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        reports = db.get_recent_reports(limit=10)
        return JSONResponse(content={"success": True, "reports": reports})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.get("/api/scheduled-reports")
async def get_scheduled_reports(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        scheduled = db.get_scheduled_reports()
        return JSONResponse(content={"success": True, "scheduled_reports": scheduled})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/schedule-report")
async def schedule_report(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        for f in ['report_type', 'schedule_name', 'frequency']:
            if not data.get(f):
                return JSONResponse(content={"success": False, "error": f"Missing: {f}"}, status_code=400)
        schedule_id = db.create_scheduled_report(
            name=data['schedule_name'], report_type=data['report_type'],
            frequency=data['frequency'], email_recipients=data.get('email_recipients',''),
            created_by=current_user)
        return JSONResponse(content={"success": True, "schedule_id": schedule_id})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/delete-scheduled-report")
async def delete_scheduled_report(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        if not data.get("schedule_id"):
            return JSONResponse(content={"success": False, "error": "Schedule ID required"}, status_code=400)
        db.delete_scheduled_report(data["schedule_id"])
        return JSONResponse(content={"success": True})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)