from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from database import ResumeDatabase
from hr_base import app, get_current_user, send_email, get_base_html, get_end_html
import os

db = ResumeDatabase()

# ─────────────────────────────────────────────────────────
# DASHBOARD HTML BUILDER
# ─────────────────────────────────────────────────────────
def build_dashboard_html(statistics, applications, current_user):
    total       = statistics.get('total_applicants', 0)
    scored      = statistics.get('scored_applicants', 0)
    avg_score   = statistics.get('average_score', 0)
    excellent   = statistics.get('score_distribution', {}).get('Excellent', 0)
    score_dist  = statistics.get('score_distribution', {})

    # Build table rows (last 8 apps)
    rows = ""
    for a in applications[:8]:
        status = (a.get('status') or 'pending').lower()
        smap = {
            'shortlisted': ('Shortlisted', '#27AE60', '#E8F8F0'),
            'reviewed':    ('Reviewed',    '#2D9CDB', '#E8F4FD'),
            'rejected':    ('Rejected',    '#EB5757', '#FEF0F0'),
            'pending':     ('Pending',     '#F2994A', '#FEF5EC'),
        }
        slabel, scolor, sbg = smap.get(status, ('Pending', '#F2994A', '#FEF5EC'))
        score_html = (
            f'<span class="score-badge" style="background:#E8F4FD;color:#2D9CDB;">'
            f'{float(a["resume_score"]):.0f}/100</span>'
            if a.get('resume_score') else
            '<span class="score-badge" style="background:#F5F5F5;color:#999;">—</span>'
        )
        initial = (a.get('applicant_name') or 'U')[0].upper()
        rows += f"""
        <tr>
          <td>
            <div class="emp-cell">
              <div class="emp-av">{initial}</div>
              <div>
                <div class="emp-name">{a.get('applicant_name','—')}</div>
                <div class="emp-email">{a.get('applicant_email','—')}</div>
              </div>
            </div>
          </td>
          <td>{a.get('job_title','—')}</td>
          <td>{a.get('department','—')}</td>
          <td>{score_html}</td>
          <td>
            <span class="status-pill" style="background:{sbg};color:{scolor};">{slabel}</span>
          </td>
          <td>
            <div class="act-row">
              <button class="act-btn view"   onclick="viewApp({a.get('id',0)})">View</button>
              <button class="act-btn short"  onclick="setStatus({a.get('id',0)},'shortlisted')">Shortlist</button>
              <button class="act-btn reject" onclick="setStatus({a.get('id',0)},'rejected')">Reject</button>
            </div>
          </td>
        </tr>"""

    import json
    dist_labels = json.dumps(list(score_dist.keys()))
    dist_values = json.dumps(list(score_dist.values()))

    user_initial = (current_user or 'H')[0].upper()
    user_name    = (current_user or 'HR Admin').split('@')[0].title()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>HR Dashboard — TalentFlow</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Sora:wght@600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg:       #EEF2F7;
  --white:    #FFFFFF;
  --blue:     #3B6FE8;
  --blue-lt:  #EBF0FD;
  --red:      #F05252;
  --red-lt:   #FEF0F0;
  --teal:     #0BB5B5;
  --teal-lt:  #E6F9F9;
  --amber:    #F4A83A;
  --amber-lt: #FEF5E7;
  --green:    #27AE60;
  --ink:      #1A1D2E;
  --ink2:     #4A5066;
  --ink3:     #8A8FA8;
  --border:   #E8EBF4;
  --radius:   14px;
  --radius-sm:9px;
  --shadow:   0 2px 12px rgba(30,40,90,0.07);
  --shadow-md:0 6px 28px rgba(30,40,90,0.11);
}}
*{{margin:0;padding:0;box-sizing:border-box;}}
html{{scroll-behavior:smooth;}}
body{{
  font-family:'DM Sans',sans-serif;
  background:var(--bg);color:var(--ink);font-size:14px;line-height:1.5;
  min-height:100vh;
}}

/* ══ TOP NAV ══════════════════════════════════════════ */
.topnav {{
  position:sticky;top:0;z-index:200;
  background:var(--white);
  border-bottom:1px solid var(--border);
  height:64px;
  display:flex;align-items:center;
  padding:0 28px;gap:0;
  box-shadow:0 1px 0 var(--border),var(--shadow);
}}
.tn-brand {{
  display:flex;align-items:center;gap:9px;
  text-decoration:none;margin-right:36px;flex-shrink:0;
}}
.tn-logo {{
  width:34px;height:34px;border-radius:9px;
  background:linear-gradient(135deg,#3B6FE8,#6B4FDB);
  display:flex;align-items:center;justify-content:center;
  color:#fff;font-size:15px;font-weight:800;
  font-family:'Sora',sans-serif;
  box-shadow:0 3px 10px rgba(59,111,232,0.35);
}}
.tn-name {{
  font-family:'Sora',sans-serif;font-size:16px;font-weight:700;
  color:var(--ink);letter-spacing:-0.01em;
}}
.tn-name span{{color:var(--blue);}}
.tn-links {{
  display:flex;align-items:center;gap:2px;flex:1;
}}
.tn-link {{
  display:inline-flex;align-items:center;gap:6px;
  padding:7px 14px;border-radius:8px;
  font-size:13.5px;font-weight:500;color:var(--ink2);
  text-decoration:none;cursor:pointer;border:none;background:transparent;
  font-family:'DM Sans',sans-serif;
  transition:all 0.15s;white-space:nowrap;
}}
.tn-link:hover{{background:var(--bg);color:var(--ink);}}
.tn-link.active{{background:var(--blue-lt);color:var(--blue);font-weight:600;}}
.tn-link svg{{flex-shrink:0;}}
.tn-sep{{width:1px;height:26px;background:var(--border);margin:0 10px;flex-shrink:0;}}
.tn-right{{
  display:flex;align-items:center;gap:10px;margin-left:auto;flex-shrink:0;
}}
.tn-search {{
  display:flex;align-items:center;gap:8px;
  background:var(--bg);border:1.5px solid var(--border);
  border-radius:9px;padding:7px 14px;width:220px;
  transition:border-color 0.15s;
}}
.tn-search:focus-within{{border-color:var(--blue);background:var(--white);}}
.tn-search input{{
  border:none;background:transparent;outline:none;
  font-family:'DM Sans',sans-serif;font-size:13.5px;color:var(--ink);width:100%;
}}
.tn-search input::placeholder{{color:var(--ink3);}}
.notif-btn{{
  width:36px;height:36px;border-radius:9px;border:1.5px solid var(--border);
  background:var(--white);cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  position:relative;transition:border-color 0.15s;
}}
.notif-btn:hover{{border-color:var(--blue);}}
.notif-dot{{
  position:absolute;top:6px;right:6px;
  width:7px;height:7px;border-radius:50%;
  background:var(--red);border:1.5px solid var(--white);
}}
.user-pill {{
  display:flex;align-items:center;gap:8px;
  padding:4px 12px 4px 4px;
  border:1.5px solid var(--border);border-radius:20px;
  background:var(--white);cursor:pointer;
  transition:border-color 0.15s;
}}
.user-pill:hover{{border-color:var(--blue);}}
.user-av {{
  width:28px;height:28px;border-radius:50%;
  background:linear-gradient(135deg,#3B6FE8,#6B4FDB);
  display:flex;align-items:center;justify-content:center;
  font-family:'Sora',sans-serif;font-weight:700;font-size:11px;color:#fff;
}}
.user-name{{font-size:13px;font-weight:600;color:var(--ink);}}
.logout-link{{
  font-size:12px;color:var(--red);font-weight:600;
  text-decoration:none;padding:5px 10px;border-radius:7px;
  border:1.5px solid rgba(240,82,82,0.2);
  transition:all 0.15s;background:var(--red-lt);
}}
.logout-link:hover{{background:var(--red);color:#fff;}}

/* ══ MAIN ═══════════════════════════════════════════ */
.main{{padding:28px 32px;max-width:1400px;margin:0 auto;}}

/* ══ PAGE HEADER ════════════════════════════════════ */
.page-hd{{
  display:flex;align-items:center;justify-content:space-between;
  margin-bottom:24px;
}}
.page-title{{
  font-family:'Sora',sans-serif;font-size:22px;font-weight:700;
  color:var(--ink);letter-spacing:-0.02em;
}}
.page-sub{{font-size:13px;color:var(--ink3);margin-top:2px;}}
.hd-actions{{display:flex;gap:10px;}}
.btn-primary{{
  display:inline-flex;align-items:center;gap:6px;
  padding:9px 18px;border-radius:9px;
  background:var(--blue);color:#fff;border:none;
  font-family:'DM Sans',sans-serif;font-size:13.5px;font-weight:600;
  cursor:pointer;text-decoration:none;
  box-shadow:0 3px 10px rgba(59,111,232,0.3);
  transition:all 0.15s;
}}
.btn-primary:hover{{box-shadow:0 5px 18px rgba(59,111,232,0.4);transform:translateY(-1px);}}
.btn-outline{{
  display:inline-flex;align-items:center;gap:6px;
  padding:9px 18px;border-radius:9px;
  background:var(--white);color:var(--ink2);
  border:1.5px solid var(--border);
  font-family:'DM Sans',sans-serif;font-size:13.5px;font-weight:600;
  cursor:pointer;text-decoration:none;transition:all 0.15s;
}}
.btn-outline:hover{{border-color:var(--blue);color:var(--blue);}}

/* ══ STAT TILES ═════════════════════════════════════ */
.stats-row{{
  display:grid;grid-template-columns:repeat(4,1fr);gap:16px;
  margin-bottom:24px;
}}
.stat-tile{{
  border-radius:var(--radius);padding:20px 22px;
  display:flex;align-items:center;gap:16px;
  position:relative;overflow:hidden;
  animation:fadeUp 0.4s ease both;
}}
.stat-tile:nth-child(1){{background:linear-gradient(135deg,#4776E6,#8E54E9);animation-delay:0.05s;}}
.stat-tile:nth-child(2){{background:linear-gradient(135deg,#F05252,#FF7B7B);animation-delay:0.1s;}}
.stat-tile:nth-child(3){{background:linear-gradient(135deg,#0BB5B5,#36D1C4);animation-delay:0.15s;}}
.stat-tile:nth-child(4){{background:linear-gradient(135deg,#F4A83A,#F7CB6A);animation-delay:0.2s;}}
.stat-tile::before{{
  content:'';position:absolute;top:-30px;right:-30px;
  width:100px;height:100px;border-radius:50%;
  background:rgba(255,255,255,0.12);pointer-events:none;
}}
.stat-icon{{
  width:48px;height:48px;border-radius:12px;
  background:rgba(255,255,255,0.2);
  display:flex;align-items:center;justify-content:center;
  font-size:22px;flex-shrink:0;
}}
.stat-body{{flex:1;}}
.stat-label{{font-size:12px;color:rgba(255,255,255,0.75);font-weight:500;margin-bottom:3px;}}
.stat-value{{
  font-family:'Sora',sans-serif;font-size:30px;font-weight:700;
  color:#fff;line-height:1;letter-spacing:-0.02em;
}}

/* ══ GRID LAYOUT ════════════════════════════════════ */
.grid-2{{display:grid;grid-template-columns:1fr 340px;gap:20px;margin-bottom:20px;}}
.grid-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-bottom:20px;}}

/* ══ CARD ════════════════════════════════════════════ */
.card{{
  background:var(--white);border-radius:var(--radius);
  border:1px solid var(--border);box-shadow:var(--shadow);
  overflow:hidden;animation:fadeUp 0.4s ease both;
}}
.card-hd{{
  padding:18px 22px;border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;
}}
.card-title{{
  font-family:'Sora',sans-serif;font-size:15px;font-weight:700;
  color:var(--ink);letter-spacing:-0.01em;
}}
.card-tag{{
  font-size:12px;font-weight:600;color:var(--ink3);
  background:var(--bg);padding:4px 10px;border-radius:20px;
  border:1px solid var(--border);
}}
.card-bd{{padding:20px 22px;}}

/* ══ CHART FILTER TABS ══════════════════════════════ */
.filter-tabs{{display:flex;gap:6px;align-items:center;}}
.ftab{{
  padding:5px 12px;border-radius:6px;border:1.5px solid var(--border);
  font-size:12px;font-weight:600;color:var(--ink3);background:var(--white);
  cursor:pointer;transition:all 0.15s;font-family:'DM Sans',sans-serif;
}}
.ftab.active{{border-color:var(--blue);background:var(--blue-lt);color:var(--blue);}}

/* ══ EMPLOYEE TABLE ═════════════════════════════════ */
.emp-table{{width:100%;border-collapse:collapse;}}
.emp-table th{{
  padding:11px 16px;text-align:left;
  font-size:11.5px;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;
  color:var(--ink3);background:var(--bg);
  border-bottom:1px solid var(--border);white-space:nowrap;
}}
.emp-table td{{
  padding:13px 16px;border-bottom:1px solid var(--border);
  vertical-align:middle;font-size:13.5px;
}}
.emp-table tr:last-child td{{border-bottom:none;}}
.emp-table tbody tr{{transition:background 0.1s;}}
.emp-table tbody tr:hover{{background:#FAFBFF;}}
.emp-cell{{display:flex;align-items:center;gap:10px;}}
.emp-av{{
  width:32px;height:32px;border-radius:9px;flex-shrink:0;
  background:linear-gradient(135deg,#4776E6,#8E54E9);
  display:flex;align-items:center;justify-content:center;
  font-family:'Sora',sans-serif;font-weight:700;font-size:12px;color:#fff;
}}
.emp-name{{font-weight:600;font-size:13.5px;color:var(--ink);}}
.emp-email{{font-size:11.5px;color:var(--ink3);}}
.score-badge{{
  padding:4px 10px;border-radius:6px;
  font-size:12px;font-weight:700;white-space:nowrap;
}}
.status-pill{{
  display:inline-flex;align-items:center;
  padding:4px 11px;border-radius:20px;
  font-size:12px;font-weight:700;
}}
.act-row{{display:flex;gap:5px;}}
.act-btn{{
  padding:5px 11px;border-radius:6px;border:none;
  font-family:'DM Sans',sans-serif;font-size:12px;font-weight:600;
  cursor:pointer;transition:all 0.13s;
}}
.act-btn.view  {{background:var(--blue-lt);color:var(--blue);}}
.act-btn.short {{background:#E8F8F0;color:var(--green);}}
.act-btn.reject{{background:var(--red-lt);color:var(--red);}}
.act-btn:hover{{filter:brightness(0.95);transform:translateY(-1px);}}

/* ══ DONUT CHART CARD ════════════════════════════════ */
.donut-wrap{{position:relative;display:flex;align-items:center;justify-content:center;height:200px;}}
.donut-center{{
  position:absolute;text-align:center;pointer-events:none;
}}
.donut-num{{
  font-family:'Sora',sans-serif;font-size:28px;font-weight:800;
  color:var(--ink);line-height:1;
}}
.donut-lbl{{font-size:11px;color:var(--ink3);font-weight:500;margin-top:3px;}}
.legend-list{{margin-top:14px;display:flex;flex-direction:column;gap:8px;}}
.legend-item{{display:flex;align-items:center;gap:8px;font-size:13px;}}
.legend-dot{{width:10px;height:10px;border-radius:3px;flex-shrink:0;}}
.legend-label{{flex:1;color:var(--ink2);}}
.legend-val{{font-weight:700;color:var(--ink);}}

/* ══ QUICK ACTIONS ═══════════════════════════════════ */
.qa-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;}}
.qa-btn{{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:7px;padding:18px 14px;border-radius:var(--radius-sm);
  border:1.5px solid var(--border);background:var(--white);
  cursor:pointer;text-decoration:none;transition:all 0.15s;
  font-family:'DM Sans',sans-serif;
}}
.qa-btn:hover{{border-color:var(--blue);background:var(--blue-lt);transform:translateY(-2px);box-shadow:var(--shadow);}}
.qa-btn:hover .qa-icon{{background:var(--blue);color:#fff;}}
.qa-icon{{
  width:36px;height:36px;border-radius:9px;
  background:var(--bg);
  display:flex;align-items:center;justify-content:center;
  font-size:17px;transition:all 0.15s;
}}
.qa-label{{font-size:12.5px;font-weight:600;color:var(--ink2);}}

/* ══ TOAST ═══════════════════════════════════════════ */
#toasts{{position:fixed;top:72px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px;max-width:340px;}}
.toast{{
  background:var(--white);border-radius:10px;padding:13px 16px;
  border:1px solid var(--border);box-shadow:var(--shadow-md);
  display:flex;align-items:flex-start;gap:10px;
  animation:slideIn 0.3s cubic-bezier(0.34,1.56,0.64,1);
}}
.toast-bar{{width:4px;border-radius:2px;align-self:stretch;flex-shrink:0;}}
.toast.success .toast-bar{{background:var(--green);}}
.toast.error   .toast-bar{{background:var(--red);}}
.toast.info    .toast-bar{{background:var(--blue);}}
.toast-title{{font-weight:700;font-size:13px;color:var(--ink);}}
.toast-msg{{font-size:12px;color:var(--ink3);margin-top:2px;}}
.toast-x{{margin-left:auto;cursor:pointer;color:var(--ink3);font-size:14px;background:none;border:none;flex-shrink:0;}}
@keyframes slideIn{{from{{transform:translateX(110%);opacity:0;}}to{{transform:translateX(0);opacity:1;}}}}
@keyframes fadeUp{{from{{transform:translateY(14px);opacity:0;}}to{{transform:translateY(0);opacity:1;}}}}

/* ══ RESPONSIVE ══════════════════════════════════════ */
@media(max-width:1100px){{
  .stats-row{{grid-template-columns:repeat(2,1fr);}}
}}
@media(max-width:900px){{
  .grid-2{{grid-template-columns:1fr;}}
  .grid-3{{grid-template-columns:1fr;}}
  .main{{padding:20px 16px;}}
  .tn-search{{display:none;}}
}}
</style>
</head>
<body>

<!-- 
 TOAST CONTAINER 
 -->
<div id="toasts"></div>

<!-- 
 MAIN 
 -->
<main class="main">

  <!-- Page header -->
  <div class="page-hd">
    <div>
      <div class="page-title">HR Dasboard</div>
      <div class="page-sub">Welcome back, {user_name} — here's what's happening today.</div>
    </div>
    <div class="hd-actions">
      <a href="/post-job" class="btn-primary">
        <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        Post New Job
      </a>
      <a href="/reports" class="btn-outline">
        <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>
        Reports
      </a>
    </div>
  </div>

  <!-- Stat tiles -->
  <div class="stats-row">
    <div class="stat-tile">
      <div class="stat-icon">👥</div>
      <div class="stat-body">
        <div class="stat-label">Total Applicants</div>
        <div class="stat-value">{total}</div>
      </div>
    </div>
    <div class="stat-tile">
      <div class="stat-icon">📄</div>
      <div class="stat-body">
        <div class="stat-label">Gross Scored</div>
        <div class="stat-value">{scored}</div>
      </div>
    </div>
    <div class="stat-tile">
      <div class="stat-icon">📈</div>
      <div class="stat-body">
        <div class="stat-label">Net Avg Score</div>
        <div class="stat-value">{avg_score:.0f}</div>
      </div>
    </div>
    <div class="stat-tile">
      <div class="stat-icon">🏆</div>
      <div class="stat-body">
        <div class="stat-label">Jobs Applied</div>
        <div class="stat-value">{excellent}</div>
      </div>
    </div>
  </div>

  <!-- Charts row -->
  <div class="grid-2" style="animation-delay:0.25s;">
    <!-- Bar chart -->
    <div class="card">
      <div class="card-hd">
        <span class="card-title">Job Applied</span>
        <div class="filter-tabs">
          <button class="ftab" onclick="setChartPeriod('week',this)">Week</button>
          <button class="ftab active" onclick="setChartPeriod('month',this)">Month</button>
          <button class="ftab" onclick="setChartPeriod('year',this)">Last Year</button>
        </div>
      </div>
      <div class="card-bd">
        <canvas id="barChart" height="200"></canvas>
      </div>
    </div>

    <!-- Donut chart -->
    <div class="card">
      <div class="card-hd">
        <span class="card-title">Working Format</span>
        <span class="card-tag">Breakdown</span>
      </div>
      <div class="card-bd">
        <div class="donut-wrap">
          <canvas id="donutChart" width="200" height="200"></canvas>
          <div class="donut-center">
            <div class="donut-num">{total}</div>
            <div class="donut-lbl">Total</div>
          </div>
        </div>
        <div class="legend-list" id="donutLegend"></div>
      </div>
    </div>
  </div>

  <!-- Employee table + Quick actions -->
  <div class="grid-2">
    <!-- Applications table -->
    <div class="card">
      <div class="card-hd">
        <span class="card-title">Employee Status</span>
        <div style="display:flex;gap:8px;align-items:center;">
          <span class="card-tag">{len(applications)} applicants</span>
          <button class="btn-outline" style="padding:5px 12px;font-size:12px;" onclick="window.location='/jobs'">View All</button>
        </div>
      </div>
      <div style="overflow-x:auto;">
        <table class="emp-table" id="empTable">
          <thead>
            <tr>
              <th>Employee Name</th>
              <th>Job Title</th>
              <th>Department</th>
              <th>Score</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="empBody">
            {rows}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Right column: Project overview + Quick actions -->
    <div style="display:flex;flex-direction:column;gap:20px;">
      <!-- Project overview card -->
      <div class="card">
        <div class="card-hd">
          <span class="card-title">Pipeline Overview</span>
        </div>
        <div class="card-bd">
          <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:14px;">
            <span style="font-family:'Sora',sans-serif;font-size:32px;font-weight:800;color:var(--ink);">{total}</span>
            <span style="font-size:15px;color:var(--ink2);font-weight:600;">Candidates</span>
          </div>
          <div style="display:flex;gap:4px;height:8px;border-radius:4px;overflow:hidden;margin-bottom:16px;">
            <div style="flex:{score_dist.get('Excellent',1)};background:#4776E6;"></div>
            <div style="flex:{score_dist.get('Good',1)};background:#0BB5B5;"></div>
            <div style="flex:{score_dist.get('Fair',1)};background:#F4A83A;"></div>
            <div style="flex:{score_dist.get('Poor',1)};background:#F05252;"></div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <div style="padding:12px;background:var(--bg);border-radius:9px;">
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
                <span style="width:8px;height:8px;border-radius:50%;background:#4776E6;display:inline-block;"></span>
                <span style="font-size:12px;color:var(--ink3);">Excellent</span>
              </div>
              <span style="font-family:'Sora',sans-serif;font-size:20px;font-weight:700;color:var(--ink);">{score_dist.get('Excellent',0)}</span>
            </div>
            <div style="padding:12px;background:var(--bg);border-radius:9px;">
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
                <span style="width:8px;height:8px;border-radius:50%;background:#0BB5B5;display:inline-block;"></span>
                <span style="font-size:12px;color:var(--ink3);">Good</span>
              </div>
              <span style="font-family:'Sora',sans-serif;font-size:20px;font-weight:700;color:var(--ink);">{score_dist.get('Good',0)}</span>
            </div>
            <div style="padding:12px;background:var(--bg);border-radius:9px;">
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
                <span style="width:8px;height:8px;border-radius:50%;background:#F4A83A;display:inline-block;"></span>
                <span style="font-size:12px;color:var(--ink3);">Fair</span>
              </div>
              <span style="font-family:'Sora',sans-serif;font-size:20px;font-weight:700;color:var(--ink);">{score_dist.get('Fair',0)}</span>
            </div>
            <div style="padding:12px;background:var(--bg);border-radius:9px;">
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
                <span style="width:8px;height:8px;border-radius:50%;background:#F05252;display:inline-block;"></span>
                <span style="font-size:12px;color:var(--ink3);">Poor</span>
              </div>
              <span style="font-family:'Sora',sans-serif;font-size:20px;font-weight:700;color:var(--ink);">{score_dist.get('Poor',0)}</span>
            </div>
          </div>
          <a href="/jobs" class="btn-primary" style="width:100%;justify-content:center;margin-top:16px;text-decoration:none;">
            View all candidates ↓
          </a>
        </div>
      </div>

      <!-- Quick actions -->
      <div class="card">
        <div class="card-hd"><span class="card-title">Quick Actions</span></div>
        <div class="card-bd">
          <div class="qa-grid">
            <a href="/post-job" class="qa-btn">
              <div class="qa-icon">💼</div>
              <span class="qa-label">Post Job</span>
            </a>
            <a href="/interviews" class="qa-btn">
              <div class="qa-icon">📅</div>
              <span class="qa-label">Schedule</span>
            </a>
            <a href="/communications" class="qa-btn">
              <div class="qa-icon">✉️</div>
              <span class="qa-label">Send Email</span>
            </a>
            <a href="/reports" class="qa-btn">
              <div class="qa-icon">📊</div>
              <span class="qa-label">Reports</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>

</main>

<script>
// ── CHARTS ──────────────────────────────────────────────
const BLUE_GRAD = (ctx) => {{
  const g = ctx.createLinearGradient(0,0,0,300);
  g.addColorStop(0,'rgba(59,111,232,0.85)');
  g.addColorStop(1,'rgba(107,79,219,0.75)');
  return g;
}};

// Bar chart data sets
const chartData = {{
  week:  [12, 8, 15, 6, 20, 14, 9],
  month: [24, 36, 28, 45, 38, 52, 41, 58, 47, 62, 55, 44],
  year:  [180, 210, 190, 240, 280, 260, 300, 275, 320, 295, 340, 310],
}};
const chartLabels = {{
  week:  ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
  month: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
  year:  ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
}};

let barChart;
function initBarChart(period='month') {{
  const ctx = document.getElementById('barChart').getContext('2d');
  if (barChart) barChart.destroy();
  barChart = new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: chartLabels[period],
      datasets: [{{
        data: chartData[period],
        backgroundColor: (ctx2) => {{
          const max = Math.max(...chartData[period]);
          return ctx2.dataset.data[ctx2.dataIndex] === max
            ? BLUE_GRAD(ctx) : 'rgba(59,111,232,0.22)';
        }},
        borderRadius: 7,
        borderSkipped: false,
      }}]
    }},
    options: {{
      responsive: true,
      plugins: {{ legend:{{display:false}},
        tooltip: {{
          backgroundColor: '#1A1D2E',
          titleFont: {{family:'Sora',size:12}},
          bodyFont:  {{family:'DM Sans',size:12}},
          padding: 10, cornerRadius: 8,
          callbacks: {{ label: (c) => ` ${{c.parsed.y}} applicants` }}
        }}
      }},
      scales: {{
        x: {{ grid:{{display:false}}, ticks:{{font:{{family:'DM Sans',size:12}},color:'#8A8FA8'}} }},
        y: {{ grid:{{color:'rgba(0,0,0,0.04)'}}, ticks:{{font:{{family:'DM Sans',size:12}},color:'#8A8FA8'}}, beginAtZero:true }}
      }},
    }}
  }});
}}

function setChartPeriod(p, btn) {{
  document.querySelectorAll('.ftab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  initBarChart(p);
}}

// Donut chart
const distLabels = {dist_labels};
const distValues = {dist_values};
const distColors = ['#4776E6','#0BB5B5','#F4A83A','#F05252'];

function initDonut() {{
  const ctx = document.getElementById('donutChart').getContext('2d');
  const data = distValues.length ? distValues : [1,1,1,1];
  new Chart(ctx, {{
    type: 'doughnut',
    data: {{
      labels: distLabels.length ? distLabels : ['Excellent','Good','Fair','Poor'],
      datasets: [{{ data, backgroundColor: distColors, borderWidth: 3, borderColor: '#fff', hoverOffset: 6 }}]
    }},
    options: {{
      responsive: false,
      cutout: '70%',
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          backgroundColor:'#1A1D2E',
          titleFont:{{family:'Sora',size:12}},
          bodyFont:{{family:'DM Sans',size:12}},
          padding:10, cornerRadius:8,
        }}
      }}
    }}
  }});

  const legend = document.getElementById('donutLegend');
  const labels = distLabels.length ? distLabels : ['Excellent','Good','Fair','Poor'];
  legend.innerHTML = labels.map((l,i) => `
    <div class="legend-item">
      <span class="legend-dot" style="background:${{distColors[i]}}"></span>
      <span class="legend-label">${{l}}</span>
      <span class="legend-val">${{data[i] || 0}}</span>
    </div>`).join('');
}}

initBarChart();
initDonut();

// ── TABLE SEARCH ─────────────────────────────────────────
function filterTable(q) {{
  const rows = document.querySelectorAll('#empBody tr');
  q = q.toLowerCase();
  rows.forEach(r => {{ r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none'; }});
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

// ── STATUS UPDATE ────────────────────────────────────────
function setStatus(id, status) {{
  showConfirmModal({{
    title: `Mark as ${{status}}?`,
    message: `Mark this application as ${{status}}? This action will update the application status.`,
    icon: 'warning',
    confirmText: `Mark as ${{status}}`,
    confirmType: 'primary',
    onConfirm: () => {{
      fetch('/api/update-application-status', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{application_id: id, status}})
      }})
        .then(r => r.json())
        .then(d => {{
          if (d.success) {{
            showToast('Updated', `Application marked as ${{status}}.`, 'success');
            closeConfirmModal();
            // Update badge in-place
            const row = document.querySelector(`[data-id="${{id}}"]`);
            if (row) row.closest('tr').querySelector('.status-pill').textContent = status.charAt(0).toUpperCase()+status.slice(1);
            setTimeout(() => location.reload(), 1200);
          }} else {{
            showToast('Error', d.error || 'Failed to update.', 'error');
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
  fetch('/api/update-application-status', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{application_id: id, status}})
  }})
  .then(r => r.json())
  .then(d => {{
    if (d.success) {{
      showToast('Updated', `Application marked as ${{status}}.`, 'success');
      // Update badge in-place
      const row = document.querySelector(`[data-id="${{id}}"]`);
      if (row) row.closest('tr').querySelector('.status-pill').textContent = status.charAt(0).toUpperCase()+status.slice(1);
      setTimeout(() => location.reload(), 1200);
    }} else showToast('Error', d.error || 'Failed to update.', 'error');
  }}).catch(() => showToast('Error', 'Network error.', 'error'));
}}

function viewApp(id) {{
  window.location = '/jobs';
}}

// ── TOASTS ───────────────────────────────────────────────
function showToast(title, msg, type='info', dur=4000) {{
  const c = document.getElementById('toasts');
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  t.innerHTML = `
    <div class="toast-bar"></div>
    <div style="flex:1;">
      <div class="toast-title">${{title}}</div>
      <div class="toast-msg">${{msg}}</div>
    </div>
    <button class="toast-x" onclick="this.closest('.toast').remove()">✕</button>`;
  c.appendChild(t);
  setTimeout(() => {{ t.style.animation='slideIn 0.25s reverse'; setTimeout(()=>t.remove(),250); }}, dur);
}}
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

</body>
</html>"""


# ─────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/", status_code=302)

    applications = db.get_all_applications()
    statistics   = db.get_statistics()
    dashboard_content = build_dashboard_html(statistics, applications, current_user)
    
    # Use proper base HTML structure
    full_html = get_base_html("Dashboard", "dashboard", current_user) + dashboard_content + get_end_html()
    return HTMLResponse(content=full_html)


@app.post("/api/update-application-status")
async def update_application_status(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse(content={"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data       = await request.json()
        app_id     = data.get("application_id")
        new_status = data.get("status")
        db.update_application_status(app_id, new_status)
        return JSONResponse(content={"success": True})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    print("Starting HR Dashboard  →  http://localhost:8003/dashboard")
    uvicorn.run(app, host="0.0.0.0", port=8003)