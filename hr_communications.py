from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from database import ResumeDatabase
from hr_base import app, get_current_user, get_base_html, get_end_html, send_email
import os

# Initialize database
db = ResumeDatabase()

@app.get("/communications", response_class=HTMLResponse)
async def communications(request: Request):
    """Communication page for sending emails and messages"""
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/", status_code=302)

    applications = db.get_all_applications()
    app_id = request.query_params.get("app_id")

    # Build application <option> list
    app_options = '<option value="">Select applicant…</option>'
    for a in applications:
        selected = "selected" if app_id and str(a.get("id", 0)) == app_id else ""
        app_options += (
            f'<option value="{a.get("id",0)}" {selected}>'
            f'{a.get("applicant_name","N/A")} — {a.get("job_title","N/A")}'
            f'</option>'
        )

    page_html = f"""
<!-- ══ PAGE HEADER ══ -->
<div class="page-hd">
  <div>
    <div class="page-title">Communications</div>
    <div class="page-sub">Compose emails, load templates, and review your send history.</div>
  </div>
  <div style="display:flex;gap:10px;">
    <button class="btn btn-outline" onclick="clearDraft()">
      <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.94"/></svg>
      Clear Draft
    </button>
    <button class="btn btn-primary" onclick="document.getElementById('sendBtn').click()">
      <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      Send Email
    </button>
  </div>
</div>

<!-- ══ TWO-COLUMN LAYOUT ══ -->
<div style="display:grid;grid-template-columns:1fr 340px;gap:20px;align-items:start;">

  <!-- LEFT: Compose card -->
  <div class="comm-compose card" style="animation:fadeUp 0.35s ease both;">
    <div class="card-hd">
      <span class="card-title">
        <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="vertical-align:-2px;margin-right:6px;"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
        Compose Message
      </span>
      <span class="card-tag" id="charCount">0 chars</span>
    </div>
    <div class="card-bd">
      <form id="communicationForm" autocomplete="off">

        <!-- Row 1: Application + Email -->
        <div class="form-grid" style="margin-bottom:16px;">
          <div class="form-group">
            <label class="form-label">Application *</label>
            <select class="form-ctrl" id="applicationSelect" name="application_id" required onchange="updateRecipientEmail()">
              {app_options}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Recipient Email *</label>
            <div style="position:relative;">
              <input class="form-ctrl" type="email" id="recipientEmail" name="recipient_email"
                required readonly placeholder="Auto-filled from application"
                style="padding-left:36px;background:var(--bg);cursor:default;">
              <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="var(--ink3)" stroke-width="2"
                style="position:absolute;left:11px;top:50%;transform:translateY(-50%);pointer-events:none;">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- Row 2: Type + Subject -->
        <div class="form-grid" style="margin-bottom:16px;">
          <div class="form-group">
            <label class="form-label">Message Type *</label>
            <select class="form-ctrl" id="messageType" name="message_type" required onchange="updateEmailTemplate()">
              <option value="update">Status Update</option>
              <option value="interview">Interview Invitation</option>
              <option value="rejection">Rejection</option>
              <option value="offer">Job Offer</option>
              <option value="general">General</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Subject *</label>
            <input class="form-ctrl" type="text" id="subject" name="subject" required
              placeholder="Enter email subject…">
          </div>
        </div>

        <!-- Message body -->
        <div class="form-group" style="margin-bottom:16px;">
          <label class="form-label">Message *</label>
          <textarea class="form-ctrl" id="emailBody" name="email_body" rows="12" required
            placeholder="Type your message here…"
            style="font-size:13.5px;line-height:1.65;resize:vertical;"
            oninput="updateCharCount()"></textarea>
        </div>

        <!-- CC myself -->
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:20px;">
          <input type="checkbox" id="sendCopy" name="send_copy"
            style="width:16px;height:16px;accent-color:var(--blue);cursor:pointer;">
          <label for="sendCopy" style="font-size:13px;color:var(--ink2);cursor:pointer;font-weight:500;">
            Send a copy to myself
          </label>
        </div>

        <!-- Actions -->
        <div style="display:flex;gap:10px;flex-wrap:wrap;padding-top:18px;border-top:1px solid var(--border);">
          <button type="submit" id="sendBtn" class="btn btn-primary">
            <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            Send Email
          </button>
          <button type="button" class="btn btn-outline" onclick="previewEmail()">
            <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            Preview
          </button>
          <button type="button" class="btn btn-outline" onclick="saveDraft()">
            <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
            Save Draft
          </button>
        </div>

      </form>
    </div>
  </div>

  <!-- RIGHT: Templates + Stats -->
  <div style="display:flex;flex-direction:column;gap:16px;">

    <!-- Templates -->
    <div class="card" style="animation:fadeUp 0.35s ease 0.08s both;">
      <div class="card-hd">
        <span class="card-title">Quick Templates</span>
      </div>
      <div class="card-bd" style="display:flex;flex-direction:column;gap:8px;">
        {_template_btn("interview",  "📅", "Interview Invite",  "var(--blue-lt)",   "var(--blue)")}
        {_template_btn("rejection",  "❌", "Rejection",         "var(--red-lt)",    "var(--red)")}
        {_template_btn("offer",      "🎉", "Job Offer",         "#E8F8F0",          "var(--green)")}
        {_template_btn("followup",   "🔄", "Follow-up",         "var(--amber-lt)",  "#C67C00")}
        {_template_btn("welcome",    "👋", "Welcome Aboard",    "var(--teal-lt)",   "var(--teal)")}
      </div>
    </div>

    <!-- Quick stats -->
    <div class="card" style="animation:fadeUp 0.35s ease 0.14s both;">
      <div class="card-hd"><span class="card-title">This Session</span></div>
      <div class="card-bd" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
        <div style="background:var(--blue-lt);border-radius:10px;padding:14px;text-align:center;">
          <div style="font-family:'Sora',sans-serif;font-size:24px;font-weight:800;color:var(--blue);" id="statSent">—</div>
          <div style="font-size:11px;color:var(--ink3);font-weight:600;margin-top:3px;">Total Sent</div>
        </div>
        <div style="background:#E8F8F0;border-radius:10px;padding:14px;text-align:center;">
          <div style="font-family:'Sora',sans-serif;font-size:24px;font-weight:800;color:var(--green);" id="statTypes">—</div>
          <div style="font-size:11px;color:var(--ink3);font-weight:600;margin-top:3px;">Types Used</div>
        </div>
      </div>
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

<!-- ══ HISTORY PANEL ══ -->
<div class="card" style="margin-top:8px;animation:fadeUp 0.35s ease 0.2s both;">
  <div class="card-hd">
    <span class="card-title">
      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
        style="vertical-align:-2px;margin-right:6px;"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      Sent Communications
    </span>
    <div style="display:flex;gap:8px;align-items:center;">
      <div style="position:relative;">
        <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="var(--ink3)" stroke-width="2"
          style="position:absolute;left:9px;top:50%;transform:translateY(-50%);pointer-events:none;">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input type="text" placeholder="Search history…" oninput="filterHistory(this.value)"
          style="padding:6px 12px 6px 30px;background:var(--bg);border:1.5px solid var(--border);
                 border-radius:8px;font-family:'DM Sans',sans-serif;font-size:12.5px;
                 color:var(--ink);outline:none;width:200px;transition:border-color 0.15s;"
          onfocus="this.style.borderColor='var(--blue)'" onblur="this.style.borderColor='var(--border)'">
      </div>
      <button class="btn btn-outline" style="padding:6px 12px;font-size:12px;" onclick="loadCommunicationHistory()">
        <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.94"/></svg>
        Refresh
      </button>
    </div>
  </div>
  <div id="communicationsHistory" style="padding:20px 22px;">
    <div class="history-loading">
      <div class="loading-spinner"></div>
      <span style="font-size:13px;color:var(--ink3);">Loading history…</span>
    </div>
  </div>
</div>

<!-- ══ PREVIEW MODAL ══ -->
<div id="previewModal" style="display:none;position:fixed;inset:0;background:rgba(13,14,26,0.55);
     z-index:10000;display:none;align-items:center;justify-content:center;backdrop-filter:blur(6px);">
  <div style="background:var(--white);border-radius:16px;padding:32px;max-width:640px;width:90%;
              max-height:85vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.2);position:relative;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
      <span style="font-family:'Sora',sans-serif;font-size:16px;font-weight:700;color:var(--ink);">📧 Email Preview</span>
      <button onclick="closePreview()" style="background:var(--bg);border:1px solid var(--border);
              border-radius:8px;width:32px;height:32px;cursor:pointer;font-size:16px;color:var(--ink2);">✕</button>
    </div>
    <div id="previewContent"></div>
  </div>
</div>

<!-- ══ VIEW COMM MODAL ══ -->
<div id="viewCommModal" style="display:none;position:fixed;inset:0;background:rgba(13,14,26,0.55);
     z-index:10000;align-items:center;justify-content:center;backdrop-filter:blur(6px);">
  <div style="background:var(--white);border-radius:16px;padding:32px;max-width:640px;width:90%;
              max-height:85vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.2);position:relative;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
      <span style="font-family:'Sora',sans-serif;font-size:16px;font-weight:700;color:var(--ink);">📨 Message Details</span>
      <button onclick="closeViewComm()" style="background:var(--bg);border:1px solid var(--border);
              border-radius:8px;width:32px;height:32px;cursor:pointer;font-size:16px;color:var(--ink2);">✕</button>
    </div>
    <div id="viewCommContent"></div>
  </div>
</div>

<style>
/* ── Extra page-level styles ── */
.history-loading {{
  display:flex;align-items:center;justify-content:center;gap:10px;padding:48px;
}}
.loading-spinner {{
  width:20px;height:20px;border-radius:50%;
  border:2.5px solid var(--border);
  border-top-color:var(--blue);
  animation:spin 0.7s linear infinite;
}}
@keyframes spin {{ to{{transform:rotate(360deg);}} }}

.comm-row {{
  display:flex;align-items:flex-start;gap:14px;
  padding:16px 18px;border-radius:12px;
  border:1.5px solid var(--border);background:var(--white);
  transition:all 0.15s;cursor:default;
  animation:fadeUp 0.3s ease both;
  margin-bottom:10px;
}}
.comm-row:hover {{ border-color:rgba(59,111,232,0.3);box-shadow:var(--shadow); }}
.comm-type-icon {{
  width:40px;height:40px;border-radius:10px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-size:18px;
}}
.comm-meta {{flex:1;min-width:0;}}
.comm-subject {{
  font-weight:700;font-size:14px;color:var(--ink);
  margin-bottom:4px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}}
.comm-detail-row {{
  display:flex;flex-wrap:wrap;gap:10px;
  font-size:12px;color:var(--ink3);margin-top:5px;
}}
.comm-detail-row span {{display:flex;align-items:center;gap:4px;}}
.comm-actions {{display:flex;gap:6px;flex-shrink:0;}}

.type-chip {{
  display:inline-flex;align-items:center;padding:3px 9px;
  border-radius:20px;font-size:11.5px;font-weight:700;
}}

/* Preview content */
.preview-envelope {{
  background:var(--bg);border-radius:12px;padding:20px;
  border:1px solid var(--border);
}}
.preview-field {{
  display:flex;gap:8px;margin-bottom:10px;font-size:13.5px;
}}
.preview-field-label {{
  font-weight:700;color:var(--ink2);min-width:64px;flex-shrink:0;
}}
.preview-divider {{
  height:1px;background:var(--border);margin:16px 0;
}}
.preview-body {{
  font-size:13.5px;color:var(--ink);line-height:1.7;
  white-space:pre-wrap;background:var(--white);
  padding:16px;border-radius:9px;border:1px solid var(--border);
}}

/* View comm details */
.detail-table {{width:100%;border-collapse:collapse;margin-bottom:16px;}}
.detail-table td {{padding:9px 0;border-bottom:1px solid var(--border);font-size:13.5px;vertical-align:top;}}
.detail-table td:first-child {{
  font-weight:700;color:var(--ink2);width:110px;
  font-size:11.5px;letter-spacing:0.04em;text-transform:uppercase;
}}
.detail-table tr:last-child td {{border-bottom:none;}}
.message-body-box {{
  background:var(--bg);border-radius:10px;padding:16px;
  font-size:13.5px;color:var(--ink);line-height:1.7;
  white-space:pre-wrap;max-height:260px;overflow-y:auto;
  border:1px solid var(--border);
}}

/* Template buttons */
.tpl-btn {{
  display:flex;align-items:center;gap:10px;
  padding:11px 14px;border-radius:10px;
  border:1.5px solid var(--border);background:var(--white);
  cursor:pointer;font-family:'DM Sans',sans-serif;
  font-size:13px;font-weight:600;color:var(--ink2);
  transition:all 0.15s;text-align:left;width:100%;
}}
.tpl-btn:hover {{
  border-color:var(--blue);background:var(--blue-lt);color:var(--blue);
  transform:translateX(3px);
}}
.tpl-btn:hover .tpl-icon {{ background:var(--blue);color:#fff; }}
.tpl-icon {{
  width:30px;height:30px;border-radius:8px;
  display:flex;align-items:center;justify-content:center;
  font-size:14px;transition:all 0.15s;flex-shrink:0;
}}
</style>

<script>
// ── TEMPLATE DATA ──────────────────────────────────────
const emailTemplates = {{
  interview: {{
    subject: "Interview Invitation - [Job Title]",
    body: `Dear [Applicant Name],

We are pleased to invite you for an interview for the position of [Job Title].

Interview Details:
- Type: [Interview Type]
- Date: [Date]
- Time: [Time]
- Duration: [Duration] minutes
- Interviewer: [Interviewer Name]
- Mode: [Interview Mode]

[Meeting Link/Location Information]

Please confirm your attendance by replying to this email.

We look forward to speaking with you!

Best regards,
ZIBITECH HR Team`
  }},
  rejection: {{
    subject: "Update on your application for [Job Title]",
    body: `Dear [Applicant Name],

Thank you for your interest in the [Job Title] position at ZIBITECH.

After careful consideration of your application and qualifications, we have decided not to proceed with your candidacy at this time.

We appreciate the time you invested in applying and wish you the best in your job search.

Best regards,
ZIBITECH HR Team`
  }},
  offer: {{
    subject: "Job Offer - [Job Title] at ZIBITECH",
    body: `Dear [Applicant Name],

We are delighted to offer you the position of [Job Title] at ZIBITECH!

Offer Details:
- Position: [Job Title]
- Department: [Department]
- Start Date: [Start Date]
- Salary: [Salary]
- Location: [Location]

Please review this offer and let us know your decision within [Timeframe].

We are excited about the possibility of you joining our team!

Best regards,
ZIBITECH HR Team`
  }},
  followup: {{
    subject: "Following up on your application",
    body: `Dear [Applicant Name],

I hope this email finds you well.

I'm following up on your recent application for the [Job Title] position. We wanted to let you know that your application is still under consideration.

We appreciate your patience and will update you as soon as we have more information.

If you have any questions in the meantime, please don't hesitate to reach out.

Best regards,
ZIBITECH HR Team`
  }},
  welcome: {{
    subject: "Welcome to ZIBITECH!",
    body: `Dear [Applicant Name],

Welcome to the ZIBITECH team!

We are thrilled to have you join us as [Job Title]. Your first day will be [Start Date].

Onboarding Details:
- Reporting Time: [Time]
- Location: [Address/Building]
- Dress Code: [Dress Code]
- What to Bring: [List of items]

Your first week will include:
- Orientation session
- Team introductions
- System setup
- Initial training

We look forward to welcoming you aboard!

Best regards,
ZIBITECH HR Team`
  }}
}};

// ── TYPE META (colours, icons, labels) ─────────────────
const TYPE_META = {{
  interview:  {{ bg:'var(--blue-lt)',  color:'var(--blue)',  icon:'📅', label:'Interview'  }},
  rejection:  {{ bg:'var(--red-lt)',   color:'var(--red)',   icon:'❌', label:'Rejection'  }},
  offer:      {{ bg:'#E8F8F0',         color:'var(--green)', icon:'🎉', label:'Offer'       }},
  general:    {{ bg:'var(--bg)',        color:'var(--ink3)',  icon:'💬', label:'General'     }},
  update:     {{ bg:'var(--amber-lt)', color:'#C67C00',      icon:'🔔', label:'Update'      }},
  followup:   {{ bg:'var(--teal-lt)',  color:'var(--teal)',  icon:'🔄', label:'Follow-up'   }},
  welcome:    {{ bg:'var(--teal-lt)',  color:'var(--teal)',  icon:'👋', label:'Welcome'     }},
}};

function getTypeMeta(type) {{
  return TYPE_META[type] || {{ bg:'var(--bg)', color:'var(--ink3)', icon:'📧', label:type }};
}}

// ── CHAR COUNT ─────────────────────────────────────────
function updateCharCount() {{
  const len = document.getElementById('emailBody').value.length;
  document.getElementById('charCount').textContent = len.toLocaleString() + ' chars';
}}

// ── EMAIL FETCH ────────────────────────────────────────
function updateRecipientEmail() {{
  const appSelect = document.getElementById('applicationSelect');
  const recipientEmail = document.getElementById('recipientEmail');
  if (appSelect.value) {{
    fetch('/api/application-email/' + appSelect.value)
      .then(r => r.json())
      .then(d => {{
        recipientEmail.value = d.success ? d.email : '';
        if (!d.success) showToast('Warning', 'Could not fetch applicant email.', 'warning');
      }})
      .catch(() => {{ recipientEmail.value = ''; }});
  }} else {{
    recipientEmail.value = '';
  }}
}}

// ── TEMPLATE AUTO-FILL ─────────────────────────────────
function updateEmailTemplate() {{
  const messageType = document.getElementById('messageType').value;
  const applicationId = document.getElementById('applicationSelect').value;
  const subject = document.getElementById('subject');
  const emailBody = document.getElementById('emailBody');

  if (applicationId && emailTemplates[messageType]) {{
    fetch('/api/application-details/' + applicationId)
      .then(r => r.json())
      .then(d => {{
        if (d.success) {{
          const a = d.application;
          let s = emailTemplates[messageType].subject;
          let b = emailTemplates[messageType].body;
          s = s.replace(/[[]Job Title[]]/g,      a.job_title       || 'N/A');
          s = s.replace(/[[]Applicant Name[]]/g, a.applicant_name  || 'Candidate');
          b = b.replace(/[[]Applicant Name[]]/g, a.applicant_name  || 'Candidate');
          b = b.replace(/[[]Job Title[]]/g,      a.job_title       || 'N/A');
          b = b.replace(/[[]Department[]]/g,     a.department      || 'N/A');
          b = b.replace(/[[]Application Date[]]/g, a.application_date || 'N/A');
          if (messageType === 'interview') {{
            b = b.replace('[Date]',             'TBD - Please schedule');
            b = b.replace('[Time]',             'TBD - Please schedule');
            b = b.replace('[Duration]',         '60');
            b = b.replace('[Interview Type]',   'Technical Interview');
            b = b.replace('[Interviewer Name]', 'Hiring Manager');
            b = b.replace('[Interview Mode]',   'Video Call');
            b = b.replace('[Meeting Link/Location Information]', 'Meeting link will be sent after scheduling');
          }}
          if (messageType === 'offer') {{
            b = b.replace('[Start Date]', 'TBD');
            b = b.replace('[Salary]',     'Competitive');
            b = b.replace('[Location]',   'Office Location');
            b = b.replace('[Timeframe]',  '7 days');
          }}
          subject.value  = s;
          emailBody.value = b;
          updateCharCount();
        }}
      }})
      .catch(() => {{
        subject.value   = emailTemplates[messageType].subject;
        emailBody.value = emailTemplates[messageType].body;
        updateCharCount();
      }});
  }} else if (emailTemplates[messageType]) {{
    subject.value   = emailTemplates[messageType].subject;
    emailBody.value = emailTemplates[messageType].body;
    updateCharCount();
  }}
}}

function loadTemplate(name) {{
  if (emailTemplates[name]) {{
    document.getElementById('subject').value    = emailTemplates[name].subject;
    document.getElementById('emailBody').value  = emailTemplates[name].body;
    document.getElementById('messageType').value = name in ['interview','rejection','offer','general','update'] ? name : 'general';
    updateCharCount();
    showToast('Template Loaded', `"${{name}}" template applied.`, 'info', 2500);
  }}
}}

// ── PREVIEW ────────────────────────────────────────────
function previewEmail() {{
  const subject   = document.getElementById('subject').value;
  const body      = document.getElementById('emailBody').value;
  const recipient = document.getElementById('recipientEmail').value;
  if (!subject || !body || !recipient) {{
    showToast('Missing Fields', 'Please fill subject, message and select an applicant.', 'warning');
    return;
  }}
  document.getElementById('previewContent').innerHTML = `
    <div class="preview-envelope">
      <div class="preview-field"><span class="preview-field-label">To</span><span style="color:var(--blue);font-weight:600;">${{recipient}}</span></div>
      <div class="preview-field"><span class="preview-field-label">Subject</span><span style="font-weight:600;color:var(--ink);">${{escapeHtml(subject)}}</span></div>
    </div>
    <div class="preview-divider"></div>
    <div class="preview-body">${{escapeHtml(body)}}</div>`;
  const modal = document.getElementById('previewModal');
  modal.style.display = 'flex';
}}
function closePreview() {{ document.getElementById('previewModal').style.display = 'none'; }}

// ── DRAFT ──────────────────────────────────────────────
function saveDraft() {{
  const data = {{
    application_id:  document.getElementById('applicationSelect').value,
    recipient_email: document.getElementById('recipientEmail').value,
    message_type:    document.getElementById('messageType').value,
    subject:         document.getElementById('subject').value,
    email_body:      document.getElementById('emailBody').value,
    send_copy:       document.getElementById('sendCopy').checked,
  }};
  localStorage.setItem('emailDraft', JSON.stringify(data));
  showToast('Draft Saved', 'Your draft has been saved locally.', 'success', 2500);
}}
function clearDraft() {{
  localStorage.removeItem('emailDraft');
  document.getElementById('communicationForm').reset();
  document.getElementById('charCount').textContent = '0 chars';
  showToast('Cleared', 'Draft and form cleared.', 'info', 2000);
}}

// ── HISTORY ────────────────────────────────────────────
function filterHistory(q) {{
  q = q.toLowerCase();
  document.querySelectorAll('.comm-row').forEach(r => {{
    r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}}

function loadCommunicationHistory() {{
  const div = document.getElementById('communicationsHistory');
  div.innerHTML = `<div class="history-loading"><div class="loading-spinner"></div><span style="font-size:13px;color:var(--ink3);">Loading history…</span></div>`;

  fetch('/api/communication-history')
    .then(r => r.json())
    .then(d => {{
      if (!d.success) {{
        div.innerHTML = `<div style="text-align:center;padding:48px 24px;">
          <div style="font-size:36px;margin-bottom:10px;">⚠️</div>
          <div style="font-family:'Sora',sans-serif;font-weight:700;font-size:14px;color:var(--ink2);">Error loading history</div>
          <div style="font-size:12.5px;color:var(--ink3);margin-top:4px;">${{d.error || 'Unknown error'}}</div>
          <button class="btn btn-outline" style="margin-top:16px;padding:7px 16px;font-size:12.5px;" onclick="loadCommunicationHistory()">Try Again</button>
        </div>`;
        return;
      }}

      const comms = d.communications;

      // Update stats
      document.getElementById('statSent').textContent  = comms.length;
      const types = new Set(comms.map(c => c.message_type));
      document.getElementById('statTypes').textContent = types.size;

      if (!comms.length) {{
        div.innerHTML = `<div style="text-align:center;padding:48px 24px;">
          <div style="font-size:40px;margin-bottom:10px;">✉️</div>
          <div style="font-family:'Sora',sans-serif;font-weight:700;font-size:14px;color:var(--ink2);">No messages sent yet</div>
          <div style="font-size:12.5px;color:var(--ink3);margin-top:4px;">Compose your first message above.</div>
        </div>`;
        return;
      }}

      div.innerHTML = comms.map((c, i) => {{
        const meta = getTypeMeta(c.message_type || 'general');
        const sentAt = c.sent_at ? new Date(c.sent_at).toLocaleString('en-US',
          {{month:'short',day:'numeric',year:'numeric',hour:'2-digit',minute:'2-digit'}}) : '—';
        const snippet = (c.message || '').replace(/<[^>]*>/g,'').substring(0, 90);
        return `
          <div class="comm-row" data-searchable style="animation-delay:${{i * 0.04}}s;">
            <div class="comm-type-icon" style="background:${{meta.bg}};color:${{meta.color}};">${{meta.icon}}</div>
            <div class="comm-meta">
              <div class="comm-subject">${{escapeHtml(c.subject || 'No Subject')}}</div>
              <div style="font-size:12.5px;color:var(--ink3);margin-top:2px;">${{escapeHtml(snippet)}}${{snippet.length===90?'…':''}}</div>
              <div class="comm-detail-row">
                <span>
                  <svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                  ${{escapeHtml(c.recipient_email || '—')}}
                </span>
                <span>
                  <svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
                  ${{escapeHtml(c.applicant_name || '—')}}
                </span>
                <span>
                  <svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  ${{sentAt}}
                </span>
                <span>
                  <span class="type-chip" style="background:${{meta.bg}};color:${{meta.color}};">${{meta.label}}</span>
                </span>
              </div>
            </div>
            <div class="comm-actions">
              <button class="btn btn-outline btn-sm" onclick="viewCommunication(${{c.id}})">
                <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                View
              </button>
              <button class="btn btn-danger btn-sm" onclick="deleteCommunication(${{c.id}})">
                <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
                Delete
              </button>
            </div>
          </div>`;
      }}).join('');
    }})
    .catch(err => {{
      div.innerHTML = `<div style="text-align:center;padding:48px 24px;">
        <div style="font-size:36px;margin-bottom:10px;">🔌</div>
        <div style="font-family:'Sora',sans-serif;font-weight:700;font-size:14px;color:var(--ink2);">Connection error</div>
        <div style="font-size:12.5px;color:var(--ink3);margin-top:4px;">${{err.message}}</div>
        <button class="btn btn-outline" style="margin-top:16px;padding:7px 16px;font-size:12.5px;" onclick="loadCommunicationHistory()">Retry</button>
      </div>`;
    }});
}}

// ── DELETE ─────────────────────────────────────
function deleteCommunication(id) {{
  fetch('/api/delete-communication/' + id, {{ method: 'DELETE' }})
    .then(r => r.json())
    .then(d => {{
      if (d.success) {{ showToast('Deleted', 'Communication removed.', 'success'); loadCommunicationHistory(); }}
      else showToast('Error', d.error || 'Could not delete.', 'error');
    }})
    .catch(() => showToast('Error', 'Network error.', 'error'));
}}

// ── VIEW DETAILS ───────────────────────────────────────
function viewCommunication(id) {{
  document.getElementById('viewCommContent').innerHTML =
    `<div class="history-loading"><div class="loading-spinner"></div><span style="font-size:13px;color:var(--ink3);">Loading…</span></div>`;
  document.getElementById('viewCommModal').style.display = 'flex';

  fetch('/api/communication-details/' + id)
    .then(r => r.json())
    .then(d => {{
      if (!d.success) {{
        document.getElementById('viewCommContent').innerHTML =
          `<p style="color:var(--red);">Error: ${{d.error}}</p>`;
        return;
      }}
      const c    = d.communication;
      const meta = getTypeMeta(c.message_type || 'general');
      const sentAt = c.sent_at ? new Date(c.sent_at).toLocaleString('en-US',
        {{month:'long',day:'numeric',year:'numeric',hour:'2-digit',minute:'2-digit'}}) : '—';
      document.getElementById('viewCommContent').innerHTML = `
        <table class="detail-table">
          <tr><td>To</td><td style="color:var(--blue);font-weight:600;">${{escapeHtml(c.recipient_email||'—')}}</td></tr>
          <tr><td>Subject</td><td style="font-weight:600;">${{escapeHtml(c.subject||'—')}}</td></tr>
          <tr><td>Type</td><td><span class="type-chip" style="background:${{meta.bg}};color:${{meta.color}};">${{meta.label}}</span></td></tr>
          <tr><td>Applicant</td><td>${{escapeHtml(c.applicant_name||'—')}}</td></tr>
          <tr><td>Job</td><td>${{escapeHtml(c.job_title||'—')}}</td></tr>
          <tr><td>Date</td><td>${{sentAt}}</td></tr>
        </table>
        <div style="font-size:11.5px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:var(--ink3);margin-bottom:8px;">Message Body</div>
        <div class="message-body-box">${{escapeHtml(c.message||'')}}</div>
        <div style="margin-top:16px;display:flex;gap:10px;">
          <button class="btn btn-primary" onclick="replyToComm('${{escapeHtml(c.recipient_email||'')}}','${{escapeHtml(c.subject||'')}}')">
            ↩ Reply
          </button>
          <button class="btn btn-outline" onclick="closeViewComm()">Close</button>
        </div>`;
    }})
    .catch(() => {{
      document.getElementById('viewCommContent').innerHTML =
        `<p style="color:var(--red);">Network error loading details.</p>`;
    }});
}}
function closeViewComm() {{ document.getElementById('viewCommModal').style.display = 'none'; }}

function replyToComm(email, subject) {{
  closeViewComm();
  document.getElementById('recipientEmail').value = email;
  document.getElementById('subject').value = 'Re: ' + subject;
  document.getElementById('emailBody').focus();
  window.scrollTo({{top:0, behavior:'smooth'}});
  showToast('Reply Mode', 'Email pre-filled. Add your message.', 'info', 2500);
}}

// ── FORM SUBMIT ────────────────────────────────────────
document.getElementById('communicationForm').addEventListener('submit', function(e) {{
  e.preventDefault();
  const sendBtn = document.getElementById('sendBtn');
  sendBtn.disabled = true;
  sendBtn.innerHTML = `<div class="loading-spinner" style="width:14px;height:14px;border-width:2px;border-top-color:#fff;"></div> Sending…`;

  const data = {{
    application_id:  document.getElementById('applicationSelect').value,
    recipient_email: document.getElementById('recipientEmail').value,
    message_type:    document.getElementById('messageType').value,
    subject:         document.getElementById('subject').value,
    email_body:      document.getElementById('emailBody').value,
    send_copy:       document.getElementById('sendCopy').checked ? 'on' : '',
  }};

  fetch('/api/send-communication', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify(data),
  }})
  .then(r => r.json())
  .then(d => {{
    sendBtn.disabled = false;
    sendBtn.innerHTML = `<svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg> Send Email`;
    if (d.success) {{
      showToast('Email Sent! ✓', 'Message delivered successfully.', 'success');
      this.reset();
      document.getElementById('charCount').textContent = '0 chars';
      localStorage.removeItem('emailDraft');
      loadCommunicationHistory();
    }} else {{
      showToast('Send Failed', d.error || 'Could not send email.', 'error');
    }}
  }})
  .catch(err => {{
    sendBtn.disabled = false;
    sendBtn.innerHTML = `<svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg> Send Email`;
    showToast('Network Error', err.message, 'error');
  }});
}});

// ── UTILS ──────────────────────────────────────────────
function escapeHtml(str) {{
  if (!str) return '';
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
            .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}}

// ── INIT ───────────────────────────────────────────────
window.addEventListener('load', function() {{
  // Restore draft
  const draft = localStorage.getItem('emailDraft');
  if (draft) {{
    try {{
      const data = JSON.parse(draft);
      if (data.application_id) document.getElementById('applicationSelect').value = data.application_id;
      if (data.recipient_email) document.getElementById('recipientEmail').value = data.recipient_email;
      if (data.message_type)   document.getElementById('messageType').value    = data.message_type;
      if (data.subject)        document.getElementById('subject').value         = data.subject;
      if (data.email_body)     document.getElementById('emailBody').value       = data.email_body;
      if (data.send_copy)      document.getElementById('sendCopy').checked      = data.send_copy;
      updateCharCount();
      showToast('Draft Restored', 'Your last saved draft has been loaded.', 'info', 3000);
    }} catch(e) {{ localStorage.removeItem('emailDraft'); }}
  }}

  // Auto-populate from URL ?app_id=
  const urlApp = new URLSearchParams(window.location.search).get('app_id');
  if (urlApp) {{
    document.getElementById('applicationSelect').value = urlApp;
    updateRecipientEmail();
  }}

  loadCommunicationHistory();
}});

// Close modals on backdrop click
document.getElementById('previewModal').addEventListener('click', function(e) {{
  if (e.target === this) closePreview();
}});
document.getElementById('viewCommModal').addEventListener('click', function(e) {{
  if (e.target === this) closeViewComm();
}});
</script>
"""

    return HTMLResponse(
        content=get_base_html("Communications", "communications", current_user)
        + page_html
        + get_end_html()
    )


# ── HELPER: template button HTML ──────────────────────────────────────────────
def _template_btn(name: str, icon: str, label: str, bg: str, color: str) -> str:
    return f"""<button class="tpl-btn" onclick="loadTemplate('{name}')">
  <div class="tpl-icon" style="background:{bg};color:{color};">{icon}</div>
  {label}
  <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
    style="margin-left:auto;color:var(--ink3);"><polyline points="9 18 15 12 9 6"/></svg>
</button>"""


# ── BACKEND ROUTES (100% UNCHANGED) ───────────────────────────────────────────

@app.get("/api/application-email/{app_id}")
async def get_application_email_v1(app_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        application = db.get_application_details(app_id)
        if application:
            return JSONResponse(content={"success": True, "email": application.get('applicant_email', '')})
        else:
            return JSONResponse(content={"success": False, "error": "Application not found"}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/send-communication")
async def send_communication(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        required_fields = ['recipient_email', 'subject', 'email_body', 'message_type']
        for field in required_fields:
            if not data.get(field):
                return JSONResponse(content={"success": False, "error": f"Missing required field: {field}"}, status_code=400)

        success = send_email(
            data['recipient_email'],
            data['subject'],
            data['email_body'],
            is_html=True
        )

        if success:
            if data.get('send_copy'):
                send_email(
                    current_user,
                    f"COPY: {data['subject']}",
                    f"This is a copy of the email sent to {data['recipient_email']}:\n\n{data['email_body']}",
                    is_html=False
                )
            app_id = data.get('application_id')
            if app_id:
                db.add_communication(
                    application_id=int(app_id),
                    sender_type='hr',
                    recipient_email=data['recipient_email'],
                    subject=data['subject'],
                    message=data['email_body'],
                    message_type=data['message_type']
                )
            return JSONResponse(content={"success": True, "message": "Email sent successfully"})
        else:
            error_msg = (
                "Failed to send email. Please check the email configuration in hr_base.py. "
                "For Gmail, you may need to generate an App Password: "
                "https://myaccount.google.com/apppasswords"
            )
            return JSONResponse(content={"success": False, "error": error_msg}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.get("/api/communication-history")
async def get_communication_history(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        communications = db.get_communications()
        return JSONResponse(content={"success": True, "communications": communications})
    except Exception as e:
        print(f"Error getting communications: {str(e)}")
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.delete("/api/delete-communication/{communication_id}")
async def delete_communication(communication_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        success = db.delete_communication(communication_id)
        if success:
            return JSONResponse(content={"success": True, "message": "Communication deleted successfully"})
        else:
            return JSONResponse(content={"success": False, "error": "Communication not found"}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.get("/api/communication-details/{communication_id}")
async def get_communication_details(communication_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        communications = db.get_communications()
        communication = next((c for c in communications if c.get('id') == communication_id), None)
        if communication:
            return JSONResponse(content={"success": True, "communication": communication})
        else:
            return JSONResponse(content={"success": False, "error": "Communication not found"}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    print("Starting HR Communications  →  http://localhost:8003/communications")
    uvicorn.run(app, host="0.0.0.0", port=8003)