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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from io import BytesIO
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import base64

db = ResumeDatabase()

# ── Report type metadata ──────────────────────────────────────────────────────
# SVG icon strings for each report type (replaces emojis)
_SVG = {
    "applications":        '<svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="13" y2="16"/></svg>',
    "interviews":          '<svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/><circle cx="12" cy="15" r="2"/></svg>',
    "evaluations":         '<svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    "offers":              '<svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="12" y2="17"/></svg>',
    "comprehensive":       '<svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "hiring_pipeline":     '<svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>',
    "time_to_hire":        '<svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "source_effectiveness":'<svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
}

REPORT_TYPES = [
    ("applications",        _SVG["applications"],        "Applications",       "Full breakdown of all applicants, statuses, and sources."),
    ("interviews",          _SVG["interviews"],          "Interviews",         "Interview scheduling, completion rates, and scores."),
    ("evaluations",         _SVG["evaluations"],         "Evaluations",        "Candidate evaluation scores and recommendations."),
    ("offers",              _SVG["offers"],              "Offers",             "Offer pipeline: pending, sent, accepted, rejected."),
    ("comprehensive",       _SVG["comprehensive"],       "Comprehensive",      "All HR metrics across the full recruitment funnel."),
    ("hiring_pipeline",     _SVG["hiring_pipeline"],     "Hiring Pipeline",    "Stage-by-stage conversion and bottleneck analysis."),
    ("time_to_hire",        _SVG["time_to_hire"],        "Time to Hire",       "Average days from application to offer acceptance."),
    ("source_effectiveness",_SVG["source_effectiveness"],"Source Effectiveness","Which channels produce the most hired candidates."),
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
        {_quick_btn("applications",    _SVG["applications"],    "Applications Report")}
        {_quick_btn("interviews",      _SVG["interviews"],      "Interviews Report")}
        {_quick_btn("comprehensive",   _SVG["comprehensive"],   "Full Comprehensive")}
        {_quick_btn("hiring_pipeline", _SVG["hiring_pipeline"], "Pipeline Report")}
      </div>
    </div>

  </div>
</div>

<!-- ══ REPORT OUTPUT (injected here) ══ -->
<div id="reportOutput" style="margin-top:20px;"></div>

<!-- ══ UNIVERSAL CONFIRMATION MODAL ══ -->
<div id="confirmModal" style="display:none;position:fixed;inset:0;background:rgba(13,14,26,0.55);
     z-index:10000;align-items:center;justify-content:center;backdrop-filter:blur(6px);">
  <div style="background:var(--white);border-radius:16px;padding:32px;max-width:480px;width:90%;
              box-shadow:0 20px 60px rgba(0,0,0,0.2);position:relative;text-align:center;">
    <div id="confirmIcon" style="width:64px;height:64px;border-radius:50%;
                display:flex;align-items:center;justify-content:center;margin:0 auto 20px;">
    </div>
    <h3 id="confirmTitle" style="font-size:22px;font-weight:700;color:var(--ink);margin-bottom:12px;">Confirm Action</h3>
    <p id="confirmMessage" style="color:var(--ink2);line-height:1.6;margin-bottom:24px;">
      Are you sure you want to proceed with this action?
    </p>
    <div style="display:flex;gap:12px;justify-content:center;">
      <button class="btn btn-outline" onclick="closeConfirmModal()" style="min-width:100px;">Cancel</button>
      <button class="btn btn-primary" id="confirmBtn" onclick="confirmAction()" style="min-width:100px;">
        <span id="confirmBtnText">Confirm</span>
      </button>
    </div>
  </div>
</div>

<!-- ══ PREVIEW MODAL ══ -->
<div id="previewModal" style="display:none;position:fixed;inset:0;background:rgba(13,14,26,0.55);
     z-index:10000;align-items:center;justify-content:center;backdrop-filter:blur(6px);">
  <div style="background:var(--white);border-radius:16px;padding:32px;max-width:700px;width:90%;
              max-height:86vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.2);position:relative;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
      <span style="font-family:'Sora',sans-serif;font-weight:700;font-size:16px;color:var(--ink);display:flex;align-items:center;gap:8px;"><svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg> Report Preview</span>
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
      <span style="font-family:'Sora',sans-serif;font-weight:700;font-size:16px;color:var(--ink);display:flex;align-items:center;gap:8px;"><svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg> Schedule Report</span>
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
.rt-icon {{ width:32px;height:32px;margin-bottom:10px;display:flex;align-items:center;justify-content:center;background:var(--blue-lt);border-radius:8px;color:var(--blue); }}
.rt-icon svg {{ flex-shrink:0; }}
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
.qr-icon {{width:28px;height:28px;flex-shrink:0;display:flex;align-items:center;justify-content:center;background:var(--blue-lt);border-radius:7px;color:var(--blue);}}

/* recent report rows */
.rpt-row {{
  display:flex;align-items:center;gap:12px;
  padding:13px 0;border-bottom:1px solid var(--border);
}}
.rpt-row:last-child {{border-bottom:none;}}
.rpt-icon {{
  width:36px;height:36px;border-radius:9px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;color:var(--blue);
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
        let chartsHtml = '';
        if (d.charts) {{
          chartsHtml = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:18px;">';
          for (const [name, b64] of Object.entries(d.charts)) {{
            const style = name === 'volume_trend' ? 'grid-column:1/-1;' : '';
            chartsHtml += `<div class="card" style="${{style}};margin-bottom:0;"><div class="card-bd" style="padding:10px;"><img src="data:image/png;base64,${{b64}}" style="width:100%;border-radius:6px;display:block;"/></div></div>`;
          }}
          chartsHtml += '</div>';
        }}
        out.innerHTML = `<div class="card">
          <div class="card-hd">
            <span class="card-title" style="display:flex;align-items:center;gap:8px;"><svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg> ${{d.report_type ? d.report_type.replace(/_/g,' ').replace(/\\b\\w/g,c=>c.toUpperCase()) : 'Report'}}</span>
            <div style="display:flex;gap:8px;">
              <button class="btn btn-outline" style="padding:5px 12px;font-size:12px;"
                onclick="window.open('/view-report/${{d.report_id}}','_blank')"><svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="vertical-align:-1px;margin-right:3px;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>Open Full View</button>
              <button class="btn btn-outline" style="padding:5px 12px;font-size:12px;"
                onclick="window.open('/download-report/${{d.report_id}}','_blank')"><svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="vertical-align:-1px;margin-right:3px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>Download</button>
            </div>
          </div>
          <div class="card-bd">
            ${{chartsHtml}}
            <div style="font-family:'Sora',sans-serif;font-size:11px;font-weight:800;color:var(--ink3);text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px;">Data Summary</div>
            <div style="background:var(--bg);border-radius:10px;padding:20px;font-family:'Courier New',monospace;
                        font-size:12.5px;line-height:1.65;color:var(--ink2);max-height:300px;overflow-y:auto;
                        white-space:pre-wrap;border:1px solid var(--border);">${{escHtml(d.preview||'')}}</div>
          </div>
        </div>`;
      }} else {{
        const link = document.createElement('a');
        link.href     = d.download_url;
        link.download = d.filename;
        link.click();
        out.innerHTML = `<div class="card"><div class="card-bd" style="text-align:center;padding:32px;color:var(--green);">
          <div style="width:48px;height:48px;border-radius:50%;background:var(--green,#10b981);display:flex;align-items:center;justify-content:center;margin:0 auto 12px;"><svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="white" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg></div>
          <div style="font-family:'Sora',sans-serif;font-weight:700;">Download started</div>
          <div style="font-size:12.5px;color:var(--ink3);margin-top:4px;">${{d.filename}}</div>
        </div></div>`;
      }}
      loadRecentReports();
      if (data.email_report) showToast('Emailed','Report sent to your email.','info');
    }} else {{
      out.innerHTML = `<div class="card"><div class="card-bd" style="text-align:center;padding:32px;color:var(--red);">
        <div style="width:48px;height:48px;border-radius:50%;background:var(--d-bg,rgba(239,68,68,.08));display:flex;align-items:center;justify-content:center;margin:0 auto 12px;"><svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="var(--red,#ef4444)" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></div>
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
          <div style="width:44px;height:44px;border-radius:50%;background:var(--surface,#f1f0ff);display:flex;align-items:center;justify-content:center;margin:0 auto 10px;"><svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="12" y2="17"/></svg></div>
          <div style="font-size:13px;">No reports generated yet.</div></div>`;
        return;
      }}
      const typeIcons = {{
        applications:        '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="13" y2="16"/></svg>',
        interviews:          '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
        evaluations:         '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
        offers:              '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="13" x2="15" y2="13"/></svg>',
        comprehensive:       '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
        hiring_pipeline:     '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>',
        time_to_hire:        '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        source_effectiveness:'<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
      }};
      const defaultIcon = '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>';
      div.innerHTML = d.reports.map(r => {{
        const icon = typeIcons[r.report_type] || defaultIcon;
        const label = (r.report_type||'').replace(/_/g,' ').replace(/\\b\\w/g,c=>c.toUpperCase());
        return `<div class="rpt-row">
          <div class="rpt-icon" style="background:var(--blue-lt);">${{icon}}</div>
          <div class="rpt-meta">
            <div class="rpt-name">${{label}}</div>
            <div class="rpt-date">${{r.generated_date||'—'}} · ${{r.format||'html'}}</div>
          </div>
          <div style="display:flex;gap:5px;">
            <button class="btn btn-outline btn-sm" onclick="window.open('/view-report/${{r.id}}','_blank')">View</button>
            <button class="btn btn-outline btn-sm" title="Download" onclick="window.open('/download-report/${{r.id}}','_blank')"><svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg></button>
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

// ── UNIVERSAL CONFIRMATION SYSTEM ─────────────────────────
let currentConfirmCallback = null;

function showConfirmModal(options) {{
  const {{
    title = 'Confirm Action',
    message = 'Are you sure you want to proceed with this action?',
    icon = 'warning',
    confirmText = 'Confirm',
    confirmType = 'primary',
    onConfirm
  }} = options;
  
  // Set modal content
  document.getElementById('confirmTitle').textContent = title;
  document.getElementById('confirmMessage').textContent = message;
  document.getElementById('confirmBtnText').textContent = confirmText;
  
  // Set icon
  const iconEl = document.getElementById('confirmIcon');
  const btnEl = document.getElementById('confirmBtn');
  
  if (icon === 'danger') {{
    iconEl.style.background = 'linear-gradient(135deg,#f56565,#e53e3e)';
    iconEl.innerHTML = `<svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="white" stroke-width="2.5">
      <path d="M3 6h18M19 6v12a2 2 0 0 1-2 2v2H7a2 2 0 0 1-2 2v2m3 0h6l-3 3h6m0 0h6"/>
    </svg>`;
    btnEl.className = 'btn btn-danger';
  }} else if (icon === 'warning') {{
    iconEl.style.background = 'linear-gradient(135deg,#f6ad55,#ed8936)';
    iconEl.innerHTML = `<svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="white" stroke-width="2.5">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 1-2 2v2M1.82 18h16.36M19 18l-1.27 1.36A4 4 0 0 1-2 2v2m3 0h6l-3 3h6m0 0h6"/>
      <line x1="12" y1="9" x2="12" y2="13"/>
    </svg>`;
    btnEl.className = 'btn btn-warning';
  }} else {{
    iconEl.style.background = 'linear-gradient(135deg,#4299e1,#3182ce)';
    iconEl.innerHTML = `<svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="white" stroke-width="2.5">
      <path d="M13 16h-1v-4a2 2 0 0 1-2 2v2H7a2 2 0 0 1-2 2v2m3 0h6l-3 3h6m0 0h6"/>
    </svg>`;
    btnEl.className = 'btn btn-' + confirmType;
  }}
  
  // Store callback
  currentConfirmCallback = onConfirm;
  
  // Show modal
  document.getElementById('confirmModal').style.display = 'flex';
}}

function confirmAction() {{
  const btn = document.getElementById('confirmBtn');
  const btnText = document.getElementById('confirmBtnText');
  
  btn.disabled = true;
  btnText.textContent = 'Processing...';
  
  if (currentConfirmCallback) {{
    currentConfirmCallback();
  }}
}}

function closeConfirmModal() {{
  document.getElementById('confirmModal').style.display = 'none';
  currentConfirmCallback = null;
  
  // Reset button state
  const btn = document.getElementById('confirmBtn');
  const btnText = document.getElementById('confirmBtnText');
  btn.disabled = false;
  btnText.textContent = 'Confirm';
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


def _quick_btn(val: str, svg: str, label: str) -> str:
    return f"""<button class="qr-btn" onclick="quickGenerate('{val}')">
  <span class="qr-icon">{svg}</span>{label}
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
    from reportlab.lib.units import inch

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

        # Visual Charts
        charts = rdata.get("charts", {})
        if charts:
            story.append(Paragraph("Visual Analytics", styles["sec"]))
            # Group charts: status and score side-by-side
            row = []
            for ckey in ['status_dist', 'score_dist']:
                if ckey in charts:
                    try:
                        img_data = BytesIO(base64.b64decode(charts[ckey]))
                        img = Image(img_data, width=3.4*inch, height=2.4*inch)
                        row.append(img)
                    except: pass
            
            if row:
                t = Table([row], colWidths=[3.5*inch]*len(row))
                t.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
                story.append(t)
                story.append(Spacer(1, 15))

            if 'volume_trend' in charts:
                try:
                    img_data = BytesIO(base64.b64decode(charts['volume_trend']))
                    img = Image(img_data, width=w-80, height=2.5*inch)
                    img.hAlign = 'CENTER'
                    story.append(img)
                    story.append(Spacer(1, 15))
                except: pass

        # Score distribution table
        dist = stats_raw.get("score_distribution", {})
        if dist:
            story.append(Paragraph("Score Distribution", styles["sec"]))
            total_d = sum(dist.values()) or 1
            rows    = [[k, str(v), f"{v / total_d * 100:.1f}%"] for k, v in dist.items()]
            story.append(_tbl(["Category", "Count", "Share of Total"], rows, [(w-80)*0.40, (w-80)*0.30, (w-80)*0.30]))
            story.append(Spacer(1, 20))

        # Full Data Section
        story.append(Paragraph("Full Report Data", styles["sec"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=12))

        def _render(d, depth=0):
            if not isinstance(d, dict): return
            pad = "&nbsp;" * (depth * 6)
            for k, v in d.items():
                if k == "charts": continue
                label = str(k).replace("_", " ").title()
                if isinstance(v, dict):
                    if not v: continue
                    story.append(Paragraph(f"{pad}<b>{label}</b>", styles["body"]))
                    _render(v, depth + 1)
                elif isinstance(v, list):
                    story.append(Paragraph(f"{pad}<b>{label}:</b> [{len(v)} items]", styles["body"]))
                    for item in v[:8]:
                        story.append(Paragraph(f"{pad}&nbsp;&nbsp;&nbsp;\u2022 {str(item)[:150]}", styles["code"]))
                    if len(v) > 8:
                        story.append(Paragraph(f"{pad}&nbsp;&nbsp;&nbsp;<i>\u2026 and {len(v)-8} more items</i>", styles["foot"]))
                else:
                    story.append(Paragraph(f"{pad}<b>{label}:</b> {str(v)[:250]}", styles["body"]))

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
            "preview": preview, "charts": report_data.get('charts'),
            "filename": f"hr_report_{data['report_type']}_{datetime.now().strftime('%Y%m%d')}.{'txt' if data.get('report_format')=='text' else 'json' if data.get('report_format')=='json' else 'html'}"})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


def _generate_report_data(report_type, params):
    # Fetch all relevant data
    applications = db.get_all_applications()
    all_scores = [a.get('resume_score') for a in applications if a.get('resume_score') is not None]
    statistics = db.get_statistics()
    
    # Filter by department if provided
    dept_filter = params.get('department_filter')
    if dept_filter:
        applications = [a for a in applications if a.get('department') == dept_filter]
        
    # Filter by date range if provided
    start_date = params.get('start_date')
    end_date = params.get('end_date')
    if start_date or end_date:
        # Simple date filtering (assuming application_date is ISO format or similar)
        filtered = []
        for a in applications:
            adate = a.get('application_date', '').split('T')[0]
            if not adate: continue
            if start_date and adate < start_date: continue
            if end_date and adate > end_date: continue
            filtered.append(a)
        applications = filtered

    # 1. Pipeline data
    status_counts = {}
    for a in applications:
        s = a.get('status', 'pending').replace('_', ' ').title()
        status_counts[s] = status_counts.get(s, 0) + 1
        
    # 2. Score trend / Distribution
    score_list = [a.get('resume_score') for a in applications if a.get('resume_score') is not None]
    
    # 3. Application volume by date
    volume_by_date = {}
    for a in applications:
        d = a.get('application_date', '').split('T')[0]
        if d: volume_by_date[d] = volume_by_date.get(d, 0) + 1
    
    sorted_dates = sorted(volume_by_date.items())
    dates = [d for d, c in sorted_dates]
    counts = [c for d, c in sorted_dates]

    # 4. Department breakdown
    dept_counts = {}
    for a in db.get_all_applications(): # use all for comparison if needed, or filtered
        d = a.get('department') or 'Other'
        dept_counts[d] = dept_counts.get(d, 0) + 1

    # 5. Hiring Pipeline stages (summary)
    pipeline = {
        "Applied":      len(applications),
        "Interviewing": len([a for a in applications if "interview" in (a.get('status') or '').lower()]),
        "Offer Phase":  len([a for a in applications if "offer" in (a.get('status') or '').lower()]),
        "Hired":        len([a for a in applications if "accepted" in (a.get('status') or '').lower() and "offer" in (a.get('status') or '').lower()])
    }

    data = {
        "total_applications": len(applications),
        "status_distribution": status_counts,
        "hiring_pipeline": pipeline,
        "score_data": score_list,
        "volume_trend": {"labels": dates, "values": counts},
        "department_breakdown": dept_counts,
        "statistics": statistics,
        "generated_at": datetime.now().isoformat()
    }

    # Generate charts if requested
    if params.get('include_charts'):
        data["charts"] = _generate_charts(data)

    return data


def _generate_charts(data):
    """Generates charts as base64 encoded PNG strings"""
    charts = {}
    sns.set_theme(style="whitegrid", palette="muted")
    
    # 1. Status Distribution (Donut Chart)
    try:
        dist = data.get('status_distribution', {})
        if dist:
            plt.figure(figsize=(6, 4))
            labels = list(dist.keys())
            values = list(dist.values())
            plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, pctdistance=0.85, 
                    colors=sns.color_palette("viridis", len(labels)))
            # Draw circle for donut
            centre_circle = plt.Circle((0,0), 0.70, fc='white')
            fig = plt.gcf()
            fig.gca().add_artist(centre_circle)
            plt.title('Application Status Distribution', fontweight='bold')
            charts['status_dist'] = _plot_to_base64()
    except Exception as e: print(f"Chart Error (Status): {e}")

    # 2. Score Distribution (Histogram)
    try:
        scores = data.get('score_data', [])
        if scores:
            plt.figure(figsize=(6, 4))
            sns.histplot(scores, kde=True, color="#3B6FE8")
            plt.title('Resume Score Distribution', fontweight='bold')
            plt.xlabel('Score')
            plt.ylabel('Count')
            charts['score_dist'] = _plot_to_base64()
    except Exception as e: print(f"Chart Error (Scores): {e}")

    # 3. Application Trend (Line Chart)
    try:
        trend = data.get('volume_trend', {})
        if trend and trend.get('labels'):
            plt.figure(figsize=(10, 4))
            plt.plot(trend['labels'], trend['values'], marker='o', linestyle='-', color="#6B4FDB", linewidth=2)
            plt.fill_between(trend['labels'], trend['values'], alpha=0.1, color="#6B4FDB")
            plt.title('Application Volume Trend', fontweight='bold')
            plt.xticks(rotation=45)
            plt.tight_layout()
            charts['volume_trend'] = _plot_to_base64()
    except Exception as e: print(f"Chart Error (Trend): {e}")

    return charts

def _plot_to_base64():
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def _report_preview_text(report_type: str, data: dict) -> str:
    lines = [f"REPORT: {report_type.upper().replace('_',' ')}", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    for k, v in data.items():
        if k == "charts": continue # Skip huge base64 strings in preview
        label = str(k).replace("_", " ").title()
        if isinstance(v, dict):
            lines.append(f"{label}:")
            for kk, vv in v.items():
                lines.append(f"  {str(kk).replace('_',' ').title()}: {vv}")
        elif isinstance(v, list):
            lines.append(f"{label}: {len(v)} records")
        else:
            lines.append(f"{label}: {v}")
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
        charts_html = ""
        charts_data = report.get('report_data', {}).get('charts', {})
        if charts_data:
            charts_html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:20px 0;">'
            for name, b64 in charts_data.items():
                style = "grid-column:1/-1;" if name == 'volume_trend' else ""
                charts_html += f'<div class="card" style="{style}"><div class="card-bd"><img src="data:image/png;base64,{b64}" style="width:100%;border-radius:8px;"/></div></div>'
            charts_html += '</div>'

        html = f"""<!DOCTYPE html><html><head><title>HR Intelligence Report</title>
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
        :root {{ --bg:#F4F7FB; --white:#fff; --ink:#0F172A; --ink2:#475569; --ink3:#94A3B8; --blue:#2563EB; --indigo:#4F46E5; --border:#E2E8F0; --glass:rgba(255,255,255,0.8); }}
        body {{ font-family:'Plus Jakarta Sans',sans-serif; padding:3rem; background:var(--bg); color:var(--ink); line-height:1.6; }}
        .report-box {{ background:var(--white); border-radius:24px; padding:3.5rem; max-width:1100px; margin:0 auto;
                     box-shadow:0 20px 50px rgba(0,0,0,0.05); border:1px solid var(--border); }}
        .header {{ border-bottom:2px solid var(--border); padding-bottom:2rem; margin-bottom:2.5rem; display:flex; justify-content:space-between; align-items:flex-start; }}
        h1 {{ font-size:32px; font-weight:800; color:var(--ink); margin:0; letter-spacing:-0.03em; }}
        .meta-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:24px; margin-bottom:2.5rem; }}
        .meta-item {{ display:flex; flex-direction:column; gap:4px; }}
        .meta-label {{ font-size:11px; font-weight:700; color:var(--ink3); text-transform:uppercase; letter-spacing:0.05em; }}
        .meta-value {{ font-size:14px; font-weight:600; color:var(--ink2); }}
        .chart-grid {{ display:grid; grid-template-columns:repeat(2, 1fr); gap:24px; margin-bottom:2.5rem; }}
        .chart-card {{ background:var(--white); border:1px solid var(--border); border-radius:18px; padding:20px; box-shadow:0 4px 12px rgba(0,0,0,0.02); }}
        .full-width {{ grid-column:1/-1; }}
        .section-title {{ font-size:18px; font-weight:800; color:var(--ink); margin:2rem 0 1.2rem; display:flex; align-items:center; gap:10px; }}
        .section-title::before {{ content:''; width:4px; height:20px; background:var(--blue); border-radius:2px; }}
        pre {{ background:#F8FAFC; padding:24px; border-radius:16px; border:1px solid var(--border); overflow-x:auto; font-family:'JetBrains Mono',monospace; font-size:13px; color:var(--ink2); }}
        .badge {{ display:inline-block; padding:4px 12px; border-radius:100px; font-size:12px; font-weight:700; background:var(--blue); color:white; }}
        </style></head><body><div class="report-box">
        <div class="header">
            <div>
                <h1>{report['report_type'].replace('_',' ').title()}</h1>
                <p style="color:var(--ink3);margin:5px 0 0;">HR Strategic Intelligence Intelligence Report</p>
            </div>
            <div class="badge">OFFICIAL DOCUMENT</div>
        </div>
        
        <div class="meta-grid">
            <div class="meta-item"><span class="meta-label">Generated Date</span><span class="meta-value">{report.get('generated_date','—')}</span></div>
            <div class="meta-item"><span class="meta-label">Prepared By</span><span class="meta-value">{report.get('generated_by','—')}</span></div>
            <div class="meta-item"><span class="meta-label">Report ID</span><span class="meta-value" style="font-family:monospace;font-size:11px;">{report['id'][:13]}...</span></div>
            <div class="meta-item"><span class="meta-label">Period</span><span class="meta-value">{report.get('start_date','All time')} → {report.get('end_date','Present')}</span></div>
        </div>

        {charts_html}
        
        <div class="section-title">Raw Data Analysis</div>
        <pre>{json.dumps(report.get('report_data',{}), indent=2)}</pre>
        
        <div style="margin-top:4rem; padding-top:2rem; border-top:1px solid var(--border); text-align:center; color:var(--ink3); font-size:12px;">
            This report contains sensitive HR data. Confidentiality must be maintained at all times.<br/>
            &copy; {datetime.now().year} TalentFlow Pro - HR Intelligence Module
        </div>
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