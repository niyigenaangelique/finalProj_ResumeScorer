from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from database import ResumeDatabase
from hr_base import app, get_current_user, get_base_html, get_end_html, send_email
import os
import mimetypes

db = ResumeDatabase()


@app.get("/jobs", response_class=HTMLResponse)
async def job_management(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/", status_code=302)

    jobs         = db.get_all_jobs()
    applications = db.get_all_applications()

    total_jobs  = len(jobs)
    active_jobs = sum(1 for j in jobs if (j.get("status") or "active").lower() == "active")
    total_apps  = len(applications)
    pending     = sum(1 for a in applications if (a.get("status") or "pending").lower() == "pending")

    job_rows = _build_job_rows(jobs)
    app_rows = _build_app_rows(applications)

    page = f"""
<!-- ══ PAGE HEADER ══ -->
<div class="page-hd">
  <div>
    <div class="page-title">Job Management</div>
    <div class="page-sub">Manage job postings and review all incoming applications.</div>
  </div>
  <div style="display:flex;gap:10px;">
    <a href="/post-job" class="btn btn-primary">
      <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
        <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
      </svg>
      Post New Job
    </a>
  </div>
</div>

<!-- ══ STATS ══ -->
<div class="stats-row" style="margin-bottom:24px;">
  <div class="stat-tile"><div class="stat-icon">💼</div><div class="stat-body"><div class="stat-label">Total Jobs</div><div class="stat-value">{total_jobs}</div></div></div>
  <div class="stat-tile"><div class="stat-icon">✅</div><div class="stat-body"><div class="stat-label">Active Listings</div><div class="stat-value">{active_jobs}</div></div></div>
  <div class="stat-tile"><div class="stat-icon">📋</div><div class="stat-body"><div class="stat-label">Total Applications</div><div class="stat-value">{total_apps}</div></div></div>
  <div class="stat-tile"><div class="stat-icon">⏳</div><div class="stat-body"><div class="stat-label">Pending Review</div><div class="stat-value">{pending}</div></div></div>
</div>

<!-- ══ TAB SWITCHER ══ -->
<div style="display:flex;gap:8px;margin-bottom:20px;">
  <button class="tab-btn active" id="tab-jobs" onclick="switchTab('jobs',this)">
    <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
      <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
    </svg>
    Job Postings <span class="tab-count">{total_jobs}</span>
  </button>
  <button class="tab-btn" id="tab-applications" onclick="switchTab('applications',this)">
    <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
    </svg>
    Applications <span class="tab-count">{total_apps}</span>
  </button>
</div>

<!-- ══ JOBS PANEL ══ -->
<div id="panel-jobs" class="card" style="animation:fadeUp 0.3s ease both;">
  <div class="card-hd">
    <span class="card-title">Active Job Postings</span>
    <div style="display:flex;gap:8px;align-items:center;">
      {_search_box("filterJobs(this.value)", "Search jobs…")}
      <a href="/post-job" class="btn btn-primary" style="padding:6px 14px;font-size:12.5px;">+ Add Job</a>
    </div>
  </div>
  <div style="overflow-x:auto;">
    <table class="data-table" id="jobsTable">
      <thead><tr>
        <th>Job Title</th><th>Department</th><th>Location</th>
        <th>Salary</th><th>Posted</th><th>Status</th><th>Actions</th>
      </tr></thead>
      <tbody id="jobsBody">{job_rows}</tbody>
    </table>
  </div>
</div>

<!-- ══ APPLICATIONS PANEL ══ -->
<div id="panel-applications" class="card" style="display:none;animation:fadeUp 0.3s ease both;">
  <div class="card-hd">
    <span class="card-title">All Applications</span>
    <div style="display:flex;gap:8px;align-items:center;">
      {_search_box("filterApps(this.value)", "Search applicants…")}
    </div>
  </div>
  <div style="overflow-x:auto;">
    <table class="data-table" id="appsTable">
      <thead><tr>
        <th>Applicant</th><th>Job Title</th><th>Department</th>
        <th>Score</th><th>Applied</th><th>Status</th><th>Actions</th>
      </tr></thead>
      <tbody id="appsBody">{app_rows}</tbody>
    </table>
  </div>
</div>

<!-- ══ ADD/EDIT JOB MODAL ══ -->
<div id="jobModal" style="display:none;position:fixed;inset:0;background:rgba(13,14,26,0.55);
     z-index:10000;align-items:center;justify-content:center;backdrop-filter:blur(6px);">
  <div style="background:var(--white);border-radius:16px;padding:32px;max-width:600px;width:90%;
              max-height:88vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.2);position:relative;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:22px;">
      <span class="card-title" id="jobModalTitle">Add New Job</span>
      <button onclick="closeJobModal()" style="background:var(--bg);border:1px solid var(--border);
              border-radius:8px;width:32px;height:32px;cursor:pointer;font-size:16px;color:var(--ink2);">✕</button>
    </div>
    <div class="form-grid">
      <div class="form-group full"><label class="form-label">Job Title *</label>
        <input class="form-ctrl" type="text" id="jobTitle" placeholder="e.g. Senior Software Engineer"></div>
      <div class="form-group"><label class="form-label">Department *</label>
        <input class="form-ctrl" type="text" id="jobDepartment"></div>
      <div class="form-group"><label class="form-label">Location</label>
        <input class="form-ctrl" type="text" id="jobLocation" placeholder="City or Remote"></div>
      <div class="form-group full"><label class="form-label">Salary</label>
        <input class="form-ctrl" type="text" id="jobSalary" placeholder="e.g. $80,000 – $120,000"></div>
      <div class="form-group full"><label class="form-label">Job Description</label>
        <textarea class="form-ctrl" id="jobDescription" rows="4"></textarea></div>
      <div class="form-group full"><label class="form-label">Requirements</label>
        <textarea class="form-ctrl" id="jobRequirements" rows="4"></textarea></div>
      <div class="form-group full"><label class="form-label">Status</label>
        <select class="form-ctrl" id="jobStatus">
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="closed">Closed</option>
        </select></div>
    </div>
    <div class="form-actions">
      <button class="btn btn-primary" id="jobSubmitBtn" onclick="submitJob()">Add Job</button>
      <button class="btn btn-outline" onclick="closeJobModal()">Cancel</button>
    </div>
  </div>
</div>

<!-- ══ VIEW APPLICATION MODAL ══ -->
<div id="appModal" style="display:none;position:fixed;inset:0;background:rgba(13,14,26,0.55);
     z-index:10000;align-items:center;justify-content:center;backdrop-filter:blur(6px);">
  <div style="background:var(--white);border-radius:16px;padding:32px;max-width:580px;width:90%;
              max-height:88vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.2);position:relative;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:22px;">
      <span class="card-title">Application Details</span>
      <button onclick="closeAppModal()" style="background:var(--bg);border:1px solid var(--border);
              border-radius:8px;width:32px;height:32px;cursor:pointer;font-size:16px;color:var(--ink2);">✕</button>
    </div>
    <div id="appModalContent"></div>
  </div>
</div>

<style>
.tab-btn {{
  display:inline-flex;align-items:center;gap:6px;
  padding:9px 16px;border-radius:10px;border:1.5px solid var(--border);
  background:var(--white);color:var(--ink2);font-family:'DM Sans',sans-serif;
  font-size:13.5px;font-weight:600;cursor:pointer;transition:all 0.15s;
}}
.tab-btn.active {{
  background:var(--blue-lt);border-color:var(--blue);color:var(--blue);
}}
.tab-btn:hover:not(.active) {{background:var(--bg);}}
.tab-count {{
  background:var(--bg);border:1px solid var(--border);
  padding:1px 7px;border-radius:20px;font-size:11px;font-weight:700;
}}
.tab-btn.active .tab-count {{background:var(--blue);color:#fff;border-color:var(--blue);}}

.spin {{
  width:16px;height:16px;border-radius:50%;
  border:2px solid var(--border);border-top-color:var(--blue);
  animation:spinA 0.7s linear infinite;display:inline-block;vertical-align:-3px;
}}
@keyframes spinA {{to{{transform:rotate(360deg);}}}}

/* Status select inline */
.status-sel {{
  padding:4px 8px;border:1.5px solid var(--border);border-radius:7px;
  font-family:'DM Sans',sans-serif;font-size:12.5px;color:var(--ink);
  background:var(--white);outline:none;cursor:pointer;
  transition:border-color 0.15s;
}}
.status-sel:focus {{border-color:var(--blue);}}
</style>

<script>
let editingJobId = null;

// ── TAB SWITCH ─────────────────────────────────────────
function switchTab(name, btn) {{
  ['jobs','applications'].forEach(t => {{
    document.getElementById('panel-'+t).style.display = t===name ? '' : 'none';
  }});
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}}

// ── SEARCH ─────────────────────────────────────────────
function filterJobs(q) {{
  q = q.toLowerCase();
  document.querySelectorAll('#jobsBody tr').forEach(r => {{
    r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}}
function filterApps(q) {{
  q = q.toLowerCase();
  document.querySelectorAll('#appsBody tr').forEach(r => {{
    r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}}

// ── JOB MODAL ─────────────────────────────────────────
function showAddJobForm() {{
  editingJobId = null;
  document.getElementById('jobModalTitle').textContent = 'Add New Job';
  document.getElementById('jobSubmitBtn').textContent  = 'Add Job';
  ['jobTitle','jobDepartment','jobLocation','jobSalary','jobDescription','jobRequirements'].forEach(id=>{{
    document.getElementById(id).value = '';
  }});
  document.getElementById('jobStatus').value = 'active';
  document.getElementById('jobModal').style.display = 'flex';
}}
function closeJobModal() {{ document.getElementById('jobModal').style.display = 'none'; }}

function editJob(id) {{
  editingJobId = id;
  fetch('/api/job-details/' + id)
    .then(r => r.json())
    .then(d => {{
      if (!d.success) {{ showToast('Error', d.error, 'error'); return; }}
      const j = d.job;
      document.getElementById('jobModalTitle').textContent = 'Edit Job';
      document.getElementById('jobSubmitBtn').textContent  = 'Update Job';
      document.getElementById('jobTitle').value        = j.title       || '';
      document.getElementById('jobDepartment').value   = j.department  || '';
      document.getElementById('jobLocation').value     = j.location    || '';
      document.getElementById('jobSalary').value       = j.salary      || '';
      document.getElementById('jobDescription').value  = j.description || '';
      document.getElementById('jobRequirements').value = j.requirements|| '';
      document.getElementById('jobStatus').value       = j.status      || 'active';
      document.getElementById('jobModal').style.display = 'flex';
    }})
    .catch(() => showToast('Error', 'Could not load job.', 'error'));
}}

function submitJob() {{
  const btn  = document.getElementById('jobSubmitBtn');
  const data = {{
    title:       document.getElementById('jobTitle').value,
    department:  document.getElementById('jobDepartment').value,
    location:    document.getElementById('jobLocation').value,
    salary:      document.getElementById('jobSalary').value,
    description: document.getElementById('jobDescription').value,
    requirements:document.getElementById('jobRequirements').value,
    status:      document.getElementById('jobStatus').value,
  }};
  if (!data.title || !data.department) {{
    showToast('Validation', 'Title and Department are required.', 'warning'); return;
  }}
  btn.disabled = true;
  btn.innerHTML = '<div class="spin"></div> Saving…';

  const url = editingJobId ? '/api/update-job' : '/api/add-job';
  if (editingJobId) data.job_id = editingJobId;

  fetch(url, {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}})
    .then(r => r.json())
    .then(d => {{
      btn.disabled = false;
      btn.textContent = editingJobId ? 'Update Job' : 'Add Job';
      if (d.success) {{
        showToast(editingJobId?'Updated':'Posted', 'Job saved successfully.', 'success');
        closeJobModal();
        setTimeout(() => location.reload(), 1200);
      }} else showToast('Error', d.error||'Failed.', 'error');
    }})
    .catch(() => {{ btn.disabled=false; showToast('Error','Network error.','error'); }});
}}

function deleteJob(id) {{
  if (!confirm('Delete this job? All related applications will also be removed.')) return;
  fetch('/api/delete-job', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{job_id:id}})}})
    .then(r => r.json())
    .then(d => {{
      if (d.success) {{ showToast('Deleted','Job removed.','warning'); setTimeout(()=>location.reload(),1000); }}
      else showToast('Error', d.error||'Failed.', 'error');
    }})
    .catch(() => showToast('Error','Network error.','error'));
}}

// ── APPLICATION MODAL ─────────────────────────────────
function viewApplication(id) {{
  const modal = document.getElementById('appModal');
  document.getElementById('appModalContent').innerHTML =
    '<div style="text-align:center;padding:32px;"><div class="spin" style="width:22px;height:22px;border-width:2.5px;"></div></div>';
  modal.style.display = 'flex';

  fetch('/api/application-details/' + id)
    .then(r => r.json())
    .then(d => {{
      if (!d.success) {{ document.getElementById('appModalContent').innerHTML=`<p style="color:var(--red);">${{d.error}}</p>`; return; }}
      const a = d.application;
      const sc = a.resume_score ? parseFloat(a.resume_score).toFixed(1) : null;
      const scCol = sc>=80?'var(--green)':sc>=60?'#C67C00':sc?'var(--red)':'var(--ink3)';
      const scBg  = sc>=80?'#E8F8F0':sc>=60?'var(--amber-lt)':sc?'var(--red-lt)':'var(--bg)';
      document.getElementById('appModalContent').innerHTML = `
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
          <div style="width:44px;height:44px;border-radius:11px;background:linear-gradient(135deg,#4776E6,#8E54E9);
            flex-shrink:0;display:flex;align-items:center;justify-content:center;
            font-family:'Sora',sans-serif;font-weight:800;font-size:16px;color:#fff;">
            ${{(a.applicant_name||'?')[0].toUpperCase()}}
          </div>
          <div>
            <div style="font-family:'Sora',sans-serif;font-weight:700;font-size:15px;color:var(--ink);">${{escHtml(a.applicant_name||'N/A')}}</div>
            <div style="font-size:12.5px;color:var(--ink3);">${{escHtml(a.applicant_email||'')}}</div>
          </div>
          ${{sc ? `<div style="margin-left:auto;background:${{scBg}};border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
            <span style="font-family:'Sora',sans-serif;font-weight:800;font-size:14px;color:${{scCol}};">${{sc}}</span></div>` : ''}}
        </div>
        <table style="width:100%;border-collapse:collapse;">
          ${{_dtrow('Position', a.job_title||'—')}}
          ${{_dtrow('Department', a.department||'—')}}
          ${{_dtrow('Applied', (a.application_date||'—').toString().slice(0,10))}}
          ${{_dtrow('Status', `<span class="badge ${{_appBadge(a.status)}}">${{(a.status||'pending').charAt(0).toUpperCase()+(a.status||'pending').slice(1)}}</span>`)}}
          ${{a.cover_letter ? _dtrow('Cover Letter', `<div style="max-height:100px;overflow-y:auto;font-size:13px;color:var(--ink3);line-height:1.6;">${{escHtml(a.cover_letter)}}</div>`) : ''}}
        </table>
        <div style="display:flex;gap:8px;margin-top:20px;flex-wrap:wrap;">
          <a href="/communications?app_id=${{id}}" class="btn btn-primary">✉️ Send Email</a>
          <a href="/interviews?application=${{id}}" class="btn btn-outline">📅 Schedule Interview</a>
          <button class="btn btn-outline" onclick="closeAppModal()">Close</button>
        </div>`;
    }})
    .catch(() => {{ document.getElementById('appModalContent').innerHTML='<p style="color:var(--red);">Network error.</p>'; }});
}}
function closeAppModal() {{ document.getElementById('appModal').style.display='none'; }}

function _dtrow(label, val) {{
  return `<tr style="border-bottom:1px solid var(--border);">
    <td style="padding:9px 0;font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--ink3);width:110px;">${{label}}</td>
    <td style="padding:9px 0;font-size:13.5px;color:var(--ink);">${{val}}</td>
  </tr>`;
}}

function _appBadge(s) {{
  return {{pending:'badge-amber',reviewing:'badge-teal',interview:'badge-blue',
    offered:'badge-green',rejected:'badge-red',hired:'badge-green',
    shortlisted:'badge-green'}}[(s||'').toLowerCase()] || 'badge-neutral';
}}

// ── STATUS UPDATE ─────────────────────────────────────
function updateApplicationStatus(id, val) {{
  fetch('/api/update-application-status', {{
    method:'POST', headers:{{'Content-Type':'application/json'}},
    body: JSON.stringify({{application_id:id, status:val}})
  }})
  .then(r => r.json())
  .then(d => {{
    if (d.success) showToast('Updated', 'Status changed to '+val+'.', 'success');
    else {{ showToast('Error', d.error||'Failed.', 'error'); location.reload(); }}
  }})
  .catch(() => location.reload());
}}

function scheduleInterview(id) {{
  window.location.href = '/interviews?application=' + id;
}}

// ── MODAL BACKDROP ────────────────────────────────────
['jobModal','appModal'].forEach(id => {{
  document.getElementById(id).addEventListener('click', function(e) {{
    if (e.target === this) this.style.display = 'none';
  }});
}});

// ── UTILS ─────────────────────────────────────────────
function escHtml(s) {{
  if(!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
          .replace(/"/g,'&quot;').replace(/\'/g,'&#39;');
}}

// Badge CSS (inline since hr_base provides the classes)
const bmap = {{
  'badge-amber':  ['var(--amber-lt)','#C67C00'],
  'badge-teal':   ['var(--teal-lt)','var(--teal)'],
  'badge-blue':   ['var(--blue-lt)','var(--blue)'],
  'badge-green':  ['#E8F8F0','var(--green)'],
  'badge-red':    ['var(--red-lt)','var(--red)'],
  'badge-neutral':['var(--bg)','var(--ink3)'],
}};
</script>
"""
    return HTMLResponse(content=get_base_html("Job Management", "jobs", current_user) + page + get_end_html())


# ── HTML HELPERS ──────────────────────────────────────────────────────────────

def _search_box(oninput: str, placeholder: str) -> str:
    return f"""<div style="position:relative;">
  <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="var(--ink3)" stroke-width="2"
    style="position:absolute;left:9px;top:50%;transform:translateY(-50%);pointer-events:none;">
    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
  <input type="text" placeholder="{placeholder}" oninput="{oninput}"
    style="padding:7px 12px 7px 28px;background:var(--bg);border:1.5px solid var(--border);
           border-radius:8px;font-family:'DM Sans',sans-serif;font-size:12.5px;color:var(--ink);
           outline:none;width:190px;transition:border-color .15s;"
    onfocus="this.style.borderColor='var(--blue)'" onblur="this.style.borderColor='var(--border)'">
</div>"""


_STATUS_JOB = {
    "active":   ("badge-green",  "Active"),
    "inactive": ("badge-amber",  "Inactive"),
    "closed":   ("badge-red",    "Closed"),
}
_STATUS_APP = {
    "pending":    ("badge-amber",   "Pending"),
    "reviewing":  ("badge-teal",    "Reviewing"),
    "interview":  ("badge-blue",    "Interview"),
    "offered":    ("badge-green",   "Offered"),
    "rejected":   ("badge-red",     "Rejected"),
    "hired":      ("badge-green",   "Hired"),
    "shortlisted":("badge-green",   "Shortlisted"),
}

_BADGE_STYLES = {
    "badge-green":   ("background:#E8F8F0;color:var(--green);"),
    "badge-amber":   ("background:var(--amber-lt);color:#C67C00;"),
    "badge-red":     ("background:var(--red-lt);color:var(--red);"),
    "badge-blue":    ("background:var(--blue-lt);color:var(--blue);"),
    "badge-teal":    ("background:var(--teal-lt);color:var(--teal);"),
    "badge-neutral": ("background:var(--bg);color:var(--ink3);border:1px solid var(--border);"),
}

def _badge(cls: str, label: str) -> str:
    sty = _BADGE_STYLES.get(cls, "")
    return f'<span style="display:inline-flex;align-items:center;padding:3px 10px;border-radius:20px;font-size:11.5px;font-weight:700;{sty}">{label}</span>'


def _build_job_rows(jobs: list) -> str:
    if not jobs:
        return '<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--ink3);">No jobs posted yet. <a href="/post-job" style="color:var(--blue);">Post your first job →</a></td></tr>'
    rows = ""
    for j in jobs:
        status = (j.get("status") or "active").lower()
        bcls, blabel = _STATUS_JOB.get(status, ("badge-neutral", status.title()))
        date = str(j.get("posted_date") or "")[:10] or "—"
        rows += f"""<tr>
          <td><strong style="font-size:13.5px;color:var(--ink);">{j.get('title','—')}</strong></td>
          <td>{j.get('department','—')}</td>
          <td>{j.get('location','—') or '—'}</td>
          <td style="white-space:nowrap;">{j.get('salary','—') or '—'}</td>
          <td style="white-space:nowrap;">{date}</td>
          <td>{_badge(bcls, blabel)}</td>
          <td><div class="action-grp">
            <button class="btn btn-outline btn-sm" onclick="editJob({j.get('id',0)})">✏️ Edit</button>
            <button class="btn btn-danger btn-sm" onclick="deleteJob({j.get('id',0)})">Delete</button>
          </div></td>
        </tr>"""
    return rows


def _build_app_rows(applications: list) -> str:
    if not applications:
        return '<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--ink3);">No applications yet.</td></tr>'
    rows = ""
    for a in applications:
        score = a.get("resume_score")
        if score:
            sf = float(score)
            scls = "badge-green" if sf >= 80 else "badge-amber" if sf >= 60 else "badge-red"
            score_html = _badge(scls, f"{sf:.0f}/100")
        else:
            score_html = _badge("badge-neutral", "—")

        status = (a.get("status") or "pending").lower()
        bcls, blabel = _STATUS_APP.get(status, ("badge-neutral", status.title()))

        date = str(a.get("application_date") or "")[:10] or "—"
        aid  = a.get("id", 0)
        name = (a.get("applicant_name") or "N/A")
        email = (a.get("applicant_email") or "")
        initial = name[0].upper()

        # Build status select
        opts = ""
        for val, (_, lbl) in _STATUS_APP.items():
            sel = "selected" if val == status else ""
            opts += f'<option value="{val}" {sel}>{lbl}</option>'

        rows += f"""<tr>
          <td>
            <div style="display:flex;align-items:center;gap:9px;">
              <div style="width:30px;height:30px;border-radius:8px;flex-shrink:0;
                background:linear-gradient(135deg,#4776E6,#8E54E9);
                display:flex;align-items:center;justify-content:center;
                font-family:'Sora',sans-serif;font-weight:800;font-size:11px;color:#fff;">{initial}</div>
              <div>
                <div style="font-weight:700;font-size:13px;color:var(--ink);">{name}</div>
                <div style="font-size:11.5px;color:var(--ink3);">{email}</div>
              </div>
            </div>
          </td>
          <td>{a.get('job_title','—')}</td>
          <td>{a.get('department','—')}</td>
          <td>{score_html}</td>
          <td style="white-space:nowrap;">{date}</td>
          <td>
            <select class="status-sel" onchange="updateApplicationStatus({aid}, this.value)">{opts}</select>
          </td>
          <td><div class="action-grp">
            <button class="btn btn-outline btn-sm" onclick="viewApplication({aid})">View</button>
            <button class="btn btn-success btn-sm" onclick="scheduleInterview({aid})">📅 Interview</button>
          </div></td>
        </tr>"""
    return rows


# ── BACKEND ROUTES (100% UNCHANGED) ──────────────────────────────────────────

@app.get("/api/application-details/{application_id}")
async def get_application_details(application_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        application = db.get_application_details(application_id)
        if not application:
            return JSONResponse(content={"success": False, "error": "Application not found"}, status_code=404)
        documents = db.get_applicant_documents(application.get('applicant_id', 0))
        return JSONResponse(content={"success": True, "application": application, "documents": documents, "resume_score_details": None})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.get("/application-details/{application_id}")
async def application_details_page(application_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/", status_code=302)
    try:
        application = db.get_application_details(application_id)
        if not application:
            return HTMLResponse(content="Application not found", status_code=404)
        documents = db.get_applicant_documents(application.get('applicant_id', 0))
        details_content = f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                    <h2>Application Details</h2>
                    <button class="btn btn-outline" onclick="window.close()">Close</button>
                </div>
                <div class="card" style="margin-bottom: 2rem;">
                    <h3>Applicant Information</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div>
                            <p><strong>Name:</strong> {application.get('applicant_name', 'N/A')}</p>
                            <p><strong>Email:</strong> {application.get('applicant_email', 'N/A')}</p>
                            <p><strong>Application Date:</strong> {application.get('application_date', 'N/A')}</p>
                        </div>
                        <div>
                            <p><strong>Job Title:</strong> {application.get('job_title', 'N/A')}</p>
                            <p><strong>Department:</strong> {application.get('department', 'N/A')}</p>
                            <p><strong>Status:</strong> {application.get('status', 'N/A').title()}</p>
                        </div>
                    </div>
                </div>
            </div>"""
        return HTMLResponse(content=get_base_html("Application Details", "jobs", current_user) + details_content + get_end_html())
    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)


@app.get("/view-document/{document_id}")
async def view_document(document_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/", status_code=302)
    try:
        document = db.get_document_by_id(document_id)
        if not document:
            return HTMLResponse(content="Document not found", status_code=404)
        filename = document.get('filename', '').lower()
        if not filename.endswith('.pdf'):
            return HTMLResponse(content=f"<html><body><p>Cannot preview: {document.get('filename')}</p><a href='/download-document/{document_id}'>Download</a></body></html>")
        from hr_pdf_viewer import get_pdf_viewer_page
        return HTMLResponse(content=get_pdf_viewer_page(document_id, document))
    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)


@app.get("/api/pdf-file/{document_id}")
async def serve_pdf_file(document_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/", status_code=302)
    try:
        document = db.get_document_by_id(document_id)
        if not document:
            return HTMLResponse(content="Document not found", status_code=404)
        file_path = document.get('file_path', '')
        filename  = document.get('filename', '')
        if not os.path.exists(file_path):
            return HTMLResponse(content="File not found on server", status_code=404)
        if not filename.lower().endswith('.pdf'):
            return HTMLResponse(content="File is not a PDF", status_code=400)
        return FileResponse(path=file_path, filename=filename, media_type='application/pdf')
    except Exception as e:
        return HTMLResponse(content=f"Error serving file: {str(e)}", status_code=500)


@app.get("/download-document/{document_id}")
async def download_document(document_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/", status_code=302)
    try:
        document = db.get_document_by_id(document_id)
        if not document:
            return HTMLResponse(content="Document not found", status_code=404)
        file_path = document.get('file_path', '')
        filename  = document.get('filename', '')
        if not os.path.exists(file_path):
            return HTMLResponse(content=f"<html><body><p>File not found: {filename}</p></body></html>")
        media_type, _ = mimetypes.guess_type(filename)
        return FileResponse(path=file_path, filename=filename, media_type=media_type or 'application/octet-stream')
    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)


@app.get("/api/job-details/{job_id}")
async def get_job_details(job_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        job = db.get_job(job_id)
        if job:
            return JSONResponse(content={"success": True, "job": job})
        return JSONResponse(content={"success": False, "error": "Job not found"}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/add-job")
async def add_job(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        for f in ['title', 'department']:
            if not data.get(f):
                return JSONResponse(content={"success": False, "error": f"Missing: {f}"}, status_code=400)
        job_id = db.add_job(title=data['title'], department=data['department'],
                            location=data.get('location',''), salary=data.get('salary',''),
                            description=data.get('description',''), requirements=data.get('requirements',''))
        return JSONResponse(content={"success": True, "job_id": job_id})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/update-job")
async def update_job(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        if not data.get("job_id"):
            return JSONResponse(content={"success": False, "error": "Job ID required"}, status_code=400)
        success = db.update_job(job_id=data["job_id"], title=data.get("title"),
                                department=data.get("department"), location=data.get("location"),
                                salary=data.get("salary"), description=data.get("description"),
                                requirements=data.get("requirements"), status=data.get("status"))
        return JSONResponse(content={"success": True} if success else {"success": False, "error": "Failed"})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/delete-job")
async def delete_job(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        if not data.get("job_id"):
            return JSONResponse(content={"success": False, "error": "Job ID required"}, status_code=400)
        success = db.delete_job(data["job_id"])
        return JSONResponse(content={"success": True} if success else {"success": False, "error": "Failed"})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/update-application-status")
async def update_application_status(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        if not data.get("application_id") or not data.get("status"):
            return JSONResponse(content={"success": False, "error": "ID and status required"}, status_code=400)
        db.update_application_status(data["application_id"], data["status"])
        return JSONResponse(content={"success": True})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)