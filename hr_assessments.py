"""
HR Assessment Management Module
Handles: Creating assessments, sending invites to accepted candidates,
         viewing results, and pipeline gating (accept/reject for assessment).
"""

import secrets
from datetime import datetime, timedelta
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi import Request
import json

from hr_base import app, get_current_user, get_base_html, get_end_html, send_email
from database import ResumeDatabase

db = ResumeDatabase()

# ── PIPELINE GATE: ACCEPT / REJECT FOR ASSESSMENT ─────────────────────────────

@app.post("/api/accept-for-assessment")
async def accept_for_assessment(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        application_id = int(data.get("application_id", 0))
        if not application_id:
            return JSONResponse(content={"success": False, "error": "Missing application_id"}, status_code=400)
        conn = __import__('sqlite3').connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE job_applications SET status = 'accepted_for_assessment' WHERE id = ?", (application_id,))
        conn.commit(); conn.close()
        return JSONResponse(content={"success": True, "message": "Candidate accepted for assessment"})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/reject-application")
async def reject_application(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        application_id = int(data.get("application_id", 0))
        reason = data.get("reason", "Does not meet requirements")
        if not application_id:
            return JSONResponse(content={"success": False, "error": "Missing application_id"}, status_code=400)
        conn = __import__('sqlite3').connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE job_applications SET status = 'rejected' WHERE id = ?", (application_id,))
        conn.commit(); conn.close()
        return JSONResponse(content={"success": True, "message": "Candidate rejected"})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


# ── ASSESSMENT MANAGEMENT (HR SIDE) ───────────────────────────────────────────

@app.get("/assessments", response_class=HTMLResponse)
async def assessment_management(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/", status_code=302)

    assessments = db.get_all_assessments()
    results     = db.get_all_assessment_results()
    jobs        = db.get_all_jobs()

    # Candidates accepted for assessment (pipeline gate)
    conn = __import__('sqlite3').connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute("""SELECT ja.id as app_id, a.name, a.email, j.title as job_title, ja.job_id,
                         ai_r.status as invite_status, ar.percentage, ar.passed, ar.tab_switch_count
                     FROM job_applications ja
                     JOIN applicants a ON ja.applicant_id = a.id
                     JOIN jobs j ON ja.job_id = j.id
                     LEFT JOIN assessment_invites ai_r ON ja.id = ai_r.application_id
                     LEFT JOIN assessment_results ar ON ja.id = ar.application_id
                     WHERE ja.status IN ('approved', 'assessment_sent', 'assessment_completed')
                     ORDER BY ja.application_date DESC""")
    rows = cursor.fetchall()
    accepted_cols = ['app_id','name','email','job_title','job_id','invite_status','percentage','passed','tab_switch_count']
    accepted_candidates = [dict(zip(accepted_cols, r)) for r in rows]
    conn.close()

    page = _build_assessment_page(current_user, assessments, results, jobs, accepted_candidates)
    return HTMLResponse(content=page)


def _build_assessment_page(user, assessments, results, jobs, accepted_candidates):
    def badge(s):
        colors = {
            'pending':   ('#FFF3CD','#856404'),
            'completed': ('#D1E7DD','#0A3622'),
            'failed':    ('#F8D7DA','#842029'),
            'passed':    ('#D1E7DD','#0A3622'),
        }
        bg, fg = colors.get(s, ('#e9ecef','#495057'))
        return f'<span style="padding:2px 10px;border-radius:20px;font-size:11px;font-weight:700;background:{bg};color:{fg};">{s.upper()}</span>'

    jobs_opts = ''.join(f'<option value="{j["id"]}">{j["title"]} ({j["department"]})</option>' for j in jobs)
    assess_opts = ''.join(f'<option value="{a["id"]}">{a["title"]}</option>' for a in assessments)

    candidate_rows = ''
    for c in accepted_candidates:
        score_cell = f'{c["percentage"]:.1f}%' if c["percentage"] is not None else '—'
        passed_badge = badge('passed' if c['passed'] else ('failed' if c['percentage'] is not None else 'pending'))
        cheat = ''
        if c['tab_switch_count'] and c['tab_switch_count'] > 2:
            cheat = f'<span title="Switched tabs {c["tab_switch_count"]} times" style="color:#dc3545;margin-left:6px;">{c["tab_switch_count"]} tab switches</span>'
        invite_action = ''
        if not c['invite_status'] and assessments:
            invite_action = f'''<button class="btn-xs btn-primary" onclick="sendAssessmentInvite({c['app_id']})"><svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="vertical-align:-2px;margin-right:4px;"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>Send Test</button>'''
        elif c['invite_status'] == 'pending':
            invite_action = '<span style="color:var(--ink3);font-size:12px;">Invite sent</span>'
        candidate_rows += f"""
        <tr>
          <td><strong>{c['name']}</strong><br><small style="color:var(--ink3);">{c['email']}</small></td>
          <td>{c['job_title']}</td>
          <td>{score_cell} {cheat}</td>
          <td>{passed_badge}</td>
          <td>{invite_action}</td>
        </tr>"""

    result_rows = ''
    for r in results:
        pct = r.get('percentage', 0) or 0
        bar_col = '#198754' if r['passed'] else '#dc3545'
        cheat_warn = ''
        if r.get('tab_switch_count', 0) > 2:
            cheat_warn = f'<br><small style="color:#dc3545;">{r["tab_switch_count"]} tab switches detected</small>'
        result_rows += f"""
        <tr>
          <td><strong>{r['applicant_name']}</strong></td>
          <td>{r['job_title']}</td>
          <td>{r['assessment_title']}</td>
          <td>
            <div style="display:flex;align-items:center;gap:8px;">
              <div style="flex:1;background:#e9ecef;border-radius:4px;height:8px;">
                <div style="width:{min(pct,100):.0f}%;background:{bar_col};border-radius:4px;height:8px;"></div>
              </div>
              <span style="font-weight:700;color:{bar_col};">{pct:.1f}%</span>
            </div>{cheat_warn}
          </td>
          <td>{badge('passed' if r['passed'] else 'failed')}</td>
          <td style="color:var(--ink3);font-size:12px;">{(r['completed_at'] or '')[:10]}</td>
        </tr>"""

    assess_cards = ''
    for a in assessments:
        assess_cards += f"""
        <div class="card" style="padding:20px;margin-bottom:12px;display:flex;align-items:center;gap:16px;justify-content:space-between;">
          <div>
            <div style="font-weight:700;font-size:15px;">{a['title']}</div>
            <div style="color:var(--ink3);font-size:12px;">{a.get('job_title') or 'All Jobs'} · {a['question_count']} questions · {a['time_limit_minutes']} min · Passing: {a['passing_score']}%</div>
          </div>
          <div style="display:flex;gap:8px;">
            <button class="btn-xs btn-outline" onclick="viewQuestions({a['id']})"><svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="vertical-align:-2px;margin-right:4px;"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/></svg>Questions</button>
            <button class="btn-xs btn-primary" onclick="addQuestion({a['id']})"><svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="vertical-align:-2px;margin-right:4px;"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>Add Q</button>
          </div>
        </div>"""

    if not assess_cards:
        assess_cards = '<div style="text-align:center;padding:32px;color:var(--ink3);">No assessments yet. Create one above.</div>'

    total_assessments = len(assessments)
    total_results = len(results)
    pass_count = sum(1 for r in results if r.get('passed'))
    pass_rate = (pass_count / total_results * 100) if total_results else 0
    pending_invites = sum(1 for c in accepted_candidates if c.get('invite_status') == 'pending')

    html = get_base_html("Assessment Management", "assessments") + f"""
<div class="page-hd">
  <div>
    <div class="page-title">Assessment Management</div>
    <div class="page-sub">Create tests, invite candidates, and monitor results with integrity signals.</div>
  </div>
</div>

<div class="stats-row" style="margin-bottom:24px;">
  <div class="stat-tile">
    <div class="stat-icon"><svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg></div>
    <div class="stat-body"><div class="stat-label">Assessments</div><div class="stat-value">{total_assessments}</div></div>
  </div>
  <div class="stat-tile">
    <div class="stat-icon"><svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div>
    <div class="stat-body"><div class="stat-label">Completed Results</div><div class="stat-value">{total_results}</div></div>
  </div>
  <div class="stat-tile">
    <div class="stat-icon"><svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
    <div class="stat-body"><div class="stat-label">Pass Rate</div><div class="stat-value">{pass_rate:.0f}%</div></div>
  </div>
  <div class="stat-tile">
    <div class="stat-icon"><svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></div>
    <div class="stat-body"><div class="stat-label">Pending Invites</div><div class="stat-value">{pending_invites}</div></div>
  </div>
</div>

<style>
  .grid-2 {{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:20px;
    align-items:start;
  }}
  .form-input {{
    width:100%;
    padding:10px 12px;
    border:1.5px solid var(--border);
    border-radius:8px;
    background:var(--white);
    font-family:'DM Sans',sans-serif;
    font-size:13px;
    color:var(--ink);
    outline:none;
    transition:border-color .15s;
  }}
  .form-input:focus {{ border-color:var(--blue); }}
  .btn-xs {{
    display:inline-flex;
    align-items:center;
    padding:6px 10px;
    border-radius:8px;
    border:1.5px solid var(--border);
    background:var(--white);
    font-size:12px;
    font-weight:700;
    cursor:pointer;
    transition:all .15s;
    color:var(--ink2);
  }}
  .btn-xs.btn-primary {{
    background:var(--blue);
    color:#fff;
    border-color:var(--blue);
  }}
  .btn-xs.btn-primary:hover {{ filter:brightness(.95); }}
  .btn-xs.btn-outline:hover {{ border-color:var(--blue); color:var(--blue); }}
  @media (max-width:980px) {{
    .grid-2 {{ grid-template-columns:1fr; }}
  }}
</style>

<div class="grid grid-2" style="gap:24px;margin-bottom:24px;">

  <!-- Create Assessment -->
  <div class="card" style="padding:24px;">
    <h2 style="font-size:16px;font-weight:700;margin-bottom:16px;"><svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="vertical-align:-2px;margin-right:6px;"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>Create Assessment</h2>
    <div style="display:flex;flex-direction:column;gap:12px;">
      <input id="newAssessTitle" class="form-input" placeholder="Assessment Title (e.g. Python Developer Test)">
      <select id="newAssessJob" class="form-input">
        <option value="">— Link to Job (Optional) —</option>
        {jobs_opts}
      </select>
      <textarea id="newAssessDesc" class="form-input" rows="2" placeholder="Description..."></textarea>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
        <div>
          <label style="font-size:11px;color:var(--ink3);">Time Limit (min)</label>
          <input id="newAssessTime" type="number" class="form-input" value="30" min="5" max="180">
        </div>
        <div>
          <label style="font-size:11px;color:var(--ink3);">Passing Score (%)</label>
          <input id="newAssessPass" type="number" class="form-input" value="70" min="1" max="100">
        </div>
        <div style="display:flex;align-items:flex-end;">
          <button class="btn btn-primary" style="width:100%;" onclick="createAssessment()">Create</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Pipeline: Accepted Candidates -->
  <div class="card" style="padding:24px;">
    <h2 style="font-size:16px;font-weight:700;margin-bottom:16px;"><svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="vertical-align:-2px;margin-right:6px;"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/></svg>Accepted Candidates ({len(accepted_candidates)})</h2>
    <div style="overflow-x:auto;">
      <table class="data-table" style="font-size:13px;">
        <thead><tr><th>Candidate</th><th>Job</th><th>Score</th><th>Status</th><th>Action</th></tr></thead>
        <tbody>
          {candidate_rows if candidate_rows else '<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--ink3);">No candidates accepted yet.<br><small>Use the Applications page to accept candidates.</small></td></tr>'}
        </tbody>
      </table>
    </div>
    {f'<div style="margin-top:12px;"><label style="font-size:12px;color:var(--ink3);">Send with assessment: </label><select id="inviteAssessSelect" class="form-input" style="display:inline-block;width:auto;">{assess_opts}</select></div>' if assessments else ''}
  </div>
</div>

<!-- Assessment Library -->
<div class="card" style="padding:24px;margin-bottom:24px;">
  <h2 style="font-size:16px;font-weight:700;margin-bottom:16px;"><svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="vertical-align:-2px;margin-right:6px;"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>Assessment Library ({len(assessments)})</h2>
  {assess_cards}
</div>

<!-- Results Table -->
<div class="card" style="padding:24px;">
  <h2 style="font-size:16px;font-weight:700;margin-bottom:16px;"><svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" style="vertical-align:-2px;margin-right:6px;"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>Results & Cheating Detection ({len(results)})</h2>
  <div style="overflow-x:auto;">
    <table class="data-table">
      <thead><tr><th>Candidate</th><th>Job</th><th>Assessment</th><th>Score</th><th>Result</th><th>Date</th></tr></thead>
      <tbody>
        {result_rows if result_rows else '<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--ink3);">No results yet.</td></tr>'}
      </tbody>
    </table>
  </div>
</div>

<!-- Add Question Modal -->
<div id="addQModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1000;align-items:center;justify-content:center;">
  <div style="background:#fff;border-radius:16px;padding:32px;width:600px;max-width:95vw;max-height:80vh;overflow-y:auto;">
    <h3 style="margin-bottom:16px;">Add Question</h3>
    <input type="hidden" id="addQAssessId">
    <div style="display:flex;flex-direction:column;gap:12px;">
      <select id="addQType" class="form-input" onchange="toggleQOptions()">
        <option value="multiple_choice">Multiple Choice</option>
        <option value="short_answer">Short Answer</option>
        <option value="coding">Coding Challenge</option>
        <option value="true_false">True / False</option>
      </select>
      <textarea id="addQText" class="form-input" rows="3" placeholder="Question text..."></textarea>
      <div id="optionsSection">
        <label style="font-size:12px;color:var(--ink3);">Options (one per line)</label>
        <textarea id="addQOptions" class="form-input" rows="4" placeholder="Option A&#10;Option B&#10;Option C&#10;Option D"></textarea>
        <label style="font-size:12px;color:var(--ink3);margin-top:8px;display:block;">Correct Answer</label>
        <input id="addQCorrect" class="form-input" placeholder="Exact text of correct option">
      </div>
      <div id="shortAnswerSection" style="display:none;">
        <label style="font-size:12px;color:var(--ink3);">Expected Keywords (comma-separated, for auto-grading)</label>
        <input id="addQKeywords" class="form-input" placeholder="keyword1, keyword2, keyword3">
      </div>
      <input id="addQPoints" type="number" class="form-input" value="10" placeholder="Points" min="1">
    </div>
    <div style="display:flex;gap:8px;margin-top:16px;">
      <button class="btn btn-primary" onclick="submitAddQuestion()">Add Question</button>
      <button class="btn btn-outline" onclick="document.getElementById('addQModal').style.display='none'">Cancel</button>
    </div>
  </div>
</div>

<!-- View Questions Modal -->
<div id="viewQModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1000;align-items:center;justify-content:center;">
  <div style="background:#fff;border-radius:16px;padding:32px;width:700px;max-width:95vw;max-height:80vh;overflow-y:auto;">
    <h3 id="viewQTitle" style="margin-bottom:16px;">Questions</h3>
    <div id="viewQContent"></div>
    <button class="btn btn-outline" style="margin-top:16px;" onclick="document.getElementById('viewQModal').style.display='none'">Close</button>
  </div>
</div>

<script>
function createAssessment() {{
  const title = document.getElementById('newAssessTitle').value.trim();
  if (!title) {{ alert('Please enter a title.'); return; }}
  fetch('/api/create-assessment', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{
      title,
      job_id: document.getElementById('newAssessJob').value || null,
      description: document.getElementById('newAssessDesc').value,
      time_limit: parseInt(document.getElementById('newAssessTime').value),
      passing_score: parseFloat(document.getElementById('newAssessPass').value)
    }})
  }}).then(r => r.json()).then(d => {{
    if (d.success) {{ alert('Assessment created!'); location.reload(); }}
    else alert('Error: ' + d.error);
  }});
}}

function addQuestion(assessId) {{
  document.getElementById('addQAssessId').value = assessId;
  document.getElementById('addQModal').style.display = 'flex';
}}

function toggleQOptions() {{
  const t = document.getElementById('addQType').value;
  document.getElementById('optionsSection').style.display = (t === 'multiple_choice' || t === 'true_false') ? 'block' : 'none';
  document.getElementById('shortAnswerSection').style.display = (t === 'short_answer' || t === 'coding') ? 'block' : 'none';
  if (t === 'true_false') {{
    document.getElementById('addQOptions').value = 'True\\nFalse';
  }}
}}

function submitAddQuestion() {{
  const aId = document.getElementById('addQAssessId').value;
  const qType = document.getElementById('addQType').value;
  const qText = document.getElementById('addQText').value.trim();
  if (!qText) {{ alert('Question text is required.'); return; }}
  let options = [], correct = '';
  if (qType === 'multiple_choice' || qType === 'true_false') {{
    options = document.getElementById('addQOptions').value.split('\\n').map(s => s.trim()).filter(Boolean);
    correct = document.getElementById('addQCorrect').value.trim();
  }} else {{
    correct = document.getElementById('addQKeywords').value.trim();
  }}
  fetch('/api/add-assessment-question', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{ assessment_id: aId, question_text: qText, question_type: qType, options, correct_answer: correct, points: parseInt(document.getElementById('addQPoints').value) }})
  }}).then(r => r.json()).then(d => {{
    if (d.success) {{ alert('Question added!'); document.getElementById('addQModal').style.display = 'none'; }}
    else alert('Error: ' + d.error);
  }});
}}

function viewQuestions(assessId) {{
  fetch('/api/assessment-questions/' + assessId)
    .then(r => r.json())
    .then(d => {{
      if (!d.success) {{ alert('Error loading questions.'); return; }}
      const qs = d.questions;
      document.getElementById('viewQTitle').textContent = d.assessment_title + ' — Questions (' + qs.length + ')';
      document.getElementById('viewQContent').innerHTML = qs.map((q, i) => `
        <div style="border:1px solid #e9ecef;border-radius:8px;padding:14px;margin-bottom:10px;">
          <div style="font-weight:700;margin-bottom:6px;">Q${{i+1}}. [${{q.question_type}}] ${{q.question_text}}</div>
          ${{q.options && q.options.length ? '<div style="font-size:12px;color:#495057;">' + q.options.map((o,i) => '<span style="margin-right:12px;">' + String.fromCharCode(65+i) + '. ' + o + '</span>').join('') + '</div>' : ''}}
          <div style="font-size:12px;color:#198754;margin-top:4px;">✓ ${{q.correct_answer}} · ${{q.points}} pts</div>
          <div style="margin-top:10px;display:flex;gap:8px;">
            <button class="btn-xs btn-outline" onclick='editQuestion(${{JSON.stringify(q)}})'>Edit</button>
            <button class="btn-xs btn-outline" style="border-color:#dc3545;color:#dc3545;" onclick="deleteQuestion(${{q.id}}, ${{assessId}})">Delete</button>
          </div>
        </div>`).join('') || '<p style="color:#aaa;">No questions yet.</p>';
      document.getElementById('viewQModal').style.display = 'flex';
    }});
}}

function editQuestion(q) {{
  const questionText = prompt('Edit question text:', q.question_text || '');
  if (questionText === null) return;
  const pointsRaw = prompt('Points:', String(q.points || 10));
  if (pointsRaw === null) return;
  const points = parseInt(pointsRaw, 10);
  if (!Number.isFinite(points) || points < 1) {{
    alert('Invalid points value.');
    return;
  }}

  let options = q.options || [];
  let correctAnswer = q.correct_answer || '';

  if (q.question_type === 'multiple_choice' || q.question_type === 'true_false') {{
    const optionsRaw = prompt('Options (separate with |):', (options || []).join(' | '));
    if (optionsRaw === null) return;
    options = optionsRaw.split('|').map(s => s.trim()).filter(Boolean);
    const correctRaw = prompt('Correct answer:', correctAnswer);
    if (correctRaw === null) return;
    correctAnswer = correctRaw.trim();
  }} else {{
    const keywordsRaw = prompt('Expected keywords / answer:', correctAnswer);
    if (keywordsRaw === null) return;
    correctAnswer = keywordsRaw.trim();
  }}

  fetch('/api/update-assessment-question', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{
      question_id: q.id,
      question_text: questionText.trim(),
      question_type: q.question_type,
      options: options,
      correct_answer: correctAnswer,
      points: points
    }})
  }}).then(r => r.json()).then(d => {{
    if (d.success) {{
      alert('Question updated.');
      viewQuestions(q.assessment_id);
    }} else {{
      alert('Error: ' + d.error);
    }}
  }});
}}

function deleteQuestion(questionId, assessId) {{
  if (!confirm('Delete this question?')) return;
  fetch('/api/delete-assessment-question/' + questionId, {{ method: 'DELETE' }})
    .then(r => r.json())
    .then(d => {{
      if (d.success) {{
        alert('Question deleted.');
        viewQuestions(assessId);
      }} else {{
        alert('Error: ' + d.error);
      }}
    }});
}}

function sendAssessmentInvite(appId) {{
  const sel = document.getElementById('inviteAssessSelect');
  const assessId = sel ? sel.value : null;
  if (!assessId) {{ alert('Please select an assessment first.'); return; }}
  if (!confirm('Send assessment invite to this candidate?')) return;
  fetch('/api/send-assessment-invite', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{ application_id: appId, assessment_id: assessId }})
  }}).then(r => r.json()).then(d => {{
    if (d.success) {{ alert('Invite sent! Candidate will receive the test link via email.'); location.reload(); }}
    else alert('Error: ' + d.error);
  }});
}}
</script>
""" + get_end_html()
    return html


# ── ASSESSMENT API ROUTES (HR SIDE) ───────────────────────────────────────────

@app.post("/api/create-assessment")
async def create_assessment_route(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        if not data.get('title'):
            return JSONResponse(content={"success": False, "error": "Title required"}, status_code=400)
        aid = db.create_assessment(
            title=data['title'],
            job_id=data.get('job_id'),
            description=data.get('description', ''),
            time_limit=int(data.get('time_limit', 30)),
            passing_score=float(data.get('passing_score', 70.0)),
            created_by=current_user
        )
        return JSONResponse(content={"success": True, "assessment_id": aid})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/add-assessment-question")
async def add_question_route(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        qid = db.add_assessment_question(
            assessment_id=int(data['assessment_id']),
            question_text=data['question_text'],
            question_type=data.get('question_type', 'multiple_choice'),
            options=data.get('options', []),
            correct_answer=data.get('correct_answer', ''),
            points=int(data.get('points', 10))
        )
        return JSONResponse(content={"success": True, "question_id": qid})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.get("/api/assessment-questions/{assessment_id}")
async def get_questions_route(assessment_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        questions = db.get_assessment_questions(assessment_id)
        assessment = db.get_assessment(assessment_id)
        return JSONResponse(content={"success": True, "questions": questions, "assessment_title": assessment['title'] if assessment else ""})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

@app.post("/api/update-assessment-question")
async def update_question_route(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        question_id = int(data.get('question_id', 0))
        if not question_id:
            return JSONResponse(content={"success": False, "error": "question_id is required"}, status_code=400)
        success = db.update_assessment_question(
            question_id=question_id,
            question_text=data.get('question_text', '').strip(),
            question_type=data.get('question_type', 'multiple_choice'),
            options=data.get('options', []),
            correct_answer=data.get('correct_answer', ''),
            points=int(data.get('points', 10)),
        )
        if success:
            return JSONResponse(content={"success": True})
        return JSONResponse(content={"success": False, "error": "Question not found"}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

@app.delete("/api/delete-assessment-question/{question_id}")
async def delete_question_route(question_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        success = db.delete_assessment_question(question_id)
        if success:
            return JSONResponse(content={"success": True})
        return JSONResponse(content={"success": False, "error": "Question not found"}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@app.post("/api/send-assessment-invite")
async def send_assessment_invite(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data = await request.json()
        application_id = int(data['application_id'])
        assessment_id  = int(data['assessment_id'])

        # Validate application & assessment exist
        assessment = db.get_assessment(assessment_id)
        if not assessment:
            return JSONResponse(content={"success": False, "error": "Assessment not found"}, status_code=404)

        # Get applicant email
        import sqlite3 as _sq3
        conn = _sq3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute("""SELECT a.email, a.name FROM applicants a
                          JOIN job_applications ja ON ja.applicant_id = a.id
                          WHERE ja.id = ?""", (application_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return JSONResponse(content={"success": False, "error": "Application not found"}, status_code=404)
        email, name = row

        token = secrets.token_urlsafe(32)
        expires = (datetime.now() + timedelta(days=7)).isoformat()
        db.create_assessment_invite(application_id, assessment_id, token, expires)

        # Update app status
        cursor.execute("UPDATE job_applications SET status = 'assessment_sent' WHERE id = ?", (application_id,))
        conn.commit(); conn.close()

        # Send email
        portal_url = f"http://localhost:8005/take-assessment/{token}"
        send_email(
            to_email=email,
            subject=f"TalentFlow — Assessment Invitation: {assessment['title']}",
            body=f"""<h2>Hello {name},</h2>
<p>You have been invited to complete an assessment as part of the recruitment process for <strong>{assessment['title']}</strong>.</p>
<p><strong>Time Limit:</strong> {assessment['time_limit_minutes']} minutes<br>
<strong>Passing Score:</strong> {assessment['passing_score']}%<br>
<strong>Expires:</strong> {expires[:10]}</p>
<p>Click the link below to begin your assessment:</p>
<p><a href="{portal_url}" style="background:#3b5bdb;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:700;">Start Assessment &rarr;</a></p>
<p style="color:#666;font-size:12px;">⚠️ The test must be completed in one sitting. Switching tabs will be recorded and may affect your result.</p>""",
            is_html=True
        )
        return JSONResponse(content={"success": True, "message": f"Invite sent to {email}"})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)
