from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from database import ResumeDatabase
from hr_base import app, get_current_user, get_base_html, get_end_html, send_email
from datetime import datetime, timedelta
import os

db = ResumeDatabase()

# status meta
_STATUS = {
    "pending":   ("badge-amber",   "⏳ Pending"),
    "sent":      ("badge-blue",    "📤 Sent"),
    "accepted":  ("badge-green",   "✅ Accepted"),
    "rejected":  ("badge-red",     "❌ Rejected"),
    "withdrawn": ("badge-neutral", "↩ Withdrawn"),
}
_BADGE_CSS = {
    "badge-amber":   "background:var(--amber-lt);color:#C67C00;",
    "badge-blue":    "background:var(--blue-lt);color:var(--blue);",
    "badge-green":   "background:#E8F8F0;color:var(--green);",
    "badge-red":     "background:var(--red-lt);color:var(--red);",
    "badge-neutral": "background:var(--bg);color:var(--ink3);border:1px solid var(--border);",
}

def _status_chip(s: str) -> str:
    cls, lbl = _STATUS.get((s or "pending").lower(), ("badge-neutral", s or "Pending"))
    css = _BADGE_CSS.get(cls, "")
    return f'<span style="display:inline-flex;align-items:center;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700;{css}">{lbl}</span>'


@app.get("/offers", response_class=HTMLResponse)
async def offer_management(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/", status_code=302)

    applications = db.get_all_applications()
    offers       = db.get_all_offers()

    today    = datetime.now().strftime("%Y-%m-%d")
    min_start = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    shortlisted = [a for a in applications if (a.get("status") or "").lower() == "shortlisted"]
    app_opts = '<option value="">Select shortlisted applicant…</option>'
    for a in shortlisted:
        app_opts += f'<option value="{a.get("id",0)}">{a.get("applicant_name","N/A")} — {a.get("job_title","N/A")}</option>'
    if not shortlisted:
        app_opts = '<option value="">No shortlisted applicants yet</option>'

    # Stat counts
    total_offers    = len(offers) if offers else 0
    pending_cnt     = sum(1 for o in (offers or []) if (o.get("status") or "").lower() in ("pending", "sent"))
    accepted_cnt    = sum(1 for o in (offers or []) if (o.get("status") or "").lower() == "accepted")
    rejected_cnt    = sum(1 for o in (offers or []) if (o.get("status") or "").lower() == "rejected")

    # Active offers cards
    active_offers = [o for o in (offers or []) if (o.get("status") or "pending").lower() in ("pending", "sent")]
    active_html   = _build_offer_cards(active_offers)

    page = f"""
<!-- ══ PAGE HEADER ══ -->
<div class="page-hd">
  <div>
    <div class="page-title">Offer Management</div>
    <div class="page-sub">Create, send, and track job offers for shortlisted candidates.</div>
  </div>
  <button class="btn btn-primary" onclick="scrollToForm()">
    <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
      <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
    </svg>
    Create Offer
  </button>
</div>

<!-- ══ STATS ══ -->
<div class="stats-row" style="margin-bottom:24px;">
  <div class="stat-tile"><div class="stat-icon">📝</div><div class="stat-body"><div class="stat-label">Total Offers</div><div class="stat-value">{total_offers}</div></div></div>
  <div class="stat-tile"><div class="stat-icon">⏳</div><div class="stat-body"><div class="stat-label">Active / Sent</div><div class="stat-value">{pending_cnt}</div></div></div>
  <div class="stat-tile"><div class="stat-icon">✅</div><div class="stat-body"><div class="stat-label">Accepted</div><div class="stat-value">{accepted_cnt}</div></div></div>
  <div class="stat-tile"><div class="stat-icon">❌</div><div class="stat-body"><div class="stat-label">Rejected</div><div class="stat-value">{rejected_cnt}</div></div></div>
</div>

<!-- ══ TWO-COLUMN ══ -->
<div style="display:grid;grid-template-columns:1fr 300px;gap:20px;align-items:start;">

  <!-- LEFT: Create form -->
  <div class="card" id="offerForm" style="animation:fadeUp 0.3s ease both;">
    <div class="card-hd">
      <span class="card-title">
        <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
          style="vertical-align:-2px;margin-right:6px;">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        Create Offer Letter
      </span>
      <button class="btn btn-outline" style="padding:5px 12px;font-size:12px;" onclick="clearForm()">Reset</button>
    </div>
    <div class="card-bd">

      <!-- Row 1: Application + Type -->
      <div class="form-grid" style="margin-bottom:16px;">
        <div class="form-group">
          <label class="form-label">Application *</label>
          <select class="form-ctrl" id="applicationSelect" onchange="autoFill()">
            {app_opts}
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Offer Type *</label>
          <select class="form-ctrl" id="offerType" onchange="updateSalaryPlaceholder()">
            <option value="full-time">Full-time</option>
            <option value="part-time">Part-time</option>
            <option value="contract">Contract</option>
            <option value="internship">Internship</option>
          </select>
        </div>
      </div>

      <!-- Row 2: Position + Department (auto-filled) -->
      <div class="form-grid" style="margin-bottom:16px;">
        <div class="form-group">
          <label class="form-label">Position Title *</label>
          <input class="form-ctrl" type="text" id="positionTitle" placeholder="Auto-filled from application">
        </div>
        <div class="form-group">
          <label class="form-label">Department *</label>
          <input class="form-ctrl" type="text" id="department" placeholder="Auto-filled from application">
        </div>
      </div>

      <!-- Row 3: Salary + Start Date -->
      <div class="form-grid" style="margin-bottom:16px;">
        <div class="form-group">
          <label class="form-label">Salary *</label>
          <div style="position:relative;">
            <span style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--ink3);font-weight:700;">$</span>
            <input class="form-ctrl" type="text" id="salary" placeholder="e.g. 80,000 per year" style="padding-left:26px;" required>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Start Date *</label>
          <input class="form-ctrl" type="date" id="startDate" min="{min_start}" required>
        </div>
      </div>

      <!-- Row 4: Location + Reports To -->
      <div class="form-grid" style="margin-bottom:16px;">
        <div class="form-group">
          <label class="form-label">Location *</label>
          <input class="form-ctrl" type="text" id="location" placeholder="Office or Remote" required>
        </div>
        <div class="form-group">
          <label class="form-label">Reports To *</label>
          <input class="form-ctrl" type="text" id="reportingTo" placeholder="Manager name" required>
        </div>
      </div>

      <!-- Benefits + Details -->
      <div class="form-group" style="margin-bottom:16px;">
        <label class="form-label">Benefits & Perks</label>
        <textarea class="form-ctrl" id="benefits" rows="4" style="resize:vertical;"
          placeholder="Health insurance, equity, remote work, PTO…"></textarea>
      </div>
      <div class="form-group" style="margin-bottom:16px;">
        <label class="form-label">Additional Offer Details</label>
        <textarea class="form-ctrl" id="offerDetails" rows="3" style="resize:vertical;"
          placeholder="Non-compete terms, signing bonus, relocation allowance…"></textarea>
      </div>

      <!-- Response deadline -->
      <div class="form-group" style="margin-bottom:20px;">
        <label class="form-label">Response Deadline</label>
        <input class="form-ctrl" type="date" id="responseDeadline" min="{today}">
        <div style="font-size:11.5px;color:var(--ink3);margin-top:4px;">Leave blank for no deadline.</div>
      </div>

      <!-- Actions -->
      <div style="display:flex;gap:10px;flex-wrap:wrap;padding-top:18px;border-top:1px solid var(--border);">
        <button class="btn btn-primary" id="createBtn" onclick="submitOffer()">
          <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          </svg>
          <span id="createBtnLabel">Create Offer</span>
        </button>
        <button class="btn btn-outline" onclick="openPreview()">
          <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
          </svg>
          Preview Letter
        </button>
        <button class="btn btn-outline" onclick="saveDraft()">💾 Save Draft</button>
      </div>
    </div>
  </div>

  <!-- RIGHT: Stats + tips -->
  <div style="display:flex;flex-direction:column;gap:16px;">

    <!-- Acceptance rate -->
    <div class="card" style="animation:fadeUp 0.3s ease 0.08s both;">
      <div class="card-hd"><span class="card-title">Acceptance Rate</span></div>
      <div class="card-bd" style="text-align:center;padding:20px 12px;">
        <div style="position:relative;width:100px;height:100px;margin:0 auto 12px;">
          <svg viewBox="0 0 36 36" style="transform:rotate(-90deg);width:100px;height:100px;">
            <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--border)" stroke-width="3"/>
            <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--green)" stroke-width="3"
              stroke-dasharray="{int((accepted_cnt/max(total_offers,1))*100)} 100"
              stroke-linecap="round"/>
          </svg>
          <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;">
            <span style="font-family:'Sora',sans-serif;font-size:20px;font-weight:800;color:var(--ink);">
              {int((accepted_cnt/max(total_offers,1))*100)}%
            </span>
          </div>
        </div>
        <div style="font-size:12px;color:var(--ink3);">{accepted_cnt} accepted of {total_offers} total</div>
      </div>
    </div>

    <!-- Offer tips -->
    <div class="card" style="animation:fadeUp 0.3s ease 0.14s both;">
      <div class="card-hd"><span class="card-title">Offer Tips</span></div>
      <div class="card-bd" style="display:flex;flex-direction:column;gap:10px;">
        {_offer_tip("💰","Be competitive","Research market rates. Salary is the #1 reason offers are rejected.")}
        {_offer_tip("⚡","Move fast","Top candidates receive multiple offers — send within 48 hours.")}
        {_offer_tip("📅","Set a deadline","A clear response deadline creates urgency and signals respect.")}
        {_offer_tip("📞","Follow up","Send a personal call to discuss the offer before the deadline.")}
      </div>
    </div>

  </div>
</div>

<!-- ══ ACTIVE OFFERS ══ -->
<div class="card" style="margin-top:8px;animation:fadeUp 0.3s ease 0.22s both;">
  <div class="card-hd">
    <span class="card-title">Active Offers</span>
    <span class="card-tag">{len(active_offers)} active</span>
  </div>
  <div id="activeOffersList" style="padding:16px 22px;">
    {active_html if active_html else _empty_offers("No active offers","Create an offer above to get started.")}
  </div>
</div>

<!-- ══ OFFER HISTORY ══ -->
<div class="card" style="margin-top:0;animation:fadeUp 0.3s ease 0.28s both;">
  <div class="card-hd">
    <span class="card-title">Offer History</span>
    <button class="btn btn-outline" style="padding:5px 12px;font-size:12px;" onclick="loadOfferHistory()">
      <svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.94"/>
      </svg>
      Refresh
    </button>
  </div>
  <div id="offersHistory" style="padding:16px 22px;">
    <div style="text-align:center;padding:32px;">
      <div class="spin" style="margin:0 auto 10px;"></div>
      <div style="font-size:13px;color:var(--ink3);">Loading offer history…</div>
    </div>
  </div>
</div>

<!-- ══ PREVIEW MODAL ══ -->
<div id="previewModal" style="display:none;position:fixed;inset:0;background:rgba(13,14,26,0.55);
     z-index:10000;align-items:center;justify-content:center;backdrop-filter:blur(6px);">
  <div style="background:var(--white);border-radius:16px;padding:32px;max-width:680px;width:90%;
              max-height:88vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.2);position:relative;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;">
      <span style="font-family:'Sora',sans-serif;font-weight:700;font-size:16px;color:var(--ink);">📄 Offer Letter Preview</span>
      <button onclick="closePreview()" style="background:var(--bg);border:1px solid var(--border);
              border-radius:8px;width:32px;height:32px;cursor:pointer;font-size:16px;color:var(--ink2);">✕</button>
    </div>
    <div id="previewContent"></div>
  </div>
</div>

<!-- ══ VIEW OFFER MODAL ══ -->
<div id="viewOfferModal" style="display:none;position:fixed;inset:0;background:rgba(13,14,26,0.55);
     z-index:10000;align-items:center;justify-content:center;backdrop-filter:blur(6px);">
  <div style="background:var(--white);border-radius:16px;padding:32px;max-width:580px;width:90%;
              max-height:88vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.2);position:relative;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:22px;">
      <span style="font-family:'Sora',sans-serif;font-weight:700;font-size:16px;color:var(--ink);">📝 Offer Details</span>
      <button onclick="closeViewOffer()" style="background:var(--bg);border:1px solid var(--border);
              border-radius:8px;width:32px;height:32px;cursor:pointer;font-size:16px;color:var(--ink2);">✕</button>
    </div>
    <div id="viewOfferContent"></div>
  </div>
</div>

<style>
.spin {{
  width:20px;height:20px;border-radius:50%;
  border:2.5px solid var(--border);border-top-color:var(--blue);
  animation:spinA .7s linear infinite;
}}
@keyframes spinA {{to{{transform:rotate(360deg);}}}}

.offer-card {{
  display:flex;align-items:flex-start;gap:14px;
  padding:16px 18px;border-radius:12px;
  border:1.5px solid var(--border);background:var(--white);
  margin-bottom:10px;transition:all 0.15s;
  animation:fadeUp 0.3s ease both;
}}
.offer-card:hover {{ border-color:rgba(59,111,232,.3);box-shadow:var(--shadow); }}
.offer-av {{
  width:40px;height:40px;border-radius:10px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-family:'Sora',sans-serif;font-weight:800;font-size:15px;color:#fff;
}}
.offer-body {{flex:1;min-width:0;}}
.offer-name {{font-weight:700;font-size:14px;color:var(--ink);margin-bottom:3px;}}
.offer-meta {{display:flex;flex-wrap:wrap;gap:10px;font-size:12px;color:var(--ink3);margin-top:5px;}}
.offer-actions {{display:flex;gap:6px;flex-shrink:0;flex-wrap:wrap;align-self:flex-start;}}

.otip-row {{display:flex;align-items:flex-start;gap:9px;}}
.otip-icon {{font-size:15px;flex-shrink:0;margin-top:1px;}}
.otip-title {{font-size:12.5px;font-weight:700;color:var(--ink);margin-bottom:2px;}}
.otip-desc  {{font-size:11.5px;color:var(--ink3);line-height:1.45;}}

/* Detail table in view modal */
.od-table {{width:100%;border-collapse:collapse;margin-bottom:16px;}}
.od-table td {{padding:9px 0;border-bottom:1px solid var(--border);font-size:13.5px;vertical-align:top;}}
.od-table td:first-child {{
  font-weight:700;color:var(--ink2);width:120px;
  font-size:11.5px;letter-spacing:.04em;text-transform:uppercase;
}}
.od-table tr:last-child td {{border-bottom:none;}}
.od-notes {{
  background:var(--bg);border-radius:9px;padding:13px;
  font-size:13px;color:var(--ink);line-height:1.65;
  white-space:pre-wrap;border:1px solid var(--border);
  max-height:120px;overflow-y:auto;margin-top:12px;
}}
</style>

<script>
// ── AV COLOURS ────────────────────────────────────────
const AV_COLS = [
  ['#4776E6','#8E54E9'],['#F05252','#FF7B7B'],
  ['#0BB5B5','#36D1C4'],['#F4A83A','#F7CB6A'],
  ['#27AE60','#52C87A'],['#6B4FDB','#9B6FFF'],
];
function avGrad(name) {{
  const i = (name||'?').charCodeAt(0)%AV_COLS.length;
  return `linear-gradient(135deg,${{AV_COLS[i][0]}},${{AV_COLS[i][1]}})`;
}}

// ── AUTO-FILL ─────────────────────────────────────────
function autoFill() {{
  const id = document.getElementById('applicationSelect').value;
  if (!id) return;
  fetch('/api/application-details/'+id)
    .then(r=>r.json())
    .then(d=>{{
      if (d.success) {{
        const a = d.application;
        document.getElementById('positionTitle').value = a.job_title    || '';
        document.getElementById('department').value    = a.department   || '';
      }}
    }}).catch(()=>{{}});
}}

function updateSalaryPlaceholder() {{
  const t = document.getElementById('offerType').value;
  const ph = {{internship:'e.g. 2,000/month or 20/hr',contract:'e.g. 120,000/year or 75/hr',
               'part-time':'e.g. 40,000 – 60,000/year'}}[t] || 'e.g. 80,000 – 120,000/year';
  document.getElementById('salary').placeholder = ph;
}}

function scrollToForm() {{
  document.getElementById('offerForm').scrollIntoView({{behavior:'smooth',block:'start'}});
}}

// ── PREVIEW ───────────────────────────────────────────
function openPreview() {{
  const pos = gv('positionTitle');
  const sal = gv('salary');
  if (!pos || !sal) {{ showToast('Missing','Fill in Position and Salary first.','warning'); return; }}

  const today = new Date().toLocaleDateString('en-US',{{year:'numeric',month:'long',day:'numeric'}});
  const ben   = gv('benefits');
  const det   = gv('offerDetails');
  const dead  = gv('responseDeadline');
  const start = gv('startDate');

  document.getElementById('previewContent').innerHTML = `
    <div style="border:1.5px solid var(--border);border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#3B6FE8,#6B4FDB);padding:20px 24px;text-align:center;">
        <div style="font-family:'Sora',sans-serif;font-size:22px;font-weight:800;color:#fff;">ZIBITECH</div>
        <div style="font-size:12px;color:rgba(255,255,255,.7);margin-top:3px;">Confidential Offer Letter</div>
      </div>
      <div style="padding:24px 28px;background:var(--white);">
        <p style="font-size:13px;color:var(--ink3);margin-bottom:16px;">${{today}}</p>
        <p style="font-size:14px;color:var(--ink);line-height:1.7;margin-bottom:16px;">
          Dear <strong>[Applicant Name]</strong>,<br><br>
          We are delighted to offer you the position of <strong style="color:var(--blue);">${{escHtml(pos)}}</strong> at ZIBITECH.
        </p>
        <div style="background:var(--bg);border-radius:10px;padding:16px 20px;margin-bottom:16px;">
          <div style="font-family:'Sora',sans-serif;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);margin-bottom:12px;">Offer Details</div>
          ${{_dtrow2('Position',    pos)}}
          ${{_dtrow2('Department',  gv('department'))}}
          ${{_dtrow2('Type',        gv('offerType').replace('-',' ').replace(/\\b\\w/g,c=>c.toUpperCase()))}}
          ${{_dtrow2('Salary',      '$'+escHtml(gv('salary')))}}
          ${{_dtrow2('Start Date',  start||'TBD')}}
          ${{_dtrow2('Location',    gv('location')||'—')}}
          ${{_dtrow2('Reports To',  gv('reportingTo')||'—')}}
        </div>
        ${{ben?`<div style="margin-bottom:14px;"><div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);margin-bottom:6px;">Benefits & Perks</div><div style="font-size:13.5px;color:var(--ink2);white-space:pre-wrap;line-height:1.65;">${{escHtml(ben)}}</div></div>`:''}}
        ${{det?`<div style="margin-bottom:14px;"><div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);margin-bottom:6px;">Additional Terms</div><div style="font-size:13.5px;color:var(--ink2);white-space:pre-wrap;line-height:1.65;">${{escHtml(det)}}</div></div>`:''}}
        <p style="font-size:13.5px;color:var(--ink2);line-height:1.7;">
          Please respond by <strong style="color:${{dead?'var(--red)':'var(--ink)'}}">${{dead||'as soon as possible'}}</strong>.
          If you have any questions, don't hesitate to reach out.
        </p>
        <p style="margin-top:16px;font-size:13.5px;color:var(--ink2);">Best regards,<br><strong>ZIBITECH HR Team</strong></p>
      </div>
    </div>`;
  document.getElementById('previewModal').style.display = 'flex';
}}

function _dtrow2(label, val) {{
  return `<div style="display:flex;gap:8px;padding:6px 0;border-bottom:1px solid var(--border);">
    <span style="font-size:12.5px;font-weight:700;color:var(--ink2);min-width:100px;">${{label}}</span>
    <span style="font-size:13px;color:var(--ink);">${{val||'—'}}</span>
  </div>`;
}}

function closePreview() {{ document.getElementById('previewModal').style.display='none'; }}

// ── DRAFT ─────────────────────────────────────────────
const DRAFT_IDS = ['applicationSelect','offerType','positionTitle','department','salary',
  'startDate','location','reportingTo','benefits','offerDetails','responseDeadline'];

function saveDraft() {{
  const d = {{}};
  DRAFT_IDS.forEach(id => {{ const el=document.getElementById(id); if(el) d[id]=el.value; }});
  localStorage.setItem('offerDraft', JSON.stringify(d));
  showToast('Draft Saved','Form saved locally.','success',2000);
}}
function clearForm() {{
  DRAFT_IDS.forEach(id => {{ const el=document.getElementById(id); if(el) el.value=''; }});
  localStorage.removeItem('offerDraft');
  showToast('Cleared','Form reset.','info',1500);
}}

// ── SUBMIT ────────────────────────────────────────────
function gv(id) {{ return (document.getElementById(id)?.value||'').trim(); }}

function submitOffer() {{
  const required = ['applicationSelect','positionTitle','department','salary','startDate','location','reportingTo'];
  for (const id of required) {{
    if (!gv(id)) {{
      showToast('Required', id.replace(/([A-Z])/g,' $1').replace(/^./,c=>c.toUpperCase())+' is required.','warning');
      document.getElementById(id)?.focus(); return;
    }}
  }}
  const btn = document.getElementById('createBtn');
  const lbl = document.getElementById('createBtnLabel');
  btn.disabled = true;
  lbl.innerHTML = '<div class="spin" style="width:13px;height:13px;border-width:2px;border-top-color:#fff;display:inline-block;vertical-align:-2px;"></div> Creating…';

  const data = {{
    application_id:   gv('applicationSelect'),
    offer_type:       gv('offerType'),
    position_title:   gv('positionTitle'),
    department:       gv('department'),
    salary:           gv('salary'),
    start_date:       gv('startDate'),
    location:         gv('location'),
    reporting_to:     gv('reportingTo'),
    benefits:         gv('benefits'),
    offer_details:    gv('offerDetails'),
    response_deadline:gv('responseDeadline'),
  }};

  fetch('/api/create-offer', {{
    method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(data)
  }})
  .then(r=>r.json())
  .then(d=>{{
    btn.disabled=false; lbl.textContent='Create Offer';
    if (d.success) {{
      showToast('Offer Created ✓','Offer letter generated successfully.','success');
      clearForm();
      localStorage.removeItem('offerDraft');
      setTimeout(()=>location.reload(), 1300);
    }} else showToast('Error', d.error||'Failed.','error');
  }})
  .catch(err=>{{ btn.disabled=false; lbl.textContent='Create Offer'; showToast('Network Error',err.message,'error'); }});
}}

// ── VIEW OFFER ────────────────────────────────────────
function viewOffer(id) {{
  document.getElementById('viewOfferContent').innerHTML =
    '<div style="text-align:center;padding:32px;"><div class="spin" style="margin:0 auto 10px;"></div><div style="font-size:13px;color:var(--ink3);">Loading…</div></div>';
  document.getElementById('viewOfferModal').style.display = 'flex';

  fetch('/api/offer-details/'+id)
    .then(r=>r.json())
    .then(d=>{{
      if (!d.success) {{ document.getElementById('viewOfferContent').innerHTML=`<p style="color:var(--red);">${{d.error}}</p>`; return; }}
      const o = d.offer;
      const s = (o.status||'pending').toLowerCase();
      const statusMeta = {{
        pending:  ['var(--amber-lt)','#C67C00','⏳ Pending'],
        sent:     ['var(--blue-lt)','var(--blue)','📤 Sent'],
        accepted: ['#E8F8F0','var(--green)','✅ Accepted'],
        rejected: ['var(--red-lt)','var(--red)','❌ Rejected'],
        withdrawn:['var(--bg)','var(--ink3)','↩ Withdrawn'],
      }};
      const [sbg,scol,slbl] = statusMeta[s]||['var(--bg)','var(--ink3)',s];
      document.getElementById('viewOfferContent').innerHTML = `
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
          <div style="width:44px;height:44px;border-radius:11px;flex-shrink:0;
            background:${{avGrad(o.applicant_name)}};
            display:flex;align-items:center;justify-content:center;
            font-family:'Sora',sans-serif;font-weight:800;font-size:16px;color:#fff;">
            ${{(o.applicant_name||'?')[0].toUpperCase()}}
          </div>
          <div style="flex:1;">
            <div style="font-family:'Sora',sans-serif;font-weight:700;font-size:15px;color:var(--ink);">${{escHtml(o.applicant_name||'N/A')}}</div>
            <div style="font-size:12.5px;color:var(--ink3);">${{escHtml(o.position_title||'N/A')}}</div>
          </div>
          <span style="display:inline-flex;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700;background:${{sbg}};color:${{scol}};">${{slbl}}</span>
        </div>
        <table class="od-table">
          <tr><td>Position</td><td style="font-weight:600;">${{escHtml(o.position_title||'—')}}</td></tr>
          <tr><td>Department</td><td>${{escHtml(o.department||'—')}}</td></tr>
          <tr><td>Offer Type</td><td>${{escHtml(o.offer_type||'—')}}</td></tr>
          <tr><td>Salary</td><td style="font-weight:700;color:var(--blue);">${{escHtml(o.salary||'—')}}</td></tr>
          <tr><td>Start Date</td><td>${{escHtml(o.start_date||'—')}}</td></tr>
          <tr><td>Location</td><td>${{escHtml(o.location||'—')}}</td></tr>
          <tr><td>Reports To</td><td>${{escHtml(o.reporting_to||'—')}}</td></tr>
          <tr><td>Deadline</td><td>${{escHtml(o.response_deadline||'No deadline')}}</td></tr>
        </table>
        ${{o.benefits?`<div style="font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--ink3);margin-bottom:6px;">Benefits</div><div class="od-notes">${{escHtml(o.benefits)}}</div>`:''}}
        <div style="display:flex;gap:8px;margin-top:20px;flex-wrap:wrap;">
          ${{s==='pending'?`<button class="btn btn-primary" onclick="closeViewOffer();sendOffer(${{id}})">📤 Send Offer</button>`
            : s==='sent'?`<button class="btn btn-danger" onclick="closeViewOffer();withdrawOffer(${{id}})">↩ Withdraw</button>`:''}}
          <button class="btn btn-outline" onclick="closeViewOffer()">Close</button>
        </div>`;
    }})
    .catch(()=>{{ document.getElementById('viewOfferContent').innerHTML='<p style="color:var(--red);">Network error.</p>'; }});
}}
function closeViewOffer() {{ document.getElementById('viewOfferModal').style.display='none'; }}

// ── SEND / WITHDRAW / DELETE ───────────────────────────
function sendOffer(id) {{
  if (!confirm('Send this offer to the candidate now?')) return;
  fetch('/api/send-offer/'+id, {{method:'POST'}})
    .then(r=>r.json())
    .then(d=>{{ if(d.success){{ showToast('Offer Sent ✓','Email dispatched to candidate.','success'); setTimeout(()=>location.reload(),1200); }}
      else showToast('Error', d.error||'Failed.','error'); }})
    .catch(()=>showToast('Error','Network error.','error'));
}}
function withdrawOffer(id) {{
  if (!confirm('Withdraw this offer?')) return;
  fetch('/api/withdraw-offer/'+id, {{method:'POST'}})
    .then(r=>r.json())
    .then(d=>{{ if(d.success){{ showToast('Withdrawn','Offer has been withdrawn.','warning'); setTimeout(()=>location.reload(),1200); }}
      else showToast('Error', d.error||'Failed.','error'); }})
    .catch(()=>showToast('Error','Network error.','error'));
}}
function deleteOffer(id) {{
  if (!confirm('Delete this offer permanently?')) return;
  fetch('/api/delete-offer/'+id, {{method:'DELETE'}})
    .then(r=>r.json())
    .then(d=>{{ if(d.success){{ showToast('Deleted','Offer removed.','warning'); setTimeout(()=>location.reload(),1200); }}
      else showToast('Error', d.error||'Failed.','error'); }})
    .catch(()=>showToast('Error','Network error.','error'));
}}

// ── HISTORY ──────────────────────────────────────────
function loadOfferHistory() {{
  const div = document.getElementById('offersHistory');
  div.innerHTML = '<div style="text-align:center;padding:32px;"><div class="spin" style="margin:0 auto 10px;"></div><div style="font-size:13px;color:var(--ink3);">Loading…</div></div>';
  fetch('/api/offer-history')
    .then(r=>r.json())
    .then(d=>{{
      if (!d.success||!d.offers.length) {{
        div.innerHTML = `<div style="text-align:center;padding:40px;color:var(--ink3);">
          <div style="font-size:36px;margin-bottom:10px;">📝</div>
          <div style="font-family:'Sora',sans-serif;font-weight:700;font-size:14px;color:var(--ink2);">No offer history yet</div>
        </div>`; return;
      }}
      div.innerHTML = d.offers.map((o,i) => {{
        const s = (o.status||'pending').toLowerCase();
        const statusMeta = {{
          pending:  ['var(--amber-lt)','#C67C00','⏳ Pending'],
          sent:     ['var(--blue-lt)','var(--blue)','📤 Sent'],
          accepted: ['#E8F8F0','var(--green)','✅ Accepted'],
          rejected: ['var(--red-lt)','var(--red)','❌ Rejected'],
          withdrawn:['var(--bg)','var(--ink3)','↩ Withdrawn'],
        }};
        const [sbg,scol,slbl] = statusMeta[s]||['var(--bg)','var(--ink3)',s];
        return `<div class="offer-card" style="animation-delay:${{i*0.04}}s;">
          <div class="offer-av" style="background:${{avGrad(o.applicant_name||'?')}}">${{(o.applicant_name||'?')[0].toUpperCase()}}</div>
          <div class="offer-body">
            <div class="offer-name">${{escHtml(o.applicant_name||'N/A')}} — ${{escHtml(o.position_title||'N/A')}}</div>
            <div class="offer-meta">
              <span>💰 ${{escHtml(o.salary||'—')}}</span>
              <span>🏢 ${{escHtml(o.department||'—')}}</span>
              <span>📅 ${{escHtml(o.start_date||'—')}}</span>
              <span style="display:inline-flex;padding:2px 9px;border-radius:20px;font-size:11.5px;font-weight:700;background:${{sbg}};color:${{scol}};">${{slbl}}</span>
            </div>
          </div>
          <div class="offer-actions">
            <button class="btn btn-outline btn-sm" onclick="viewOffer(${{o.id}})">View</button>
            ${{s==='pending'?`<button class="btn btn-primary btn-sm" onclick="sendOffer(${{o.id}})">Send</button>`:''}}
            ${{s==='sent'?`<button class="btn btn-warn btn-sm" onclick="withdrawOffer(${{o.id}})">Withdraw</button>`:''}}
            <button class="btn btn-danger btn-sm" onclick="deleteOffer(${{o.id}})">Delete</button>
          </div>
        </div>`;
      }}).join('');
    }})
    .catch(()=>{{
      div.innerHTML='<div style="text-align:center;padding:32px;color:var(--red);">Error loading history. <button class="btn btn-outline" style="margin-top:10px;" onclick="loadOfferHistory()">Retry</button></div>';
    }});
}}

// ── UTILS ─────────────────────────────────────────────
function escHtml(s) {{
  if(!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/\'/g,'&#39;');
}}

// Backdrop close
['previewModal','viewOfferModal'].forEach(id=>{{
  document.getElementById(id).addEventListener('click', function(e){{ if(e.target===this) this.style.display='none'; }});
}});

// Init
window.addEventListener('load', () => {{
  loadOfferHistory();
  const draft = localStorage.getItem('offerDraft');
  if (draft) {{
    try {{
      const data = JSON.parse(draft);
      Object.keys(data).forEach(id => {{ const el=document.getElementById(id); if(el&&data[id]) el.value=data[id]; }});
      showToast('Draft Restored','Last saved draft loaded.','info',2500);
    }} catch(e) {{ localStorage.removeItem('offerDraft'); }}
  }}
}});
</script>
"""
    return HTMLResponse(content=get_base_html("Offer Management", "offers", current_user) + page + get_end_html())


# ── HTML HELPERS ──────────────────────────────────────────────────────────────

def _offer_tip(icon: str, title: str, desc: str) -> str:
    return f"""<div class="otip-row">
  <span class="otip-icon">{icon}</span>
  <div><div class="otip-title">{title}</div><div class="otip-desc">{desc}</div></div>
</div>"""


def _empty_offers(title: str, desc: str) -> str:
    return f"""<div style="text-align:center;padding:40px 24px;color:var(--ink3);">
  <div style="font-size:40px;margin-bottom:10px;">📝</div>
  <div style="font-family:'Sora',sans-serif;font-weight:700;font-size:14px;color:var(--ink2);">{title}</div>
  <div style="font-size:12.5px;margin-top:4px;">{desc}</div>
</div>"""

_AV_COLS = [
    ("#4776E6","#8E54E9"), ("#F05252","#FF7B7B"),
    ("#0BB5B5","#36D1C4"), ("#F4A83A","#F7CB6A"),
    ("#27AE60","#52C87A"), ("#6B4FDB","#9B6FFF"),
]
def _av_grad(name: str) -> str:
    idx = ord((name or "?")[0]) % len(_AV_COLS)
    c = _AV_COLS[idx]
    return f"linear-gradient(135deg,{c[0]},{c[1]})"


def _build_offer_cards(offers: list) -> str:
    if not offers:
        return ""
    html = ""
    for i, o in enumerate(offers):
        status = (o.get("status") or "pending").lower()
        cls, lbl = _STATUS.get(status, ("badge-neutral", status.title()))
        css = _BADGE_CSS.get(cls, "")
        name = o.get("applicant_name") or "N/A"
        delay = f"{i*0.04:.2f}"
        html += f"""<div class="offer-card" style="animation-delay:{delay}s;">
  <div class="offer-av" style="background:{_av_grad(name)};">{name[0].upper()}</div>
  <div class="offer-body">
    <div class="offer-name">{name} — {o.get('position_title','—')}</div>
    <div class="offer-meta">
      <span>💰 {o.get('salary','—')}</span>
      <span>📅 Start: {o.get('start_date','—')}</span>
      <span>📋 {(o.get('offer_type') or '').replace('-',' ').title()}</span>
      <span style="display:inline-flex;padding:2px 9px;border-radius:20px;font-size:11.5px;font-weight:700;{css}">{lbl}</span>
    </div>
  </div>
  <div class="offer-actions">
    <button class="btn btn-outline btn-sm" onclick="viewOffer({o.get('id',0)})">View</button>
    {"<button class='btn btn-primary btn-sm' onclick='sendOffer(" + str(o.get('id',0)) + ")'>📤 Send</button>" if status=="pending" else ""}
    {"<button class='btn btn-warn btn-sm' onclick='withdrawOffer(" + str(o.get('id',0)) + ")'>Withdraw</button>" if status=="sent" else ""}
    <button class="btn btn-danger btn-sm" onclick="deleteOffer({o.get('id',0)})">Delete</button>
  </div>
</div>"""
    return html


# ── BACKEND ROUTES (100% UNCHANGED) ──────────────────────────────────────────

@app.post("/api/create-offer")
async def create_offer(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        required_fields = ['application_id','position_title','department','salary','start_date','location','reporting_to','offer_type']
        for f in required_fields:
            if not data.get(f):
                return JSONResponse(content={"success": False, "error": f"Missing: {f}"}, status_code=400)
        offer_id = db.create_job_offer(
            application_id=data['application_id'], position_title=data['position_title'],
            department=data['department'], salary=data['salary'], start_date=data['start_date'],
            location=data['location'], reporting_to=data['reporting_to'], offer_type=data['offer_type'],
            benefits=data.get('benefits',''), offer_details=data.get('offer_details',''),
            response_deadline=data.get('response_deadline'), created_by=current_user)
        return JSONResponse(content={"success": True, "offer_id": offer_id})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.get("/api/offer-details/{offer_id}")
async def get_offer_details(offer_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        offer = db.get_offer_details(offer_id)
        if offer:
            return JSONResponse(content={"success": True, "offer": offer})
        return JSONResponse(content={"success": False, "error": "Offer not found"}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/send-offer/{offer_id}")
async def send_offer_route(offer_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        offer = db.get_offer_details(offer_id)
        if not offer:
            return JSONResponse(content={"success": False, "error": "Offer not found"}, status_code=404)
        application = db.get_application_details(offer.get('application_id', 0))
        if not application:
            return JSONResponse(content={"success": False, "error": "Application not found"}, status_code=404)
        success = db.update_offer_status(offer_id, 'sent')
        if not success:
            return JSONResponse(content={"success": False, "error": "Failed to update status"}, status_code=500)
        body = f"""<h2>Job Offer from ZIBITECH</h2>
        <p>Dear {application.get('applicant_name','Candidate')},</p>
        <p>We are delighted to offer you <strong>{offer.get('position_title','Position')}</strong> at ZIBITECH!</p>
        <ul>
          <li><strong>Salary:</strong> {offer.get('salary','N/A')}</li>
          <li><strong>Start Date:</strong> {offer.get('start_date','N/A')}</li>
          <li><strong>Location:</strong> {offer.get('location','N/A')}</li>
          <li><strong>Reports To:</strong> {offer.get('reporting_to','N/A')}</li>
        </ul>
        {offer.get('benefits','')}
        <p>Please respond within 7 days. We look forward to hearing from you!</p>
        <p>Best regards,<br>ZIBITECH HR Team</p>"""
        email_sent = send_email(application.get('applicant_email'),
            f"Job Offer — {offer.get('position_title','Position')} at ZIBITECH", body, is_html=True)
        if email_sent:
            return JSONResponse(content={"success": True})
        return JSONResponse(content={"success": False, "error": "Failed to send email"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/withdraw-offer/{offer_id}")
async def withdraw_offer_route(offer_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        success = db.update_offer_status(offer_id, 'withdrawn')
        return JSONResponse(content={"success": True} if success else {"success": False, "error": "Not found"})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.delete("/api/delete-offer/{offer_id}")
async def delete_offer_route(offer_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        success = db.delete_offer_letter(offer_id)
        return JSONResponse(content={"success": True} if success else {"success": False, "error": "Not found"})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.get("/api/offer-history")
async def get_offer_history(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        offers = db.get_all_offers()
        return JSONResponse(content={"success": True, "offers": offers})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


# Keep legacy POST routes for compatibility
@app.post("/api/send-offer")
async def send_offer_legacy(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        offer_id = data.get("offer_id")
        if not offer_id:
            return JSONResponse(content={"success": False, "error": "Offer ID required"}, status_code=400)
        db.update_offer_status(offer_id, 'sent')
        return JSONResponse(content={"success": True})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/withdraw-offer")
async def withdraw_offer_legacy(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        offer_id = data.get("offer_id")
        if not offer_id:
            return JSONResponse(content={"success": False, "error": "Offer ID required"}, status_code=400)
        db.update_offer_status(offer_id, 'withdrawn')
        return JSONResponse(content={"success": True})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)