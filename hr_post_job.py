from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from database import ResumeDatabase
from hr_base import app, get_current_user, get_base_html, get_end_html, send_email
from datetime import datetime
import os

db = ResumeDatabase()

TEMPLATES = {
    "software_engineer": {
        "job_title": "Software Engineer", "department": "Engineering",
        "employment_type": "full-time", "experience_level": "mid",
        "location": "Kigali, Rwanda", "work_mode": "hybrid",
        "salary_min": "$100,000", "salary_max": "$150,000",
        "job_description": "We are looking for a talented Software Engineer to join our growing team. You will design, develop, and maintain high-quality software solutions.\n\nKey Responsibilities:\n- Design and develop scalable, maintainable solutions\n- Write clean, well-documented code\n- Collaborate with cross-functional teams\n- Participate in code reviews\n- Troubleshoot and debug existing systems",
        "requirements": "• Bachelor's degree in Computer Science or related field\n• 3+ years professional experience\n• Proficiency in Python, JavaScript, or Java\n• Experience with web frameworks\n• Knowledge of SQL and NoSQL databases\n• Git version control",
        "nice_to_have": "• Experience with microservices architecture\n• Docker & Kubernetes knowledge\n• CI/CD pipeline experience\n• Open-source contributions",
        "benefits": "• Competitive salary & equity\n• Health, dental, vision insurance\n• Flexible work arrangements\n• Professional development budget\n• Generous PTO",
    },
    "product_manager": {
        "job_title": "Product Manager", "department": "Product",
        "employment_type": "full-time", "experience_level": "mid",
        "location": "Kigali, Rwanda", "work_mode": "hybrid",
        "salary_min": "$110,000", "salary_max": "$160,000",
        "job_description": "We are seeking a strategic Product Manager to drive product development. You will define product vision, strategy, and roadmap while working closely with engineering, design, and business teams.",
        "requirements": "• Bachelor's in Business, Engineering, or related field\n• 3+ years product management experience\n• Strong analytical skills\n• Excellent communication and presentation skills\n• Data-driven decision making approach",
        "nice_to_have": "• MBA or advanced degree\n• Experience in SaaS\n• Agile methodology knowledge",
        "benefits": "• Competitive salary and bonuses\n• Stock options\n• Comprehensive health benefits\n• Flexible work arrangements",
    },
    "designer": {
        "job_title": "UX/UI Designer", "department": "Design",
        "employment_type": "full-time", "experience_level": "junior",
        "location": "Kigali, Rwanda", "work_mode": "remote",
        "salary_min": "$70,000", "salary_max": "$100,000",
        "job_description": "We're looking for a creative UX/UI Designer to shape exceptional user experiences. You'll work across product, engineering, and marketing to deliver beautiful, functional interfaces.",
        "requirements": "• Portfolio demonstrating strong design sensibility\n• Proficiency in Figma, Sketch, or Adobe XD\n• 2+ years UX/UI design experience\n• Understanding of design systems\n• Strong communication skills",
        "nice_to_have": "• Experience with motion design\n• Basic front-end coding knowledge\n• User research experience",
        "benefits": "• Remote-first culture\n• Design tools budget\n• Continuous learning allowance",
    },
    "marketing": {
        "job_title": "Marketing Specialist", "department": "Marketing",
        "employment_type": "full-time", "experience_level": "junior",
        "location": "Kigali, Rwanda", "work_mode": "hybrid",
        "salary_min": "$60,000", "salary_max": "$85,000",
        "job_description": "Join our marketing team and help grow ZIBITECH's brand. You'll run campaigns, manage social channels, and analyze performance data to maximize ROI.",
        "requirements": "• 2+ years marketing experience\n• Strong writing and communication skills\n• Experience with digital marketing tools\n• Analytics mindset",
        "nice_to_have": "• SEO/SEM experience\n• Graphic design skills\n• B2B marketing background",
        "benefits": "• Competitive pay\n• Health insurance\n• Marketing conferences budget",
    },
}


@app.get("/post-job", response_class=HTMLResponse)
async def post_job_page(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/", status_code=302)

    today = datetime.now().strftime("%Y-%m-%d")

    # Build template select options
    tpl_btns = ""
    labels = {"software_engineer":"Software Engineer","product_manager":"Product Manager",
               "designer":"UX/UI Designer","marketing":"Marketing Specialist"}
    for key, label in labels.items():
        tpl_btns += f'<button type="button" class="tpl-btn" onclick="applyTemplate(\'{key}\')">{label}</button>'

    # Serialise templates for JS
    import json as _json
    tpl_js = _json.dumps(TEMPLATES)

    page = f"""
<!-- ══ PAGE HEADER ══ -->
<div class="page-hd">
  <div>
    <div class="page-title">Post a New Job</div>
    <div class="page-sub">Create a compelling job posting to attract the best candidates.</div>
  </div>
  <div style="display:flex;gap:10px;">
    <button class="btn btn-outline" onclick="clearDraft()">Clear Draft</button>
    <button class="btn btn-outline" onclick="openPreview()"><svg width='13' height='13' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><path d='M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z'/><circle cx='12' cy='12' r='3'/></svg> Preview</button>
    <button class="btn btn-primary" onclick="document.getElementById('postBtn').click()">
      <svg width='13' height='13' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2.5'>
        <line x1='12' y1='5' x2='12' y2='19'/><line x1='5' y1='12' x2='19' y2='12'/>
      </svg>
      Post Job
    </button>
  </div>
</div>

<!-- ══ TWO-COLUMN ══ -->
<div style="display:grid;grid-template-columns:1fr 280px;gap:20px;align-items:start;">

  <!-- LEFT: Form -->
  <div style="display:flex;flex-direction:column;gap:20px;">

    <!-- Basic info -->
    <div class="card" style="animation:fadeUp 0.3s ease both;">
      <div class="card-hd"><span class="card-title">Basic Information</span></div>
      <div class="card-bd">
        <div class="form-grid">
          <div class="form-group full"><label class="form-label">Job Title *</label>
            <input class="form-ctrl" type="text" id="job_title" placeholder="e.g. Senior Software Engineer" required></div>
          <div class="form-group"><label class="form-label">Department *</label>
            <select class="form-ctrl" id="department" required>
              <option value="">Select Department</option>
              <option value="Engineering">Engineering</option>
              <option value="Marketing">Marketing</option>
              <option value="Sales">Sales</option>
              <option value="HR">Human Resources</option>
              <option value="Finance">Finance</option>
              <option value="Operations">Operations</option>
              <option value="Customer Service">Customer Service</option>
              <option value="Product">Product</option>
              <option value="Design">Design</option>
            </select></div>
          <div class="form-group"><label class="form-label">Employment Type *</label>
            <select class="form-ctrl" id="employment_type" required>
              <option value="">Select Type</option>
              <option value="full-time">Full-time</option>
              <option value="part-time">Part-time</option>
              <option value="contract">Contract</option>
              <option value="internship">Internship</option>
              <option value="temporary">Temporary</option>
            </select></div>
          <div class="form-group"><label class="form-label">Experience Level *</label>
            <select class="form-ctrl" id="experience_level" required>
              <option value="">Select Level</option>
              <option value="entry">Entry Level (0–2 yrs)</option>
              <option value="junior">Junior (2–5 yrs)</option>
              <option value="mid">Mid-Level (5–8 yrs)</option>
              <option value="senior">Senior (8–12 yrs)</option>
              <option value="lead">Lead (12+ yrs)</option>
            </select></div>
          <div class="form-group"><label class="form-label">Location *</label>
            <input class="form-ctrl" type="text" id="location" placeholder="City or Remote" required></div>
          <div class="form-group"><label class="form-label">Work Mode *</label>
            <select class="form-ctrl" id="work_mode" required>
              <option value="">Select Mode</option>
              <option value="onsite">On-site</option>
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
              <option value="flexible">Flexible</option>
            </select></div>
          <div class="form-group"><label class="form-label">Min Salary</label>
            <input class="form-ctrl" type="text" id="salary_min" placeholder="e.g. $80,000"></div>
          <div class="form-group"><label class="form-label">Max Salary</label>
            <input class="form-ctrl" type="text" id="salary_max" placeholder="e.g. $120,000"></div>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="card" style="animation:fadeUp 0.3s ease 0.07s both;">
      <div class="card-hd">
        <span class="card-title">Job Content</span>
        <span class="card-tag" id="charInfo">0 chars</span>
      </div>
      <div class="card-bd">
        <div class="form-group" style="margin-bottom:16px;">
          <label class="form-label">Job Description *</label>
          <textarea class="form-ctrl" id="job_description" rows="9" required
            placeholder="Describe the role, key responsibilities, and what the candidate will do day-to-day…"
            style="resize:vertical;" oninput="updateCharCount()"></textarea>
        </div>
        <div class="form-group" style="margin-bottom:16px;">
          <label class="form-label">Requirements *</label>
          <textarea class="form-ctrl" id="requirements" rows="6" required
            placeholder="Required qualifications, skills, and experience…"
            style="resize:vertical;"></textarea>
        </div>
        <div class="form-group" style="margin-bottom:16px;">
          <label class="form-label">Nice to Have</label>
          <textarea class="form-ctrl" id="nice_to_have" rows="4"
            placeholder="Preferred qualifications that would make a candidate stand out…"
            style="resize:vertical;"></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Benefits & Perks</label>
          <textarea class="form-ctrl" id="benefits" rows="4"
            placeholder="Health insurance, equity, remote work, learning budget…"
            style="resize:vertical;"></textarea>
        </div>
      </div>
    </div>

    <!-- Extra settings -->
    <div class="card" style="animation:fadeUp 0.3s ease 0.14s both;">
      <div class="card-hd"><span class="card-title">Additional Settings</span></div>
      <div class="card-bd">
        <div class="form-grid">
          <div class="form-group"><label class="form-label">Application Deadline</label>
            <input class="form-ctrl" type="date" id="application_deadline" min="{today}"></div>
          <div class="form-group"><label class="form-label">Hiring Manager</label>
            <input class="form-ctrl" type="text" id="hiring_manager" placeholder="Manager full name"></div>
          <div class="form-group"><label class="form-label">Team Size</label>
            <input class="form-ctrl" type="number" id="team_size" min="1" placeholder="Number of people on team"></div>
        </div>
        <div style="display:flex;gap:20px;margin-top:16px;flex-wrap:wrap;">
          <label style="display:flex;align-items:center;gap:7px;font-size:13px;color:var(--ink2);cursor:pointer;">
            <input type="checkbox" id="featured_job" style="width:15px;height:15px;accent-color:var(--blue);">
            ⭐ Feature on careers page
          </label>
          <label style="display:flex;align-items:center;gap:7px;font-size:13px;color:var(--ink2);cursor:pointer;">
            <input type="checkbox" id="urgent_hiring" style="width:15px;height:15px;accent-color:var(--red);">
            <svg width='13' height='13' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><path d='M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z'/></svg> Mark as urgent
          </label>
        </div>
      </div>
    </div>

    <!-- Submit -->
    <div style="display:flex;gap:12px;flex-wrap:wrap;padding-bottom:32px;">
      <button type="button" id="postBtn" class="btn btn-primary btn-lg" onclick="submitJob()">
        <svg width='14' height='14' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'>
          <line x1='12' y1='5' x2='12' y2='19'/><line x1='5' y1='12' x2='19' y2='12'/>
        </svg>
        <span id="postBtnLabel">Post Job</span>
      </button>
      <button type="button" class="btn btn-outline btn-lg" onclick="openPreview()">Preview</button>
      <button type="button" class="btn btn-outline btn-lg" onclick="saveDraft()"><svg width='13' height='13' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><path d='M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z'/><polyline points='17 21 17 13 7 13 7 21'/><polyline points='7 3 7 8 15 8'/></svg> Save Draft</button>
    </div>
  </div>

  <!-- RIGHT: Templates + Tips -->
  <div style="display:flex;flex-direction:column;gap:16px;">

    <!-- Templates -->
    <div class="card" style="animation:fadeUp 0.3s ease 0.06s both;">
      <div class="card-hd"><span class="card-title">Load Template</span></div>
      <div class="card-bd" style="display:flex;flex-direction:column;gap:8px;">
        {tpl_btns}
      </div>
    </div>

    <!-- Writing tips -->
    <div class="card" style="animation:fadeUp 0.3s ease 0.12s both;">
      <div class="card-hd"><span class="card-title">Writing Tips</span></div>
      <div class="card-bd">
        <div style="display:flex;flex-direction:column;gap:10px;">
          {_tip("<svg width='16' height='16' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><path d='M12 20h9'/><path d='M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z'/></svg>","Be specific","Vague titles get fewer applicants. Be precise about the role.")}
          {_tip("<svg width='16' height='16' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><line x1='18' y1='20' x2='18' y2='10'/><line x1='12' y1='20' x2='12' y2='4'/><line x1='6' y1='20' x2='6' y2='14'/></svg>","Include salary","Posts with salary ranges get 30% more quality applications.")}
          {_tip("<svg width='16' height='16' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><circle cx='12' cy='12' r='10'/><circle cx='12' cy='12' r='6'/><circle cx='12' cy='12' r='2'/></svg>","List must-haves only","Keep requirements to the essentials — long lists deter talent.")}
          {_tip("<svg width='16' height='16' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><polygon points='12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2'/></svg>","Sell the role","Mention growth opportunities, team culture, and impact.")}
        </div>
      </div>
    </div>

    <!-- Auto-save indicator -->
    <div style="background:var(--bg);border-radius:10px;padding:12px 14px;border:1px solid var(--border);
                text-align:center;font-size:12px;color:var(--ink3);" id="autoSaveIndicator">
      Auto-save every 30s
    </div>

  </div>
</div>

<!-- ══ PREVIEW MODAL ══ -->
<div id="previewModal" style="display:none;position:fixed;inset:0;background:rgba(13,14,26,0.55);
     z-index:10000;align-items:center;justify-content:center;backdrop-filter:blur(6px);">
  <div style="background:var(--white);border-radius:16px;padding:32px;max-width:720px;width:90%;
              max-height:88vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.2);position:relative;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;">
      <span style="font-family:'Sora',sans-serif;font-weight:700;font-size:16px;color:var(--ink);"><svg width='14' height='14' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><path d='M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2'/><rect x='9' y='3' width='6' height='4' rx='1'/></svg> Job Posting Preview</span>
      <button onclick="closePreview()" style="background:var(--bg);border:1px solid var(--border);
              border-radius:8px;width:32px;height:32px;cursor:pointer;font-size:16px;color:var(--ink2);"><svg width='14' height='14' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><line x1='18' y1='6' x2='6' y2='18'/><line x1='6' y1='6' x2='18' y2='18'/></svg></button>
    </div>
    <div id="previewContent"></div>
  </div>
</div>

<style>
.tpl-btn {{
  display:flex;align-items:center;gap:8px;
  padding:10px 14px;border-radius:9px;border:1.5px solid var(--border);
  background:var(--white);cursor:pointer;font-family:'DM Sans',sans-serif;
  font-size:13px;font-weight:600;color:var(--ink2);transition:all 0.13s;
  text-align:left;width:100%;
}}
.tpl-btn:hover {{border-color:var(--blue);background:var(--blue-lt);color:var(--blue);transform:translateX(3px);}}

.tip-row {{display:flex;align-items:flex-start;gap:10px;}}
.tip-icon {{font-size:16px;flex-shrink:0;margin-top:1px;}}
.tip-body {{flex:1;}}
.tip-title {{font-size:12.5px;font-weight:700;color:var(--ink);margin-bottom:2px;}}
.tip-desc  {{font-size:11.5px;color:var(--ink3);line-height:1.45;}}

.spin {{width:14px;height:14px;border-radius:50%;border:2px solid var(--border);
  border-top-color:#fff;animation:spinA .7s linear infinite;display:inline-block;vertical-align:-2px;}}
@keyframes spinA {{to{{transform:rotate(360deg);}}}}

/* Preview chips */
.pv-chip {{
  display:inline-flex;align-items:center;padding:3px 11px;border-radius:20px;
  font-size:12px;font-weight:700;margin-right:6px;margin-bottom:6px;
}}
</style>

<script>
const TEMPLATES = {tpl_js};

// ── TEMPLATE ──────────────────────────────────────────
function applyTemplate(key) {{
  const t = TEMPLATES[key];
  if (!t) return;
  Object.keys(t).forEach(k => {{
    const el = document.getElementById(k);
    if (el) el.value = t[k];
  }});
  updateCharCount();
  saveDraft();
  showToast('Template Applied','Form pre-filled with '+key.replace(/_/g,' ')+' template.','success',2500);
}}

// ── CHAR COUNT ─────────────────────────────────────────
function updateCharCount() {{
  const d = (document.getElementById('job_description').value||'').length;
  const r = (document.getElementById('requirements').value||'').length;
  document.getElementById('charInfo').textContent = (d+r).toLocaleString()+' chars';
}}

// ── PREVIEW ────────────────────────────────────────────
function openPreview() {{
  const title  = gv('job_title');
  const desc   = gv('job_description');
  if (!title || !desc) {{ showToast('Missing','Fill in at least Title and Description.','warning'); return; }}

  const dept   = gv('department');
  const type   = gv('employment_type').replace('-',' ').replace(/\\b\\w/g,c=>c.toUpperCase());
  const loc    = gv('location');
  const mode   = gv('work_mode').charAt(0).toUpperCase()+gv('work_mode').slice(1);
  const smin   = gv('salary_min');
  const smax   = gv('salary_max');
  const lvl    = {{'entry':'Entry Level','junior':'Junior','mid':'Mid-Level','senior':'Senior','lead':'Lead'}}[gv('experience_level')]||gv('experience_level');
  const salary = smin||smax ? (smin||'—')+' – '+(smax||'—') : 'Competitive';
  const req    = gv('requirements');
  const nth    = gv('nice_to_have');
  const ben    = gv('benefits');
  const dead   = gv('application_deadline');
  const urgent = document.getElementById('urgent_hiring').checked;
  const feat   = document.getElementById('featured_job').checked;

  document.getElementById('previewContent').innerHTML = `
    <div style="border-radius:12px;overflow:hidden;border:1.5px solid var(--border);">
      <div style="background:linear-gradient(135deg,#3B6FE8,#6B4FDB);padding:24px 28px;">
        ${{urgent?'<span class="pv-chip" style="background:rgba(240,82,82,0.3);color:#ffb3b3;">Urgent</span>':''}}
        ${{feat?'<span class="pv-chip" style="background:rgba(255,255,255,0.2);color:#fff;">Featured</span>':''}}
        <h2 style="font-family:\'Sora\',sans-serif;font-size:22px;font-weight:800;color:#fff;margin:8px 0 12px;">${{escHtml(title)}}</h2>
        <div>
          ${{dept?`<span class="pv-chip" style="background:rgba(255,255,255,0.15);color:rgba(255,255,255,.9);"><svg width='11' height='11' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><path d='M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/><polyline points='9 22 9 12 15 12 15 22'/></svg> ${{escHtml(dept)}}</span>`:''}}
          ${{type?`<span class="pv-chip" style="background:rgba(255,255,255,0.15);color:rgba(255,255,255,.9);"><svg width='12' height='12' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><rect x='2' y='7' width='20' height='14' rx='2'/><path d='M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2'/></svg> ${{escHtml(type)}}</span>`:''}}
          ${{loc?`<span class="pv-chip" style="background:rgba(255,255,255,0.15);color:rgba(255,255,255,.9);"><svg width='11' height='11' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><path d='M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z'/><circle cx='12' cy='10' r='3'/></svg> ${{escHtml(loc)}}</span>`:''}}
          ${{mode?`<span class="pv-chip" style="background:rgba(255,255,255,0.15);color:rgba(255,255,255,.9);"><svg width='12' height='12' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><circle cx='12' cy='12' r='10'/><line x1='2' y1='12' x2='22' y2='12'/><path d='M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z'/></svg> ${{escHtml(mode)}}</span>`:''}}
        </div>
      </div>
      <div style="padding:24px 28px;background:var(--white);">
        <div style="display:flex;gap:24px;margin-bottom:20px;flex-wrap:wrap;">
          <div><div style="font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);font-weight:700;">Salary</div>
            <div style="font-family:\'Sora\',sans-serif;font-size:15px;font-weight:700;color:var(--ink);">${{escHtml(salary)}}</div></div>
          ${{lvl?`<div><div style="font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);font-weight:700;">Level</div>
            <div style="font-family:\'Sora\',sans-serif;font-size:15px;font-weight:700;color:var(--ink);">${{escHtml(lvl)}}</div></div>`:''}}
          ${{dead?`<div><div style="font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);font-weight:700;">Deadline</div>
            <div style="font-family:\'Sora\',sans-serif;font-size:15px;font-weight:700;color:var(--red);">${{escHtml(dead)}}</div></div>`:''}}
        </div>
        <h4 style="font-family:\'Sora\',sans-serif;font-size:13px;color:var(--ink);margin-bottom:8px;text-transform:uppercase;letter-spacing:.05em;">Job Description</h4>
        <div style="font-size:13.5px;color:var(--ink2);line-height:1.7;white-space:pre-wrap;margin-bottom:20px;">${{escHtml(desc)}}</div>
        ${{req?`<h4 style="font-family:\'Sora\',sans-serif;font-size:13px;color:var(--ink);margin-bottom:8px;text-transform:uppercase;letter-spacing:.05em;">Requirements</h4>
        <div style="font-size:13.5px;color:var(--ink2);line-height:1.7;white-space:pre-wrap;margin-bottom:20px;">${{escHtml(req)}}</div>`:''}}
        ${{nth?`<h4 style="font-family:\'Sora\',sans-serif;font-size:13px;color:var(--ink);margin-bottom:8px;text-transform:uppercase;letter-spacing:.05em;">Nice to Have</h4>
        <div style="font-size:13.5px;color:var(--ink2);line-height:1.7;white-space:pre-wrap;margin-bottom:20px;">${{escHtml(nth)}}</div>`:''}}
        ${{ben?`<h4 style="font-family:\'Sora\',sans-serif;font-size:13px;color:var(--ink);margin-bottom:8px;text-transform:uppercase;letter-spacing:.05em;">Benefits & Perks</h4>
        <div style="font-size:13.5px;color:var(--ink2);line-height:1.7;white-space:pre-wrap;">${{escHtml(ben)}}</div>`:''}}
      </div>
    </div>`;
  document.getElementById('previewModal').style.display = 'flex';
}}
function closePreview() {{ document.getElementById('previewModal').style.display='none'; }}
document.getElementById('previewModal').addEventListener('click', function(e){{ if(e.target===this) closePreview(); }});

// ── DRAFT ─────────────────────────────────────────────
const DRAFT_FIELDS = ['job_title','department','employment_type','experience_level','location',
  'work_mode','salary_min','salary_max','job_description','requirements','nice_to_have',
  'benefits','application_deadline','hiring_manager','team_size'];

function saveDraft() {{
  const data = {{}};
  DRAFT_FIELDS.forEach(id => {{ const el = document.getElementById(id); if(el) data[id]=el.value; }});
  data.featured_job  = document.getElementById('featured_job').checked;
  data.urgent_hiring = document.getElementById('urgent_hiring').checked;
  localStorage.setItem('jobDraft', JSON.stringify(data));
  const ind = document.getElementById('autoSaveIndicator');
  ind.textContent = 'Saved at '+new Date().toLocaleTimeString();
  setTimeout(()=>{{ ind.textContent='Auto-save every 30s'; }}, 2500);
}}

function clearDraft() {{
  DRAFT_FIELDS.forEach(id => {{ const el = document.getElementById(id); if(el) el.value=''; }});
  document.getElementById('featured_job').checked  = false;
  document.getElementById('urgent_hiring').checked = false;
  localStorage.removeItem('jobDraft');
  updateCharCount();
  showToast('Cleared','Form and draft cleared.','info',2000);
}}

function loadDraft() {{
  const raw = localStorage.getItem('jobDraft');
  if (!raw) return;
  try {{
    const data = JSON.parse(raw);
    DRAFT_FIELDS.forEach(id => {{ const el = document.getElementById(id); if(el && data[id]) el.value=data[id]; }});
    if (data.featured_job)  document.getElementById('featured_job').checked  = true;
    if (data.urgent_hiring) document.getElementById('urgent_hiring').checked = true;
    updateCharCount();
    showToast('Draft Restored','Your last saved draft has been loaded.','info',3000);
  }} catch(e) {{ localStorage.removeItem('jobDraft'); }}
}}

setInterval(saveDraft, 30000);

// ── SUBMIT ────────────────────────────────────────────
function gv(id) {{ return (document.getElementById(id)?.value||'').trim(); }}

function submitJob() {{
  const required = ['job_title','department','employment_type','experience_level','location','work_mode','job_description','requirements'];
  for (const id of required) {{
    if (!gv(id)) {{
      showToast('Required Field', id.replace(/_/g,' ').replace(/\\b\\w/g,c=>c.toUpperCase())+' is required.', 'warning');
      document.getElementById(id)?.focus();
      return;
    }}
  }}

  const btn = document.getElementById('postBtn');
  const lbl = document.getElementById('postBtnLabel');
  btn.disabled = true;
  lbl.innerHTML = '<div class="spin"></div> Posting…';

  const data = {{}};
  DRAFT_FIELDS.forEach(id => {{ data[id] = gv(id); }});
  data.featured_job  = document.getElementById('featured_job').checked;
  data.urgent_hiring = document.getElementById('urgent_hiring').checked;

  fetch('/api/post-job', {{
    method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(data)
  }})
  .then(r => r.json())
  .then(d => {{
    btn.disabled = false;
    lbl.textContent = 'Post Job';
    if (d.success) {{
      showToast('Job Posted','Redirecting to job management…','success');
      localStorage.removeItem('jobDraft');
      setTimeout(()=>{{ window.location.href='/jobs'; }},1400);
    }} else {{
      showToast('Error', d.error||'Failed to post.','error');
    }}
  }})
  .catch(err => {{
    btn.disabled=false; lbl.textContent='Post Job';
    showToast('Network Error', err.message,'error');
  }});
}}

// ── UTILS ─────────────────────────────────────────────
function escHtml(s) {{
  if(!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/\'/g,'&#39;');
}}

window.addEventListener('load', loadDraft);
</script>
"""
    return HTMLResponse(content=get_base_html("Post Job", "post-job", current_user) + page + get_end_html())


def _tip(icon: str, title: str, desc: str) -> str:
    return f"""<div class="tip-row">
  <span class="tip-icon">{icon}</span>
  <div class="tip-body">
    <div class="tip-title">{title}</div>
    <div class="tip-desc">{desc}</div>
  </div>
</div>"""


# ── BACKEND ROUTE (100% UNCHANGED) ───────────────────────────────────────────

@app.post("/api/post-job")
async def post_job(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        required_fields = ['job_title','department','employment_type','experience_level','location','work_mode','job_description','requirements']
        for f in required_fields:
            if not data.get(f):
                return JSONResponse(content={"success": False, "error": f"Missing: {f}"}, status_code=400)
        job_id = db.create_job(
            title=data['job_title'], department=data['department'],
            employment_type=data['employment_type'], experience_level=data['experience_level'],
            location=data['location'], work_mode=data['work_mode'],
            salary_min=data.get('salary_min'), salary_max=data.get('salary_max'),
            job_description=data['job_description'], requirements=data['requirements'],
            nice_to_have=data.get('nice_to_have',''), benefits=data.get('benefits',''),
            application_deadline=data.get('application_deadline'),
            hiring_manager=data.get('hiring_manager'),
            team_size=data.get('team_size'),
            featured_job=data.get('featured_job', False),
            urgent_hiring=data.get('urgent_hiring', False),
            posted_by=current_user)
        send_email(current_user,
            f"New Job Posted: {data['job_title']}",
            f"<h2>New Job Posting</h2><p><strong>{data['job_title']}</strong> — {data['department']}<br>Location: {data['location']}<br>Posted by: {current_user}</p>",
            is_html=True)
        return JSONResponse(content={"success": True, "job_id": job_id})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)