from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from database import ResumeDatabase
from hr_base import app, get_current_user, get_base_html, get_end_html, send_email
from datetime import datetime, timedelta
import os

# Initialize database
db = ResumeDatabase()


@app.get("/interviews", response_class=HTMLResponse)
async def interview_scheduling(request: Request):
    """Interview scheduling page"""
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/", status_code=302)

    applications = db.get_all_applications()
    interviews   = db.get_interviews()

    today = datetime.now().strftime("%Y-%m-%d")

    # Build <option> list for applications
    app_options = '<option value="">Select applicant…</option>'
    for a in applications:
        if (a.get("status") or "").lower() == "assessment_passed":
            app_options += (
                f'<option value="{a.get("id",0)}">'
                f'{a.get("applicant_name","N/A")} — {a.get("job_title","N/A")}'
                f'</option>'
            )

    # Build interview cards (server-rendered for initial load)
    interview_cards = _build_interview_cards(interviews)

    # Stats for the header tiles
    total_iv   = len(interviews)
    upcoming   = sum(1 for iv in interviews if (iv.get("interview_date") or iv.get("scheduled_date","")) >= today)
    completed  = sum(1 for iv in interviews if iv.get("status","").lower() == "completed")
    cancelled  = sum(1 for iv in interviews if iv.get("status","").lower() == "cancelled")

    page_html = f"""
<!-- ══ PAGE HEADER ══ -->
<div class="page-hd">
  <div>
    <div class="page-title">Interview Scheduling</div>
    <div class="page-sub">Schedule, manage, and track all candidate interviews.</div>
  </div>
  <button class="btn btn-primary" onclick="scrollToForm()">
    <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
      <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
    </svg>
    Schedule Interview
  </button>
</div>

<!-- ══ STAT TILES ══ -->
<div class="stats-row" style="margin-bottom:24px;">
  <div class="stat-tile">
    <div class="stat-icon"><svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div>
    <div class="stat-body">
      <div class="stat-label">Total Scheduled</div>
      <div class="stat-value">{total_iv}</div>
    </div>
  </div>
  <div class="stat-tile">
    <div class="stat-icon"><svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M5 2h14M5 22h14M5 2a7 7 0 0 1 7 7M19 2a7 7 0 0 0-7 7M5 22a7 7 0 0 0 7-7M19 22a7 7 0 0 1-7-7"/></svg></div>
    <div class="stat-body">
      <div class="stat-label">Upcoming</div>
      <div class="stat-value">{upcoming}</div>
    </div>
  </div>
  <div class="stat-tile">
    <div class="stat-icon"><svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
    <div class="stat-body">
      <div class="stat-label">Completed</div>
      <div class="stat-value">{completed}</div>
    </div>
  </div>
  <div class="stat-tile">
    <div class="stat-icon"><svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg></div>
    <div class="stat-body">
      <div class="stat-label">Cancelled</div>
      <div class="stat-value">{cancelled}</div>
    </div>
  </div>
</div>

<!-- ══ TWO-COLUMN LAYOUT ══ -->
<div style="display:grid;grid-template-columns:1fr 320px;gap:20px;align-items:start;">

  <!-- LEFT: Schedule form -->
  <div class="card" id="scheduleForm" style="animation:fadeUp 0.35s ease both;">
    <div class="card-hd">
      <span class="card-title">
        <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
          style="vertical-align:-2px;margin-right:6px;">
          <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        <span id="formTitle">Schedule New Interview</span>
      </span>
      <button class="btn btn-outline" style="padding:5px 12px;font-size:12px;"
        id="resetFormBtn" onclick="resetForm()" style="display:none;">
        <svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <polyline points="1 4 1 10 7 10"/>
          <path d="M3.51 15a9 9 0 1 0 .49-4.94"/>
        </svg>
        Reset
      </button>
    </div>

    <div class="card-bd">
      <form id="interviewForm" autocomplete="off">
        <input type="hidden" id="editInterviewId" value="">

        <!-- Row 1: Application + Type -->
        <div class="form-grid" style="margin-bottom:16px;">
          <div class="form-group">
            <label class="form-label">Application *</label>
            <select class="form-ctrl" id="applicationSelect" name="application_id" required>
              {app_options}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Interview Type *</label>
            <select class="form-ctrl" id="interviewType" name="interview_type" required>
              <option value="phone">Phone Screen</option>
              <option value="technical">Technical Interview</option>
              <option value="behavioral">Behavioral Interview</option>
              <option value="final">Final Interview</option>
            </select>
          </div>
        </div>

        <!-- Row 2: Date + Time -->
        <div class="form-grid" style="margin-bottom:16px;">
          <div class="form-group">
            <label class="form-label">Date *</label>
            <input class="form-ctrl" type="date" id="interviewDate" name="interview_date"
              min="{today}" required>
          </div>
          <div class="form-group">
            <label class="form-label">Time *</label>
            <input class="form-ctrl" type="time" id="interviewTime" name="interview_time" required>
          </div>
        </div>

        <!-- Row 3: Duration + Interviewer -->
        <div class="form-grid" style="margin-bottom:16px;">
          <div class="form-group">
            <label class="form-label">Duration (minutes) *</label>
            <div style="position:relative;">
              <input class="form-ctrl" type="number" id="interviewDuration" name="duration"
                min="15" max="240" value="60" required style="padding-right:60px;">
              <span style="position:absolute;right:12px;top:50%;transform:translateY(-50%);
                font-size:12px;color:var(--ink3);font-weight:600;pointer-events:none;">min</span>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Interviewer Name *</label>
            <input class="form-ctrl" type="text" id="interviewerName" name="interviewer_name"
              placeholder="Full name" required>
          </div>
        </div>

        <!-- Row 4: Mode + Link -->
        <div class="form-grid" style="margin-bottom:16px;">
          <div class="form-group">
            <label class="form-label">Interview Mode *</label>
            <select class="form-ctrl" id="interviewMode" name="interview_mode" required
              onchange="updateLinkField()">
              <option value="in-person">In-Person</option>
              <option value="video">Video Call</option>
              <option value="phone">Phone Call</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label" id="linkLabel">Meeting Link / Location</label>
            <div style="position:relative;">
              <input class="form-ctrl" type="text" id="meetingLink" name="meeting_link"
                placeholder="Zoom link, Google Meet, or office location"
                style="padding-left:34px;">
              <span id="linkIcon" style="position:absolute;left:11px;top:50%;transform:translateY(-50%);
                font-size:14px;pointer-events:none;"><svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></span>
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div class="form-group" style="margin-bottom:20px;">
          <label class="form-label">Additional Notes</label>
          <textarea class="form-ctrl" id="interviewNotes" name="notes" rows="4"
            placeholder="Topics to cover, special requirements, access instructions…"
            style="resize:vertical;"></textarea>
        </div>

        <!-- Actions -->
        <div style="display:flex;gap:10px;flex-wrap:wrap;padding-top:18px;border-top:1px solid var(--border);">
          <button type="submit" id="submitBtn" class="btn btn-primary">
            <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/>
              <line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            <span id="submitLabel">Schedule Interview</span>
          </button>
          <button type="button" class="btn btn-outline" id="cancelEditBtn"
            onclick="resetForm()" style="display:none;">
            Cancel Edit
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- RIGHT: Interview tips / reminders -->
  <div style="display:flex;flex-direction:column;gap:16px;">

    <!-- Mode guide -->
    <div class="card" style="animation:fadeUp 0.35s ease 0.08s both;">
      <div class="card-hd"><span class="card-title">Mode Guide</span></div>
      <div class="card-bd" style="display:flex;flex-direction:column;gap:10px;">
        {_mode_tip("", "In-Person", "Provide exact room/building. Confirm parking if needed.", "#E8F8F0", "var(--green)")}
        {_mode_tip("", "Video Call", "Share Zoom/Meet link at least 1 hour before.", "var(--blue-lt)", "var(--blue)")}
        {_mode_tip("", "Phone", "Confirm candidate has the right number.", "var(--amber-lt)", "#C67C00")}
      </div>
    </div>

    <!-- Quick durations -->
    <div class="card" style="animation:fadeUp 0.35s ease 0.14s both;">
      <div class="card-hd"><span class="card-title">Quick Duration</span></div>
      <div class="card-bd" style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
        {_duration_btn(15,  "Quick Chat")}
        {_duration_btn(30,  "Phone Screen")}
        {_duration_btn(45,  "Behavioral")}
        {_duration_btn(60,  "Standard")}
        {_duration_btn(90,  "Technical")}
        {_duration_btn(120, "Deep Dive")}
      </div>
    </div>

  </div>
</div>

<!-- ══ VIEW / EDIT MODAL ══ -->
<div id="viewModal" style="display:none;position:fixed;inset:0;background:rgba(13,14,26,0.55);
     z-index:10000;align-items:center;justify-content:center;backdrop-filter:blur(6px);">
  <div style="background:var(--white);border-radius:16px;padding:32px;max-width:560px;width:90%;
              max-height:88vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.2);position:relative;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
      <span style="font-family:'Sora',sans-serif;font-size:16px;font-weight:700;color:var(--ink);"
        id="viewModalTitle"><svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg> Interview Details</span>
      <button onclick="closeModal()" style="background:var(--bg);border:1px solid var(--border);
              border-radius:8px;width:32px;height:32px;cursor:pointer;font-size:16px;color:var(--ink2);"><svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
    </div>
    <div id="viewModalContent"></div>
  </div>
</div>

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

<!-- ══ INTERVIEWS LIST ══ -->
<div class="card" style="margin-top:8px;animation:fadeUp 0.35s ease 0.22s both;">
  <div class="card-hd">
    <span class="card-title">
      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
        style="vertical-align:-2px;margin-right:6px;">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
      Scheduled Interviews
    </span>
    <div style="display:flex;gap:8px;align-items:center;">
      <!-- Filter tabs -->
      <div class="filter-tabs" id="filterTabs">
        <button class="ftab active" onclick="filterInterviews('all',this)">All</button>
        <button class="ftab" onclick="filterInterviews('upcoming',this)">Upcoming</button>
        <button class="ftab" onclick="filterInterviews('completed',this)">Done</button>
        <button class="ftab" onclick="filterInterviews('cancelled',this)">Cancelled</button>
      </div>
      <!-- Search -->
      <div style="position:relative;">
        <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="var(--ink3)" stroke-width="2"
          style="position:absolute;left:9px;top:50%;transform:translateY(-50%);pointer-events:none;">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input type="text" placeholder="Search…" oninput="searchInterviews(this.value)"
          style="padding:6px 12px 6px 28px;background:var(--bg);border:1.5px solid var(--border);
                 border-radius:8px;font-family:'DM Sans',sans-serif;font-size:12.5px;color:var(--ink);
                 outline:none;width:160px;transition:border-color 0.15s;"
          onfocus="this.style.borderColor='var(--blue)'" onblur="this.style.borderColor='var(--border)'">
      </div>
    </div>
  </div>
  <div id="interviewsList" style="padding:16px 22px;">
    {interview_cards}
  </div>
</div>

<!-- ══ VIEW / EDIT MODAL ══ -->
<div id="viewModal" style="display:none;position:fixed;inset:0;background:rgba(13,14,26,0.55);
     z-index:10000;align-items:center;justify-content:center;backdrop-filter:blur(6px);">
  <div style="background:var(--white);border-radius:16px;padding:32px;max-width:560px;width:90%;
              max-height:88vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.2);position:relative;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
      <span style="font-family:'Sora',sans-serif;font-size:16px;font-weight:700;color:var(--ink);"
        id="viewModalTitle"><svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg> Interview Details</span>
      <button onclick="closeModal()" style="background:var(--bg);border:1px solid var(--border);
              border-radius:8px;width:32px;height:32px;cursor:pointer;font-size:16px;color:var(--ink2);"><svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
    </div>
    <div id="viewModalContent"></div>
  </div>
</div>

<style>
/* ── Interview row cards ── */
.iv-row {{
  display:flex;align-items:flex-start;gap:14px;
  padding:16px 18px;border-radius:12px;
  border:1.5px solid var(--border);background:var(--white);
  transition:all 0.15s;margin-bottom:10px;
  animation:fadeUp 0.3s ease both;
}}
.iv-row:hover {{ border-color:rgba(59,111,232,0.3);box-shadow:var(--shadow); }}
.iv-row.is-cancelled {{ opacity:0.55; }}
.iv-avatar {{
  width:42px;height:42px;border-radius:11px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-size:18px;font-weight:800;
  font-family:'Sora',sans-serif;color:#fff;
}}
.iv-body {{ flex:1;min-width:0; }}
.iv-name {{
  font-weight:700;font-size:14px;color:var(--ink);
  margin-bottom:3px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}}
.iv-role {{ font-size:12.5px;color:var(--ink3);margin-bottom:7px; }}
.iv-chips {{ display:flex;flex-wrap:wrap;gap:7px; }}
.chip {{
  display:inline-flex;align-items:center;gap:4px;
  padding:3px 9px;border-radius:20px;font-size:11.5px;font-weight:600;
}}
.iv-actions {{ display:flex;gap:6px;flex-shrink:0;align-self:flex-start; }}

/* status chips */
.chip-upcoming   {{ background:var(--blue-lt);    color:var(--blue);   }}
.chip-completed  {{ background:#E8F8F0;            color:var(--green);  }}
.chip-cancelled  {{ background:var(--red-lt);      color:var(--red);    }}
.chip-scheduled  {{ background:var(--blue-lt);     color:var(--blue);   }}
.chip-phone      {{ background:var(--amber-lt);    color:#C67C00;       }}
.chip-technical  {{ background:#EDE9FF;            color:#6B4FDB;       }}
.chip-behavioral {{ background:var(--teal-lt);     color:var(--teal);   }}
.chip-final      {{ background:#E8F8F0;            color:var(--green);  }}
.chip-video      {{ background:var(--blue-lt);     color:var(--blue);   }}
.chip-in-person  {{ background:#E8F8F0;            color:var(--green);  }}
.chip-neutral    {{ background:var(--bg);          color:var(--ink3);border:1px solid var(--border); }}

/* duration pill buttons */
.dur-btn {{
  padding:8px 10px;border-radius:9px;border:1.5px solid var(--border);
  background:var(--white);cursor:pointer;font-family:'DM Sans',sans-serif;
  font-size:12px;font-weight:600;color:var(--ink2);transition:all 0.13s;
  text-align:center;
}}
.dur-btn:hover {{ border-color:var(--blue);background:var(--blue-lt);color:var(--blue); }}

/* Mode tip rows */
.mode-tip {{
  display:flex;align-items:flex-start;gap:10px;
  padding:10px 12px;border-radius:9px;
  border:1.5px solid var(--border);
}}
.mode-tip-icon {{
  width:30px;height:30px;border-radius:8px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;font-size:14px;
}}
.mode-tip-body {{ flex:1; }}
.mode-tip-title {{ font-size:12.5px;font-weight:700;color:var(--ink);margin-bottom:2px; }}
.mode-tip-desc  {{ font-size:11.5px;color:var(--ink3);line-height:1.45; }}

/* Detail modal table */
.iv-detail-table {{width:100%;border-collapse:collapse;margin-bottom:16px;}}
.iv-detail-table td {{
  padding:9px 0;border-bottom:1px solid var(--border);
  font-size:13.5px;vertical-align:top;
}}
.iv-detail-table td:first-child {{
  font-weight:700;color:var(--ink2);width:120px;
  font-size:11.5px;letter-spacing:0.04em;text-transform:uppercase;
}}
.iv-detail-table tr:last-child td {{border-bottom:none;}}
.notes-box {{
  background:var(--bg);border-radius:9px;padding:13px 15px;
  font-size:13px;color:var(--ink);line-height:1.65;
  border:1px solid var(--border);margin-top:12px;
  max-height:120px;overflow-y:auto;
}}

/* Loading spinner */
.spin {{
  width:20px;height:20px;border-radius:50%;
  border:2.5px solid var(--border);border-top-color:var(--blue);
  animation:spinA 0.7s linear infinite;display:inline-block;
}}
@keyframes spinA {{ to{{transform:rotate(360deg);}} }}

/* filter tabs (re-declared here just in case hr_base doesn't include them) */
.filter-tabs {{ display:flex;gap:4px; }}
.ftab {{
  padding:5px 11px;border-radius:7px;border:1.5px solid var(--border);
  font-size:12px;font-weight:600;color:var(--ink3);background:var(--white);
  cursor:pointer;transition:all 0.13s;font-family:'DM Sans',sans-serif;
}}
.ftab.active {{ border-color:var(--blue);background:var(--blue-lt);color:var(--blue); }}
</style>

<script>
// ── AVATAR COLOURS ─────────────────────────────────────
const AV_COLORS = [
  ['#4776E6','#8E54E9'],['#F05252','#FF7B7B'],
  ['#0BB5B5','#36D1C4'],['#F4A83A','#F7CB6A'],
  ['#27AE60','#52C87A'],['#6B4FDB','#9B6FFF'],
];
function avatarGrad(name) {{
  const idx = (name||'?').charCodeAt(0) % AV_COLORS.length;
  return `linear-gradient(135deg,${{AV_COLORS[idx][0]}},${{AV_COLORS[idx][1]}})`;
}}

// ── TYPE / MODE META ──────────────────────────────────
const TYPE_META = {{
  phone:      {{ cls:'chip-phone',      label:'Phone Screen',   icon:'<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.36 12a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.27 1h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 8a16 16 0 0 0 7.92 7.92l1.35-1.35a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>' }},
  technical:  {{ cls:'chip-technical',  label:'Technical',      icon:'<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>' }},
  behavioral: {{ cls:'chip-behavioral', label:'Behavioral',     icon:'<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M9 3a3 3 0 0 0-3 3 3 3 0 0 0-3 3 4 4 0 0 0 4 4h1v7h4v-7h1a4 4 0 0 0 4-4 3 3 0 0 0-3-3 3 3 0 0 0-3-3z"/></svg>' }},
  final:      {{ cls:'chip-final',      label:'Final Round',    icon:'<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>' }},
}};
const MODE_META = {{
  'in-person': {{ cls:'chip-in-person', label:'In-Person', icon:'<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>' }},
  'video':     {{ cls:'chip-video',     label:'Video Call', icon:'<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>' }},
  'phone':     {{ cls:'chip-phone',     label:'Phone Call', icon:'<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.36 12a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.27 1h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 8a16 16 0 0 0 7.92 7.92l1.35-1.35a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>' }},
}};
const STATUS_META = {{
  upcoming:  {{ cls:'chip-upcoming',  label:'Upcoming'  }},
  completed: {{ cls:'chip-completed', label:'Completed' }},
  cancelled: {{ cls:'chip-cancelled', label:'Cancelled' }},
  scheduled: {{ cls:'chip-scheduled', label:'Scheduled' }},
}};

function getType(t)   {{ return TYPE_META[t]   || {{ cls:'chip-neutral',  label:t||'—',   icon:'<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>' }}; }}
function getMode(m)   {{ return MODE_META[m]   || {{ cls:'chip-neutral',  label:m||'—',   icon:'<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>' }}; }}
function getStatus(s) {{ return STATUS_META[(s||'').toLowerCase()] || {{ cls:'chip-neutral', label:s||'Scheduled' }}; }}

// ── FORM HELPERS ───────────────────────────────────────
function scrollToForm() {{
  document.getElementById('scheduleForm').scrollIntoView({{behavior:'smooth',block:'start'}});
}}

function updateLinkField() {{
  const mode = document.getElementById('interviewMode').value;
  const icon  = document.getElementById('linkIcon');
  const label = document.getElementById('linkLabel');
  const input = document.getElementById('meetingLink');
  if (mode === 'video') {{
    icon.innerHTML  = '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>';
    label.textContent = 'Video Meeting Link *';
    input.placeholder = 'Zoom, Google Meet, or Teams link';
    input.required    = true;
  }} else if (mode === 'in-person') {{
    icon.innerHTML  = '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>';
    label.textContent = 'Office Location *';
    input.placeholder = 'Building, room number, or address';
    input.required    = true;
  }} else {{
    icon.innerHTML  = '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.36 12a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.27 1h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 8a16 16 0 0 0 7.92 7.92l1.35-1.35a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>';
    label.textContent = 'Phone Number (optional)';
    input.placeholder = 'Dial-in number (optional)';
    input.required    = false;
  }}
}}

function setDuration(mins) {{
  document.getElementById('interviewDuration').value = mins;
}}

function resetForm() {{
  document.getElementById('interviewForm').reset();
  document.getElementById('editInterviewId').value = '';
  document.getElementById('formTitle').textContent  = 'Schedule New Interview';
  document.getElementById('submitLabel').textContent = 'Schedule Interview';
  document.getElementById('submitBtn').className    = 'btn btn-primary';
  document.getElementById('cancelEditBtn').style.display = 'none';
  document.getElementById('resetFormBtn').style.display  = 'none';
  updateLinkField();
}}

// ── FILTER & SEARCH ────────────────────────────────────
let activeFilter = 'all';
const today = '{today}';

function filterInterviews(filter, btn) {{
  activeFilter = filter;
  document.querySelectorAll('.ftab').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  applyFilters();
}}

function searchInterviews(q) {{
  applyFilters(q);
}}

function applyFilters(q='') {{
  q = q.toLowerCase();
  document.querySelectorAll('.iv-row').forEach(row => {{
    const matchSearch = !q || row.textContent.toLowerCase().includes(q);
    const status = (row.dataset.status||'').toLowerCase();
    const date   = row.dataset.date || '';
    let matchFilter = true;
    if (activeFilter === 'upcoming')  matchFilter = date >= today && status !== 'cancelled' && status !== 'completed';
    if (activeFilter === 'completed') matchFilter = status === 'completed';
    if (activeFilter === 'cancelled') matchFilter = status === 'cancelled';
    row.style.display = (matchSearch && matchFilter) ? '' : 'none';
  }});
}}

// ── VIEW DETAILS MODAL ─────────────────────────────────
function viewInterview(id) {{
  const modal = document.getElementById('viewModal');
  const content = document.getElementById('viewModalContent');
  content.innerHTML = `<div style="text-align:center;padding:32px;">
    <div class="spin"></div>
    <div style="font-size:13px;color:var(--ink3);margin-top:10px;">Loading…</div>
  </div>`;
  modal.style.display = 'flex';

  fetch('/api/interview-details/' + id)
    .then(r => r.json())
    .then(d => {{
      if (!d.success) {{
        content.innerHTML = `<p style="color:var(--red);">Error: ${{d.error}}</p>`;
        return;
      }}
      const iv     = d.interview;
      const typeM  = getType(iv.interview_type);
      const modeM  = getMode(iv.interview_mode);
      const statM  = getStatus(iv.status);
      const date   = iv.interview_date || iv.scheduled_date || '—';
      const time   = iv.interview_time || iv.scheduled_time || '—';
      const linkHtml = iv.meeting_link
        ? `<a href="${{iv.meeting_link}}" target="_blank" style="color:var(--blue);font-weight:600;">
             ${{escHtml(iv.meeting_link)}}
           </a>`
        : '—';

      content.innerHTML = `
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
          <div style="width:46px;height:46px;border-radius:12px;flex-shrink:0;
            background:${{avatarGrad(iv.applicant_name)}};
            display:flex;align-items:center;justify-content:center;
            font-family:'Sora',sans-serif;font-weight:800;font-size:16px;color:#fff;">
            ${{(iv.applicant_name||'?')[0].toUpperCase()}}
          </div>
          <div>
            <div style="font-family:'Sora',sans-serif;font-weight:700;font-size:15px;color:var(--ink);">
              ${{escHtml(iv.applicant_name||'N/A')}}
            </div>
            <div style="font-size:12.5px;color:var(--ink3);">${{escHtml(iv.job_title||'N/A')}}</div>
          </div>
          <span class="chip ${{statM.cls}}" style="margin-left:auto;">${{statM.label}}</span>
        </div>
        <table class="iv-detail-table">
          <tr><td>Type</td><td><span class="chip ${{typeM.cls}}">${{typeM.icon}} ${{typeM.label}}</span></td></tr>
          <tr><td>Date</td><td style="font-weight:600;">${{date}}</td></tr>
          <tr><td>Time</td><td style="font-weight:600;">${{time}}</td></tr>
          <tr><td>Duration</td><td>${{iv.duration||60}} minutes</td></tr>
          <tr><td>Interviewer</td><td>${{escHtml(iv.interviewer_name||'—')}}</td></tr>
          <tr><td>Mode</td><td><span class="chip ${{modeM.cls}}">${{modeM.icon}} ${{modeM.label}}</span></td></tr>
          <tr><td>Link / Loc.</td><td>${{linkHtml}}</td></tr>
        </table>
        ${{iv.notes ? `<div style="font-size:11.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--ink3);margin-bottom:6px;">Notes</div>
        <div class="notes-box">${{escHtml(iv.notes)}}</div>` : ''}}
        <div style="display:flex;gap:10px;margin-top:20px;flex-wrap:wrap;">
          <button class="btn btn-primary" onclick="closeModal();editInterview(${{iv.id}})">
            <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg> Edit
          </button>
          ${{(iv.status||'').toLowerCase() !== 'cancelled'
            ? `<button class="btn btn-danger" onclick="closeModal();cancelInterview(${{iv.id}})"><svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg> Cancel</button>`
            : ''}}
          <button class="btn btn-outline" onclick="closeModal()">Close</button>
        </div>`;
    }})
    .catch(err => {{
      content.innerHTML = `<p style="color:var(--red);">Network error: ${{err.message}}</p>`;
    }});
}}

function closeModal() {{
  document.getElementById('viewModal').style.display = 'none';
}}
document.getElementById('viewModal').addEventListener('click', function(e) {{
  if (e.target === this) closeModal();
}});

// ── EDIT ──────────────────────────────────────────────
function editInterview(id) {{
  fetch('/api/interview-details/' + id)
    .then(r => r.json())
    .then(d => {{
      if (!d.success) {{ showToast('Error', d.error, 'error'); return; }}
      const iv = d.interview;
      document.getElementById('editInterviewId').value   = id;
      document.getElementById('applicationSelect').value = iv.application_id || '';
      document.getElementById('interviewType').value     = iv.interview_type  || '';
      document.getElementById('interviewDate').value     = iv.interview_date  || iv.scheduled_date || '';
      document.getElementById('interviewTime').value     = iv.interview_time  || iv.scheduled_time || '';
      document.getElementById('interviewDuration').value = iv.duration        || 60;
      document.getElementById('interviewerName').value   = iv.interviewer_name || '';
      document.getElementById('interviewMode').value     = iv.interview_mode  || 'in-person';
      document.getElementById('meetingLink').value       = iv.meeting_link    || '';
      document.getElementById('interviewNotes').value    = iv.notes           || '';

      document.getElementById('formTitle').textContent    = 'Edit Interview';
      document.getElementById('submitLabel').textContent  = 'Update Interview';
      document.getElementById('submitBtn').className      = 'btn btn-success';
      document.getElementById('cancelEditBtn').style.display = 'inline-flex';
      document.getElementById('resetFormBtn').style.display  = 'inline-flex';

      updateLinkField();
      scrollToForm();
      showToast('Edit Mode', 'Form pre-filled. Make your changes and save.', 'info', 3000);
    }})
    .catch(() => showToast('Error', 'Could not load interview.', 'error'));
}}

async function setInterviewResult(id, result) {{
  showConfirmModal({{
    title: `Mark Interview as ${{result.toUpperCase()}}?`,
    message: `Are you sure you want to mark this interview as ${{result.toUpperCase()}}? This action cannot be undone.`,
    icon: 'warning',
    confirmText: `Mark as ${{result.toUpperCase()}}`,
    confirmType: 'primary',
    onConfirm: async () => {{
      try {{
        const r = await fetch('/api/interview-result', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{ interview_id: id, result: result }})
        }});
        const d = await r.json();
        if (d.success) {{
          showToast('Success', d.message);
          closeConfirmModal();
          setTimeout(() => location.reload(), 1000);
        }} else {{
          showToast('Error', d.error, 'error');
          closeConfirmModal();
        }}
      }} catch (e) {{
        showToast('Error', e.message, 'error');
        closeConfirmModal();
      }}
    }}
  }});
}}
  try {{
    const r = await fetch('/api/interview-result', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{ interview_id: id, result: result }})
    }});
    const d = await r.json();
    if (d.success) {{
      showToast('Success', d.message);
      setTimeout(() => location.reload(), 1000);
    }} else {{
      showToast('Error', d.error, 'error');
    }}
  }} catch (e) {{
    showToast('Error', e.message, 'error');
  }}
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

// ── CANCEL ────────────────────────────────────────────
function cancelInterview(id) {{
  showConfirmModal({{
    title: 'Cancel Interview?',
    message: 'Cancel this interview? This will notify the candidate.',
    icon: 'warning',
    confirmText: 'Cancel Interview',
    confirmType: 'warning',
    onConfirm: () => {{
      fetch('/api/cancel-interview', {{
        method:'POST',
        headers:{{'Content-Type':'application/json'}},
        body: JSON.stringify({{interview_id: id}})
      }})
      .then(r => r.json())
      .then(d => {{
        if (d.success) {{
          showToast('Cancelled', 'Interview has been cancelled.', 'warning');
          closeConfirmModal();
          setTimeout(() => location.reload(), 1200);
        }} else {{
          showToast('Error', d.error || 'Could not cancel.', 'error');
          closeConfirmModal();
        }}
      }})
      .catch(() => {{
        showToast('Error', 'Network error.', 'error');
        closeConfirmModal();
      }});
    }}
  }});
}}

// ── FORM SUBMIT ────────────────────────────────────────
document.getElementById('interviewForm').addEventListener('submit', function(e) {{
  e.preventDefault();
  const editId = document.getElementById('editInterviewId').value;
  const btn    = document.getElementById('submitBtn');
  btn.disabled = true;
  btn.innerHTML = `<div class="spin" style="width:14px;height:14px;border-width:2px;border-top-color:#fff;display:inline-block;"></div> ${{editId ? 'Updating…' : 'Scheduling…'}}`;

  const data = {{
    application_id:  document.getElementById('applicationSelect').value,
    interview_type:  document.getElementById('interviewType').value,
    interview_date:  document.getElementById('interviewDate').value,
    interview_time:  document.getElementById('interviewTime').value,
    duration:        document.getElementById('interviewDuration').value,
    interviewer_name:document.getElementById('interviewerName').value,
    interview_mode:  document.getElementById('interviewMode').value,
    meeting_link:    document.getElementById('meetingLink').value,
    notes:           document.getElementById('interviewNotes').value,
  }};

  const url    = editId ? '/api/update-interview' : '/api/schedule-interview';
  if (editId) data.interview_id = editId;

  fetch(url, {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify(data),
  }})
  .then(r => r.json())
  .then(d => {{
    btn.disabled = false;
    btn.innerHTML = editId
      ? `<svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/></svg> Update Interview`
      : `<svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg> Schedule Interview`;
    if (d.success) {{
      showToast(
        editId ? 'Interview Updated' : 'Interview Scheduled',
        editId ? 'Changes saved successfully.' : 'Invitation sent to candidate.',
        'success'
      );
      resetForm();
      setTimeout(() => location.reload(), 1400);
    }} else {{
      showToast('Error', d.error || 'Request failed.', 'error');
    }}
  }})
  .catch(err => {{
    btn.disabled = false;
    showToast('Network Error', err.message, 'error');
  }});
}});

// ── UTILS ──────────────────────────────────────────────
function escHtml(s) {{
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
          .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}}
</script>
"""

    return HTMLResponse(
        content=get_base_html("Interview Scheduling", "interviews", current_user)
        + page_html
        + get_end_html()
    )


# ── HTML BUILDER HELPERS ──────────────────────────────────────────────────────

def _mode_tip(icon: str, title: str, desc: str, bg: str, color: str) -> str:
    return f"""<div class="mode-tip">
  <div class="mode-tip-icon" style="background:{bg};color:{color};">{icon}</div>
  <div class="mode-tip-body">
    <div class="mode-tip-title">{title}</div>
    <div class="mode-tip-desc">{desc}</div>
  </div>
</div>"""


def _duration_btn(mins: int, label: str) -> str:
    return f"""<button type="button" class="dur-btn" onclick="setDuration({mins})">
  <div style="font-family:'Sora',sans-serif;font-weight:800;font-size:16px;color:var(--ink);">{mins}</div>
  <div style="font-size:10.5px;color:var(--ink3);margin-top:1px;">{label}</div>
</button>"""


# Avatar gradient colours (Python-side, must match JS)
_AV_COLORS = [
    ("#4776E6", "#8E54E9"), ("#F05252", "#FF7B7B"),
    ("#0BB5B5", "#36D1C4"), ("#F4A83A", "#F7CB6A"),
    ("#27AE60", "#52C87A"), ("#6B4FDB", "#9B6FFF"),
]

def _av_grad(name: str) -> str:
    idx = ord((name or "?")[0]) % len(_AV_COLORS)
    c = _AV_COLORS[idx]
    return f"linear-gradient(135deg,{c[0]},{c[1]})"


_TYPE_CHIP = {
    "phone":      ("chip-phone",      "Phone Screen"),
    "technical":  ("chip-technical",  "Technical"),
    "behavioral": ("chip-behavioral", "Behavioral"),
    "final":      ("chip-final",      "Final Round"),
}
_MODE_CHIP = {
    "in-person":  ("chip-in-person", "In-Person"),
    "video":      ("chip-video",     "Video Call"),
    "phone":      ("chip-phone",     "Phone Call"),
}
_STATUS_CHIP = {
    "upcoming":   ("chip-upcoming",  "Upcoming"),
    "completed":  ("chip-completed", "Completed"),
    "cancelled":  ("chip-cancelled", "Cancelled"),
    "scheduled":  ("chip-scheduled", "Scheduled"),
}

def _chip(val: str, lookup: dict) -> str:
    cls, label = lookup.get((val or "").lower(), ("chip-neutral", val or "—"))
    return f'<span class="chip {cls}">{label}</span>'


def _build_interview_cards(interviews: list) -> str:
    if not interviews:
        return """<div style="text-align:center;padding:48px 24px;">
  <div style="margin-bottom:12px;"><svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div>
  <div style="font-family:'Sora',sans-serif;font-weight:700;font-size:14px;color:var(--ink2);">No interviews yet</div>
  <div style="font-size:12.5px;color:var(--ink3);margin-top:4px;">Use the form above to schedule your first interview.</div>
</div>"""

    html = ""
    for i, iv in enumerate(interviews):
        name    = iv.get("applicant_name") or "N/A"
        job     = iv.get("job_title")      or "N/A"
        date    = iv.get("interview_date") or iv.get("scheduled_date") or "—"
        time    = iv.get("interview_time") or iv.get("scheduled_time") or "—"
        dur     = iv.get("duration", 60)
        itype   = (iv.get("interview_type")  or "").lower()
        mode    = (iv.get("interview_mode")  or "").lower()
        status  = (iv.get("status")          or "scheduled").lower()
        ivid    = iv.get("id", 0)
        link    = iv.get("meeting_link", "") or ""
        interviewer = iv.get("interviewer_name") or "—"

        type_cls,   type_lbl   = _TYPE_CHIP.get(itype,   ("chip-neutral", itype or "—"))
        mode_cls,   mode_lbl   = _MODE_CHIP.get(mode,    ("chip-neutral", mode or "—"))
        status_cls, status_lbl = _STATUS_CHIP.get(status, ("chip-neutral", status.title()))

        cancelled_class = "is-cancelled" if status == "cancelled" else ""
        delay = f"{i * 0.04:.2f}"

        link_chip = (
            f'<a href="{link}" target="_blank" class="chip chip-video" '
            f'style="text-decoration:none;"><svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg> Join</a>'
            if link else ""
        )

        html += f"""<div class="iv-row {cancelled_class}" data-status="{status}" data-date="{date}"
  style="animation-delay:{delay}s;">
  <div class="iv-avatar" style="background:{_av_grad(name)};">{name[0].upper()}</div>
  <div class="iv-body">
    <div class="iv-name">{name}</div>
    <div class="iv-role">{job} · <svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg> {interviewer}</div>
    <div class="iv-chips">
      <span class="chip {type_cls}">{type_lbl}</span>
      <span class="chip {mode_cls}">{mode_lbl}</span>
      <span class="chip chip-neutral">
        <svg width="10" height="10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <rect x="3" y="4" width="18" height="18" rx="2"/>
          <line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        {date}
      </span>
      <span class="chip chip-neutral"><svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg> {time}</span>
      <span class="chip chip-neutral"><svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg> {dur}min</span>
      <span class="chip {status_cls}">{status_lbl}</span>
      {link_chip}
    </div>
  </div>
  <div class="iv-actions">
    <button class="btn btn-outline btn-sm" onclick="viewInterview({ivid})">
      <svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
      </svg>
      View
    </button>
    <button class="btn btn-outline btn-sm" onclick="editInterview({ivid})" {"disabled" if status=="cancelled" else ""}>
      <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg> Edit
    </button>
    {f'''
    <button class="btn btn-primary btn-sm" onclick="setInterviewResult({ivid}, 'pass')" style="background:#27AE60;border-color:#27AE60;">Pass</button>
    <button class="btn btn-danger btn-sm" onclick="setInterviewResult({ivid}, 'fail')">Fail</button>
    ''' if status == "scheduled" or status == "interview_scheduled" else ""}
    {"" if status=="cancelled" else f'<button class="btn btn-outline btn-sm" onclick="cancelInterview({ivid})"><svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg></button>'}
  </div>
</div>"""

    return html


# ── BACKEND ROUTES (100% UNCHANGED) ──────────────────────────────────────────

@app.post("/api/schedule-interview")
async def schedule_interview(request: Request):
    """Schedule a new interview"""
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)

    try:
        data = await request.json()

        required_fields = [
            'application_id', 'interview_type', 'interview_date',
            'interview_time', 'duration', 'interviewer_name', 'interview_mode'
        ]
        for field in required_fields:
            if not data.get(field):
                return JSONResponse(
                    content={"success": False, "error": f"Missing required field: {field}"},
                    status_code=400
                )

        interview_id = db.schedule_interview(
            application_id=data['application_id'],
            interview_type=data['interview_type'],
            interview_date=data['interview_date'],
            interview_time=data['interview_time'],
            duration=data['duration'],
            interviewer_name=data['interviewer_name'],
            interview_mode=data['interview_mode'],
            meeting_link=data.get('meeting_link', ''),
            notes=data.get('notes', '')
        )

        application = db.get_application_details(data['application_id'])
        if application:
            email_subject = f"Interview Invitation - {application.get('job_title', 'Position')}"
            email_body = f"""
            <h2>Interview Invitation</h2>
            <p>Dear {application.get('applicant_name', 'Candidate')},</p>
            <p>We are pleased to invite you for an interview for the position of
            <strong>{application.get('job_title', 'Position')}</strong>.</p>
            <p><strong>Interview Details:</strong></p>
            <ul>
                <li><strong>Type:</strong> {data['interview_type'].title()}</li>
                <li><strong>Date:</strong> {data['interview_date']}</li>
                <li><strong>Time:</strong> {data['interview_time']}</li>
                <li><strong>Duration:</strong> {data['duration']} minutes</li>
                <li><strong>Interviewer:</strong> {data['interviewer_name']}</li>
                <li><strong>Mode:</strong> {data['interview_mode'].replace('-', ' ').title()}</li>
            """
            if data.get('meeting_link'):
                if data['interview_mode'] == 'video':
                    email_body += f"<li><strong>Video Link:</strong> <a href='{data['meeting_link']}'>Join Interview</a></li>"
                else:
                    email_body += f"<li><strong>Location:</strong> {data['meeting_link']}</li>"
            email_body += f"""
            </ul>
            {data.get('notes', '')}
            <p>Please confirm your attendance by replying to this email.</p>
            <p>We look forward to speaking with you!</p>
            <p>Best regards,<br>ZIBITECH HR Team</p>
            """
            send_email(application.get('applicant_email'), email_subject, email_body, is_html=True)

        return JSONResponse(content={
            "success": True,
            "message": "Interview scheduled successfully",
            "interview_id": interview_id
        })

    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.get("/api/interview-details/{interview_id}")
async def get_interview_details(interview_id: int, request: Request):
    """Get details for a specific interview"""
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)

    try:
        interviews = db.get_interviews()
        interview = next((iv for iv in interviews if iv.get('id') == interview_id), None)
        if interview:
            return JSONResponse(content={"success": True, "interview": interview})
        else:
            return JSONResponse(content={"success": False, "error": "Interview not found"}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/update-interview")
async def update_interview(request: Request):
    """Update an existing interview"""
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)

    try:
        data = await request.json()
        interview_id = data.get("interview_id")
        if not interview_id:
            return JSONResponse(content={"success": False, "error": "Interview ID required"}, status_code=400)

        success = db.update_interview(
            interview_id=interview_id,
            interview_type=data.get("interview_type"),
            scheduled_date=data.get("interview_date") or data.get("scheduled_date"),
            scheduled_time=data.get("interview_time") or data.get("scheduled_time"),
            duration=data.get("duration"),
            interviewer_name=data.get("interviewer_name"),
            interview_mode=data.get("interview_mode"),
            meeting_link=data.get("meeting_link"),
            location=data.get("location"),
            notes=data.get("notes")
        )

        if success:
            return JSONResponse(content={"success": True, "message": "Interview updated successfully"})
        else:
            return JSONResponse(content={"success": False, "error": "Failed to update interview"}, status_code=500)

    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/interview-result")
async def set_interview_result(request: Request):
    """Mark interview as pass or fail"""
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)

    try:
        data = await request.json()
        interview_id = data.get("interview_id")
        result = data.get("result") # 'pass' or 'fail'

        if not interview_id or not result:
            return JSONResponse(content={"success": False, "error": "Missing ID or result"}, status_code=400)

        interviews = db.get_interviews()
        interview = next((iv for iv in interviews if iv.get('id') == interview_id), None)
        if not interview:
            return JSONResponse(content={"success": False, "error": "Interview not found"}, status_code=404)

        application_id = interview.get('application_id')
        new_status = 'interview_passed' if result == 'pass' else 'interview_failed'
        
        # Update application status
        db.update_application_status(application_id, new_status)
        
        # Update interview status to 'completed'
        db.update_interview_status(interview_id, 'completed')

        return JSONResponse(content={
            "success": True, 
            "message": f"Interview marked as {result.upper()}. Candidate is now {new_status.replace('_', ' ')}."
        })

    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/cancel-interview")
async def cancel_interview(request: Request):
    """Cancel an interview"""
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)

    try:
        data = await request.json()
        interview_id = data.get("interview_id")
        if not interview_id:
            return JSONResponse(content={"success": False, "error": "Interview ID required"}, status_code=400)

        db.cancel_interview(interview_id)
        return JSONResponse(content={"success": True, "message": "Interview cancelled successfully"})

    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    print("Starting HR Interview Scheduling  →  http://localhost:8003/interviews")
    uvicorn.run(app, host="0.0.0.0", port=8003)