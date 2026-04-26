from fastapi import FastAPI, Request, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import ResumeDatabase
from simple_app import SimpleResumeScorer
import os
import secrets
import pypdf
import os
import shutil
import uuid
from typing import Optional

app = FastAPI(title="Job Application Portal", description="Modern Job Portal for Applicants and HR")

# Initialize database and scorer
db = ResumeDatabase()
scorer = SimpleResumeScorer()

# Create templates directory
os.makedirs("templates", exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SHARED SNIPPETS (from modern_portal.py)
# ─────────────────────────────────────────────────────────────────────────────

_BASE_HEAD = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Nunito+Sans:wght@300;400;600&display=swap" rel="stylesheet">
<style>
  :root {
    --blue:       #3b5bdb;
    --blue-dark:  #2846c4;
    --blue-light: #5c7cfa;
    --violet:     #7048e8;
    --red:        #fa5252;
    --white:      #ffffff;
    --off:        #f8f9fc;
    --text:       #2d3748;
    --muted:      #718096;
    --border:     #e8edf5;
    --card-sh:    0 8px 40px rgba(59,91,219,.10);
    --card-sh-h:  0 16px 60px rgba(59,91,219,.18);
  }
  *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
  html { scroll-behavior:smooth; }
  body { font-family:'Nunito Sans', sans-serif; background:var(--white); color:var(--text); overflow-x:hidden; }
  ::-webkit-scrollbar { width:4px; }
  ::-webkit-scrollbar-thumb { background:var(--blue); border-radius:2px; }

  @keyframes fadeUp    { from{opacity:0;transform:translateY(30px)} to{opacity:1;transform:translateY(0)} }
  @keyframes fadeIn    { from{opacity:0} to{opacity:1} }
  @keyframes floatUI   { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-14px)} }
  @keyframes slideDown { from{opacity:0;transform:translateY(-16px)} to{opacity:1;transform:translateY(0)} }
  @keyframes loaderOut { to{opacity:0;pointer-events:none} }
  @keyframes spin      { to{transform:rotate(360deg)} }

  .page-loader { position:fixed;inset:0;background:var(--white);z-index:9999;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:1rem;animation:loaderOut .3s 1s ease both; }
  .loader-logo { font-family:'Nunito',sans-serif;font-size:1.6rem;font-weight:900;color:var(--blue); }
  .loader-spin { width:28px;height:28px;border:3px solid var(--border);border-top-color:var(--blue);border-radius:50%;animation:spin .7s linear infinite; }

  .reveal { opacity:0;transform:translateY(28px);transition:opacity .65s ease,transform .65s ease; }
  .reveal.visible { opacity:1;transform:translateY(0); }
  .reveal-d1{transition-delay:.1s} .reveal-d2{transition-delay:.2s} .reveal-d3{transition-delay:.3s} .reveal-d4{transition-delay:.4s}

  /* NAV */
  nav { position:fixed;top:0;left:0;right:0;z-index:200;display:flex;align-items:center;justify-content:space-between;padding:.9rem 4rem;background:rgba(255,255,255,.96);backdrop-filter:blur(16px);box-shadow:0 2px 20px rgba(59,91,219,.08);animation:slideDown .5s ease both; }
  .nav-logo { font-family:'Nunito',sans-serif;font-size:1.3rem;font-weight:900;color:var(--blue);text-decoration:none;display:flex;align-items:center;gap:.5rem; }
  .nav-logo-dot { width:8px;height:8px;border-radius:50%;background:var(--red);display:inline-block; }
  .nav-links-list { display:flex;align-items:center;gap:2.5rem;list-style:none; }
  .nav-links-list a { color:var(--text);text-decoration:none;font-size:.88rem;font-weight:600;letter-spacing:.02em;transition:color .2s; }
  .nav-links-list a:hover { color:var(--blue); }
  .nav-signin { background:var(--red);color:var(--white);padding:.55rem 1.5rem;border-radius:4px;font-weight:700;font-size:.88rem;text-decoration:none;font-family:'Nunito Sans',sans-serif;transition:background .2s,transform .2s; }
  .nav-signin:hover { background:#e53e3e;transform:translateY(-1px); }

  /* HERO */
  .hero { min-height:100vh;background:linear-gradient(135deg, var(--blue) 0%, var(--violet) 55%, #6b3fcf 100%);position:relative;overflow:hidden;display:flex;align-items:center;padding:7rem 4rem 5rem; }
  .hero::after { content:'';position:absolute;bottom:-2px;left:0;right:0;height:120px;background:var(--white);clip-path:polygon(0 60%, 100% 0, 100% 100%, 0 100%); }
  .hero-blob { position:absolute;border-radius:50%;filter:blur(60px);pointer-events:none; }
  .hero-blob-1 { width:400px;height:400px;background:rgba(255,255,255,.06);top:-100px;right:30%; }
  .hero-blob-2 { width:250px;height:250px;background:rgba(112,72,232,.4);bottom:10%;left:5%; }
  .hero-content { position:relative;z-index:2;max-width:500px; }
  .hero h1 { font-family:'Nunito',sans-serif;font-size:clamp(2.4rem,5vw,3.4rem);font-weight:900;color:var(--white);line-height:1.15;margin-bottom:1.25rem;opacity:0;animation:fadeUp .8s .3s ease both; }
  .hero-sub { font-size:1rem;color:rgba(255,255,255,.82);line-height:1.8;margin-bottom:2rem;opacity:0;animation:fadeUp .8s .5s ease both; }
  .hero-btn { display:inline-flex;align-items:center;gap:.6rem;background:var(--red);color:var(--white);padding:.85rem 2rem;border-radius:4px;font-weight:800;font-size:.92rem;text-decoration:none;letter-spacing:.02em;opacity:0;animation:fadeUp .8s .7s ease both;transition:background .2s,transform .2s,box-shadow .2s; }
  .hero-btn:hover { background:#e53e3e;transform:translateY(-2px);box-shadow:0 8px 30px rgba(250,82,82,.4); }

  /* JOB LISTINGS */
  .jobs-section { padding:5rem 4rem;background:var(--white); }
  .section-title { font-family:'Nunito',sans-serif;font-size:2.2rem;font-weight:900;color:var(--text);margin-bottom:1rem; }
  .section-subtitle { color:var(--muted);font-size:1rem;line-height:1.6;margin-bottom:3rem; }
  .jobs-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:2rem; }
  .job-card { background:var(--white);border-radius:12px;border:1px solid var(--border);padding:2rem;transition:all .3s ease;position:relative;overflow:hidden; }
  .job-card::before { content:'';position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,var(--blue),var(--violet));transform:translateX(-100%);transition:transform .3s ease; }
  .job-card:hover { transform:translateY(-4px);box-shadow:var(--card-sh-h); }
  .job-card:hover::before { transform:translateX(0); }
  .job-header { display:flex;justify-content:space-between;align-items:start;margin-bottom:1rem; }
  .job-title { font-family:'Nunito',sans-serif;font-size:1.3rem;font-weight:800;color:var(--text);margin-bottom:.5rem; }
  .job-company { color:var(--muted);font-size:.95rem;margin-bottom:1rem; }
  .job-meta { display:flex;flex-wrap:wrap;gap:1rem;margin-bottom:1.5rem; }
  .job-meta-item { display:flex;align-items:center;gap:.4rem;color:var(--muted);font-size:.85rem; }
  .job-tags { display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:1.5rem; }
  .job-tag { background:rgba(59,91,219,.1);color:var(--blue);padding:.3rem .8rem;border-radius:20px;font-size:.75rem;font-weight:600; }
  .job-description { color:var(--text);line-height:1.6;margin-bottom:1.5rem;font-size:.9rem; }
  .job-actions { display:flex;gap:1rem; }
  .job-apply-btn { background:var(--blue);color:var(--white);padding:.8rem 1.5rem;border-radius:6px;font-weight:700;text-decoration:none;font-size:.9rem;transition:all .2s; }
  .job-apply-btn:hover { background:var(--blue-dark);transform:translateY(-1px); }
  .job-save-btn { background:transparent;color:var(--blue);border:1px solid var(--blue);padding:.8rem 1.5rem;border-radius:6px;font-weight:700;text-decoration:none;font-size:.9rem;transition:all .2s; }
  .job-save-btn:hover { background:var(--blue);color:var(--white); }

  /* APPLICATION FORM */
  .application-section { padding:5rem 4rem;background:var(--off); }
  .application-container { max-width:800px;margin:0 auto; }
  .form-card { background:var(--white);border-radius:16px;box-shadow:var(--card-sh);padding:3rem; }
  .form-title { font-family:'Nunito',sans-serif;font-size:1.8rem;font-weight:900;color:var(--text);margin-bottom:2rem; }
  .form-group { margin-bottom:1.5rem; }
  .form-label { display:block;font-weight:600;color:var(--text);margin-bottom:.5rem;font-size:.9rem; }
  .form-input, .form-textarea, .form-select { width:100%;padding:.8rem 1rem;border:1px solid var(--border);border-radius:6px;font-family:'Nunito Sans',sans-serif;font-size:.9rem;transition:all .2s; }
  .form-input:focus, .form-textarea:focus, .form-select:focus { outline:none;border-color:var(--blue);box-shadow:0 0 0 3px rgba(59,91,219,.1); }
  .form-textarea { min-height:120px;resize:vertical; }
  .form-file { border:2px dashed var(--border);border-radius:8px;padding:2rem;text-align:center;transition:all .2s;cursor:pointer; }
  .form-file:hover { border-color:var(--blue);background:rgba(59,91,219,.02); }
  .form-submit { background:var(--blue);color:var(--white);padding:1rem 2rem;border-radius:6px;font-weight:700;font-size:1rem;border:none;cursor:pointer;transition:all .2s;width:100%; }
  .form-submit:hover { background:var(--blue-dark);transform:translateY(-1px); }

  /* FOOTER */
  footer { background:var(--text);color:var(--white);padding:3rem 4rem 1rem; }
  .footer-content { display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:2rem;margin-bottom:2rem; }
  .footer-section h3 { font-family:'Nunito',sans-serif;font-size:1.1rem;font-weight:800;margin-bottom:1rem; }
  .footer-section a { color:rgba(255,255,255,.7);text-decoration:none;display:block;margin-bottom:.5rem;font-size:.9rem;transition:color .2s; }
  .footer-section a:hover { color:var(--white); }
  .footer-bottom { text-align:center;padding-top:2rem;border-top:1px solid rgba(255,255,255,.1);color:rgba(255,255,255,.6);font-size:.85rem; }

  @media (max-width:768px) {
    nav { padding:.9rem 2rem; }
    .nav-links-list { display:none; }
    .hero { padding:5rem 2rem 3rem; }
    .jobs-section, .application-section { padding:3rem 2rem; }
    .jobs-grid { grid-template-columns:1fr; }
    .form-card { padding:2rem; }
  }
</style>
"""

_NAV = """
<nav>
  <a href="/" class="nav-logo">
    TalentFlow<span class="nav-logo-dot"></span>
  </a>
  <ul class="nav-links-list">
        <li><a href="http://localhost:8005">Home</a></li>
    <li><a href="/jobs">Jobs</a></li>

  </ul>
  <a href="/track-application" class="nav-signin">Track Application</a>
</nav>
"""

_FOOTER_HTML = """
<footer>
  <div class="footer-content">
    <div class="footer-section">
      <h3>TalentFlow</h3>
      <a href="#">About Us</a>
      <a href="#">Careers</a>
      <a href="#">Blog</a>
      <a href="#">Press</a>
    </div>
    <div class="footer-section">
      <h3>For Candidates</h3>
      <a href="#">Browse Jobs</a>
      <a href="#">Career Advice</a>
      <a href="#">Resume Tips</a>
      <a href="#">Interview Prep</a>
    </div>
    <div class="footer-section">
      <h3>For Employers</h3>
      <a href="#">Post a Job</a>
      <a href="#">Pricing</a>
      <a href="#">Recruiting Solutions</a>
      <a href="#">Enterprise</a>
    </div>
    <div class="footer-section">
      <h3>Support</h3>
      <a href="#">Help Center</a>
      <a href="#">Privacy Policy</a>
      <a href="#">Terms of Service</a>
      <a href="#">Contact Us</a>
    </div>
  </div>
  <div class="footer-bottom">
    <p>&copy; 2026 TalentFlow. All rights reserved.</p>
  </div>
</footer>
"""

# HTML template for job portal
job_portal_template = """<!DOCTYPE html>
<html lang="en">
<head>
""" + _BASE_HEAD + """
  <title>Find Your Dream Job - TalentFlow</title>
</head>
<body>
<div class="page-loader"><div class="loader-logo">TalentFlow</div><div class="loader-spin"></div></div>
""" + _NAV + """

<!-- HERO SECTION -->
<section class="hero">
  <div class="hero-blob hero-blob-1"></div>
  <div class="hero-blob hero-blob-2"></div>
  <div class="hero-content">
    <h1>Find Your Dream Job</h1>
    <p class="hero-sub">Discover opportunities that match your skills and aspirations. Join thousands of professionals who've found their perfect career match through TalentFlow.</p>
    <a href="#" class="hero-btn">Browse Available Jobs &#8594;</a>
  </div>
</section>

<!-- JOBS SECTION -->
<section class="jobs-section" id="jobs">
  <div class="reveal">
    <h2 class="section-title">Open <span>Positions</span></h2>
    <p class="section-subtitle">Explore our latest job opportunities across various departments and locations</p>
  </div>
  
  <div class="jobs-grid">
    {% for job in jobs %}
    <div class="job-card reveal reveal-d{{ loop.index0 % 4 + 1 }}">
      <div class="job-header">
        <div>
          <h3 class="job-title">{{ job.title }}</h3>
          <div class="job-company">{{ job.department }}</div>
        </div>
      </div>
      
      <div class="job-meta">
        <div class="job-meta-item">📍 {{ job.location or 'Remote' }}</div>
        <div class="job-meta-item">💰 {{ job.salary or 'Competitive' }}</div>
        <div class="job-meta-item">⏰ {{ job.job_type or 'Full-time' }}</div>
      </div>
      
      <div class="job-description">
        {{ job.description[:200] }}{% if job.description|length > 200 %}...{% endif %}
      </div>
      
      <div class="job-tags">
        <span class="job-tag">{{ job.department }}</span>
        {% if job.job_type %}
        <span class="job-tag">{{ job.job_type }}</span>
        {% endif %}
      </div>
      
      <div class="job-actions">
        <a href="/jobs/{{ job.id }}" class="job-apply-btn">Apply Now</a>
        <button class="job-save-btn" onclick="this.textContent='Saved!'">Save</button>
      </div>
    </div>
    {% else %}
    <div style="grid-column:1/-1;"></div>
    {% endfor %}
  </div>
</section>

<!-- APPLICATION FORM SECTION -->
{% if job %}
<section class="application-section">
  <div class="application-container">
    <div class="form-card reveal">
      <h2 class="form-title">Apply for {{ job.title }}</h2>
      
      <form action="/apply/{{ job.id }}" method="post" enctype="multipart/form-data">
        <div class="form-group">
          <label class="form-label">Full Name *</label>
          <input type="text" name="name" class="form-input" required>
        </div>
        
        <div class="form-group">
          <label class="form-label">Email Address *</label>
          <input type="email" name="email" class="form-input" required>
        </div>
        
        <div class="form-group">
          <label class="form-label">Phone Number</label>
          <input type="tel" name="phone" class="form-input">
        </div>
        
        <div class="form-group">
          <label class="form-label">Cover Letter</label>
          <textarea name="cover_letter" class="form-textarea" placeholder="Tell us why you're interested in this position..."></textarea>
        </div>
        
        <div class="form-group">
          <label class="form-label">Resume Text (Optional if file uploaded)</label>
          <textarea name="resume_text" id="resume_text" class="form-textarea" placeholder="Paste your resume text here..."></textarea>
        </div>
        
        <div class="form-group">
          <label class="form-label">Or Upload Resume File</label>
          <div class="form-file">
            <input type="file" name="resume" accept=".pdf,.doc,.docx" style="display:none;" id="resume-file" onchange="document.getElementById('file-name').textContent = this.files[0].name">
            <label for="resume-file" style="cursor:pointer;">
              <div style="font-size:2rem;margin-bottom:1rem;">📄</div>
              <div id="file-name">Click to upload your resume</div>
              <div style="color:var(--muted);font-size:.85rem;margin-top:.5rem;">PDF, DOC, DOCX (Max 5MB)</div>
            </label>
          </div>
        </div>
        <div class="form-group" style="margin-top:1rem; display:flex; align-items:flex-start; gap:0.8rem;">
          <input type="checkbox" name="consent" id="consent" required style="margin-top:0.3rem;">
          <label for="consent" style="font-size:0.85rem; color:var(--muted); line-height:1.5;">
            I consent to ZibiTech storing my resume and data for up to 6 months for recruitment purposes. *
          </label>
        </div>
        
        <button type="submit" class="form-submit" style="margin-top:1rem;">Submit Application</button>
      </form>
    </div>
  </div>
</section>
{% endif %}

""" + _FOOTER_HTML + """

<script>
  // Reveal animations on scroll
  const reveals = document.querySelectorAll('.reveal');
  function revealOnScroll() {
    reveals.forEach(element => {
      const windowHeight = window.innerHeight;
      const elementTop = element.getBoundingClientRect().top;
      const elementVisible = 150;
      
      if (elementTop < windowHeight - elementVisible) {
        element.classList.add('visible');
      }
    });
  }
  
  window.addEventListener('scroll', revealOnScroll);
  window.addEventListener('load', revealOnScroll);
  
  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      document.querySelector(this.getAttribute('href')).scrollIntoView({
        behavior: 'smooth'
      });
    });
  });
  
  // Handle application form submission
  document.querySelector('form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    
    // Check if either text or file is provided
    const resumeText = formData.get('resume_text');
    const resumeFile = formData.get('resume');
    
    if (!resumeText && (!resumeFile || resumeFile.size === 0)) {
        alert('Please either paste your resume text or upload a PDF file.');
        return;
    }
    
    try {
      const response = await fetch('/apply/{{ job.id }}', {
        method: 'POST',
        body: formData // Send as FormData
      });
      
      const result = await response.json();
      
      if (result.success) {
        alert('Application submitted successfully!');
        window.location.href = '/';
      } else {
        alert('Error: ' + result.error);
      }
    } catch (error) {
      alert('Error submitting application: ' + error.message);
    }
  });
</script>
</body>
</html>
"""

# My Applications template
my_applications_template = """<!DOCTYPE html>
<html lang="en">
<head>
""" + _BASE_HEAD + """
  <title>My Applications - TalentFlow</title>
</head>
<body>
<div class="page-loader"><div class="loader-logo">TalentFlow</div><div class="loader-spin"></div></div>
""" + _NAV + """

<div class="application-section">
  <div class="application-container">
    <div class="form-card reveal">
      <h2 class="form-title">My Applications</h2>
      
      {% if applications %}
      <div class="applications-table">
        {% for app in applications %}
        <div class="job-card" style="margin-bottom: 2rem;">
          <div class="job-header">
            <div>
              <h3 class="job-title">{{ app.job_title }}</h3>
              <div class="job-company">{{ app.department }}</div>
            </div>
            <span class="status-badge status-{{ app.status or 'pending' }}">{{ app.status or 'pending' }}</span>
          </div>
          
          <div class="job-meta">
            <div class="job-meta-item">📅 Applied: {{ app.application_date }}</div>
            {% if app.resume_score %}
            <div class="job-meta-item">📊 Score: {{ app.resume_score.toFixed(1) }}/100</div>
            {% endif %}
          </div>
          
          {% if app.cover_letter %}
          <div class="job-description">
            <strong>Cover Letter:</strong> {{ app.cover_letter[:200] }}{% if app.cover_letter|length > 200 %}...{% endif %}
          </div>
          {% endif %}
        </div>
        {% endfor %}
      </div>
      {% else %}
      <div style="text-align:center;padding:3rem;">
        <h3 style="color:var(--muted);margin-bottom:1rem;">No applications yet</h3>
        <p style="color:var(--muted);">Start by <a href="/" style="color:var(--blue);">browsing available positions</a>.</p>
      </div>
      {% endif %}
    </div>
  </div>
</div>

""" + _FOOTER_HTML + """

<script>
  const reveals = document.querySelectorAll('.reveal');
  function revealOnScroll() {
    reveals.forEach(element => {
      const windowHeight = window.innerHeight;
      const elementTop = element.getBoundingClientRect().top;
      const elementVisible = 150;
      
      if (elementTop < windowHeight - elementVisible) {
        element.classList.add('visible');
      }
    });
  }
  
  window.addEventListener('scroll', revealOnScroll);
  window.addEventListener('load', revealOnScroll);
</script>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def job_listings(request: Request):
    """Main job listings page"""
    jobs = db.get_all_jobs()
    from jinja2 import Template
    html = Template(job_portal_template).render(jobs=jobs, job=None)
    return HTMLResponse(content=html)

@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_details(request: Request, job_id: int):
    """Individual job details page with application form"""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    from jinja2 import Template
    html = Template(job_portal_template).render(jobs=[], job=job)
    return HTMLResponse(content=html)

def normalize_spaced_text(text: str) -> str:
    """Detects and fixes spaced-out text (e.g. 'P r o d u c t')"""
    if not text: return ""
    sample = text[:500]
    words = sample.split()
    if not words: return text
    single_chars = [w for w in words if len(w) == 1 and w.isalnum()]
    if len(words) > 10 and len(single_chars) / len(words) > 0.6:
        text = text.replace('  ', '|||').replace(' ', '').replace('|||', ' ')
        text = re.sub(r'\n+', '\n', text)
    return text

def _extract_text_from_pdf(file: UploadFile) -> str:
    """Extract text from uploaded PDF file using pypdf"""
    try:
        pdf_reader = pypdf.PdfReader(file.file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return normalize_spaced_text(text.strip())
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

@app.post("/apply/{job_id}")
async def submit_application(
    job_id: int,
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    cover_letter: Optional[str] = Form(""),
    resume_text: Optional[str] = Form(None),
    consent: bool = Form(False),
    resume: Optional[UploadFile] = File(None)
):
    """Handle job application submission"""
    try:
        # Extract resume text if file is provided
        if resume and resume.filename.endswith('.pdf'):
            extracted_text = _extract_text_from_pdf(resume)
            if extracted_text:
                resume_text = extracted_text
            try:
                resume.file.seek(0)
            except Exception:
                pass
        
        # Normalize text
        if resume_text:
            resume_text = normalize_spaced_text(resume_text)
        
        if not resume_text:
            return JSONResponse(content={'success': False, 'error': 'Resume text or PDF file is required'}, status_code=400)

        # Add applicant to database
        applicant_id = db.add_applicant(
            name=name,
            email=email,
            phone=phone,
            position="", # Will be set by application record
            consent=consent
        )

        # Persist the uploaded resume as a "Document" so HR can view it later
        if resume and getattr(resume, "filename", None):
            uploads_dir = os.path.join(os.path.dirname(__file__), "uploaded_documents")
            os.makedirs(uploads_dir, exist_ok=True)
            safe_name = os.path.basename(resume.filename)
            unique_name = f"{uuid.uuid4().hex}_{safe_name}"
            out_path = os.path.join(uploads_dir, unique_name)
            try:
                # ensure we're at file start
                try:
                    resume.file.seek(0)
                except Exception:
                    pass
                with open(out_path, "wb") as f:
                    shutil.copyfileobj(resume.file, f)
                file_size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
                db.add_document(
                    applicant_id=applicant_id,
                    document_type="resume",
                    filename=safe_name,
                    file_path=out_path,
                    file_size=file_size,
                )
            except Exception as e:
                # Non-fatal: application can proceed even if file persistence fails
                print(f"[WARN] Failed to store resume document: {e}")
        
        # Score the resume
        result = scorer.score_resume(resume_text)
        
        # Save the score
        db.save_resume_score(
            applicant_id=applicant_id,
            resume_text=resume_text,
            score=result['score'],
            features=result['features'],
            recommendations=result['recommendations']
        )
        
        # Create job application
        db.add_job_application(
            job_id=job_id,
            applicant_id=applicant_id,
            cover_letter=cover_letter
        )
        
        return JSONResponse(content={
            'success': True,
            'message': 'Application submitted successfully'
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JSONResponse(content={
            'success': False,
            'error': str(e)
        }, status_code=500)

@app.get("/track-application", response_class=HTMLResponse)
async def track_application_redirect():
    """Redirect to main portal's tracking page"""
    return RedirectResponse(url="http://localhost:8005/track-application", status_code=302)

if __name__ == "__main__":
    import uvicorn
    print("Starting Modern Job Portal...")
    print("Open http://localhost:8001 in your browser")
    print("Track applications at: http://localhost:8005/track-application")
    uvicorn.run(app, host="0.0.0.0", port=8001)
