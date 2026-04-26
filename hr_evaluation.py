from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from database import ResumeDatabase
from hr_base import app, get_current_user, get_base_html, get_end_html, send_email
import os
import mimetypes
import sqlite3

db = ResumeDatabase()

# ── SVG icon helpers ──────────────────────────────────────────────────────────
def _svg(w, h, path, sw="2", extra=""):
    return f'<svg width="{w}" height="{h}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="{sw}"{" " + extra if extra else ""}>{path}</svg>'

_P = {
    "users":    '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "clip":     '<path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/>',
    "check":    '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    "star":     '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    "cal":      '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
    "bars":     '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    "trend":    '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    "edit":     '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>',
    "trash":    '<polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>',
    "close":    '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
    "refr":     '<polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.94"/>',
    "search":   '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "msg":      '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "sliders":  '<line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>',
    "save":     '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>',
    "brain":    '<path d="M9 3a3 3 0 0 0-3 3 3 3 0 0 0-3 3 4 4 0 0 0 4 4h1v7h4v-7h1a4 4 0 0 0 4-4 3 3 0 0 0-3-3 3 3 0 0 0-3-3z"/>',
    "award":    '<circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/>',
    "chat":     '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "people":   '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>',
    "doc":      '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
    "filter":   '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>',
    "warn":     '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
}

def _icon(key, size=16, sw="2", style="", cls=""):
    extra = ""
    if style: extra += f' style="{style}"'
    if cls:   extra += f' class="{cls}"'
    return _svg(size, size, _P[key], sw, extra.strip())


@app.get("/evaluations", response_class=HTMLResponse)
async def evaluations_page(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/", status_code=302)

    page_html = _build_page()
    return HTMLResponse(
        content=get_base_html("Evaluations", "evaluations", current_user)
        + page_html
        + get_end_html()
    )


def _build_page() -> str:
    # Pre-build all SVG icon strings used in HTML and JS
    close_x  = _icon("close",  14, "2.5")
    save_ic   = _icon("save",   13)
    edit_ic   = _icon("edit",   13)
    trash_ic  = _icon("trash",  13)
    refr_ic   = _icon("refr",   12)
    src_ic    = _icon("search", 12)
    flt_ic    = _icon("filter", 12)
    cal_ic    = _icon("cal",    20, "1.8")
    star_ic   = _icon("star",   20, "1.8")
    clip_ic   = _icon("clip",   20, "1.8")
    trend_ic  = _icon("trend",  20, "1.8")
    brain_ic  = _icon("brain",  14)
    award_ic  = _icon("award",  14)
    chat_ic   = _icon("chat",   14)
    people_ic = _icon("people", 14)
    warn_ic   = _icon("warn",   18, "1.8")
    doc_ic    = _icon("doc",    32, "1.5")

    return f"""
<!-- ══ PAGE HEADER ══ -->
<div class="page-hd">
  <div>
    <div class="page-title">Applicant Evaluations</div>
    <div class="page-sub">Score and review shortlisted candidates across key criteria.</div>
  </div>
</div>

<!-- ══ STAT TILES ══ -->
<div class="stats-row" style="margin-bottom:24px;" id="statTiles">
  <div class="stat-tile">
    <div class="stat-icon">{cal_ic}</div>
    <div class="stat-body"><div class="stat-label">Total Evaluations</div><div class="stat-value" id="statTotal">—</div></div>
  </div>
  <div class="stat-tile">
    <div class="stat-icon">{star_ic}</div>
    <div class="stat-body"><div class="stat-label">Average Score</div><div class="stat-value" id="statAvg">—</div></div>
  </div>
  <div class="stat-tile">
    <div class="stat-icon">{trend_ic}</div>
    <div class="stat-body"><div class="stat-label">High Scores (8+)</div><div class="stat-value" id="statHigh">—</div></div>
  </div>
  <div class="stat-tile">
    <div class="stat-icon">{clip_ic}</div>
    <div class="stat-body"><div class="stat-label">This Month</div><div class="stat-value" id="statMonth">—</div></div>
  </div>
</div>

<!-- ══ TAB SWITCHER ══ -->
<div style="display:flex;gap:8px;margin-bottom:20px;">
  <button class="ev-tab active" id="tab-eval" onclick="switchTab('eval',this)">
    {_icon("people", 13)} To Evaluate
    <span class="ev-tab-count" id="evalCount">—</span>
  </button>
  <button class="ev-tab" id="tab-hist" onclick="switchTab('hist',this)">
    {_icon("cal", 13)} History
    <span class="ev-tab-count" id="histCount">—</span>
  </button>
</div>

<!-- ══ TO-EVALUATE PANEL ══ -->
<div id="panel-eval" style="animation:fadeUp 0.3s ease both;">

  <!-- Filters -->
  <div class="card" style="margin-bottom:16px;">
    <div class="card-bd" style="padding:16px 20px;">
      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;">
        <!-- Search -->
        <div style="flex:1;min-width:200px;">
          <div style="font-size:11.5px;font-weight:700;color:var(--ink3);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">{src_ic} Search</div>
          <div style="position:relative;">
            <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="var(--ink3)" stroke-width="2"
              style="position:absolute;left:10px;top:50%;transform:translateY(-50%);pointer-events:none;">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input type="text" id="evalSearch" placeholder="Name or email…"
              style="width:100%;padding:8px 12px 8px 32px;background:var(--bg);border:1.5px solid var(--border);
                     border-radius:8px;font-family:'DM Sans',sans-serif;font-size:13px;color:var(--ink);outline:none;"
              oninput="filterApplicants()"
              onfocus="this.style.borderColor='var(--blue)'" onblur="this.style.borderColor='var(--border)'">
          </div>
        </div>
        <!-- Status -->
        <div style="min-width:150px;">
          <div style="font-size:11.5px;font-weight:700;color:var(--ink3);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">{flt_ic} Status</div>
          <select id="evalStatus" class="form-ctrl" style="padding:8px 12px;font-size:13px;" onchange="filterApplicants()">
            <option value="">All Statuses</option>
            <option value="reviewed">Reviewed</option>
            <option value="shortlisted">Shortlisted</option>
            <option value="interview_scheduled">Interviewing</option>
            <option value="interview_passed">Passed Interview</option>
            <option value="evaluated">Evaluated</option>
          </select>
        </div>
        <!-- Department -->
        <div style="min-width:160px;">
          <div style="font-size:11.5px;font-weight:700;color:var(--ink3);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">{flt_ic} Department</div>
          <select id="evalDept" class="form-ctrl" style="padding:8px 12px;font-size:13px;" onchange="filterApplicants()">
            <option value="">All Departments</option>
          </select>
        </div>
        <!-- Refresh -->
        <button class="btn btn-outline" style="padding:8px 14px;font-size:12.5px;white-space:nowrap;"
          onclick="loadApplicants()">
          {refr_ic} Refresh
        </button>
      </div>
    </div>
  </div>

  <!-- Applicant cards grid -->
  <div id="applicantsGrid" style="min-height:200px;">
    <div style="text-align:center;padding:48px;color:var(--ink3);">
      <div class="spin" style="margin:0 auto 12px;"></div>
      <div style="font-size:13px;">Loading applicants…</div>
    </div>
  </div>
</div>

<!-- ══ HISTORY PANEL ══ -->
<div id="panel-hist" style="display:none;animation:fadeUp 0.3s ease both;">

  <!-- Filters -->
  <div class="card" style="margin-bottom:16px;">
    <div class="card-bd" style="padding:16px 20px;">
      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;">
        <div style="flex:1;min-width:200px;">
          <div style="font-size:11.5px;font-weight:700;color:var(--ink3);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">{src_ic} Search</div>
          <div style="position:relative;">
            <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="var(--ink3)" stroke-width="2"
              style="position:absolute;left:10px;top:50%;transform:translateY(-50%);pointer-events:none;">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input type="text" id="histSearch" placeholder="Name or email…"
              style="width:100%;padding:8px 12px 8px 32px;background:var(--bg);border:1.5px solid var(--border);
                     border-radius:8px;font-family:'DM Sans',sans-serif;font-size:13px;color:var(--ink);outline:none;"
              oninput="filterHistory()"
              onfocus="this.style.borderColor='var(--blue)'" onblur="this.style.borderColor='var(--border)'">
          </div>
        </div>
        <div style="min-width:150px;">
          <div style="font-size:11.5px;font-weight:700;color:var(--ink3);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">{flt_ic} Score</div>
          <select id="histScore" class="form-ctrl" style="padding:8px 12px;font-size:13px;" onchange="filterHistory()">
            <option value="">All Scores</option>
            <option value="high">High (8–10)</option>
            <option value="medium">Medium (5–7.9)</option>
            <option value="low">Low (0–4.9)</option>
          </select>
        </div>
        <div style="min-width:150px;">
          <div style="font-size:11.5px;font-weight:700;color:var(--ink3);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">{flt_ic} Date</div>
          <select id="histDate" class="form-ctrl" style="padding:8px 12px;font-size:13px;" onchange="filterHistory()">
            <option value="">All Time</option>
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
          </select>
        </div>
        <button class="btn btn-outline" style="padding:8px 14px;font-size:12.5px;white-space:nowrap;"
          onclick="loadEvaluationHistory()">
          {refr_ic} Refresh
        </button>
      </div>
    </div>
  </div>

  <!-- History table -->
  <div class="card" style="animation:fadeUp 0.3s ease both;overflow:hidden;">
    <div style="overflow-x:auto;">
      <table class="data-table" id="histTable">
        <thead><tr>
          <th>Applicant</th><th>Position</th>
          <th>{brain_ic} Technical</th>
          <th>{award_ic} Experience</th>
          <th>{chat_ic} Communication</th>
          <th>{people_ic} Culture</th>
          <th>Overall</th>
          <th>Feedback</th>
          <th>Date</th>
          <th>Actions</th>
        </tr></thead>
        <tbody id="histBody">
          <tr><td colspan="10" style="text-align:center;padding:40px;color:var(--ink3);">
            <div class="spin" style="margin:0 auto 10px;"></div>
            Loading history…
          </td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<!-- ══ EVALUATION MODAL ══ -->
<div id="evalModal" style="display:none;position:fixed;inset:0;background:rgba(13,14,26,0.6);
     z-index:10000;align-items:center;justify-content:center;backdrop-filter:blur(6px);">
  <div style="background:var(--white);border-radius:18px;max-width:720px;width:90%;
              max-height:90vh;overflow-y:auto;box-shadow:0 24px 64px rgba(0,0,0,0.22);position:relative;">

    <!-- Modal header -->
    <div style="display:flex;align-items:center;justify-content:space-between;
                padding:22px 28px;border-bottom:1px solid var(--border);">
      <div>
        <div style="font-family:'Sora',sans-serif;font-weight:800;font-size:16px;color:var(--ink);"
          id="modalTitle">Evaluate Applicant</div>
        <div style="font-size:12px;color:var(--ink3);margin-top:2px;" id="modalSub">Score this candidate across four criteria</div>
      </div>
      <button onclick="closeModal()"
        style="background:var(--bg);border:1px solid var(--border);border-radius:8px;
               width:32px;height:32px;cursor:pointer;display:flex;align-items:center;justify-content:center;">
        {close_x}
      </button>
    </div>

    <!-- Applicant info bar -->
    <div id="applicantBar" style="margin:20px 28px 0;background:var(--bg);border-radius:12px;
         padding:16px 18px;border:1px solid var(--border);display:none;">
    </div>

    <!-- Scoring -->
    <div style="padding:24px 28px;">
      <div style="font-family:'Sora',sans-serif;font-size:13px;font-weight:700;
                  text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);margin-bottom:16px;">
        Scoring Criteria
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">
        {_score_field("technical",     brain_ic,  "Technical Skills")}
        {_score_field("experience",    award_ic,  "Experience")}
        {_score_field("communication", chat_ic,   "Communication")}
        {_score_field("culture",       people_ic, "Culture Fit")}
      </div>

      <!-- Overall score bar -->
      <div style="background:linear-gradient(135deg,var(--blue),#6B4FDB);border-radius:12px;
                  padding:16px 20px;display:flex;align-items:center;justify-content:space-between;">
        <div>
          <div style="font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;
                      color:rgba(255,255,255,.7);">Overall Score</div>
          <div style="font-size:11px;color:rgba(255,255,255,.5);margin-top:2px;">Average of all four criteria</div>
        </div>
        <div style="font-family:'Sora',sans-serif;font-size:36px;font-weight:800;color:#fff;"
          id="overallDisplay">5.0</div>
      </div>

      <!-- Feedback -->
      <div style="margin-top:20px;">
        <div style="font-family:'Sora',sans-serif;font-size:13px;font-weight:700;
                    text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);margin-bottom:8px;">
          Feedback
        </div>
        <textarea id="feedbackText" rows="4"
          placeholder="Provide detailed feedback about this candidate — strengths, concerns, recommendations…"
          style="width:100%;padding:12px 14px;background:var(--bg);border:1.5px solid var(--border);
                 border-radius:10px;font-family:'DM Sans',sans-serif;font-size:13.5px;
                 color:var(--ink);line-height:1.65;resize:vertical;outline:none;"
          onfocus="this.style.borderColor='var(--blue)'" onblur="this.style.borderColor='var(--border)'">
        </textarea>
      </div>

      <!-- Interview Outcome -->
      <div style="margin-top:20px;">
        <div style="font-family:'Sora',sans-serif;font-size:13px;font-weight:700;
                    text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);margin-bottom:12px;">
          Interview Result
        </div>
        <div style="display:flex;gap:12px;">
          <label style="flex:1;cursor:pointer;">
            <input type="radio" name="interviewResult" value="passed" style="display:none;" id="resPass" checked>
            <div class="res-btn" onclick="document.getElementById('resPass').checked=true" id="btnPass">
              Hire Candidate
            </div>
          </label>
          <label style="flex:1;cursor:pointer;">
            <input type="radio" name="interviewResult" value="failed" style="display:none;" id="resFail">
            <div class="res-btn fail" onclick="document.getElementById('resFail').checked=true" id="btnFail">
              Reject Candidate
            </div>
          </label>
        </div>
      </div>
    </div>

    <!-- Modal footer -->
    <div style="display:flex;justify-content:flex-end;gap:10px;
                padding:18px 28px;border-top:1px solid var(--border);">
      <button class="btn btn-outline" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="saveEvaluation()">
        {save_ic} <span id="saveLabel">Save Evaluation</span>
      </button>
    </div>
  </div>
</div>

<style>
/* ── Tabs ── */
.ev-tab {{
  display:inline-flex;align-items:center;gap:6px;
  padding:9px 16px;border-radius:10px;border:1.5px solid var(--border);
  background:var(--white);color:var(--ink2);font-family:'DM Sans',sans-serif;
  font-size:13.5px;font-weight:600;cursor:pointer;transition:all 0.15s;
}}
.ev-tab.active {{
  background:var(--blue-lt);border-color:var(--blue);color:var(--blue);
}}
.ev-tab:hover:not(.active) {{ background:var(--bg); }}
.ev-tab-count {{
  background:var(--bg);border:1px solid var(--border);
  padding:1px 7px;border-radius:20px;font-size:11px;font-weight:700;
}}
.ev-tab.active .ev-tab-count {{ background:var(--blue);color:#fff;border-color:var(--blue); }}

/* ── Applicant cards ── */
.app-grid {{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:14px;
}}
.app-card {{
  background:var(--white);border:1.5px solid var(--border);border-radius:14px;
  padding:18px 20px;cursor:pointer;transition:all 0.15s;animation:fadeUp 0.3s ease both;
}}
.app-card:hover {{
  border-color:var(--blue);box-shadow:var(--shadow);transform:translateY(-1px);
}}
.app-av {{
  width:38px;height:38px;border-radius:10px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-family:'Sora',sans-serif;font-weight:800;font-size:14px;color:#fff;
}}
.app-name {{ font-weight:700;font-size:14px;color:var(--ink);margin-bottom:2px; }}
.app-email {{ font-size:12px;color:var(--ink3); }}

/* ── Detail rows inside card ── */
.drow {{
  display:flex;justify-content:space-between;align-items:center;
  padding:6px 0;border-bottom:1px solid var(--border);font-size:12.5px;
}}
.drow:last-child {{ border-bottom:none; }}
.drow-label {{ color:var(--ink3);font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.04em; }}
.drow-val   {{ font-weight:600;color:var(--ink); }}

/* ── Status badges ── */
.sb {{
  display:inline-flex;padding:3px 10px;border-radius:20px;
  font-size:11.5px;font-weight:700;text-transform:capitalize;
}}
.sb-reviewed    {{ background:var(--blue-lt);color:var(--blue); }}
.sb-shortlisted {{ background:#E8F8F0;color:var(--green); }}
.sb-interview_scheduled {{ background:var(--blue-lt);color:var(--blue); }}
.sb-interview_passed    {{ background:#E8F8F0;color:var(--green); }}
.sb-evaluated   {{ background:#EDE9FF;color:#6B4FDB; }}
.sb-default     {{ background:var(--bg);color:var(--ink3); }}

/* ── Score badges ── */
.scb {{ display:inline-flex;padding:2px 8px;border-radius:6px;font-size:11.5px;font-weight:700; }}
.scb-h {{ background:#E8F8F0;color:var(--green); }}
.scb-m {{ background:var(--amber-lt);color:#C67C00; }}
.scb-l {{ background:var(--red-lt);color:var(--red); }}
.scb-n {{ background:var(--bg);color:var(--ink3);border:1px solid var(--border); }}

/* ── Slider ── */
.ev-slider {{
  width:100%;height:5px;border-radius:3px;
  background:var(--border);outline:none;cursor:pointer;
  -webkit-appearance:none;appearance:none;
}}
.ev-slider::-webkit-slider-thumb {{
  -webkit-appearance:none;width:18px;height:18px;border-radius:50%;
  background:var(--blue);cursor:pointer;border:2px solid #fff;
  box-shadow:0 1px 4px rgba(59,111,232,.35);
}}
.ev-slider::-moz-range-thumb {{
  width:18px;height:18px;border-radius:50%;
  background:var(--blue);cursor:pointer;border:2px solid #fff;
  box-shadow:0 1px 4px rgba(59,111,232,.35);
}}

/* ── Score field card ── */
.sf-card {{
  background:var(--bg);border-radius:10px;padding:14px 16px;border:1.5px solid var(--border);
}}
.sf-head {{ display:flex;align-items:center;justify-content:space-between;margin-bottom:10px; }}
.sf-label {{ display:flex;align-items:center;gap:6px;font-size:12.5px;font-weight:700;color:var(--ink); }}
.sf-val {{
  font-family:'Sora',sans-serif;font-size:18px;font-weight:800;color:var(--blue);
  min-width:32px;text-align:right;
}}

/* ── Spinner ── */
.spin {{
  width:20px;height:20px;border-radius:50%;
  border:2.5px solid var(--border);border-top-color:var(--blue);
  animation:spinA .7s linear infinite;
}}
@keyframes spinA {{ to{{transform:rotate(360deg);}} }}

/* ── Empty state ── */
.ev-empty {{
  text-align:center;padding:56px 24px;color:var(--ink3);
}}
.ev-empty svg {{ margin:0 auto 14px;display:block;opacity:.4; }}
.ev-empty-title {{ font-family:'Sora',sans-serif;font-weight:700;font-size:15px;color:var(--ink2);margin-bottom:4px; }}
.ev-empty-sub {{ font-size:12.5px; }}

/* ── Feedback truncation in table ── */
.fb-clip {{
  max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
  font-size:12.5px;color:var(--ink3);
}}

/* ── Edit / Delete mini buttons ── */
.act-btn {{
  display:inline-flex;align-items:center;gap:4px;
  padding:4px 9px;border-radius:6px;font-size:11.5px;font-weight:700;
  cursor:pointer;border:none;transition:all .12s;
}}
.act-edit  {{ background:var(--amber-lt);color:#C67C00; }}
.act-edit:hover  {{ background:#FDE68A; }}
.act-del   {{ background:var(--red-lt);color:var(--red); }}
.act-del:hover   {{ background:#FCA5A5; }}

.res-btn {{
  padding:12px;border-radius:10px;text-align:center;font-weight:700;font-size:13.5px;
  border:2px solid var(--border);color:var(--ink2);transition:all 0.2s;
}}
input[value="passed"]:checked + .res-btn {{ border-color:var(--green);background:#E8F8F0;color:var(--green); }}
input[value="failed"]:checked + .res-btn {{ border-color:var(--red);background:#FFF5F5;color:var(--red); }}
</style>

<script>
let _applicants = [];
let _evaluations = [];
let _currentApp = null;

// ── INIT ─────────────────────────────────────────────
window.addEventListener('load', () => {{
  loadApplicants();
  loadEvaluationHistory();
  setupSliders();
}});

// ── TABS ─────────────────────────────────────────────
function switchTab(tab, btn) {{
  ['eval','hist'].forEach(t => {{
    document.getElementById('panel-'+t).style.display = t===tab ? '' : 'none';
  }});
  document.querySelectorAll('.ev-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}}

// ── LOAD APPLICANTS ────────────────────────────────────
async function loadApplicants() {{
  document.getElementById('applicantsGrid').innerHTML =
    '<div style="text-align:center;padding:48px;color:var(--ink3);"><div class="spin" style="margin:0 auto 12px;"></div><div style="font-size:13px;">Loading applicants…</div></div>';
  try {{
    const r = await fetch('/api/applicants-for-evaluation');
    _applicants = await r.json();
    populateDeptFilter(_applicants);
    renderApplicants(_applicants);
    document.getElementById('evalCount').textContent = _applicants.length;
  }} catch(e) {{
    document.getElementById('applicantsGrid').innerHTML =
      '<div class="ev-empty">{warn_ic}<div class="ev-empty-title">Failed to load applicants</div><div class="ev-empty-sub">Please refresh and try again.</div></div>';
  }}
}}

function populateDeptFilter(apps) {{
  const depts = [...new Set(apps.map(a => a.department).filter(Boolean))].sort();
  const sel = document.getElementById('evalDept');
  sel.innerHTML = '<option value="">All Departments</option>';
  depts.forEach(d => sel.innerHTML += `<option value="${{d}}">${{d}}</option>`);
}}

function renderApplicants(apps) {{
  const grid = document.getElementById('applicantsGrid');
  if (!apps.length) {{
    grid.innerHTML = `<div class="ev-empty">{doc_ic}<div class="ev-empty-title">No applicants found</div><div class="ev-empty-sub">No applicants match your filters.</div></div>`;
    return;
  }}
  grid.innerHTML = `<div class="app-grid">${{apps.map((a, i) => _appCard(a, i)).join('')}}</div>`;
}}

function _appCard(a, i) {{
  const init = (a.name || '?')[0].toUpperCase();
  const colors = [['#4776E6','#8E54E9'],['#F05252','#FF7B7B'],['#0BB5B5','#36D1C4'],
                  ['#F4A83A','#F7CB6A'],['#27AE60','#52C87A'],['#6B4FDB','#9B6FFF']];
  const [c1, c2] = colors[a.name.charCodeAt(0) % colors.length];
  const sc = a.resume_score;
  const scHtml = sc ? `<span class="scb ${{sc >= 70 ? 'scb-h' : sc >= 50 ? 'scb-m' : 'scb-l'}}">${{sc}}/100</span>` : '<span class="scb scb-n">N/A</span>';
  const status = (a.status || 'reviewed').toLowerCase();
  const sbCls = {{
    reviewed: 'sb-reviewed',
    shortlisted: 'sb-shortlisted',
    interview_scheduled: 'sb-interview_scheduled',
    interview_passed: 'sb-interview_passed',
    evaluated: 'sb-evaluated'
  }}[status] || 'sb-default';
  const date = a.application_date ? new Date(a.application_date).toLocaleDateString('en-US',{{month:'short',day:'numeric',year:'numeric'}}) : '—';
  return `<div class="app-card" onclick="openModal(${{a.application_id}})" style="animation-delay:${{i*0.04}}s;">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
    <div class="app-av" style="background:linear-gradient(135deg,${{c1}},${{c2}});">${{init}}</div>
    <div style="flex:1;min-width:0;">
      <div class="app-name">${{escH(a.name)}}</div>
      <div class="app-email">${{escH(a.email)}}</div>
    </div>
    <span class="sb ${{sbCls}}">${{status}}</span>
  </div>
  <div>
    <div class="drow"><span class="drow-label">Position</span><span class="drow-val">${{escH(a.job_title)}}</span></div>
    <div class="drow"><span class="drow-label">Department</span><span class="drow-val">${{escH(a.department || '—')}}</span></div>
    <div class="drow"><span class="drow-label">Applied</span><span class="drow-val">${{date}}</span></div>
    <div class="drow"><span class="drow-label">Resume Score</span><span class="drow-val">${{scHtml}}</span></div>
  </div>
</div>`;
}}

function filterApplicants() {{
  const q   = document.getElementById('evalSearch').value.toLowerCase();
  const st  = document.getElementById('evalStatus').value;
  const dep = document.getElementById('evalDept').value;
  const filtered = _applicants.filter(a => {{
    const matchQ = !q || a.name.toLowerCase().includes(q) || a.email.toLowerCase().includes(q);
    const matchS = !st  || a.status === st;
    const matchD = !dep || a.department === dep;
    return matchQ && matchS && matchD;
  }});
  renderApplicants(filtered);
}}

// ── LOAD HISTORY ───────────────────────────────────────
async function loadEvaluationHistory() {{
  document.getElementById('histBody').innerHTML =
    '<tr><td colspan="10" style="text-align:center;padding:40px;color:var(--ink3);"><div class="spin" style="margin:0 auto 10px;"></div>Loading…</td></tr>';
  try {{
    const r = await fetch('/api/evaluation-history');
    _evaluations = await r.json();
    updateStats(_evaluations);
    renderHistory(_evaluations);
    document.getElementById('histCount').textContent = _evaluations.length;
  }} catch(e) {{
    document.getElementById('histBody').innerHTML =
      '<tr><td colspan="10" style="text-align:center;padding:40px;color:var(--red);">Failed to load history.</td></tr>';
  }}
}}

function updateStats(evals) {{
  const total = evals.length;
  const avg   = total ? (evals.reduce((s,e)=>s+parseFloat(e.overall_score||0),0)/total).toFixed(1) : '—';
  const high  = evals.filter(e=>parseFloat(e.overall_score||0)>=8).length;
  const month = new Date(); month.setDate(1);
  const mth   = evals.filter(e=>new Date(e.evaluation_date)>=month).length;
  document.getElementById('statTotal').textContent = total;
  document.getElementById('statAvg').textContent   = avg;
  document.getElementById('statHigh').textContent  = high;
  document.getElementById('statMonth').textContent = mth;
}}

function renderHistory(evals) {{
  const tbody = document.getElementById('histBody');
  if (!evals.length) {{
    tbody.innerHTML = `<tr><td colspan="10"><div class="ev-empty">{doc_ic}<div class="ev-empty-title">No evaluations yet</div><div class="ev-empty-sub">Evaluate an applicant to see history here.</div></div></td></tr>`;
    return;
  }}
  tbody.innerHTML = evals.map(e => {{
    const sc = v => parseFloat(v||0);
    const badge = v => `<span class="scb ${{sc(v)>=7?'scb-h':sc(v)>=5?'scb-m':'scb-l'}}">${{v||'—'}}</span>`;
    const date = e.evaluation_date ? new Date(e.evaluation_date).toLocaleDateString('en-US',{{month:'short',day:'numeric',year:'numeric'}}) : '—';
    return `<tr>
      <td><div style="font-weight:700;font-size:13px;color:var(--ink);">${{escH(e.applicant_name)}}</div>
          <div style="font-size:11.5px;color:var(--ink3);">${{escH(e.applicant_email)}}</div></td>
      <td style="font-size:13px;">${{escH(e.job_title)}}</td>
      <td>${{badge(e.technical_score)}}</td>
      <td>${{badge(e.experience_score)}}</td>
      <td>${{badge(e.communication_score)}}</td>
      <td>${{badge(e.culture_score)}}</td>
      <td><span style="font-family:'Sora',sans-serif;font-weight:800;font-size:15px;color:var(--blue);">${{e.overall_score||'—'}}</span></td>
      <td><div class="fb-clip" title="${{escH(e.feedback||'')}}">${{escH(e.feedback||'—')}}</div></td>
      <td style="font-size:12px;color:var(--ink3);white-space:nowrap;">${{date}}</td>
      <td><div style="display:flex;gap:5px;">
        <button class="act-btn act-edit" onclick="editEvaluation(${{e.application_id}})">{edit_ic} Edit</button>
        <button class="act-btn act-del"  onclick="deleteEvaluation(${{e.id}})">{trash_ic} Del</button>
      </div></td>
    </tr>`;
  }}).join('');
}}

function filterHistory() {{
  const q   = document.getElementById('histSearch').value.toLowerCase();
  const sc  = document.getElementById('histScore').value;
  const dt  = document.getElementById('histDate').value;
  const now = new Date();
  const filtered = _evaluations.filter(e => {{
    const mq = !q  || (e.applicant_name||'').toLowerCase().includes(q) || (e.applicant_email||'').toLowerCase().includes(q);
    const s  = parseFloat(e.overall_score||0);
    const ms = !sc || (sc==='high'&&s>=8)||(sc==='medium'&&s>=5&&s<8)||(sc==='low'&&s<5);
    const ed = new Date(e.evaluation_date);
    const today = new Date(); today.setHours(0,0,0,0);
    const week  = new Date(today); week.setDate(today.getDate()-7);
    const month = new Date(today); month.setDate(1);
    const md = !dt ||(dt==='today'&&ed>=today)||(dt==='week'&&ed>=week)||(dt==='month'&&ed>=month);
    return mq && ms && md;
  }});
  renderHistory(filtered);
}}

// ── MODAL ─────────────────────────────────────────────
function setupSliders() {{
  ['technical','experience','communication','culture'].forEach(k => {{
    const sl = document.getElementById('sl-'+k);
    const vl = document.getElementById('sv-'+k);
    sl.addEventListener('input', function() {{
      vl.textContent = parseFloat(this.value).toFixed(1);
      updateOverall();
    }});
  }});
}}

function updateOverall() {{
  const vals = ['technical','experience','communication','culture'].map(k =>
    parseFloat(document.getElementById('sl-'+k).value));
  const avg = (vals.reduce((s,v)=>s+v,0)/4).toFixed(1);
  document.getElementById('overallDisplay').textContent = avg;
}}

async function openModal(appId) {{
  _currentApp = null;
  document.getElementById('evalModal').style.display = 'flex';
  document.getElementById('applicantBar').style.display = 'none';
  document.getElementById('modalSub').textContent = 'Loading…';

  try {{
    const r = await fetch('/api/applicant/'+appId);
    const a = await r.json();
    _currentApp = a;

    const init = (a.name||'?')[0].toUpperCase();
    const colors = [['#4776E6','#8E54E9'],['#F05252','#FF7B7B'],['#0BB5B5','#36D1C4'],
                    ['#F4A83A','#F7CB6A'],['#27AE60','#52C87A'],['#6B4FDB','#9B6FFF']];
    const [c1,c2] = colors[(a.name||'?').charCodeAt(0)%colors.length];
    const sc = a.resume_score;
    const scHtml = sc ? `<span class="scb ${{sc>=70?'scb-h':sc>=50?'scb-m':'scb-l'}}">${{sc}}/100</span>` : '—';

    document.getElementById('applicantBar').innerHTML = `
      <div style="display:flex;align-items:center;gap:12px;">
        <div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;
          background:linear-gradient(135deg,${{c1}},${{c2}});
          display:flex;align-items:center;justify-content:center;
          font-family:'Sora',sans-serif;font-weight:800;font-size:15px;color:#fff;">${{init}}</div>
        <div style="flex:1;">
          <div style="font-weight:700;font-size:14px;color:var(--ink);">${{escH(a.name)}}</div>
          <div style="font-size:12px;color:var(--ink3);">${{escH(a.email)}}</div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:11px;color:var(--ink3);margin-bottom:2px;">Resume Score</div>
          ${{scHtml}}
        </div>
        <div style="text-align:right;border-left:1px solid var(--border);padding-left:14px;">
          <div style="font-size:11px;color:var(--ink3);margin-bottom:2px;">Position</div>
          <div style="font-size:12.5px;font-weight:700;color:var(--ink);">${{escH(a.job_title)}}</div>
        </div>
      </div>`;
    document.getElementById('applicantBar').style.display = 'block';
    document.getElementById('modalTitle').textContent = 'Evaluate — ' + a.name;
    document.getElementById('modalSub').textContent = a.job_title + (a.department ? ' · ' + a.department : '');

    // Load existing evaluation
    const er = await fetch('/api/evaluation/'+appId);
    if (er.ok) {{
      const ev = await er.json();
      if (ev) {{
        ['technical','experience','communication','culture'].forEach(k => {{
          const val = ev[k+'_score'] || 5;
          document.getElementById('sl-'+k).value = val;
          document.getElementById('sv-'+k).textContent = parseFloat(val).toFixed(1);
        }});
        document.getElementById('feedbackText').value = ev.feedback || '';
        updateOverall();
      }}
    }}
  }} catch(e) {{
    document.getElementById('modalSub').textContent = 'Error loading applicant data.';
  }}
}}

function closeModal() {{
  document.getElementById('evalModal').style.display = 'none';
  _currentApp = null;
  ['technical','experience','communication','culture'].forEach(k => {{
    document.getElementById('sl-'+k).value = 5;
    document.getElementById('sv-'+k).textContent = '5.0';
  }});
  document.getElementById('feedbackText').value = '';
  document.getElementById('overallDisplay').textContent = '5.0';
  document.getElementById('applicantBar').style.display = 'none';
}}

document.getElementById('evalModal').addEventListener('click', function(e) {{
  if (e.target===this) closeModal();
}});

async function saveEvaluation() {{
  if (!_currentApp) return;
  const btn = document.getElementById('saveLabel');
  btn.textContent = 'Saving…';

  const scores = {{}};
  ['technical','experience','communication','culture'].forEach(k => {{
    scores[k] = parseFloat(document.getElementById('sl-'+k).value);
  }});
  const overall = parseFloat(document.getElementById('overallDisplay').textContent);
  const feedback = document.getElementById('feedbackText').value;

  const passed = document.querySelector('input[name="interviewResult"]:checked').value === 'passed';
  const newStatus = passed ? 'hiring_approved' : 'rejected';

  try {{
    const r = await fetch('/api/save-evaluation', {{
      method:'POST', headers:{{'Content-Type':'application/json'}},
      body: JSON.stringify({{
        application_id: _currentApp.application_id,
        evaluator_id: 1,
        scores, feedback, overall_score: overall,
        status: newStatus
      }})
    }});
    btn.textContent = 'Save Evaluation';
    if (r.ok) {{
      showToast('Saved','Evaluation saved successfully.','success');
      closeModal();
      loadApplicants();
      loadEvaluationHistory();
    }} else {{
      showToast('Error','Failed to save evaluation.','error');
    }}
  }} catch(e) {{
    btn.textContent = 'Save Evaluation';
    showToast('Network Error', e.message, 'error');
  }}
}}

async function editEvaluation(appId) {{
  document.getElementById('tab-eval').click();
  await loadApplicants();
  openModal(appId);
}}

async function deleteEvaluation(evalId) {{
  if (!confirm('Delete this evaluation? This cannot be undone.')) return;
  try {{
    const r = await fetch('/api/delete-evaluation/'+evalId, {{method:'DELETE'}});
    if (r.ok) {{
      showToast('Deleted','Evaluation removed.','warning');
      loadEvaluationHistory();
    }} else {{
      showToast('Error','Failed to delete evaluation.','error');
    }}
  }} catch(e) {{
    showToast('Network Error', e.message, 'error');
  }}
}}

function escH(s) {{
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
                  .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}}
</script>
"""


def _score_field(key: str, icon_html: str, label: str) -> str:
    """Render a score slider card for the evaluation modal."""
    return f"""<div class="sf-card">
  <div class="sf-head">
    <div class="sf-label">{icon_html} {label}</div>
    <div class="sf-val" id="sv-{key}">5.0</div>
  </div>
  <input type="range" id="sl-{key}" class="ev-slider" min="0" max="10" value="5" step="0.5">
  <div style="display:flex;justify-content:space-between;font-size:10.5px;color:var(--ink3);margin-top:4px;">
    <span>0</span><span>5</span><span>10</span>
  </div>
</div>"""


# ── BACKEND ROUTES (100% UNCHANGED) ──────────────────────────────────────────

@app.get("/api/applicants-for-evaluation")
async def get_applicants_for_evaluation():
    try:
        applicants = db.get_applicants_for_evaluation()
        return JSONResponse(content=applicants)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/applicant/{application_id}")
async def get_applicant_details(application_id: int):
    try:
        applicants = db.get_applicants_for_evaluation()
        applicant = next((a for a in applicants if a['application_id'] == application_id), None)
        if not applicant:
            return JSONResponse(content={"error": "Applicant not found"}, status_code=404)
        return JSONResponse(content=applicant)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/evaluation/{application_id}")
async def get_evaluation(application_id: int):
    try:
        evaluation = db.get_evaluation_by_application(application_id)
        return JSONResponse(content=evaluation)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/evaluation-history")
async def get_evaluation_history():
    try:
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                e.*,
                a.name as applicant_name,
                a.email as applicant_email,
                j.title as job_title,
                ja.application_date
            FROM evaluations e
            JOIN job_applications ja ON e.application_id = ja.id
            JOIN applicants a ON ja.applicant_id = a.id
            JOIN jobs j ON ja.job_id = j.id
            WHERE e.overall_score IS NOT NULL
            ORDER BY e.evaluation_date DESC
        ''')
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        evaluations = [dict(zip(columns, row)) for row in results]
        conn.close()
        return JSONResponse(content=evaluations)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.delete("/api/delete-evaluation/{evaluation_id}")
async def delete_evaluation(evaluation_id: int):
    try:
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM evaluations WHERE id = ?', (evaluation_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        if success:
            return JSONResponse(content={"success": True})
        return JSONResponse(content={"error": "Evaluation not found"}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/api/save-evaluation")
async def save_evaluation(request: Request):
    try:
        data = await request.json()
        print(f"[DEBUG] Received evaluation save request: {data}")
        success = db.save_evaluation(
            application_id=data['application_id'],
            evaluator_id=data['evaluator_id'],
            scores=data['scores'],
            feedback=data['feedback'],
            overall_score=data['overall_score']
        )
        
        # Update application status if provided (Sync error is non-fatal for evaluation saving)
        if success and 'status' in data:
            try:
                db.update_application_status(data['application_id'], data['status'])
            except Exception as e:
                print(f"[SYNC ERROR] Non-fatal sync error: {e}")
                # We still return success: true because the evaluation itself was saved
            
        if success:
            return JSONResponse(content={"success": True})
        return JSONResponse(content={"error": "Failed to save evaluation"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)