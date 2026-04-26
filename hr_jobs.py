from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from database import ResumeDatabase
import sqlite3
from hr_base import app, get_current_user, get_base_html, get_end_html, send_email
import os
import mimetypes
import json
import urllib.request
import urllib.error

db = ResumeDatabase()

def _hrms_base_url() -> str:
    hire_url = os.getenv("TALENTFLOW_HRMS_URL", "http://localhost:8000/api/external-recruitment/hire").strip()
    if "/api/" in hire_url:
        return hire_url.split("/api/")[0]
    return hire_url.rstrip("/")

def _hrms_headers() -> dict:
    token = os.getenv("TALENTFLOW_HRMS_TOKEN", "talentflow_secret_token_123").strip()
    # We support either an external-token style header or a Bearer token depending on HRMS setup.
    return {
        "Accept": "application/json",
        "X-Recruitment-Token": token,
        "Authorization": f"Bearer {token}",
    }

def _fetch_hrms_list(url: str):
    req = urllib.request.Request(url, headers=_hrms_headers(), method="GET")
    with urllib.request.urlopen(req, timeout=8) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return json.loads(body)


@app.get("/api/hrms-metadata")
async def hrms_metadata(request: Request):
    """Fetch departments, positions, and shifts from Laravel HRMS (best-effort)."""
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)

    base = _hrms_base_url()

    # Allow explicit override per resource.
    dep_url = os.getenv("TALENTFLOW_HRMS_DEPARTMENTS_URL", "").strip()
    pos_url = os.getenv("TALENTFLOW_HRMS_POSITIONS_URL", "").strip()
    shf_url = os.getenv("TALENTFLOW_HRMS_SHIFTS_URL", "").strip()
    meta_url = os.getenv("TALENTFLOW_HRMS_METADATA_URL", f"{base}/api/external-recruitment/metadata").strip()

    defaults = {
        "departments": ["Engineering", "Marketing", "Sales", "Human Resources", "Finance", "Operations", "Customer Service", "Product", "Design"],
        "positions": [],
        "shifts": ["Day Shift", "Night Shift", "Flexible", "On-call"],
    }

    def normalize_list(payload, key_guess: str):
        if payload is None:
            return []
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for k in (key_guess, "data", "items", "results"):
                v = payload.get(k)
                if isinstance(v, list):
                    return v
        return []

    try:
        departments = defaults["departments"]
        positions = defaults["positions"]
        shifts = defaults["shifts"]

        # Prefer a single metadata endpoint (recommended); fall back to per-resource URLs if provided.
        try:
            meta_payload = _fetch_hrms_list(meta_url)
            if isinstance(meta_payload, dict) and meta_payload.get("success") is True:
                meta_deps = normalize_list(meta_payload, "departments")
                meta_pos  = normalize_list(meta_payload, "positions")
                meta_shf  = normalize_list(meta_payload, "shifts")
                if meta_deps: departments = meta_deps
                if meta_pos:  positions   = meta_pos
                if meta_shf:  shifts      = meta_shf
        except Exception:
            pass

        if dep_url:
            try:
                departments_payload = _fetch_hrms_list(dep_url)
                departments_list = normalize_list(departments_payload, "departments")
                if departments_list:
                    departments = departments_list
            except Exception:
                pass

        if pos_url:
            try:
                positions_payload = _fetch_hrms_list(pos_url)
                positions_list = normalize_list(positions_payload, "positions")
                if positions_list:
                    positions = positions_list
            except Exception:
                pass

        if shf_url:
            try:
                shifts_payload = _fetch_hrms_list(shf_url)
                shifts_list = normalize_list(shifts_payload, "shifts")
                if shifts_list:
                    shifts = shifts_list
            except Exception:
                pass

        return JSONResponse(content={
            "success": True,
            "departments": departments,
            "positions": positions,
            "shifts": shifts,
        })
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e), **defaults}, status_code=200)


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
  <div class="stat-tile"><div class="stat-icon"><svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg></div><div class="stat-body"><div class="stat-label">Total Jobs</div><div class="stat-value">{total_jobs}</div></div></div>
  <div class="stat-tile"><div class="stat-icon"><svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div><div class="stat-body"><div class="stat-label">Active Listings</div><div class="stat-value">{active_jobs}</div></div></div>
  <div class="stat-tile"><div class="stat-icon"><svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/></svg></div><div class="stat-body"><div class="stat-label">Total Applications</div><div class="stat-value">{total_apps}</div></div></div>
  <div class="stat-tile"><div class="stat-icon"><svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M5 2h14M5 22h14M5 2a7 7 0 0 1 7 7M19 2a7 7 0 0 0-7 7M5 22a7 7 0 0 0 7-7M19 22a7 7 0 0 1-7-7"/></svg></div><div class="stat-body"><div class="stat-label">Pending Review</div><div class="stat-value">{pending}</div></div></div>
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
        <th>Applicant</th><th>Job Title</th><th>Dept</th>
        <th>Keyword Score</th><th>AI Score</th><th>AI Status</th><th>Applied</th><th>Status</th><th>Actions</th>
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
              border-radius:8px;width:32px;height:32px;cursor:pointer;font-size:16px;color:var(--ink2);"><svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
    </div>
    <div class="form-grid">
      <div class="form-group full"><label class="form-label">Job Title *</label>
        <select class="form-ctrl" id="jobTitle"></select></div>
      <div class="form-group"><label class="form-label">Department *</label>
        <select class="form-ctrl" id="jobDepartment"></select></div>
      <div class="form-group"><label class="form-label">Location</label>
        <input class="form-ctrl" type="text" id="jobLocation" placeholder="City or Remote"></div>
      <div class="form-group"><label class="form-label">Work Mode (Shift)</label>
        <select class="form-ctrl" id="jobWorkMode"></select></div>
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
              border-radius:8px;width:32px;height:32px;cursor:pointer;font-size:16px;color:var(--ink2);"><svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
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
let HRMS_META = null;

function _opt(label, value) {{
  const o = document.createElement('option');
  o.value = value;
  o.textContent = label;
  return o;
}}

function _fillSelect(selId, items, placeholder) {{
  const sel = document.getElementById(selId);
  if(!sel) return;
  sel.innerHTML = '';
  sel.appendChild(_opt(placeholder || 'Select…', ''));
  (items || []).forEach(it => {{
    const name = (typeof it === 'string') ? it : (it.name || it.title || it.label || it.value || '');
    const val  = (typeof it === 'string') ? it : (it.name || it.title || it.label || it.value || '');
    if(name) sel.appendChild(_opt(name, val));
  }});
}}

async function loadHrmsMeta() {{
  if (HRMS_META) return HRMS_META;
  try {{
    const r = await fetch('/api/hrms-metadata');
    const d = await r.json();
    if(d && d.success) HRMS_META = d;
  }} catch(e) {{}}
  HRMS_META = HRMS_META || {{success:false, departments:[], positions:[], shifts:[]}};
  return HRMS_META;
}}

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
  ['jobTitle','jobDepartment','jobLocation','jobWorkMode','jobSalary','jobDescription','jobRequirements'].forEach(id=>{{
    const el = document.getElementById(id);
    if (el) el.value = '';
  }});
  document.getElementById('jobStatus').value = 'active';
  loadHrmsMeta().then(meta => {{
    _fillSelect('jobDepartment', meta.departments || [], 'Select Department');
    _fillSelect('jobTitle', meta.positions || [], 'Select Position');
    _fillSelect('jobWorkMode', meta.shifts || [], 'Select Shift');
  }});
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
      loadHrmsMeta().then(meta => {{
        _fillSelect('jobDepartment', meta.departments || [], 'Select Department');
        _fillSelect('jobTitle', meta.positions || [], 'Select Position');
        _fillSelect('jobWorkMode', meta.shifts || [], 'Select Shift');
        document.getElementById('jobTitle').value        = j.title       || '';
        document.getElementById('jobDepartment').value   = j.department  || '';
        document.getElementById('jobWorkMode').value     = j.work_mode   || '';
      }});
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
    work_mode:   document.getElementById('jobWorkMode').value,
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
  window.tfDialog.confirm({
    title: 'Delete Job',
    message: 'Delete this job? All related applications will also be removed.',
    okText: 'Delete',
    cancelText: 'Cancel',
    danger: true
  }).then(ok => {{
    if(!ok) return;
  fetch('/api/delete-job', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{job_id:id}})}})
    .then(r => r.json())
    .then(d => {{
      if (d.success) {{ showToast('Deleted','Job removed.','warning'); setTimeout(()=>location.reload(),1000); }}
      else showToast('Error', d.error||'Failed.', 'error');
    }})
    .catch(() => showToast('Error','Network error.','error'));
  }});
}}

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
      const docs = d.documents || [];
      let docsHtml = '';
      if (docs.length > 0) {{
        docsHtml = docs.map(doc => `
          <div style="display:flex;align-items:center;justify-content:space-between;padding:8px;background:var(--bg);border-radius:8px;margin-bottom:6px;">
            <span style="font-size:12px;color:var(--ink2);">${{escHtml(doc.filename)}}</span>
            <a href="/view-document/${{doc.id}}" target="_blank" class="btn btn-sm btn-outline" style="padding:2px 8px;font-size:11px;">View PDF</a>
          </div>
        `).join('');
      }} else {{
        docsHtml = '<p style="font-size:12px;color:var(--ink3);">No documents uploaded.</p>';
      }}

        let actionsHtml = '';
        if (a.status === 'pending') {{
          actionsHtml += `<button class="btn btn-primary" onclick="updateApplicationStatus(${{id}}, 'approved')">Approve</button>`;
          actionsHtml += `<button class="btn btn-danger" onclick="updateApplicationStatus(${{id}}, 'rejected')">Reject</button>`;
        }} else if (a.status === 'approved') {{
          actionsHtml += `<a href="/assessments" class="btn btn-primary">Go to Assessments</a>`;
        }} else if (a.status === 'assessment_passed') {{
          actionsHtml += `<button class="btn btn-primary" onclick="scheduleInterview(${{id}})">Schedule Interview</button>`;
        }} else if (a.status === 'interview_scheduled') {{
          actionsHtml += `<a href="/evaluations" class="btn btn-primary">Go to Evaluations</a>`;
        }} else if (a.status === 'interview_passed' || a.status === 'offer_accepted') {{
          // If they passed interview, they go to evaluation, then offer, then hire.
          // The user said: "if you pass interview, you get to be evaluated, and you will be hired or rejected."
          actionsHtml += `<button class="btn btn-success" onclick="updateApplicationStatus(${{id}}, 'hired')">Hire Now</button>`;
        }}

        document.getElementById('appModalContent').innerHTML = `
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
          <div style="width:44px;height:44px;border-radius:11px;background:linear-gradient(135deg,#4776E6,#8E54E9);
            flex-shrink:0;display:flex;align-items:center;justify-content:center;
            font-family:\'Sora\',sans-serif;font-weight:800;font-size:16px;color:#fff;">
            ${{(a.applicant_name||\'?\')[0].toUpperCase()}}
          </div>
          <div>
            <div style="font-family:\'Sora\',sans-serif;font-weight:700;font-size:15px;color:var(--ink);">${{escHtml(a.applicant_name||\'N/A\')}}</div>
            <div style="font-size:12.5px;color:var(--ink3);">${{escHtml(a.applicant_email||\'\')}}</div>
          </div>
          <div style="margin-left:auto;display:flex;gap:10px;align-items:center;">
            ${{a.ai_score ? `
            <div style="text-align:center;">
              <div style="font-size:9px;color:var(--ink3);text-transform:uppercase;">AI Score</div>
              <div style="font-family:\'Sora\',sans-serif;font-weight:800;font-size:14px;color:var(--blue);">${{parseFloat(a.ai_score).toFixed(1)}}</div>
            </div>` : ''}}
            ${{sc ? `<div style="background:${{scBg}};border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
              <span style="font-family:\'Sora\',sans-serif;font-weight:800;font-size:14px;color:${{scCol}};">${{sc}}</span></div>` : ''}}
          </div>
        </div>
        <table style="width:100%;border-collapse:collapse;margin-bottom:15px;">
          ${{_dtrow(\'Position\', a.job_title||\'—\')}}
          ${{_dtrow(\'Department\', a.department||\'—\')}}
          ${{_dtrow(\'Applied\', (a.application_date||\'—\').toString().slice(0,10))}}
          ${{_dtrow(\'Status\', `<span class="badge ${{_appBadge(a.status)}}">${{(a.status||\'pending\').charAt(0).toUpperCase()+(a.status||\'pending\').slice(1).replace(\'_\',\' \')}}</span>`)}}
        </table>
        
        <div style="margin-bottom:15px;">
          <h4 style="font-size:12px;text-transform:uppercase;color:var(--ink3);margin-bottom:8px;">Documents</h4>
          ${{docsHtml}}
        </div>

        ${{a.cover_letter ? `
        <div style="margin-bottom:15px;">
          <h4 style="font-size:12px;text-transform:uppercase;color:var(--ink3);margin-bottom:8px;">Cover Letter</h4>
          <div style="background:var(--bg);padding:12px;border-radius:8px;font-size:13px;color:var(--ink2);line-height:1.6;max-height:120px;overflow-y:auto;white-space:pre-wrap;">
            ${{escHtml(a.cover_letter)}}
          </div>
        </div>` : ''}}
        
        ${{a.resume_text ? `
        <div style="margin-bottom:15px;">
          <h4 style="font-size:12px;text-transform:uppercase;color:var(--ink3);margin-bottom:8px;">Resume Text (Parsed)</h4>
          <div style="background:var(--bg);padding:12px;border-radius:8px;font-size:13px;color:var(--ink2);line-height:1.6;max-height:200px;overflow-y:auto;white-space:pre-wrap;">
            ${{escHtml(a.resume_text)}}
          </div>
        </div>` : ''}}

        <div style="display:flex;gap:8px;margin-top:20px;flex-wrap:wrap;">
          ${{actionsHtml}}
          <a href="/communications?app_id=${{id}}" class="btn btn-outline">Email</a>
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
  return {{
    pending:             \'badge-amber\',
    shortlisted:         \'badge-green\',
    rejected:            \'badge-red\',
    assessment_pending:  \'badge-blue\',
    assessment_passed:   \'badge-green\',
    assessment_failed:   \'badge-red\',
    interview_scheduled: \'badge-blue\',
    interview_passed:    \'badge-green\',
    interview_failed:    \'badge-red\',
    offer_made:          \'badge-blue\',
    offer_accepted:      \'badge-green\',
    offer_rejected:      \'badge-red\',
    hired:               \'badge-green\'
  }}[(s||\'\').toLowerCase()] || \'badge-neutral\';
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
    "pending":            ("badge-amber",   "Pending"),
    "approved":           ("badge-green",   "Approved"),
    "rejected":           ("badge-red",     "Rejected"),
    "assessment_sent":    ("badge-blue",    "Assessment Sent"),
    "assessment_passed":  ("badge-green",   "Assessment Passed"),
    "assessment_failed":  ("badge-red",     "Assessment Failed"),
    "interview_scheduled":("badge-blue",    "Interviewing"),
    "interview_passed":   ("badge-green",   "Passed Interview"),
    "hiring_approved":    ("badge-teal",    "Hiring Approved"),
    "interview_failed":   ("badge-red",     "Interview Failed"),
    "offer_sent":         ("badge-blue",    "Offer Sent"),
    "offer_accepted":     ("badge-green",   "Offer Accepted"),
    "offer_rejected":     ("badge-red",     "Offer Rejected"),
    "hired":              ("badge-purple",  "Hired"),
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
            <button class="btn btn-outline btn-sm" onclick="editJob({j.get('id',0)})"><svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg> Edit</button>
            <button class="btn btn-danger btn-sm" onclick="deleteJob({j.get('id',0)})">Delete</button>
          </div></td>
        </tr>"""
    return rows


def _build_app_rows(applications: list) -> str:
    if not applications:
        return '<tr><td colspan="9" style="text-align:center;padding:40px;color:var(--ink3);">No applications yet.</td></tr>'
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

        # Build status select (Strictly Approve/Reject for pending)
        opts = ""
        if status == "pending":
            opts = f"""
                <option value="pending" selected>Pending</option>
                <option value="approved">Approve</option>
                <option value="rejected">Reject</option>
            """
        else:
            # For other statuses, just show the current one and a Reject option
            lbl = _STATUS_APP.get(status, ("badge-neutral", status.title()))[1]
            opts = f'<option value="{status}" selected>{lbl}</option>'
            
            # Workflow transitions
            if status == "approved":
                opts += '<option value="assessment_sent">Send Assessment</option>'
            elif status == "assessment_passed":
                opts += '<option value="interview_scheduled">Schedule Interview</option>'
            elif status == "hiring_approved":
                opts += '<option value="offer_sent">Prepare Offer</option>'
            elif status == "offer_accepted":
                opts += '<option value="hired">Finalize Hire</option>'
                
            if status not in ["rejected", "hired"]:
                opts += '<option value="rejected">Reject</option>'

        # AI Score display
        ai_score = a.get("ai_score")
        if ai_score is not None:
            asf = float(ai_score)
            ascls = "badge-green" if asf >= 75 else "badge-amber" if asf >= 50 else "badge-red"
            ai_score_html = _badge(ascls, f"{asf:.1f}")
        else:
            ai_score_html = _badge("badge-neutral", "—")
            
        ai_status = (a.get("ai_status") or "pending").title()
        ai_status_html = _badge("badge-blue" if ai_status.lower() == "recommended" else "badge-neutral", ai_status)

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
          <td>{ai_score_html}</td>
          <td>{ai_status_html}</td>
          <td style="white-space:nowrap;">{date}</td>
          <td>
            <select class="status-sel" onchange="updateApplicationStatus({aid}, this.value)">{opts}</select>
          </td>
          <td><div class="action-grp">
            <button class="btn btn-outline btn-sm" onclick="viewApplication({aid})">View</button>
            {f'<a href="/evaluations" class="btn btn-primary btn-sm" style="text-decoration:none;">Evaluate</a>' if status == 'interview_passed' else ''}
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
        # Use extended job creator so we can persist work_mode if present.
        job_id = db.create_job(
            title=data['title'],
            department=data['department'],
            location=data.get('location',''),
            work_mode=data.get('work_mode') or None,
            salary_min=None,
            salary_max=None,
            job_description=data.get('description',''),
            requirements=data.get('requirements',''),
        )
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
        # Best-effort: persist work_mode when present (and column exists).
        if data.get("work_mode") is not None:
            try:
                conn = sqlite3.connect(db.db_path)
                cur = conn.cursor()
                cur.execute("PRAGMA table_info(jobs)")
                cols = [r[1] for r in cur.fetchall()]
                if "work_mode" in cols:
                    cur.execute("UPDATE jobs SET work_mode = ? WHERE id = ?", (data.get("work_mode"), data["job_id"]))
                    conn.commit()
                conn.close()
            except Exception:
                pass
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