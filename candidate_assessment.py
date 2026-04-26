"""
Candidate Assessment Portal
Accessible via unique token link emailed to the candidate.
Features: Timed test, cheating detection (tab-switch tracking), auto-grading.
"""

import json
import sqlite3
from datetime import datetime
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request

# from modern_portal import app   # REMOVED to avoid circular import
from database import ResumeDatabase

db = ResumeDatabase()


def register_assessment_routes(app):
    @app.get("/take-assessment/{token}", response_class=HTMLResponse)
    async def take_assessment(token: str, request: Request):
        invite = db.get_invite_by_token(token)
        if not invite:
            return HTMLResponse("<h2 style='text-align:center;padding:60px;font-family:sans-serif;'>Invalid or expired assessment link.</h2>", status_code=404)

        if invite['status'] in ('completed', 'failed'):
            return HTMLResponse(f"""<!DOCTYPE html>
    <html><head><title>Assessment Completed</title>
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;900&family=Nunito+Sans:wght@400;600&display=swap" rel="stylesheet">
    <style>body{{font-family:'Nunito Sans',sans-serif;background:#f8f9fc;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;}}
    .card{{background:#fff;border-radius:16px;padding:48px;text-align:center;box-shadow:0 8px 40px rgba(0,0,0,.1);max-width:480px;}}</style>
    </head><body>
    <div class="card">
      <div style="font-size:56px;color:#3b5bdb;">
        <svg width="56" height="56" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
      </div>
      <h1 style="font-family:'Nunito';color:#3b5bdb;">Assessment Submitted</h1>
      <p>You have already completed this assessment. You can view your score on the <a href="/track-application" style="color:#3b5bdb;">Track Application</a> page.</p>
    </div></body></html>""")

        # Check application status - only shortlisted or assessment_pending can take the test
        app_details = db.get_application_details(invite['application_id'])
        allowed_statuses = ['shortlisted', 'assessment_pending', 'assessment_sent', 'assessment_passed', 'assessment_failed']
        if app_details.get('status') not in allowed_statuses:
            return HTMLResponse(f"""<h2 style='text-align:center;padding:60px;font-family:sans-serif;'>You are not eligible to take this assessment yet.<br>Current Status: {app_details.get('status', 'Unknown')}</h2>""", status_code=403)


        questions = db.get_assessment_questions(invite['assessment_id'])
        if not questions:
            return HTMLResponse("<h2 style='text-align:center;padding:60px;font-family:sans-serif;'>This assessment has no questions yet. Please contact the recruiter.</h2>")

        # Render questions as HTML
        q_html = ''
        for i, q in enumerate(questions):
            q_type = q['question_type']
            opts_html = ''
            if q_type in ('multiple_choice', 'true_false') and q['options']:
                opts_html = '<div style="display:flex;flex-direction:column;gap:8px;margin-top:10px;">'
                for j, opt in enumerate(q['options']):
                    letter = chr(65 + j)
                    opts_html += f"""<label style="display:flex;align-items:center;gap:10px;padding:10px 14px;border:1px solid #dee2e6;border-radius:8px;cursor:pointer;transition:background .15s;" 
                      onmouseover="this.style.background='#f0f4ff'" onmouseout="this.style.background='#fff'">
                      <input type="radio" name="q_{q['id']}" value="{opt}" style="accent-color:#3b5bdb;">
                      <span><strong>{letter}.</strong> {opt}</span>
                    </label>"""
                opts_html += '</div>'
            elif q_type == 'true_false':
                for val in ['True', 'False']:
                    opts_html += f"""<label style="margin-right:20px;"><input type="radio" name="q_{q['id']}" value="{val}"> {val}</label>"""
            elif q_type in ('short_answer', 'coding'):
                rows = 8 if q_type == 'coding' else 3
                font = 'monospace' if q_type == 'coding' else 'inherit'
                opts_html = f'<textarea name="q_{q["id"]}" id="q_{q["id"]}" rows="{rows}" style="width:100%;padding:10px;border:1px solid #dee2e6;border-radius:8px;font-family:{font};margin-top:10px;font-size:14px;" placeholder="Type your answer here..."></textarea>'

            type_badge = {'multiple_choice':'Multiple Choice','true_false':'True/False','short_answer':'Short Answer','coding':'Coding'}.get(q_type, q_type)
            q_html += f"""
            <div class="q-card" id="q-{i}" style="background:#fff;border:1px solid #e9ecef;border-radius:12px;padding:24px;margin-bottom:16px;{'display:none;' if i > 0 else ''}">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <span style="font-size:12px;background:#e7f0fd;color:#3b5bdb;padding:2px 10px;border-radius:20px;font-weight:700;">{type_badge}</span>
                <span style="font-size:12px;color:#6c757d;">{q['points']} pts</span>
              </div>
              <p style="font-weight:700;font-size:15px;margin-bottom:4px;">Question {i+1} of {len(questions)}</p>
              <p style="color:#2d3748;font-size:15px;line-height:1.6;">{q['question_text']}</p>
              {opts_html}
            </div>"""

        time_seconds = int(invite['time_limit_minutes']) * 60

        return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{invite['assessment_title']} — TalentFlow Assessment</title>
  <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;900&family=Nunito+Sans:wght@400;600&display=swap" rel="stylesheet">
  <style>
    *{{box-sizing:border-box;margin:0;padding:0;}}
    body{{font-family:'Nunito Sans',sans-serif;background:#f0f4ff;color:#2d3748;}}
    .topbar{{background:#3b5bdb;color:#fff;padding:14px 24px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:100;box-shadow:0 2px 12px rgba(59,91,219,.3);}}
    .timer{{font-family:'Nunito';font-size:22px;font-weight:900;background:rgba(255,255,255,.15);padding:6px 20px;border-radius:20px;}}
    .timer.warn{{background:#dc3545;animation:pulse .8s infinite;}}
    @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.6}}}}
    .container{{max-width:760px;margin:32px auto;padding:0 16px;}}
    .progress-bar{{height:6px;background:#dee2e6;border-radius:3px;margin-bottom:24px;}}
    .progress-fill{{height:6px;background:linear-gradient(90deg,#3b5bdb,#7048e8);border-radius:3px;transition:width .3s;}}
    .form-input{{width:100%;padding:10px 14px;border:1px solid #dee2e6;border-radius:8px;font-family:'Nunito Sans';font-size:14px;}}
    .btn{{padding:10px 24px;border-radius:8px;font-weight:700;font-size:15px;cursor:pointer;border:none;transition:all .2s;}}
    .btn-primary{{background:#3b5bdb;color:#fff;}} .btn-primary:hover{{background:#2846c4;}}
    .btn-outline{{background:#fff;color:#3b5bdb;border:1px solid #3b5bdb;}} .btn-outline:hover{{background:#f0f4ff;}}
    .cheat-banner{{display:none;background:#dc3545;color:#fff;text-align:center;padding:10px;font-weight:700;font-size:14px;}}
  </style>
</head>
<body>
<div id="cheatBanner" class="cheat-banner">Tab switch detected. This has been recorded.</div>
<div class="topbar">
  <div>
    <div style="font-family:'Nunito';font-weight:900;font-size:18px;">{invite['assessment_title']}</div>
    <div style="font-size:12px;opacity:.8;">Hello, {invite['applicant_name']} · {invite['job_title']}</div>
  </div>
  <div class="timer" id="timer">--:--</div>
</div>

<div class="container">
  <div class="progress-bar"><div class="progress-fill" id="progressFill" style="width:0%"></div></div>

  <form id="assessmentForm">
    {q_html}
  </form>

  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:24px;">
    <button class="btn btn-outline" id="prevBtn" onclick="prevQ()" style="display:none;">← Previous</button>
    <div style="flex:1;"></div>
    <button class="btn btn-primary" id="nextBtn" onclick="nextQ()">Next →</button>
    <button class="btn btn-primary" id="submitBtn" onclick="submitAssessment()" style="display:none;background:#198754;">Submit Assessment ✓</button>
  </div>
</div>

<script>
const TOTAL = {len(questions)};
const INVITE_TOKEN = "{token}";
let current = 0;
let tabSwitches = 0;
let cheatingFlags = [];
let timeLeft = {time_seconds};
let timerInterval;

// ── TIMER ──
function startTimer() {{
  timerInterval = setInterval(() => {{
    timeLeft--;
    const m = String(Math.floor(timeLeft / 60)).padStart(2,'0');
    const s = String(timeLeft % 60).padStart(2,'0');
    document.getElementById('timer').textContent = m + ':' + s;
    if (timeLeft <= 60) document.getElementById('timer').classList.add('warn');
    if (timeLeft <= 0) {{
      clearInterval(timerInterval);
      cheatingFlags.push('Time expired — auto-submitted');
      submitAssessment();
    }}
  }}, 1000);
}}

// ── CHEATING DETECTION ──
document.addEventListener('visibilitychange', () => {{
  if (document.hidden) {{
    tabSwitches++;
    cheatingFlags.push('Tab hidden at ' + new Date().toISOString());
    document.getElementById('cheatBanner').style.display = 'block';
    setTimeout(() => document.getElementById('cheatBanner').style.display = 'none', 3000);
  }}
}});
window.addEventListener('blur', () => {{
  tabSwitches++;
  cheatingFlags.push('Window blur at ' + new Date().toISOString());
}});

// ── NAVIGATION ──
function showQ(idx) {{
  document.querySelectorAll('.q-card').forEach(c => c.style.display = 'none');
  document.getElementById('q-' + idx).style.display = 'block';
  document.getElementById('progressFill').style.width = (((idx + 1) / TOTAL) * 100) + '%';
  document.getElementById('prevBtn').style.display = idx > 0 ? 'inline-block' : 'none';
  document.getElementById('nextBtn').style.display = idx < TOTAL - 1 ? 'inline-block' : 'none';
  document.getElementById('submitBtn').style.display = idx === TOTAL - 1 ? 'inline-block' : 'none';
  current = idx;
}}
function nextQ() {{ if (current < TOTAL - 1) showQ(current + 1); }}
function prevQ() {{ if (current > 0) showQ(current - 1); }}

// ── SUBMIT ──
async function submitAssessment() {{
  if (!confirm('Submit your assessment? You cannot change answers after submission.')) return;
  clearInterval(timerInterval);
  document.getElementById('submitBtn').disabled = true;
  document.getElementById('submitBtn').textContent = 'Submitting...';

  const form = document.getElementById('assessmentForm');
  const answers = {{}};
  form.querySelectorAll('input[type=radio]:checked').forEach(el => {{
    answers[el.name] = el.value;
  }});
  form.querySelectorAll('textarea').forEach(el => {{
    if (el.name) answers[el.name] = el.value;
  }});

  try {{
    const res = await fetch('/api/submit-assessment', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        token: INVITE_TOKEN,
        answers,
        tab_switch_count: tabSwitches,
        cheating_flags: cheatingFlags
      }})
    }});
    const d = await res.json();
    if (d.success) {{
      document.body.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:center;min-height:100vh;background:#f0f4ff;font-family:'Nunito Sans',sans-serif;">
          <div style="background:#fff;border-radius:16px;padding:48px;text-align:center;box-shadow:0 8px 40px rgba(0,0,0,.1);max-width:480px;">
            <div style="font-size:56px;color:#3b5bdb;">${{d.passed ? '<svg width="56" height="56" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>' : '<svg width="56" height="56" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'}}</div>
            <h1 style="font-family:'Nunito';color:#3b5bdb;margin:16px 0;">${{d.passed ? 'Congratulations!' : 'Assessment Submitted'}}</h1>
            <p style="font-size:18px;font-weight:700;margin-bottom:8px;">Your Score: ${{d.percentage.toFixed(1)}}%</p>
            <p style="color:#6c757d;margin-bottom:24px;">${{d.passed ? '✅ You passed! The HR team will contact you for the next steps.' : 'Thank you for completing the assessment. The HR team will review your results.'}}</p>
            <a href="/track-application" style="background:#3b5bdb;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:700;">Track Application →</a>
          </div>
        </div>`;
    }} else {{
      alert('Error: ' + d.error);
      document.getElementById('submitBtn').disabled = false;
      document.getElementById('submitBtn').textContent = 'Submit Assessment ✓';
    }}
  }} catch(e) {{
    alert('Network error: ' + e.message);
    document.getElementById('submitBtn').disabled = false;
    document.getElementById('submitBtn').textContent = 'Submit Assessment ✓';
  }}
}}

// Start on load
showQ(0);
startTimer();
</script>
</body>
</html>""")


    @app.post("/api/submit-assessment")
    async def submit_assessment_api(request: Request):
        try:
            data = await request.json()
            token = data.get('token')
            answers = data.get('answers', {})
            tab_switches = int(data.get('tab_switch_count', 0))
            cheating_flags = data.get('cheating_flags', [])

            invite = db.get_invite_by_token(token)
            if not invite:
                return JSONResponse(content={"success": False, "error": "Invalid token"}, status_code=404)
            if invite['status'] in ('completed', 'failed'):
                return JSONResponse(content={"success": False, "error": "Already submitted"}, status_code=400)

            questions = db.get_assessment_questions(invite['assessment_id'])

            # Auto-grade
            total_score = 0
            max_score = sum(q['points'] for q in questions)

            for q in questions:
                key = f"q_{q['id']}"
                given = answers.get(key, '').strip()
                correct = (q['correct_answer'] or '').strip()
                q_type = q['question_type']

                if q_type in ('multiple_choice', 'true_false'):
                    if given.lower() == correct.lower():
                        total_score += q['points']
                elif q_type in ('short_answer', 'coding'):
                    # Keyword-based partial grading
                    keywords = [k.strip().lower() for k in correct.split(',') if k.strip()]
                    if keywords:
                        matched = sum(1 for kw in keywords if kw in given.lower())
                        total_score += q['points'] * (matched / len(keywords))
                    else:
                        # No keywords set — give full points if anything written
                        if given:
                            total_score += q['points']

            # Add cheating penalty
            if tab_switches > 5:
                cheating_flags.append(f"Heavy tab-switching penalty applied ({tab_switches} switches)")
                total_score = max(0, total_score * 0.7)

            percentage = (total_score / max_score * 100) if max_score > 0 else 0
            passing = float(invite['passing_score'])
            passed = percentage >= passing

            db.save_assessment_result(
                invite_id=invite['id'],
                application_id=invite['application_id'],
                assessment_id=invite['assessment_id'],
                score=total_score,
                max_score=max_score,
                answers=answers,
                tab_switch_count=tab_switches,
                cheating_flags=cheating_flags
            )

            # Update application status
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            new_status = 'assessment_passed' if passed else 'assessment_failed'
            cursor.execute('UPDATE job_applications SET status = ? WHERE id = ?', (new_status, invite['application_id']))
            conn.commit(); conn.close()

            return JSONResponse(content={
                "success": True,
                "score": round(total_score, 1),
                "max_score": max_score,
                "percentage": round(percentage, 2),
                "passed": passed
            })

        except Exception as e:
            return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)
