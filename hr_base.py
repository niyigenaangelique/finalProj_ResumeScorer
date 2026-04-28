from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from database import ResumeDatabase
import secrets
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template

app = FastAPI(title="TalentFlow Pro HR Portal", description="Professional HR Management System")

# Initialize database
db = ResumeDatabase()

# Session storage (in production, use Redis or database)
sessions = {}

# Password reset tokens storage (in production, use database)
password_reset_tokens = {}

# ─────────────────────────────────────────────────────────
# EMAIL CONFIG
# ─────────────────────────────────────────────────────────
EMAIL_HOST     = "smtp.gmail.com"
EMAIL_PORT     = 587
EMAIL_USER     = "angelbrenna20@gmail.com"
EMAIL_PASSWORD = "exlk kuuy mtfn ftti"   # Gmail App Password
EMAIL_FROM     = "TalentFlow HR <angelbrenna20@gmail.com>"

def send_email(to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
    """Send email notification — returns True on success, False on failure."""
    try:
        msg = MIMEMultipart()
        msg["From"]    = EMAIL_FROM
        msg["To"]      = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html" if is_html else "plain"))

        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[EMAIL SENT] To: {to_email}")
        return True
    except Exception as e:
        err = str(e)
        print(f"[EMAIL ERROR] {err}")
        if "Application-specific password required" in err:
            print("[EMAIL INFO] Gmail requires an App Password.")
            print("[EMAIL INFO] Visit: https://myaccount.google.com/apppasswords")
        return False


# ─────────────────────────────────────────────────────────
# SESSION HELPERS
# ─────────────────────────────────────────────────────────
def get_current_user(request: Request) -> str | None:
    token = request.cookies.get("hr_token")
    if token and token in sessions:
        return sessions[token]["email"]
    return None

def create_session(email: str) -> str:
    token = secrets.token_urlsafe(32)
    sessions[token] = {"email": email, "created": datetime.now()}
    return token


# ─────────────────────────────────────────────────────────
# DESIGN TOKENS  (shared across every page)
# ─────────────────────────────────────────────────────────
FONTS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Sora:wght@600;700;800&display=swap" rel="stylesheet">
"""

SHARED_CSS = FONTS + """
<style>
:root {
  --bg:        #EEF2F7;
  --white:     #FFFFFF;
  --blue:      #3B6FE8;
  --blue-lt:   #EBF0FD;
  --red:       #F05252;
  --red-lt:    #FEF0F0;
  --teal:      #0BB5B5;
  --teal-lt:   #E6F9F9;
  --amber:     #F4A83A;
  --amber-lt:  #FEF5E7;
  --green:     #27AE60;
  --ink:       #1A1D2E;
  --ink2:      #4A5066;
  --ink3:      #8A8FA8;
  --border:    #E8EBF4;
  --radius:    14px;
  --radius-sm: 9px;
  --shadow:    0 2px 12px rgba(30,40,90,0.07);
  --shadow-md: 0 6px 28px rgba(30,40,90,0.11);
}
*, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
html { scroll-behavior:smooth; }
body {
  font-family: 'DM Sans', sans-serif;
  background: var(--bg);
  color: var(--ink);
  font-size: 14px;
  line-height: 1.5;
  min-height: 100vh;
}

/* ══ TOP NAV ══════════════════════════════════════════ */
.topnav {
  position: sticky; top: 0; z-index: 200;
  background: var(--white);
  border-bottom: 1px solid var(--border);
  height: 64px;
  display: flex; align-items: center;
  padding: 0 28px; gap: 0;
  box-shadow: 0 1px 0 var(--border), var(--shadow);
  overflow-x: auto;
}
.topnav::-webkit-scrollbar { display: none; }

.tn-brand {
  display: flex; align-items: center; gap: 9px;
  text-decoration: none; margin-right: 32px; flex-shrink: 0;
}
.tn-logo {
  width: 34px; height: 34px; border-radius: 9px;
  background: linear-gradient(135deg, #3B6FE8, #6B4FDB);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 14px; font-weight: 800;
  font-family: 'Sora', sans-serif;
  box-shadow: 0 3px 10px rgba(59,111,232,0.35);
  flex-shrink: 0;
}
.tn-name {
  font-family: 'Sora', sans-serif; font-size: 16px; font-weight: 700;
  color: var(--ink); letter-spacing: -0.01em; white-space: nowrap;
}
.tn-name span { color: var(--blue); }

.tn-links {
  display: flex; align-items: center; gap: 2px; flex: 1;
  overflow-x: auto;
}
.tn-links::-webkit-scrollbar { display: none; }

.tn-link {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 13px; border-radius: 8px;
  font-size: 13.5px; font-weight: 500; color: var(--ink2);
  text-decoration: none; cursor: pointer;
  border: none; background: transparent;
  font-family: 'DM Sans', sans-serif;
  transition: all 0.15s; white-space: nowrap; flex-shrink: 0;
}
.tn-link:hover { background: var(--bg); color: var(--ink); }
.tn-link.active { background: var(--blue-lt); color: var(--blue); font-weight: 600; }

.tn-sep {
  width: 1px; height: 26px; background: var(--border);
  margin: 0 8px; flex-shrink: 0;
}

/* ══ DIALOG (replaces alert/confirm/prompt) ═══════════════ */
.tf-backdrop{
  position:fixed; inset:0; z-index:99998;
  display:none; align-items:center; justify-content:center;
  background:rgba(15,18,30,0.55);
  padding:20px;
}
.tf-backdrop.show{ display:flex; }
.tf-dialog{
  width:min(720px, 96vw);
  background:var(--white);
  border:1px solid var(--border);
  border-radius:16px;
  box-shadow:var(--shadow-md);
  overflow:hidden;
  animation:fadeUp 0.18s ease;
}
.tf-dialog-hd{
  padding:16px 16px 12px 16px;
  display:flex; align-items:center; justify-content:space-between; gap:12px;
  border-bottom:1px solid var(--border);
}
.tf-dialog-title{ font-family:'Sora',sans-serif; font-weight:800; font-size:14px; color:var(--ink); }
.tf-dialog-bd{ padding:16px; color:var(--ink2); font-size:13.5px; line-height:1.55; }
.tf-dialog-ft{
  padding:14px 16px;
  display:flex; gap:10px; justify-content:flex-end; align-items:center;
  border-top:1px solid var(--border);
  background:linear-gradient(to bottom, rgba(238,242,247,0.35), rgba(238,242,247,0));
}
.tf-input{
  width:100%;
  padding:10px 12px;
  border-radius:10px;
  border:1.5px solid var(--border);
  background:var(--white);
  font-family:'DM Sans',sans-serif;
  font-size:13.5px;
  outline:none;
}
.tf-input:focus{ border-color:rgba(59,111,232,0.55); box-shadow:0 0 0 3px rgba(59,111,232,0.12); }
.tn-right {
  display: flex; align-items: center; gap: 10px;
  margin-left: auto; flex-shrink: 0;
  position: relative;
}
.tn-search {
  display: flex; align-items: center; gap: 8px;
  background: var(--bg); border: 1.5px solid var(--border);
  border-radius: 9px; padding: 7px 14px; width: 220px;
  transition: border-color 0.15s;
}
.tn-search:focus-within { border-color: var(--blue); background: var(--white); }
.tn-search input {
  border: none; background: transparent; outline: none;
  font-family: 'DM Sans', sans-serif; font-size: 13.5px; color: var(--ink); width: 100%;
}
.tn-search input::placeholder { color: var(--ink3); }

.notif-btn {
  width: 36px; height: 36px; border-radius: 9px;
  border: 1.5px solid var(--border); background: var(--white);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  position: relative; transition: border-color 0.15s;
}
.notif-btn:hover { border-color: var(--blue); }
.notif-dot {
  position: absolute; top: 6px; right: 6px;
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--red); border: 1.5px solid var(--white);
}
.notif-dropdown {
  position: fixed; top: 70px; right: 30px;
  background: var(--white); border: 3px solid var(--blue);
  border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  min-width: 320px; max-width: 400px;
  z-index: 99999; display: none;
  padding: 20px;
}
.notif-dropdown.show {
  display: block;
}
.notif-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; border-bottom: 1px solid var(--border);
}
.notif-header h4 {
  margin: 0; font-size: 0.9rem; font-weight: 600;
  color: var(--text);
}
.notif-clear {
  background: none; border: none; color: var(--muted);
  font-size: 0.75rem; cursor: pointer; padding: 4px 8px;
  border-radius: 4px; transition: all 0.15s;
}
.notif-clear:hover {
  background: var(--off); color: var(--red);
}
.notif-list {
  max-height: 300px; overflow-y: auto;
}
.notif-empty {
  padding: 20px; text-align: center; color: var(--muted);
  font-size: 0.85rem;
}
.notif-item {
  padding: 12px 16px; border-bottom: 1px solid var(--border);
  cursor: pointer; transition: background 0.15s;
}
.notif-item:hover {
  background: var(--off);
}
.notif-item.unread {
  background: #f0f9ff; border-left: 3px solid var(--blue);
}
.notif-title {
  font-size: 0.85rem; font-weight: 600; color: var(--text);
  margin-bottom: 4px;
}
.notif-message {
  font-size: 0.8rem; color: var(--muted);
  line-height: 1.4;
}
.notif-time {
  font-size: 0.75rem; color: var(--muted);
  margin-top: 4px;
}
.user-pill {
  display: flex; align-items: center; gap: 8px;
  padding: 4px 12px 4px 4px;
  border: 1.5px solid var(--border); border-radius: 20px;
  background: var(--white); cursor: pointer;
  transition: border-color 0.15s;
}
.user-pill:hover { border-color: var(--blue); }
.user-av {
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, #3B6FE8, #6B4FDB);
  display: flex; align-items: center; justify-content: center;
  font-family: 'Sora', sans-serif; font-weight: 700; font-size: 11px; color: #fff;
}
.user-name { font-size: 13px; font-weight: 600; color: var(--ink); }
.logout-link {
  font-size: 12px; color: var(--red); font-weight: 600;
  text-decoration: none; padding: 5px 10px; border-radius: 7px;
  border: 1.5px solid rgba(240,82,82,0.2);
  transition: all 0.15s; background: var(--red-lt);
}
.logout-link:hover { background: var(--red); color: #fff; }

/* ══ LAYOUT ══════════════════════════════════════════ */
.main {
  padding: 28px 32px;
  max-width: 1400px;
  margin: 0 auto;
}

/* ══ CARDS ══════════════════════════════════════════ */
.card {
  background: var(--white);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
  overflow: hidden;
  margin-bottom: 20px;
}
.card-hd {
  padding: 18px 22px;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
}
.card-title {
  font-family: 'Sora', sans-serif;
  font-size: 15px; font-weight: 700; color: var(--ink);
  letter-spacing: -0.01em;
}
.card-tag {
  font-size: 12px; font-weight: 600; color: var(--ink3);
  background: var(--bg); padding: 4px 10px; border-radius: 20px;
  border: 1px solid var(--border);
}
.card-bd { padding: 20px 22px; }

/* ══ STAT TILES ══════════════════════════════════════ */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px; margin-bottom: 24px;
}
.stat-tile {
  border-radius: var(--radius); padding: 20px 22px;
  display: flex; align-items: center; gap: 16px;
  position: relative; overflow: hidden;
}
.stat-tile:nth-child(1) { background: linear-gradient(135deg,#4776E6,#8E54E9); }
.stat-tile:nth-child(2) { background: linear-gradient(135deg,#F05252,#FF7B7B); }
.stat-tile:nth-child(3) { background: linear-gradient(135deg,#0BB5B5,#36D1C4); }
.stat-tile:nth-child(4) { background: linear-gradient(135deg,#F4A83A,#F7CB6A); }
.stat-tile::before {
  content:''; position:absolute; top:-30px; right:-30px;
  width:100px; height:100px; border-radius:50%;
  background:rgba(255,255,255,0.12); pointer-events:none;
}
.stat-icon {
  width:48px; height:48px; border-radius:12px;
  background:rgba(255,255,255,0.2);
  display:flex; align-items:center; justify-content:center;
  font-size:22px; flex-shrink:0;
}
.stat-body { flex:1; }
.stat-label { font-size:12px; color:rgba(255,255,255,0.75); font-weight:500; margin-bottom:3px; }
.stat-value {
  font-family:'Sora',sans-serif; font-size:30px; font-weight:700;
  color:#fff; line-height:1; letter-spacing:-0.02em;
}

/* ══ BUTTONS ══════════════════════════════════════════ */
.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 18px; border-radius: 9px; border: none;
  font-family: 'DM Sans', sans-serif; font-size: 13.5px; font-weight: 600;
  cursor: pointer; text-decoration: none; transition: all 0.15s; white-space: nowrap;
}
.btn-primary {
  background: var(--blue); color: #fff;
  box-shadow: 0 3px 10px rgba(59,111,232,0.3);
}
.btn-primary:hover { box-shadow:0 5px 18px rgba(59,111,232,0.4); transform:translateY(-1px); }
.btn-outline {
  background: var(--white); color: var(--ink2);
  border: 1.5px solid var(--border);
}
.btn-outline:hover { border-color:var(--blue); color:var(--blue); }
.btn-success { background: var(--green); color: #fff; }
.btn-success:hover { filter:brightness(1.1); transform:translateY(-1px); }
.btn-danger { background: var(--red); color: #fff; }
.btn-danger:hover { filter:brightness(1.1); transform:translateY(-1px); }
.btn-warning { background: var(--amber); color: #fff; }
.btn-warning:hover { filter:brightness(1.1); transform:translateY(-1px); }
.btn-sm { padding:5px 12px; font-size:12px; border-radius:7px; }

/* ══ TABLES ══════════════════════════════════════════ */
.data-table { width:100%; border-collapse:collapse; }
.data-table th {
  padding:11px 16px; text-align:left;
  font-size:11.5px; font-weight:700; letter-spacing:0.05em; text-transform:uppercase;
  color:var(--ink3); background:var(--bg);
  border-bottom:1px solid var(--border); white-space:nowrap;
}
.data-table td {
  padding:13px 16px; border-bottom:1px solid var(--border);
  vertical-align:middle; font-size:13.5px; color:var(--ink);
}
.data-table tr:last-child td { border-bottom:none; }
.data-table tbody tr { transition:background 0.1s; }
.data-table tbody tr:hover { background:#FAFBFF; }

/* ══ BADGES ══════════════════════════════════════════ */
.badge {
  display:inline-flex; align-items:center;
  padding:4px 11px; border-radius:20px;
  font-size:12px; font-weight:700;
}
.badge-blue    { background:var(--blue-lt); color:var(--blue); }
.badge-green   { background:#E8F8F0;        color:var(--green); }
.badge-red     { background:var(--red-lt);  color:var(--red); }
.badge-amber   { background:var(--amber-lt);color:#C67C00; }
.badge-teal    { background:var(--teal-lt); color:var(--teal); }
.badge-neutral { background:var(--bg);      color:var(--ink3); border:1px solid var(--border); }

/* ══ FORMS ══════════════════════════════════════════ */
.form-section {
  background: var(--white); border-radius: var(--radius);
  border: 1px solid var(--border); box-shadow: var(--shadow);
  padding: 28px; margin-bottom: 24px;
}
.form-section-title {
  font-family: 'Sora', sans-serif; font-size: 15px; font-weight: 700;
  color: var(--ink); margin-bottom: 20px;
  display: flex; align-items: center; gap: 8px;
}
.form-section-title::before {
  content:''; width:4px; height:18px;
  background: linear-gradient(135deg,#3B6FE8,#6B4FDB);
  border-radius:2px;
}
.form-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
.form-grid.cols-1 { grid-template-columns:1fr; }
.form-grid.cols-3 { grid-template-columns:1fr 1fr 1fr; }
.form-group { display:flex; flex-direction:column; gap:6px; }
.form-group.full { grid-column:1/-1; }
.form-label {
  font-size:11.5px; font-weight:700; letter-spacing:0.06em;
  text-transform:uppercase; color:var(--ink2);
}
.form-ctrl {
  padding:10px 14px;
  background:var(--bg); border:1.5px solid var(--border);
  border-radius:var(--radius-sm);
  font-family:'DM Sans',sans-serif; font-size:14px; color:var(--ink);
  outline:none; transition:all 0.2s; width:100%;
}
.form-ctrl:focus { border-color:var(--blue); background:var(--white); box-shadow:0 0 0 3px rgba(59,111,232,0.1); }
textarea.form-ctrl { resize:vertical; min-height:90px; }
select.form-ctrl { cursor:pointer; }
.form-actions {
  display:flex; gap:12px; margin-top:24px;
  padding-top:18px; border-top:1px solid var(--border);
}

/* ══ TOAST ══════════════════════════════════════════ */
#toasts {
  position:fixed; top:72px; right:20px; z-index:9999;
  display:flex; flex-direction:column; gap:8px; max-width:340px;
}
.toast {
  background:var(--white); border-radius:10px; padding:13px 16px;
  border:1px solid var(--border); box-shadow:var(--shadow-md);
  display:flex; align-items:flex-start; gap:10px;
  animation:toastIn 0.3s cubic-bezier(0.34,1.56,0.64,1);
}
.toast-bar { width:4px; border-radius:2px; align-self:stretch; flex-shrink:0; }
.toast.success .toast-bar { background:var(--green); }
.toast.error   .toast-bar { background:var(--red); }
.toast.info    .toast-bar { background:var(--blue); }
.toast.warning .toast-bar { background:var(--amber); }
.toast-title { font-weight:700; font-size:13px; color:var(--ink); }
.toast-msg { font-size:12px; color:var(--ink3); margin-top:2px; }
.toast-x { margin-left:auto; cursor:pointer; color:var(--ink3); font-size:14px; background:none; border:none; }
@keyframes toastIn  { from{transform:translateX(110%);opacity:0;} to{transform:translateX(0);opacity:1;} }
@keyframes toastOut { from{transform:translateX(0);opacity:1;} to{transform:translateX(110%);opacity:0;} }
@keyframes fadeUp   { from{transform:translateY(14px);opacity:0;} to{transform:translateY(0);opacity:1;} }

/* ══ PAGE HEADER ══════════════════════════════════════ */
.page-hd {
  display:flex; align-items:center; justify-content:space-between;
  margin-bottom:24px; flex-wrap:wrap; gap:12px;
}
.page-title {
  font-family:'Sora',sans-serif; font-size:22px; font-weight:700;
  color:var(--ink); letter-spacing:-0.02em;
}
.page-sub { font-size:13px; color:var(--ink3); margin-top:2px; }

/* ══ EMPTY STATE ══════════════════════════════════════ */
.empty {
  text-align:center; padding:48px 24px; color:var(--ink3);
}
.empty-icon { font-size:40px; margin-bottom:12px; }
.empty-title {
  font-family:'Sora',sans-serif; font-weight:700; font-size:15px;
  color:var(--ink2); margin-bottom:6px;
}
.empty-desc { font-size:13px; }

/* ══ MISC ════════════════════════════════════════════ */
.emp-cell { display:flex; align-items:center; gap:10px; }
.emp-av {
  width:32px; height:32px; border-radius:9px; flex-shrink:0;
  background:linear-gradient(135deg,#4776E6,#8E54E9);
  display:flex; align-items:center; justify-content:center;
  font-family:'Sora',sans-serif; font-weight:700; font-size:12px; color:#fff;
}
.action-grp { display:flex; gap:5px; flex-wrap:wrap; }

/* ══ SCROLLBAR ════════════════════════════════════════ */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:rgba(0,0,0,0.15); }

/* ══ RESPONSIVE ══════════════════════════════════════ */
@media(max-width:1100px) { .stats-row { grid-template-columns:repeat(2,1fr); } }
@media(max-width:900px) {
  .main { padding:20px 16px; }
  .tn-search { display:none; }
  .form-grid { grid-template-columns:1fr; }
  .form-grid.cols-3 { grid-template-columns:1fr; }
}
</style>
"""

# ─────────────────────────────────────────────────────────
# NAV CONFIG
# ─────────────────────────────────────────────────────────
NAV_ITEMS = [
    ("dashboard",      "Overview",       "📊"),
    ("jobs",           "Job Management", "💼"),
    ("ai-screening",   "AI Screening",   "🧠"),
    ("interviews",     "Interviews",     "📅"),
    ("assessments",    "Assessments",    "📋"),
    ("communications", "Messages",       "✉️"),
    ("offers",         "Offers",         "📝"),
    ("evaluations",    "Evaluation",     "📝"),
    ("reports",        "Reports",        "🗒️"),
    ("post-job",       "Post Job",       "➕"),
]

# Pages that go in the secondary (right) group
SECONDARY_PAGES = {"reports", "post-job"}

# SVG icons for nav links
NAV_ICONS = {
    "dashboard":      '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
    "jobs":           '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>',
    "interviews":     '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
    "offers":         '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    "Evaluations":    '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    "assessments":    '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><rect x="9" y="2" width="6" height="4" rx="1"/><path d="M9 2H5a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2h-4"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="13" y2="16"/></svg>',
    "reports":        '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "post-job":       '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
    "ai-screening":   '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>',
    "communications": '<svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>',
   
}


def _build_topnav(current_page: str, current_user: str) -> str:
    """Render the top navigation bar HTML."""
    user_initial = (current_user or "H")[0].upper()
    user_name    = (current_user or "HR Admin").split("@")[0].replace(".", " ").title()

    # Primary links (left group)
    primary_links = ""
    secondary_links = ""
    for page, label, _ in NAV_ITEMS:
        active = 'active' if page == current_page else ''
        icon   = NAV_ICONS.get(page, "")
        link   = f'<a class="tn-link {active}" href="/{page}">{icon} {label}</a>'
        if page in SECONDARY_PAGES:
            secondary_links += link
        else:
            primary_links += link

    return f"""
<nav class="topnav">
  <a class="tn-brand" href="/dashboard">
    <div class="tn-logo">TF</div>
    <span class="tn-name">TalentFlow.<span>Pro</span></span>
  </a>

  <div class="tn-links">
    {primary_links}
    <div class="tn-sep"></div>
    {secondary_links}
  </div>

  <div class="tn-right">
    <div class="tn-search">
      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="#8A8FA8" stroke-width="2.5">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input type="text" placeholder="Search anything…" id="globalSearch" oninput="globalSearchFn(this.value)">
    </div>
    <button class="notif-btn" title="Notifications" onclick="toggleNotifications()">
      <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
      <span class="notif-dot" id="notifCount"></span>
    </button>
    <div class="notif-dropdown" id="notifDropdown">
      <div class="notif-header">
        <h4>Notifications</h4>
        <button class="notif-clear" onclick="clearAllNotifications()">Clear All</button>
      </div>
      <div class="notif-list" id="notifList">
        <div class="notif-empty">No new notifications</div>
      </div>
    </div>
    <div class="user-pill">
      <div class="user-av">{user_initial}</div>
      <span class="user-name">{user_name}</span>
      <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="#8A8FA8" stroke-width="2.5">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </div>
    <a href="/logout" class="logout-link">⏏ Logout</a>
  </div>
</nav>
<div id="toasts"></div>
<div class="tf-backdrop" id="tfBackdrop" role="dialog" aria-modal="true" aria-hidden="true">
  <div class="tf-dialog" role="document" aria-labelledby="tfDialogTitle">
    <div class="tf-dialog-hd">
      <div class="tf-dialog-title" id="tfDialogTitle">Confirm</div>
      <button class="btn btn-sm btn-outline" onclick="window.tfDialog?.close(false)">Close</button>
    </div>
    <div class="tf-dialog-bd" id="tfDialogBody"></div>
    <div class="tf-dialog-ft" id="tfDialogFooter"></div>
  </div>
</div>
"""


def _shared_js() -> str:
    """Toast utility + global search stub — included on every page."""
    return """
<script>
function showToast(title, msg, type='info', dur=4500) {
  const c = document.getElementById('toasts');
  if (!c) return;
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  t.innerHTML = `
    <div class="toast-bar"></div>
    <div style="flex:1">
      <div class="toast-title">${title}</div>
      <div class="toast-msg">${msg}</div>
    </div>
    <button class="toast-x" onclick="this.closest('.toast').remove()">✕</button>`;
  c.appendChild(t);
  setTimeout(() => {
    t.style.animation = 'toastOut 0.25s ease forwards';
    setTimeout(() => t.remove(), 250);
  }, dur);
}
const showSuccess = (m,t='Success') => showToast(t,m,'success');
const showError   = (m,t='Error')   => showToast(t,m,'error',  8000);
const showWarning = (m,t='Warning') => showToast(t,m,'warning',6000);
const showInfo    = (m,t='Info')    => showToast(t,m,'info',   4000);

// Professional dialogs (avoid "localhost says..." browser popups)
window.tfDialog = (function(){
  let resolver = null;
  function _els(){
    return {
      back: document.getElementById('tfBackdrop'),
      title: document.getElementById('tfDialogTitle'),
      body: document.getElementById('tfDialogBody'),
      foot: document.getElementById('tfDialogFooter'),
    };
  }
  function _open({title='Confirm', bodyHtml='', footerButtons=[]}){
    const {back, title:ti, body, foot} = _els();
    if(!back) return;
    ti.textContent = title;
    body.innerHTML = bodyHtml;
    foot.innerHTML = '';
    footerButtons.forEach(btn => foot.appendChild(btn));
    back.classList.add('show');
    back.setAttribute('aria-hidden','false');
  }
  function close(val){
    const {back, body, foot} = _els();
    if(back){
      back.classList.remove('show');
      back.setAttribute('aria-hidden','true');
      body.innerHTML = '';
      foot.innerHTML = '';
    }
    if(resolver){ const r = resolver; resolver = null; r(val); }
  }
  function confirm({title='Confirm', message='Are you sure?', okText='Confirm', cancelText='Cancel', danger=false}){
    return new Promise((resolve) => {
      resolver = resolve;
      const ok = document.createElement('button');
      ok.className = danger ? 'btn btn-danger' : 'btn btn-primary';
      ok.textContent = okText;
      ok.onclick = () => close(true);

      const cancel = document.createElement('button');
      cancel.className = 'btn btn-outline';
      cancel.textContent = cancelText;
      cancel.onclick = () => close(false);

      _open({
        title,
        bodyHtml: `<div style="white-space:pre-wrap;">${String(message||'')}</div>`,
        footerButtons: [cancel, ok],
      });
    });
  }
  function prompt({title='Input', label='Reason', placeholder='', defaultValue='', okText='Save', cancelText='Cancel', multiline=true}){
    return new Promise((resolve) => {
      resolver = resolve;
      const id = 'tfPromptInput';
      const inputHtml = multiline
        ? `<textarea class="tf-input" id="${id}" rows="4" placeholder="${placeholder}"></textarea>`
        : `<input class="tf-input" id="${id}" placeholder="${placeholder}" />`;

      const ok = document.createElement('button');
      ok.className = 'btn btn-primary';
      ok.textContent = okText;
      ok.onclick = () => {
        const el = document.getElementById(id);
        close(el ? el.value : '');
      };

      const cancel = document.createElement('button');
      cancel.className = 'btn btn-outline';
      cancel.textContent = cancelText;
      cancel.onclick = () => close(null);

      _open({
        title,
        bodyHtml: `
          <div style="font-size:12px;font-weight:800;color:var(--ink3);text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;">${label}</div>
          ${inputHtml}
        `,
        footerButtons: [cancel, ok],
      });

      const el = document.getElementById(id);
      if(el){
        el.value = defaultValue || '';
        setTimeout(()=>el.focus(), 40);
      }
    });
  }
  // Close on backdrop click / Esc
  document.addEventListener('keydown', (e) => {
    if(e.key === 'Escape'){
      const back = document.getElementById('tfBackdrop');
      if(back && back.classList.contains('show')) close(false);
    }
  });
  document.addEventListener('click', (e) => {
    const back = document.getElementById('tfBackdrop');
    if(back && e.target === back && back.classList.contains('show')) close(false);
  });
  return { confirm, prompt, close };
})();

// Global search — pages can override this
function globalSearchFn(q) {
  q = q.toLowerCase();
  document.querySelectorAll('[data-searchable]').forEach(r => {
    r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

// Notification system
let notifications = [];
let notificationInterval;

function toggleNotifications() {
  console.log('Notification button clicked!');
  const dropdown = document.getElementById('notifDropdown');
  console.log('Dropdown element found:', dropdown);
  
  if (dropdown) {
    dropdown.classList.toggle('show');
    console.log('Dropdown classes after toggle:', dropdown.className);
    console.log('Is show class present?', dropdown.classList.contains('show'));
    
    // Close when clicking outside
    if (dropdown.classList.contains('show')) {
      setTimeout(() => {
        document.addEventListener('click', closeNotificationsOutside);
      }, 100);
    }
  } else {
    console.error('notifDropdown element not found!');
  }
}

function closeNotificationsOutside(e) {
  const dropdown = document.getElementById('notifDropdown');
  if (!dropdown.contains(e.target) && !e.target.closest('.notif-btn')) {
    dropdown.classList.remove('show');
    document.removeEventListener('click', closeNotificationsOutside);
  }
}

function loadNotifications() {
  console.log('Loading notifications...');
  fetch('/api/contact-messages/unread')
    .then(response => response.json())
    .then(data => {
      console.log('Notifications data received:', data);
      notifications = data;
      updateNotificationUI();
    })
    .catch(error => console.error('Error loading notifications:', error));
}

function updateNotificationUI() {
  console.log('Updating notification UI with:', notifications);
  const notifCount = document.getElementById('notifCount');
  const notifList = document.getElementById('notifList');
  
  console.log('notifCount element:', notifCount);
  console.log('notifList element:', notifList);
  
  if (notifications.length === 0) {
    console.log('No notifications, hiding count');
    if (notifCount) notifCount.style.display = 'none';
    if (notifList) notifList.innerHTML = '<div class="notif-empty">No new notifications</div>';
  } else {
    console.log('Found', notifications.length, 'notifications');
    if (notifCount) {
      notifCount.style.display = 'block';
      notifCount.textContent = notifications.length;
    }
    
    const notifHTML = notifications.map(notif => `
      <div class="notif-item unread" onclick="markAsRead(${notif.id})">
        <div class="notif-title">New Contact Message</div>
        <div class="notif-message">${notif.name}: ${notif.subject}</div>
        <div class="notif-time">${formatTime(notif.created_at)}</div>
      </div>
    `).join('');
    
    console.log('Generated notification HTML:', notifHTML);
    if (notifList) notifList.innerHTML = notifHTML;
  }
}

function markAsRead(messageId) {
  fetch(`/api/contact-messages/${messageId}/mark-read`, {
    method: 'PUT'
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Remove from notifications list
      notifications = notifications.filter(n => n.id !== messageId);
      updateNotificationUI();
      showSuccess('Message marked as read');
    }
  })
  .catch(error => console.error('Error marking as read:', error));
}

function clearAllNotifications() {
  if (notifications.length === 0) return;
  
  if (confirm('Clear all notifications?')) {
    Promise.all(notifications.map(n => 
      fetch(`/api/contact-messages/${n.id}/mark-read`, { method: 'PUT' })
    ))
    .then(() => {
      notifications = [];
      updateNotificationUI();
      showSuccess('All notifications cleared');
    })
    .catch(error => console.error('Error clearing notifications:', error));
  }
}

function formatTime(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;
  
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return Math.floor(diff / 60000) + ' minutes ago';
  if (diff < 86400000) return Math.floor(diff / 3600000) + ' hours ago';
  return date.toLocaleDateString();
}

// Auto-refresh notifications every 30 seconds
function startNotificationRefresh() {
  loadNotifications();
  notificationInterval = setInterval(loadNotifications, 30000);
}

// Stop refresh when page is hidden
document.addEventListener('visibilitychange', function() {
  if (document.hidden) {
    clearInterval(notificationInterval);
  } else {
    startNotificationRefresh();
  }
});

// Start notification system
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(startNotificationRefresh, 500); // Small delay to ensure page is ready
});
</script>
"""


# ─────────────────────────────────────────────────────────
# PUBLIC API  (used by page modules)
# ─────────────────────────────────────────────────────────
def get_base_html(title: str, current_page: str = "", current_user: str = "") -> str:
    """
    Return the opening HTML for a page — everything up to (and including)
    <div class="main">.  Call get_end_html() to close it.
    """
    user_name = (current_user or "HR Admin").split("@")[0].replace(".", " ").title()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — TalentFlow HR</title>
  {SHARED_CSS}
</head>
<body>
{_build_topnav(current_page, current_user)}
<div class="main">
"""


def get_end_html() -> str:
    """Return the closing HTML for a page."""
    return f"""
</div><!-- /main -->
{_shared_js()}
</body>
</html>"""


# ─────────────────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────────────────
LOGIN_HTML = FONTS + """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TalentFlow HR — Sign In</title>
  <style>
  *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family:'DM Sans',sans-serif;
    min-height:100vh; display:flex; align-items:center; justify-content:center;
    background:#EEF2F7; padding:40px 20px;
  }
  .login-wrapper {
    width:100%; max-width:1200px;
    height:600px; background:#fff; border-radius:20px;
    box-shadow:0 20px 60px rgba(30,40,90,0.15);
    display:flex; overflow:hidden;
  }
  .brand {
    flex:0 0 52%;
    background:linear-gradient(145deg,#3B6FE8 0%,#5B3FDB 50%,#6B4FDB 100%);
    display:flex; flex-direction:column; justify-content:space-between;
    padding:52px 64px; position:relative; overflow:hidden;
  }
  .brand::after {
    content:''; position:absolute; top:0; right:-1px;
    width:120px; height:100%; background:#EEF2F7;
    clip-path:polygon(100% 0,100% 100%,0 100%);
  }
  .brand-hero { position:relative; z-index:2; }
  .brand-logo {
    display:flex; align-items:center; gap:10px; margin-bottom:48px;
  }
  .brand-logo-mark {
    width:38px; height:38px; border-radius:10px;
    background:rgba(255,255,255,0.2);
    display:flex; align-items:center; justify-content:center;
    font-family:'Sora',sans-serif; font-weight:800; font-size:14px; color:#fff;
  }
  .brand-logo-name {
    font-family:'Sora',sans-serif; font-weight:700; font-size:18px; color:#fff;
  }
  .brand-headline {
    font-family:'Sora',sans-serif; font-weight:800;
    font-size:clamp(40px,4vw,62px); line-height:0.95;
    color:#fff; letter-spacing:-0.03em; margin-bottom:20px;
  }
  .brand-headline em { font-style:normal; opacity:0.45; }
  .brand-desc {
    font-size:15px; color:rgba(255,255,255,0.65);
    line-height:1.7; max-width:360px; margin-bottom:40px;
  }
  .feat-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
  .feat {
    background:rgba(255,255,255,0.09); border:1px solid rgba(255,255,255,0.12);
    border-radius:11px; padding:13px 15px;
    display:flex; align-items:center; gap:8px;
    font-size:12.5px; color:rgba(255,255,255,0.78); font-weight:500;
  }
  .brand-footer { font-size:11px; color:rgba(255,255,255,0.28); position:relative; z-index:2; }

  .login-pane {
    flex:1; display:flex; align-items:center; justify-content:center;
    padding:60px 48px;
    background:#fff;
  }
  .login-inner { width:100%; max-width:380px; }
  .login-logo {
    display:flex; align-items:center; gap:9px; margin-bottom:36px;
  }
  .login-logo-mark {
    width:36px; height:36px; border-radius:9px;
    background:linear-gradient(135deg,#3B6FE8,#6B4FDB);
    display:flex; align-items:center; justify-content:center;
    font-family:'Sora',sans-serif; font-weight:800; font-size:13px; color:#fff;
    box-shadow:0 3px 10px rgba(59,111,232,0.35);
  }
  .login-logo-name {
    font-family:'Sora',sans-serif; font-weight:700; font-size:16px; color:#1A1D2E;
  }
  .login-heading {
    font-family:'Sora',sans-serif; font-weight:800; font-size:28px;
    color:#1A1D2E; margin-bottom:6px; letter-spacing:-0.02em;
  }
  .login-sub { font-size:14px; color:#8A8FA8; margin-bottom:32px; }
  .field { margin-bottom:18px; }
  .field label {
    display:block; font-size:11px; font-weight:700;
    letter-spacing:0.08em; text-transform:uppercase;
    color:#4A5066; margin-bottom:7px;
  }
  .field input {
    width:100%; padding:12px 15px;
    background:#fff; border:1.5px solid #E8EBF4;
    border-radius:9px;
    font-family:'DM Sans',sans-serif; font-size:14px; color:#1A1D2E;
    outline:none; transition:all 0.2s;
  }
  .field input:focus { border-color:#3B6FE8; box-shadow:0 0 0 3px rgba(59,111,232,0.1); }
  .submit-btn {
    width:100%; padding:13px;
    background:linear-gradient(135deg,#3B6FE8,#6B4FDB);
    color:#fff; border:none; border-radius:9px;
    font-family:'Sora',sans-serif; font-size:14px; font-weight:700;
    cursor:pointer; transition:all 0.2s; margin-top:6px;
    box-shadow:0 4px 14px rgba(59,111,232,0.35);
  }
  .submit-btn:hover { box-shadow:0 6px 22px rgba(59,111,232,0.5); transform:translateY(-1px); }
  .err { background:#FEF0F0; border:1px solid rgba(240,82,82,0.25); border-radius:9px;
         color:#F05252; font-size:13px; padding:11px 14px; margin-bottom:18px; }
  .divider { height:1px; background:#E8EBF4; margin:24px 0; }
  .trust { display:flex; gap:12px; flex-wrap:wrap; }
  .trust-pill {
    font-size:11px; color:#8A8FA8;
    display:flex; align-items:center; gap:5px;
    padding:4px 11px; background:#fff;
    border:1px solid #E8EBF4; border-radius:20px;
  }
  .trust-dot { width:6px; height:6px; border-radius:50%; background:#27AE60; }
  @media(max-width:860px){
    body{padding:20px 16px;}
    .login-wrapper{
      max-width:100%; height:auto; min-height:500px; flex-direction:column;
    }
    .brand{flex:none;min-height:300px;padding:36px;}
    .brand::after{display:none;}
    .login-pane{padding:36px;}
    .feat-grid{grid-template-columns:1fr 1fr;}
  }
  @media(max-width:480px){
    .login-wrapper{height:auto; min-height:400px;}
    .brand{min-height:250px; padding:24px;}
    .login-pane{padding:24px;}
  }
  </style>
</head>
<body>
<div class="login-wrapper">
  <div class="brand">
    <div class="brand-hero">
      <div class="brand-logo">
        <div class="brand-logo-mark">TF</div>
        <span class="brand-logo-name">TalentFlowPro</span>
      </div>
      <h1 class="brand-headline">Talent<br><em>Flow</em><br>Pro</h1>
      <p class="brand-desc">
        Your all-in-one HR intelligence platform — score resumes, schedule
        interviews, and manage your hiring pipeline with ease.
      </p>
      <div class="feat-grid">
        <div class="feat">🧠 AI Resume Scoring</div>
        <div class="feat">📊 Live Analytics</div>
        <div class="feat">📅 Interview Scheduler</div>
        <div class="feat">✉️ Email Automation</div>
        <div class="feat">🗂️ ATS Pipeline</div>
        <div class="feat">📝 Offer Management</div>
      </div>
    </div>
    <div class="brand-footer">© 2025 ZIBITECH · All rights reserved.</div>
  </div>

  <div class="login-pane">
    <div class="login-inner">
    <div class="login-logo">
      <div class="login-logo-mark">TF</div>
      <span class="login-logo-name">TalentFlow Pro</span>
    </div>
    <h2 class="login-heading">Welcome back</h2>
    <p class="login-sub">Sign in to your HR workspace</p>

    {% if error %}<div class="err">⚠ {{ error }}</div>{% endif %}

    <form method="post" action="/login">
      <div class="field">
        <label for="email">Email address</label>
        <input type="email" id="email" name="email" placeholder="you@zibitech.com" required>
      </div>
      <div class="field">
        <label for="password">Password</label>
        <input type="password" id="password" name="password" placeholder="••••••••••" required>
      </div>
      <button type="submit" class="submit-btn">Sign In →</button>
    </form>

    <div class="divider"></div>
    
    <div style="text-align: center; margin-top: 1rem;">
      <a href="/forgot-password" style="color: var(--ink3); text-decoration: none; font-size: 0.9rem; transition: color 0.2s;">Forgot your password?</a>
    </div>
    
  </div>
  </div>
</div>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────
# AUTH ROUTES
# ____________________________________________________________________________

HR_CREDENTIALS = {
    "angelbrenna20@gmail.com": "Niyigena2003@",
    "manager@zibitech.com":    "manager@",
}

@app.get("/", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(content=Template(LOGIN_HTML).render(error=None))


@app.get("/login", response_class=HTMLResponse)
async def login_page_get():
    return HTMLResponse(content=Template(LOGIN_HTML).render(error=None))


@app.post("/login")
async def login(request: Request):
    form  = await request.form()
    email = form.get("email", "")
    pwd   = form.get("password", "")

    if email in HR_CREDENTIALS and HR_CREDENTIALS[email] == pwd:
        token = create_session(email)
        # Non-blocking notification — ignore failure
        send_email(
            email,
            "HR Portal Login Notification",
            f"<h3>Login detected</h3><p>Email: {email}<br>Time: {datetime.now()}</p>",
            is_html=True,
        )
        resp = RedirectResponse(url="/dashboard", status_code=302)
        resp.set_cookie("hr_token", token, httponly=True)
        return resp

    # Failed login
    return HTMLResponse(
        content=Template(LOGIN_HTML).render(error="Invalid email or password"),
        status_code=401,
    )


@app.get("/sso/hr")
async def hr_sso_login(request: Request):
    """
    One-click SSO for HRMS → recruitment portal.
    HRMS redirects here with a shared secret; we create an HR session and redirect to the requested page.
    """
    token = (request.query_params.get("token") or "").strip()
    next_path = (request.query_params.get("next") or "/post-job").strip()
    if not next_path.startswith("/"):
        next_path = "/post-job"

    expected = os.getenv("TALENTFLOW_HR_SSO_TOKEN", "").strip()
    if not expected or not token or not secrets.compare_digest(expected, token):
        return HTMLResponse(content="Unauthorized", status_code=403)

    email = os.getenv("TALENTFLOW_HR_SSO_EMAIL", "angelbrenna20@gmail.com").strip() or "angelbrenna20@gmail.com"
    sess = create_session(email)
    resp = RedirectResponse(url=next_path, status_code=302)
    resp.set_cookie("hr_token", sess, httponly=True)
    return resp


@app.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("hr_token")
    if token and token in sessions:
        del sessions[token]
    resp = RedirectResponse(url="http://localhost:8005", status_code=302)
    resp.delete_cookie("hr_token")
    return resp


# Forgot password functionality moved to separate file to avoid syntax errors
# Import the simple forgot password implementation
try:
    import forgot_password_simple
except ImportError:
    pass  # If file doesn't exist, HR portal will still work


# ─────────────────────────────────────────────────────────
# STATUS API  (shared across pages)
# ─────────────────────────────────────────────────────────
@app.post("/api/update-application-status")
async def update_application_status(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse({"success": False, "error": "Unauthorized"}, status_code=401)
    try:
        data       = await request.json()
        app_id     = data.get("application_id")
        new_status = data.get("status")
        db.update_application_status(app_id, new_status)
        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    print("Starting TalentFlow HR Portal  →  http://localhost:8003")
    uvicorn.run(app, host="0.0.0.0", port=8003)