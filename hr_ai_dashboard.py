from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from hr_base import app, get_current_user, get_base_html, get_end_html, db
import json

@app.get("/ai-screening", response_class=HTMLResponse)
async def ai_screening_dashboard(request: Request):
    """AI Screening Dashboard for HR to view screening results and candidate rankings"""
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/", status_code=302)

    # Get all AI screening results
    ai_screenings = db.get_ai_screening_results()
    
    # Get applications with AI scores
    all_apps = db.get_all_applications()
    applications = []
    for screening in ai_screenings:
        # Get applicant details
        applicant = db.get_applicant_with_score(screening['applicant_id'])
        if applicant:
            # Get job details
            job = db.get_job(screening['job_id'])
            if job:
                app_row = next(
                    (a for a in all_apps if a.get("applicant_id") == screening["applicant_id"] and a.get("job_id") == screening["job_id"]),
                    None
                )
                applications.append({
                    'applicant': applicant,
                    'job': job,
                    'ai_screening': screening,
                    'application_id': app_row.get('id') if app_row else None,
                    'ai_score': screening['ai_score'],
                    'ai_status': screening['ai_status'],
                    'match_details': screening.get('match_details', '{}'),
                    'interview_questions': screening.get('interview_questions', '[]')
                })
    
    # Sort by AI score
    applications.sort(key=lambda x: x['ai_score'], reverse=True)
    
    # Build Table Rows
    rows = ""
    safe_screening_data = []
    for idx, app_data in enumerate(applications):
        applicant = app_data['applicant']
        job = app_data['job']
        score = app_data['ai_score']
        status = app_data['ai_status']
        
        # Determine score color
        score_color = "#EB5757" # Red
        if score >= 80: score_color = "#27AE60" # Green
        elif score >= 60: score_color = "#F2994A" # Orange
        
        # Parse match details
        match_details = {}
        try:
            if isinstance(app_data['match_details'], str):
                match_details = json.loads(app_data['match_details'])
            else:
                match_details = app_data['match_details']
        except:
            match_details = {}
            
        summary = match_details.get('summary', 'No summary available')
        
        # Only keep what the frontend needs (avoid oversized / non-serializable payloads)
        safe_screening_data.append({
            "application_id": app_data.get("application_id"),
            "ai_score": app_data.get("ai_score"),
            "match_details": app_data.get("match_details", "{}"),
            "interview_questions": app_data.get("interview_questions", "[]"),
        })
        rows += f"""
        <tr data-searchable>
            <td>
                <div class="emp-cell">
                    <div class="emp-av">{(applicant['name'] or 'U')[0]}</div>
                    <div>
                        <div class="emp-name">{applicant['name']}</div>
                        <div class="emp-email">{applicant['email']}</div>
                    </div>
                </div>
            </td>
            <td>{job['title']}</td>
            <td>
                <div style="font-weight:700; color:{score_color}; font-size:16px;">
                    {score:.0f}/100
                </div>
                <div style="font-size:11px;color:var(--ink3);margin-top:2px;">Resume Score: {((float(applicant.get('score') or 0) * 100) if float(applicant.get('score') or 0) <= 1.5 else float(applicant.get('score') or 0)):.0f}/100</div>
            </td>
            <td>
                <span class="badge {'badge-green' if status in ('shortlisted', 'recommended') else 'badge-amber' if status=='review_needed' else 'badge-red'}">
                    {status.title()}
                </span>
            </td>
            <td>
                <div style="max-width:300px; font-size:12px; color:var(--ink2); line-height:1.4;">
                    {summary[:100]}{'...' if len(summary)>100 else ''}
                </div>
            </td>
            <td>
                <div class="action-grp">
                    <button class="btn btn-sm btn-outline" onclick="viewMatchDetailsByIndex({idx})">View Insights</button>
                   </div>
            </td>
        </tr>
        """

    html_content = f"""
    <div class="page-hd">
        <div>
            <h2 class="page-title">AI Screening Dashboard</h2>
            <p class="page-sub">Ranked candidates based on AI-powered resume analysis</p>
            <p style="margin-top:6px;font-size:12px;color:var(--ink3);max-width:760px;">
                AI Score measures job-match fit (experience, required skills, certifications, and education).
                Resume Score is a general CV quality score. They can differ because they optimize different goals.
            </p>
        </div>
    </div>

    <div class="stats-row">
        <div class="stat-tile">
        <div class="stat-icon"><svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M9 3a3 3 0 0 0-3 3 3 3 0 0 0-3 3 4 4 0 0 0 4 4h1v7h4v-7h1a4 4 0 0 0 4-4 3 3 0 0 0-3-3 3 3 0 0 0-3-3z"/></svg></div>
            <div class="stat-body">
                <div class="stat-label">Total Screened</div>
                <div class="stat-value">{len(ai_screenings)}</div>
            </div>
        </div>
        <div class="stat-tile">
        <div class="stat-icon"><svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
            <div class="stat-body">
                <div class="stat-label">Recommended</div>
                <div class="stat-value">{len([s for s in ai_screenings if s['ai_status'] == 'recommended'])}</div>
            </div>
        </div>
        <div class="stat-tile">
        <div class="stat-icon"><svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg></div>
            <div class="stat-body">
                <div class="stat-label">Average Match</div>
                <div class="stat-value">{sum(s['ai_score'] for s in ai_screenings)/len(ai_screenings) if ai_screenings else 0:.0f}%</div>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-hd">
            <span class="card-title">Candidate Rankings</span>
            <span class="card-tag">Sorted by AI Score</span>
        </div>
        <div style="overflow-x:auto;">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Candidate</th>
                        <th>Applied For</th>
                        <th>AI Score</th>
                        <th>AI Status</th>
                        <th>Quick Insight</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {rows if rows else '<tr><td colspan="6" class="empty">No screening results found.</td></tr>'}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Modal for Insights -->
    <div id="insightModal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:1000; align-items:center; justify-content:center; padding:20px;">
        <div class="card" style="max-width:800px; width:100%; max-height:90vh; overflow-y:auto; animation:fadeUp 0.3s ease;">
            <div class="card-hd">
                <span class="card-title">AI Analysis & Interview Guide</span>
                <button class="btn btn-sm btn-outline" onclick="closeModal()">Close</button>
            </div>
            <div class="card-bd" id="modalContent">
                <!-- Content injected via JS -->
            </div>
        </div>
    </div>
    """
    
    js_content = """
    <script>
    const SCREENING_DATA = __SCREENING_DATA__;

    function viewMatchDetailsByIndex(i) {
        const data = SCREENING_DATA[i];
        if (!data) return;
        const modal = document.getElementById('insightModal');
        const content = document.getElementById('modalContent');
        
        let matchDetails = {};
        try {
            matchDetails = typeof data.match_details === 'string' ? JSON.parse(data.match_details) : data.match_details;
        } catch(e) {}

        let questions = [];
        try {
            questions = typeof data.interview_questions === 'string' ? JSON.parse(data.interview_questions) : data.interview_questions;
        } catch(e) {}

        let skillsHtml = (matchDetails.matched_skills || []).map(s => `<span class="badge badge-blue" style="margin:2px">${s}</span>`).join('');
        let gapsHtml = (matchDetails.missing_skills || []).map(s => `<span class="badge badge-red" style="margin:2px">${s}</span>`).join('');
        
        content.innerHTML = `
            <div style="display:flex; gap:20px; margin-bottom:20px;">
                <div style="flex:1;">
                    <h4 style="margin-bottom:8px;">Match Summary</h4>
                    <p style="font-size:14px; line-height:1.6; color:var(--ink2);">${matchDetails.summary || 'No summary available'}</p>
                </div>
                <div style="width:120px; text-align:center; padding:15px; background:var(--bg); border-radius:12px;">
                    <div style="font-size:12px; color:var(--ink3);">AI Score</div>
                    <div style="font-size:28px; font-weight:800; color:var(--blue);">${data.ai_score}/100</div>
                </div>
            </div>

            <div style="margin-bottom:20px;">
                <h4 style="margin-bottom:8px;">Skill Match</h4>
                <div style="margin-bottom:10px;">
                    <div style="font-size:12px; font-weight:700; margin-bottom:4px;">Matched Skills:</div>
                    ${skillsHtml || '<span style="color:var(--ink3)">None identified</span>'}
                </div>
                <div>
                    <div style="font-size:12px; font-weight:700; margin-bottom:4px;">Identified Gaps:</div>
                    ${gapsHtml || '<span style="color:var(--ink3)">None identified</span>'}
                </div>
            </div>

            <div style="padding:15px; background:var(--blue-lt); border-radius:12px; border:1px solid rgba(59,111,232,0.2);">
                <h4 style="margin-bottom:12px; color:var(--blue); display:flex; align-items:center; gap:8px;">
                    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>
                    Recommended Interview Questions
                </h4>
                <ul style="padding-left:20px; font-size:14px; line-height:1.6; color:var(--ink);">
                    ${questions.map(q => `<li style="margin-bottom:8px;">${typeof q === 'object' ? (q.question || q.text || JSON.stringify(q)) : q}</li>`).join('') || '<li>No questions generated</li>'}
                </ul>
            </div>

            <div style="margin-top:24px; padding-top:20px; border-top:1px solid var(--border); display:flex; gap:12px; justify-content:flex-end;">
                <button class="btn btn-outline" onclick="rejectApplication(${data.application_id || 0})">Reject</button>
                <button class="btn btn-primary" onclick="acceptForAssessment(${data.application_id || 0})">Accept for Assessment</button>
            </div>
        `;
        
        modal.style.display = 'flex';
    }

    function closeModal() {
        document.getElementById('insightModal').style.display = 'none';
    }

    async function hireCandidate(applicantId, fullName, email, jobId) {{
        const ok = await window.tfDialog.confirm({
            title: 'Confirm Hire',
            message: `Hire ${fullName} and sync to HRMS?`,
            okText: 'Hire & Sync',
            cancelText: 'Cancel'
        });
        if(!ok) return;
        
        showInfo('Processing hire and syncing data...');
        
        // Split name into first and last
        const nameParts = fullName.split(' ');
        const firstName = nameParts[0] || '';
        const lastName = nameParts.slice(1).join(' ') || '';
        
        // Use the recruitment API to sync to Laravel
        fetch('http://127.0.0.1:8000/api/external-recruitment/hire', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
                'X-Recruitment-Token': 'talentflow_secret_token_123'
            }},
            body: JSON.stringify({{
                first_name: firstName,
                last_name: lastName,
                email: email,
                position_id: 1, // Default or derived from job_id
                department_id: 1,
                join_date: new Date().toISOString().split('T')[0]
            }})
        }})
        .then(r => r.json())
        .then(data => {{
            if (data.message) {{
                showSuccess('Candidate hired! Data synced to HRMS successfully.');
                setTimeout(() => location.reload(), 2000);
            }} else {{
                showError('Integration failed. Please check HRMS logs.');
            }}
        }})
        .catch(e => {
            showError('Sync failed. Is the Laravel server running?');
            console.error(e);
        });
    }

    async function acceptForAssessment(appId) {
        if (!appId) { showError('Application ID not found for this candidate.'); return; }
        const ok = await window.tfDialog.confirm({
            title: 'Move to Assessment',
            message: 'Send this candidate to the assessment phase?',
            okText: 'Send',
            cancelText: 'Cancel'
        });
        if(!ok) return;
        fetch('/api/accept-for-assessment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ application_id: appId })
        })
        .then(r => r.json())
        .then(d => {
            if(d.success) {
                showSuccess('Candidate moved to assessment phase.');
                location.href = '/assessments';
            } else showError(d.error || 'Failed to update candidate.');
        });
    }

    async function rejectApplication(appId) {
        if (!appId) { showError('Application ID not found for this candidate.'); return; }
        const reason = await window.tfDialog.prompt({
            title: 'Reject Candidate',
            label: 'Reason for rejection',
            placeholder: 'Add a short reason (will be saved in the system)',
            defaultValue: 'Does not meet technical requirements',
            okText: 'Reject',
            cancelText: 'Cancel',
            multiline: true
        });
        if(reason === null) return;
        fetch('/api/reject-application', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ application_id: appId, reason: reason })
        })
        .then(r => r.json())
        .then(d => {
            if(d.success) {
                showWarning('Candidate rejected.');
                location.reload();
            } else showError(d.error || 'Failed to reject candidate.');
        });
    }
    </script>
    """
    js_content = js_content.replace("__SCREENING_DATA__", json.dumps(safe_screening_data))
    
    content = html_content + js_content
    
    return HTMLResponse(content=get_base_html("AI Screening", "ai-screening", current_user) + content + get_end_html())
