from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from database import ResumeDatabase
from simple_app import SimpleResumeScorer

app = FastAPI(title="Talent Flow Style Portal", description="Modern recruitment portal")
db = ResumeDatabase()
scorer = SimpleResumeScorer()

# ─────────────────────────────────────────────────────────────────────────────
#  SHARED PIECES
# ─────────────────────────────────────────────────────────────────────────────

_BASE_HEAD = """<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Nunito+Sans:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root{--blue:#3b5bdb;--blue-dark:#2846c4;--blue-light:#5c7cfa;--violet:#7048e8;--red:#fa5252;--white:#ffffff;--off:#f8f9fc;--text:#2d3748;--muted:#718096;--border:#e8edf5;--card-sh:0 8px 40px rgba(59,91,219,.10);--card-sh-h:0 16px 60px rgba(59,91,219,.18);}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{font-family:'Nunito Sans',sans-serif;background:var(--white);color:var(--text);overflow-x:hidden;}
::-webkit-scrollbar{width:4px;}::-webkit-scrollbar-thumb{background:var(--blue);border-radius:2px;}
@keyframes fadeUp{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes floatUI{0%,100%{transform:translateY(0)}50%{transform:translateY(-14px)}}
@keyframes slideDown{from{opacity:0;transform:translateY(-16px)}to{opacity:1;transform:translateY(0)}}
@keyframes loaderOut{to{opacity:0;pointer-events:none}}
@keyframes spin{to{transform:rotate(360deg)}}
.page-loader{position:fixed;inset:0;background:var(--white);z-index:9999;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:1rem;animation:loaderOut .3s 1s ease both;}
.loader-logo{font-family:'Nunito',sans-serif;font-size:1.6rem;font-weight:900;color:var(--blue);}
.loader-spin{width:28px;height:28px;border:3px solid var(--border);border-top-color:var(--blue);border-radius:50%;animation:spin .7s linear infinite;}
.reveal{opacity:0;transform:translateY(28px);transition:opacity .65s ease,transform .65s ease;}
.reveal.visible{opacity:1;transform:translateY(0);}
.reveal-d1{transition-delay:.1s}.reveal-d2{transition-delay:.2s}.reveal-d3{transition-delay:.3s}.reveal-d4{transition-delay:.4s}
nav{position:fixed;top:0;left:0;right:0;z-index:200;display:flex;align-items:center;justify-content:space-between;padding:.9rem 4rem;background:rgba(255,255,255,.96);backdrop-filter:blur(16px);box-shadow:0 2px 20px rgba(59,91,219,.08);animation:slideDown .5s ease both;}
.nav-logo{font-family:'Nunito',sans-serif;font-size:1.3rem;font-weight:900;color:var(--blue);text-decoration:none;display:flex;align-items:center;gap:.5rem;}
.nav-logo-dot{width:8px;height:8px;border-radius:50%;background:var(--red);display:inline-block;}
.nav-links-list{display:flex;align-items:center;gap:2.5rem;list-style:none;}
.nav-links-list a{color:var(--text);text-decoration:none;font-size:.88rem;font-weight:600;transition:color .2s;}
.nav-links-list a:hover{color:var(--blue);}
.nav-signin{background:var(--red);color:var(--white);padding:.55rem 1.5rem;border-radius:4px;font-weight:700;font-size:.88rem;text-decoration:none;transition:background .2s,transform .2s;}
.nav-signin:hover{background:#e53e3e;transform:translateY(-1px);}
.hero{min-height:100vh;background:linear-gradient(135deg,var(--blue) 0%,var(--violet) 55%,#6b3fcf 100%);position:relative;overflow:hidden;display:flex;align-items:center;padding:7rem 4rem 5rem;}
.hero::after{content:'';position:absolute;bottom:-2px;left:0;right:0;height:120px;background:var(--white);clip-path:polygon(0 60%,100% 0,100% 100%,0 100%);}
.hero-blob{position:absolute;border-radius:50%;filter:blur(60px);pointer-events:none;}
.hero-blob-1{width:400px;height:400px;background:rgba(255,255,255,.06);top:-100px;right:30%;}
.hero-blob-2{width:250px;height:250px;background:rgba(112,72,232,.4);bottom:10%;left:5%;}
.hero-content{position:relative;z-index:2;max-width:500px;}
.hero h1{font-family:'Nunito',sans-serif;font-size:clamp(2.4rem,5vw,3.4rem);font-weight:900;color:var(--white);line-height:1.15;margin-bottom:1.25rem;opacity:0;animation:fadeUp .8s .3s ease both;}
.hero-sub{font-size:1rem;color:rgba(255,255,255,.82);line-height:1.8;margin-bottom:2rem;opacity:0;animation:fadeUp .8s .5s ease both;}
.hero-btn{display:inline-flex;align-items:center;gap:.6rem;background:var(--red);color:var(--white);padding:.85rem 2rem;border-radius:4px;font-weight:800;font-size:.92rem;text-decoration:none;opacity:0;animation:fadeUp .8s .7s ease both;transition:background .2s,transform .2s,box-shadow .2s;}
.hero-btn:hover{background:#e53e3e;transform:translateY(-2px);box-shadow:0 8px 30px rgba(250,82,82,.4);}
.hero-mockup{position:absolute;right:4%;top:50%;transform:translateY(-50%);z-index:2;width:460px;opacity:0;animation:floatUI 5s 1s ease-in-out infinite,fadeIn .9s .6s ease both;}
.mockup-card{background:var(--white);border-radius:16px;box-shadow:0 30px 80px rgba(0,0,0,.25);padding:1.5rem;position:relative;}
.mockup-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem;}
.mockup-title{font-family:'Nunito',sans-serif;font-size:.95rem;font-weight:800;color:var(--text);}
.mockup-badge{background:var(--blue);color:#fff;font-size:.65rem;font-weight:700;padding:.2rem .6rem;border-radius:999px;}
.mockup-stat{display:flex;align-items:center;gap:1rem;margin-bottom:1rem;}
.mockup-circle{width:64px;height:64px;border-radius:50%;background:conic-gradient(var(--blue) 0% 68%,var(--border) 68% 100%);display:flex;align-items:center;justify-content:center;font-family:'Nunito',sans-serif;font-size:.82rem;font-weight:900;color:var(--blue);}
.mockup-rows{display:flex;flex-direction:column;gap:.5rem;flex:1;}
.mockup-row{height:8px;background:var(--border);border-radius:4px;overflow:hidden;}
.mockup-row-fill{height:100%;background:linear-gradient(90deg,var(--blue),var(--blue-light));border-radius:4px;}
.mockup-tags{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:1rem;}
.mockup-tag{font-size:.7rem;font-weight:700;padding:.25rem .7rem;border-radius:999px;background:var(--off);color:var(--muted);}
.mockup-tag.active{background:rgba(59,91,219,.12);color:var(--blue);}
.mockup-mini{position:absolute;left:-90px;top:40%;background:var(--white);border-radius:12px;box-shadow:0 10px 40px rgba(0,0,0,.15);padding:1rem 1.25rem;min-width:190px;}
.mini-label{font-size:.7rem;color:var(--muted);font-weight:600;margin-bottom:.4rem;}
.mini-title{font-family:'Nunito',sans-serif;font-size:.92rem;font-weight:800;color:var(--text);margin-bottom:.4rem;}
.mini-bar-wrap{height:6px;background:var(--border);border-radius:3px;overflow:hidden;}
.mini-bar{height:100%;width:72%;background:var(--red);border-radius:3px;}
.services-section{padding:5rem 4rem;background:var(--white);}
.services-intro{display:grid;grid-template-columns:1fr 1fr;gap:5rem;align-items:start;}
.eyebrow{display:inline-block;font-size:.72rem;font-weight:700;color:var(--blue);letter-spacing:.18em;text-transform:uppercase;margin-bottom:1rem;}
.section-title{font-family:'Nunito',sans-serif;font-size:clamp(1.8rem,3.5vw,2.4rem);font-weight:900;color:var(--text);line-height:1.2;margin-bottom:1rem;}
.section-title span{color:var(--blue);}
.cards-grid{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;}
.svc-card{background:var(--white);border-radius:14px;padding:2rem;box-shadow:var(--card-sh);transition:transform .3s,box-shadow .3s;position:relative;overflow:hidden;}
.svc-card:hover{transform:translateY(-6px);box-shadow:var(--card-sh-h);}
.svc-card::before{content:'';position:absolute;top:0;left:0;width:3px;height:0;background:var(--blue);transition:height .4s ease;}
.svc-card:hover::before{height:100%;}
.svc-icon{width:44px;height:44px;border-radius:10px;background:rgba(59,91,219,.1);display:flex;align-items:center;justify-content:center;font-size:1.2rem;margin-bottom:1.25rem;}
.svc-card h3{font-family:'Nunito',sans-serif;font-size:1rem;font-weight:800;color:var(--text);margin-bottom:.6rem;}
.svc-card p{font-size:.87rem;color:var(--muted);line-height:1.7;margin-bottom:1rem;}
.read-more{font-size:.82rem;font-weight:700;color:var(--blue);text-decoration:none;display:inline-flex;align-items:center;gap:.4rem;transition:gap .2s;}
.read-more:hover{gap:.7rem;}
.diag-divider{height:80px;background:var(--off);clip-path:polygon(0 0,100% 40%,100% 100%,0 100%);}
.diag-divider-rev{height:80px;background:var(--white);clip-path:polygon(0 40%,100% 0,100% 100%,0 100%);}
.about-section{background:var(--off);padding:6rem 4rem;}
.about-grid{display:grid;grid-template-columns:1fr 1fr;gap:5rem;align-items:center;}
.about-blob-bg{width:380px;height:340px;background:linear-gradient(135deg,rgba(59,91,219,.08),rgba(112,72,232,.08));border-radius:60% 40% 50% 50%/50% 60% 40% 50%;display:flex;align-items:center;justify-content:center;}
.about-people{font-size:5.5rem;animation:floatUI 6s ease-in-out infinite;}
.about-content p{font-size:.95rem;color:var(--muted);line-height:1.85;margin-bottom:1rem;}
.about-actions{display:flex;align-items:center;gap:1.25rem;margin-top:2rem;flex-wrap:wrap;}
.about-btn{background:var(--red);color:var(--white);padding:.75rem 1.75rem;border-radius:4px;font-weight:800;font-size:.88rem;text-decoration:none;transition:background .2s,transform .2s;}
.about-btn:hover{background:#e53e3e;transform:translateY(-1px);}
.why-section{background:var(--white);padding:6rem 4rem;}
.why-grid{display:grid;grid-template-columns:1fr 1fr;gap:2.5rem;margin-top:4rem;}
.why-card{display:flex;gap:1.25rem;align-items:flex-start;}
.why-icon{width:52px;height:52px;border-radius:12px;background:var(--off);display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0;transition:background .3s,transform .3s;}
.why-card:hover .why-icon{background:rgba(59,91,219,.1);transform:scale(1.08);}
.why-card h4{font-family:'Nunito',sans-serif;font-size:.98rem;font-weight:800;color:var(--text);margin-bottom:.5rem;}
.why-card p{font-size:.87rem;color:var(--muted);line-height:1.7;}
.jobs-section{background:var(--off);padding:6rem 4rem;}
.jobs-header{text-align:center;margin-bottom:3rem;}
.jobs-header p{color:var(--muted);font-size:.97rem;max-width:520px;margin:.75rem auto 0;line-height:1.75;}
.filter-bar{display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap;margin-bottom:2.5rem;}
.filter-btn{padding:.5rem 1.25rem;border:2px solid var(--border);background:var(--white);color:var(--muted);border-radius:999px;font-size:.82rem;font-family:'Nunito Sans',sans-serif;font-weight:700;cursor:pointer;transition:all .25s;}
.filter-btn:hover,.filter-btn.active{border-color:var(--blue);color:var(--blue);background:rgba(59,91,219,.07);}
.jobs-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.5rem;}
.job-card{background:var(--white);border-radius:14px;padding:1.75rem;box-shadow:var(--card-sh);transition:transform .3s,box-shadow .3s;}
.job-card:hover{transform:translateY(-5px);box-shadow:var(--card-sh-h);}
.job-card-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem;}
.dept-tag{font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--blue);background:rgba(59,91,219,.1);padding:.28rem .75rem;border-radius:999px;}
.type-tag{font-size:.7rem;font-weight:700;color:var(--muted);background:var(--off);padding:.28rem .75rem;border-radius:999px;}
.job-name{font-family:'Nunito',sans-serif;font-size:1.05rem;font-weight:800;margin-bottom:.6rem;color:var(--text);}
.job-blurb{font-size:.86rem;color:var(--muted);line-height:1.7;margin-bottom:1.25rem;}
.job-foot{display:flex;justify-content:space-between;align-items:center;padding-top:1rem;border-top:1px solid var(--border);}
.job-sal{font-size:.82rem;font-weight:700;color:#2f855a;}
.job-cta{display:inline-flex;align-items:center;gap:.4rem;font-size:.82rem;font-weight:700;color:var(--blue);text-decoration:none;transition:gap .2s;}
.job-cta:hover{gap:.7rem;}
.testi-section{background:var(--white);padding:6rem 4rem;}
.testi-grid{display:grid;grid-template-columns:1fr 1fr;gap:5rem;align-items:center;}
.avatar-cluster{position:relative;width:280px;height:280px;margin:0 auto;}
.av{position:absolute;width:68px;height:68px;border-radius:50%;border:3px solid var(--white);box-shadow:0 4px 20px rgba(0,0,0,.12);background:var(--off);display:flex;align-items:center;justify-content:center;font-size:1.7rem;}
.av-1{top:0;left:50%;transform:translateX(-50%)}.av-2{top:22%;left:0}.av-3{top:22%;right:0}.av-4{bottom:12%;left:12%}.av-5{bottom:12%;right:12%}.av-6{bottom:0;left:50%;transform:translateX(-50%)}
.active-av{border-color:var(--blue);box-shadow:0 0 0 4px rgba(59,91,219,.2);}
.testi-content blockquote{font-family:'Nunito',sans-serif;font-size:1.15rem;font-weight:700;color:var(--text);line-height:1.65;margin-bottom:1.5rem;font-style:italic;}
.testi-author{font-weight:700;color:var(--text);font-size:.9rem;}
.testi-author span{color:var(--muted);font-weight:400;}
.read-more-btn{display:inline-flex;align-items:center;gap:.5rem;background:var(--red);color:var(--white);padding:.7rem 1.6rem;border-radius:4px;font-weight:700;font-size:.85rem;text-decoration:none;margin-top:1.75rem;transition:background .2s,transform .2s;}
.read-more-btn:hover{background:#e53e3e;transform:translateY(-1px);}
.bottom-section{background:linear-gradient(135deg,var(--blue) 0%,var(--violet) 60%,#6b3fcf 100%);padding:6rem 4rem;position:relative;overflow:hidden;}
.bottom-section::before{content:'';position:absolute;top:-80px;left:0;right:0;height:120px;background:var(--white);clip-path:polygon(0 0,100% 60%,100% 100%,0 100%);}
.bottom-grid{display:grid;grid-template-columns:1fr 1fr;gap:5rem;position:relative;z-index:2;}
.newsletter h3{font-family:'Nunito',sans-serif;font-size:1.6rem;font-weight:900;color:var(--white);margin-bottom:.75rem;}
.newsletter p{color:rgba(255,255,255,.8);font-size:.95rem;line-height:1.75;margin-bottom:1.5rem;}
.nl-input{width:100%;padding:.8rem 1.1rem;border:none;border-radius:4px;font-size:.9rem;font-family:'Nunito Sans',sans-serif;margin-bottom:.75rem;background:rgba(255,255,255,.15);color:var(--white);}
.nl-input::placeholder{color:rgba(255,255,255,.5);}
.nl-input:focus{outline:none;background:rgba(255,255,255,.22);}
.nl-btn{background:var(--red);color:var(--white);border:none;padding:.8rem 2rem;border-radius:4px;font-weight:800;font-size:.9rem;cursor:pointer;transition:background .2s,transform .2s;font-family:'Nunito Sans',sans-serif;}
.nl-btn:hover{background:#e53e3e;transform:translateY(-1px);}
.contact-card{background:var(--white);border-radius:16px;padding:2.5rem;box-shadow:0 20px 60px rgba(0,0,0,.2);}
.contact-card h3{font-family:'Nunito',sans-serif;font-size:1.3rem;font-weight:900;color:var(--text);margin-bottom:1.5rem;}
.cf-input{width:100%;padding:.8rem 1rem;border:2px solid var(--border);border-radius:6px;font-size:.9rem;font-family:'Nunito Sans',sans-serif;margin-bottom:1rem;transition:border-color .25s;color:var(--text);}
.cf-input:focus{outline:none;border-color:var(--blue);}
.cf-input::placeholder{color:#b0b8c8;}
.cf-textarea{resize:vertical;min-height:90px;}
.cf-btn{background:var(--red);color:var(--white);border:none;padding:.8rem 2rem;border-radius:4px;font-weight:800;font-size:.9rem;cursor:pointer;width:100%;transition:background .2s,transform .2s;font-family:'Nunito Sans',sans-serif;}
.cf-btn:hover{background:#e53e3e;transform:translateY(-1px);}
.site-footer{background:#1a1f36;padding:3.5rem 4rem 2rem;color:rgba(255,255,255,.65);}
.footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1.5fr;gap:3rem;margin-bottom:3rem;}
.footer-brand-logo{font-family:'Nunito',sans-serif;font-size:1.3rem;font-weight:900;color:var(--white);text-decoration:none;display:flex;align-items:center;gap:.5rem;margin-bottom:1rem;}
.footer-brand-desc{font-size:.87rem;line-height:1.7;}
.footer-col h4{font-family:'Nunito',sans-serif;font-size:.88rem;font-weight:800;color:var(--white);margin-bottom:1rem;}
.footer-col ul{list-style:none;display:flex;flex-direction:column;gap:.6rem;}
.footer-col a{color:rgba(255,255,255,.6);text-decoration:none;font-size:.85rem;transition:color .2s;}
.footer-col a:hover{color:var(--white);}
.footer-addr{font-size:.85rem;line-height:1.9;}
.footer-addr a{color:rgba(255,255,255,.6);text-decoration:none;}
.footer-bottom{border-top:1px solid rgba(255,255,255,.1);padding-top:1.5rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;}
.footer-copy{font-size:.8rem;}
.social-links{display:flex;gap:.75rem;}
.social-links a{width:32px;height:32px;border-radius:50%;background:rgba(255,255,255,.1);display:flex;align-items:center;justify-content:center;font-size:.75rem;color:rgba(255,255,255,.7);text-decoration:none;transition:background .2s;}
.social-links a:hover{background:var(--blue);}
/* TRACKER */
.tracker-hero{padding:8rem 4rem 6rem;background:linear-gradient(135deg,var(--blue) 0%,var(--violet) 100%);position:relative;overflow:hidden;}
.tracker-hero::after{content:'';position:absolute;bottom:-2px;left:0;right:0;height:80px;background:var(--off);clip-path:polygon(0 60%,100% 0,100% 100%,0 100%);}
.tracker-hero h1{font-family:'Nunito',sans-serif;font-size:clamp(2rem,5vw,3rem);font-weight:900;color:var(--white);margin-bottom:.75rem;}
.tracker-hero p{color:rgba(255,255,255,.8);font-size:1rem;max-width:480px;line-height:1.75;}
.tracker-body{padding:4rem;background:var(--off);min-height:50vh;}
.tracker-form-card{background:var(--white);border-radius:16px;padding:2.5rem;box-shadow:var(--card-sh);max-width:600px;margin:0 auto;}
.tf-label{display:block;font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.6rem;}
.tf-input{width:100%;padding:.85rem 1.1rem;border:2px solid var(--border);border-radius:6px;font-size:.9rem;font-family:'Nunito Sans',sans-serif;transition:border-color .25s;color:var(--text);margin-bottom:1rem;}
.tf-input:focus{outline:none;border-color:var(--blue);}
.tf-input::placeholder{color:#b0b8c8;}
.tf-btn{background:var(--blue);color:var(--white);border:none;padding:.85rem 2rem;border-radius:6px;font-weight:800;font-size:.9rem;cursor:pointer;transition:background .2s,transform .2s;font-family:'Nunito Sans',sans-serif;width:100%;}
.tf-btn:hover{background:var(--blue-dark);transform:translateY(-1px);}
.tf-btn:disabled{opacity:.6;cursor:not-allowed;transform:none;}
.result-card{background:var(--white);border-radius:14px;padding:2rem;margin-top:1.5rem;box-shadow:var(--card-sh);max-width:600px;margin-left:auto;margin-right:auto;}
.result-title{font-family:'Nunito',sans-serif;font-size:1.1rem;font-weight:800;color:var(--text);}
.result-meta{color:var(--muted);font-size:.82rem;margin-top:.25rem;}
.result-header{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:.75rem;margin-bottom:1.25rem;}
.status-pill{display:inline-flex;padding:.3rem .9rem;border-radius:999px;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;}
.status-pending{background:#fff9e6;color:#b7791f;}
.status-reviewed{background:#ebf4ff;color:#2b6cb0;}
.status-shortlisted{background:#f0fff4;color:#276749;}
.status-rejected{background:#fff5f5;color:#c53030;}
.score-section{margin-bottom:1.25rem;}
.score-label{font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.5rem;}
.score-row{display:flex;align-items:center;gap:1rem;}
.score-bar-outer{height:6px;background:var(--border);border-radius:3px;overflow:hidden;flex:1;max-width:180px;}
.score-bar-inner{height:100%;background:linear-gradient(90deg,var(--blue),#7048e8);border-radius:3px;transition:width 1.2s ease;}
.score-val{font-size:.82rem;font-weight:700;color:var(--blue);}
.tl{position:relative;padding-left:1.4rem;margin-top:1.25rem;}
.tl::before{content:'';position:absolute;left:0;top:6px;bottom:6px;width:2px;background:var(--border);}
.tl-ev{position:relative;margin-bottom:.9rem;}
.tl-ev::before{content:'';position:absolute;left:-1.4rem;top:6px;width:8px;height:8px;border-radius:50%;background:var(--blue);border:2px solid var(--white);}
.tl-ev-title{font-size:.875rem;font-weight:700;color:var(--text);}
.tl-ev-date{font-size:.76rem;color:var(--muted);margin-top:.15rem;}
.offer-banner{background:#f0fff4;border:1px solid #9ae6b4;border-radius:10px;padding:1.25rem 1.5rem;margin-bottom:1.5rem;}
.offer-banner-title{font-family:'Nunito',sans-serif;font-size:1rem;font-weight:800;color:#276749;margin-bottom:.5rem;}
.offer-banner p{font-size:.875rem;color:#2f855a;line-height:1.7;}
.err-box{background:#fff9e6;border:1px solid #f6e05e;border-radius:10px;padding:1.25rem 1.5rem;margin-top:1.5rem;max-width:600px;margin-left:auto;margin-right:auto;}
.err-box h4{font-family:'Nunito',sans-serif;font-size:.92rem;font-weight:800;color:#744210;margin-bottom:.75rem;}
.err-box p{font-size:.82rem;color:#744210;line-height:1.7;margin-bottom:.4rem;}
.err-box code{background:#fef3c7;padding:.15rem .4rem;border-radius:3px;font-family:monospace;font-size:.78rem;}
@media(max-width:1000px){
  nav{padding:.9rem 1.5rem;}
  .nav-links-list{display:none;}
  .hero,.services-section,.about-section,.why-section,.jobs-section,.testi-section,.bottom-section,.tracker-hero,.tracker-body,.site-footer{padding-left:1.5rem;padding-right:1.5rem;}
  .hero-mockup{display:none;}
  .services-intro,.about-grid,.testi-grid,.bottom-grid,.footer-grid{grid-template-columns:1fr;}
  .why-grid,.cards-grid{grid-template-columns:1fr;}
}
</style>"""

_NAV = """<nav>
  <a href="/" class="nav-logo"><span class="nav-logo-dot"></span> TalentFlow</a>
  <ul class="nav-links-list">
    <li><a href="/">Home</a></li>
    <li><a href="/#services">Service</a></li>
    <li><a href="/#about">About</a></li>
    <li><a href="/jobs">Jobs</a></li>
    <li><a href="/#contact">Contact</a></li>
  </ul>
  <a href="http://localhost:8003" class="nav-signin">Sign In</a>
  
</nav>"""

_FOOTER = """<div class="site-footer">
  <div class="footer-grid">
    <div class="footer-col">
      <a href="/" class="footer-brand-logo"><span style="color:var(--red);">&#9679;</span> TalentFlow</a>
      <p class="footer-brand-desc">The ServiceNow recruitment agency built exclusively for the ServiceNow community.</p>
    </div>
    <div class="footer-col"><h4>Company</h4><ul><li><a href="/#about">About Us</a></li><li><a href="/jobs">Careers</a></li><li><a href="/#contact">Contact</a></li></ul></div>
    <div class="footer-col"><h4>Services</h4><ul><li><a href="/#services">Permanent</a></li><li><a href="/#services">Contract</a></li><li><a href="/#services">Projects</a></li></ul></div>
    <div class="footer-col"><h4>Portal</h4><ul><li><a href="/jobs">Browse Jobs</a></li><li><a href="/track-application">Track App</a></li><li><a href="http://localhost:8003">HR Login</a></li></ul></div>
    <div class="footer-col footer-addr"><h4>Contact</h4>Kicukiro, Kigali, Rwanda<br><br><a href="tel:+250784466887">+250 7844 66887</a><br><a href="mailto:angel@talentflow.tech">angel@talentflow.tech</a></div>
  </div>
  <div class="footer-bottom">
    <div class="footer-copy">Copyright &copy; 2026 Talent Flow Recruitment &mdash; All Rights Reserved.</div>
    <div class="social-links"><a href="#">in</a><a href="#">tw</a><a href="#">fb</a></div>
  </div>
</div>
<script>
  var obs = new IntersectionObserver(function(entries){
    entries.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('visible'); obs.unobserve(e.target); } });
  },{threshold:.12});
  document.querySelectorAll('.reveal').forEach(function(el){ obs.observe(el); });
</script>"""

# ─────────────────────────────────────────────────────────────────────────────
#  LANDING PAGE
# ─────────────────────────────────────────────────────────────────────────────
modern_landing_template = (
    """<!DOCTYPE html><html lang="en"><head>"""
    + _BASE_HEAD
    + """<title>TalentFlow &mdash; ServiceNow Recruitment Experts</title></head><body>
<div class="page-loader"><div class="loader-logo">TalentFlow</div><div class="loader-spin"></div></div>"""
    + _NAV
    + """
<section class="hero" id="home">
  <div class="hero-blob hero-blob-1"></div>
  <div class="hero-blob hero-blob-2"></div>
  <div class="hero-content">
    <h1>TalentFlow lets your<br>career so easy.</h1>
    <p class="hero-sub">Talent Flow is a ServiceNow recruitment agency, created to look after the needs of the ServiceNow community. Permanent, contract, and project roles.</p>
    <a href="/jobs" class="hero-btn">Browse Available Jobs &rarr;</a>
  </div>
  <div class="hero-mockup">
    <div style="position:relative;">
      <div class="mockup-mini">
        <div class="mini-label">Active Applications</div>
        <div class="mini-title">ServiceNow Roles</div>
        <div class="mini-bar-wrap"><div class="mini-bar"></div></div>
      </div>
      <div class="mockup-card">
        <div class="mockup-header"><div class="mockup-title">&#128084; Open Positions</div><span class="mockup-badge">LIVE</span></div>
        <div class="mockup-stat">
          <div class="mockup-circle">34K</div>
          <div class="mockup-rows">
            <div class="mockup-row"><div class="mockup-row-fill" style="width:78%"></div></div>
            <div class="mockup-row"><div class="mockup-row-fill" style="width:55%"></div></div>
            <div class="mockup-row"><div class="mockup-row-fill" style="width:90%"></div></div>
            <div class="mockup-row"><div class="mockup-row-fill" style="width:40%"></div></div>
          </div>
        </div>
        <div class="mockup-tags">
          <span class="mockup-tag active">ITSM</span><span class="mockup-tag active">Platform</span>
          <span class="mockup-tag">CSM</span><span class="mockup-tag">SecOps</span>
          <span class="mockup-tag">HRSD</span><span class="mockup-tag">ITOM</span>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="services-section" id="services">
  <div class="services-intro">
    <div class="reveal">
      <span class="eyebrow">Our Services</span>
      <h2 class="section-title">Our Core <span>Featured</span> Service</h2>
      <p style="color:var(--muted);font-size:.97rem;line-height:1.8;">We specialise exclusively in the ServiceNow ecosystem &mdash; connecting the right people with the right roles, every time.<br><br>
      Unlike standard automation tools, TalentFlow utilizes &ldquo;Agentic AI&rdquo; to perform tasks autonomously. A recruiter can activate an AI agent that handles screening, follow-ups, and question generation without manual input.</p>
    </div>
    <div class="cards-grid">
      <div class="svc-card reveal reveal-d1"><div class="svc-icon">&#128084;</div><h3>Permanent Recruitment</h3><p>Shortlist of prequalified, certified ServiceNow Specialists for your permanent positions.</p><a href="/#contact" class="read-more">Read More &rarr;</a></div>
      <div class="svc-card reveal reveal-d2"><div class="svc-icon">&#9889;</div><h3>Contract Recruitment</h3><p>Certified ServiceNow Specialists available within 48hrs for your urgent contract needs.</p><a href="/#contact" class="read-more">Read More &rarr;</a></div>
      <div class="svc-card reveal reveal-d3"><div class="svc-icon">&#128274;</div><h3>Project Privacy</h3><p>Complete discretion and confidentiality throughout every placement process.</p><a href="/#contact" class="read-more">Read More &rarr;</a></div>
      <div class="svc-card reveal reveal-d4"><div class="svc-icon">&#128640;</div><h3>Project Delivery</h3><p>Outsource your ServiceNow project to our team of experienced professionals.</p><a href="/#contact" class="read-more">Read More &rarr;</a></div>
    </div>
  </div>
</section>

<div class="diag-divider"></div>
<section class="about-section" id="about">
  <div class="about-grid">
    <div class="reveal"><div class="about-blob-bg"><div class="about-people">&#128105;&#8205;&#128188;&#128104;&#8205;&#128188;</div></div></div>
    <div class="reveal reveal-d1">
      <span class="eyebrow">Who We Are</span>
      <h2 class="section-title">We are the Best Online<br><span>Recruitment Firm</span> in the world</h2>
      <div class="about-content">
        <p>With over 10 years in Technology Recruitment and the last 5 years specifically devoted to the ServiceNow ecosystem, we bring unmatched specialist expertise to every hire.</p>
        <p>We are not generalist recruiters &mdash; we understand certifications, modules, release cycles, and what makes a ServiceNow professional truly exceptional.</p>
      </div>
      <div class="about-actions"><a href="/#contact" class="about-btn">More About Us</a></div>
    </div>
  </div>
</section>

<div class="diag-divider-rev"></div>
<section class="why-section">
  <div style="text-align:center;" class="reveal">
    <span class="eyebrow">Why Choose Us</span>
    <h2 class="section-title">Why we are the <span>Best?</span></h2>
    <p style="color:var(--muted);max-width:500px;margin:.75rem auto 0;font-size:.95rem;line-height:1.75;">We are not measured by how many hours we work, but by the quality of talent we place.</p>
  </div>
  <div class="why-grid">
    <div class="why-card reveal reveal-d1"><div class="why-icon">&#9654;&#65039;</div><div><h4>Optimized for Speed &amp; Quality</h4><p>Contractors available within 48 hours. Permanent placements with a curated shortlist, delivered fast.</p></div></div>
    <div class="why-card reveal reveal-d2"><div class="why-icon">&#128273;</div><div><h4>Flexible Usability</h4><p>Whether permanent, contract or project &mdash; we adapt to your exact hiring model and timeline.</p></div></div>
    <div class="why-card reveal reveal-d3"><div class="why-icon">&#128101;</div><div><h4>24/7 Hours Support</h4><p>Angel and the team are always available. Your recruitment never stops because your business never stops.</p></div></div>
    <div class="why-card reveal reveal-d4"><div class="why-icon">&#127760;</div><div><h4>Worldwide Coverage</h4><p>Active across the UK, Europe, Africa and beyond &mdash; wherever ServiceNow talent is needed.</p></div></div>
  </div>
</section>

<section class="jobs-section" id="jobs">
  <div class="jobs-header reveal">
    <span class="eyebrow">Open Positions</span>
    <h2 class="section-title">&#127775; Featured <span>Opportunities</span></h2>
    <p>Currently recruiting active vacancies with both partners and end user organisations across all ServiceNow specialisms.</p>
  </div>
  <div class="filter-bar reveal">
    <button class="filter-btn active" onclick="filterJobs('all',this)">All Roles</button>
    <button class="filter-btn" onclick="filterJobs('ITSM',this)">ITSM</button>
    <button class="filter-btn" onclick="filterJobs('Platform',this)">Platform</button>
    <button class="filter-btn" onclick="filterJobs('CSM',this)">CSM</button>
    <button class="filter-btn" onclick="filterJobs('Contract',this)">Contract</button>
    <button class="filter-btn" onclick="filterJobs('Permanent',this)">Permanent</button>
  </div>
  <div class="jobs-grid" id="jobsGrid">
    {% for job in jobs[:6] %}
    <div class="job-card" data-dept="{{ job.department }}" data-type="{{ job.job_type if job.job_type else '' }}">
      <div class="job-card-top">
        <span class="dept-tag">{{ job.department }}</span>
        <span class="type-tag">{{ job.job_type if job.job_type else 'Open' }}</span>
      </div>
      <div class="job-name">{{ job.title }}</div>
      <div class="job-blurb">{{ job.description[:110] }}{% if job.description|length > 110 %}...{% endif %}</div>
      <div class="job-foot">
        <span class="job-sal">{{ job.salary if job.salary else 'Competitive' }}</span>
        <a href="/jobs/{{ job.id }}" class="job-cta">View Details &rarr;</a>
      </div>
    </div>
    {% else %}
    <div style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--muted);">
      <div style="font-family:'Nunito',sans-serif;font-size:1.2rem;font-weight:800;margin-bottom:.5rem;">No open roles right now</div>
      <div>Check back soon or <a href="#contact" style="color:var(--blue);">get in touch</a>.</div>
    </div>
    {% endfor %}
  </div>
</section>

<section class="testi-section">
  <div class="testi-grid">
    <div class="reveal">
      <div class="avatar-cluster">
        <div class="av av-1">&#128105;</div><div class="av av-2 active-av">&#128104;&#8205;&#128187;</div>
        <div class="av av-3">&#128105;&#8205;&#128188;</div><div class="av av-4">&#128104;</div>
        <div class="av av-5">&#128105;&#8205;&#127979;</div><div class="av av-6">&#128104;&#8205;&#128188;</div>
      </div>
    </div>
    <div class="testi-content reveal reveal-d1">
      <span class="eyebrow">Client Feedback</span>
      <h2 class="section-title">Great stories from our <span>Clients</span></h2>
      <blockquote>&ldquo;TalentFlow found us a senior ServiceNow architect within 72 hours. The quality of candidates was exceptional and Angel truly understood our technical requirements.&rdquo;</blockquote>
      <div class="testi-author">Karim Benneja <span>&mdash; CTO, Enterprise Solutions Ltd</span></div>
      <a href="/#contact" class="read-more-btn">Read More &rarr;</a>
    </div>
  </div>
</section>

<div class="bottom-section" id="contact">
  <div class="bottom-grid">
    <div class="newsletter reveal">
      <h3>Subscribe our<br>weekly Newsletter</h3>
      <p>Stay updated with the latest ServiceNow roles, market insights, and recruitment tips from Angel.</p>
      <input type="email" class="nl-input" placeholder="Your email*">
      <br><button class="nl-btn" onclick="this.textContent='Subscribed! \u2713'">Subscribe</button>
    </div>
    <div class="reveal reveal-d1">
      <div class="contact-card">
        <h3>Send us a Message</h3>
        <input type="email" class="cf-input" placeholder="Your email*">
        <input type="text" class="cf-input" placeholder="Subject*">
        <textarea class="cf-input cf-textarea" placeholder="Message"></textarea>
        <button class="cf-btn" onclick="this.textContent='Message Sent! \u2713'">Send Message</button>
      </div>
    </div>
  </div>
</div>
"""
    + _FOOTER
    + """
<script>
function filterJobs(term, btn) {
  document.querySelectorAll('.filter-btn').forEach(function(b){ b.classList.remove('active'); });
  btn.classList.add('active');
  document.querySelectorAll('#jobsGrid .job-card').forEach(function(card){
    var dept = card.dataset.dept || '';
    var type = card.dataset.type || '';
    var show = term === 'all' || dept.toLowerCase().indexOf(term.toLowerCase()) > -1 || type.toLowerCase().indexOf(term.toLowerCase()) > -1;
    card.style.display = show ? '' : 'none';
  });
}
</script>
</body></html>"""
)


# ─────────────────────────────────────────────────────────────────────────────
#  TRACKER PAGE  — built as a plain function, zero string concatenation
#  trackApps() is a plain global function — NOT inside any IIFE
# ─────────────────────────────────────────────────────────────────────────────
def build_tracker_page():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Nunito+Sans:wght@300;400;600&display=swap" rel="stylesheet">
<title>Track Your Application &mdash; TalentFlow</title>
<style>
:root{--blue:#3b5bdb;--blue-dark:#2846c4;--blue-light:#5c7cfa;--violet:#7048e8;--red:#fa5252;--white:#ffffff;--off:#f8f9fc;--text:#2d3748;--muted:#718096;--border:#e8edf5;--card-sh:0 8px 40px rgba(59,91,219,.10);}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{font-family:'Nunito Sans',sans-serif;background:var(--white);color:var(--text);}
@keyframes slideDown{from{opacity:0;transform:translateY(-16px)}to{opacity:1;transform:translateY(0)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes loaderOut{to{opacity:0;pointer-events:none}}
.page-loader{position:fixed;inset:0;background:var(--white);z-index:9999;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:1rem;animation:loaderOut .3s 1s ease both;}
.loader-logo{font-family:'Nunito',sans-serif;font-size:1.6rem;font-weight:900;color:var(--blue);}
.loader-spin{width:28px;height:28px;border:3px solid var(--border);border-top-color:var(--blue);border-radius:50%;animation:spin .7s linear infinite;}
nav{position:fixed;top:0;left:0;right:0;z-index:200;display:flex;align-items:center;justify-content:space-between;padding:.9rem 4rem;background:rgba(255,255,255,.96);backdrop-filter:blur(16px);box-shadow:0 2px 20px rgba(59,91,219,.08);animation:slideDown .5s ease both;}
.nav-logo{font-family:'Nunito',sans-serif;font-size:1.3rem;font-weight:900;color:var(--blue);text-decoration:none;display:flex;align-items:center;gap:.5rem;}
.nav-logo-dot{width:8px;height:8px;border-radius:50%;background:var(--red);display:inline-block;}
.nav-links-list{display:flex;align-items:center;gap:2.5rem;list-style:none;}
.nav-links-list a{color:var(--text);text-decoration:none;font-size:.88rem;font-weight:600;transition:color .2s;}
.nav-links-list a:hover{color:var(--blue);}
.nav-signin{background:var(--red);color:var(--white);padding:.55rem 1.5rem;border-radius:4px;font-weight:700;font-size:.88rem;text-decoration:none;}
.tracker-hero{padding:8rem 4rem 6rem;background:linear-gradient(135deg,#3b5bdb 0%,#7048e8 100%);position:relative;overflow:hidden;}
.tracker-hero::after{content:'';position:absolute;bottom:-2px;left:0;right:0;height:80px;background:var(--off);clip-path:polygon(0 60%,100% 0,100% 100%,0 100%);}
.tracker-hero h1{font-family:'Nunito',sans-serif;font-size:clamp(2rem,5vw,3rem);font-weight:900;color:#fff;margin-bottom:.75rem;}
.tracker-hero p{color:rgba(255,255,255,.8);font-size:1rem;max-width:480px;line-height:1.75;}
.tracker-body{padding:4rem;background:var(--off);min-height:50vh;}
.tracker-form-card{background:var(--white);border-radius:16px;padding:2.5rem;box-shadow:var(--card-sh);max-width:600px;margin:0 auto;}
.tf-label{display:block;font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.6rem;}
.tf-input{width:100%;padding:.85rem 1.1rem;border:2px solid var(--border);border-radius:6px;font-size:.9rem;font-family:'Nunito Sans',sans-serif;transition:border-color .25s;color:var(--text);margin-bottom:1rem;display:block;}
.tf-input:focus{outline:none;border-color:#3b5bdb;}
.tf-input::placeholder{color:#b0b8c8;}
.tf-btn{background:#3b5bdb;color:#fff;border:none;padding:.85rem 2rem;border-radius:6px;font-weight:800;font-size:.9rem;cursor:pointer;font-family:'Nunito Sans',sans-serif;width:100%;transition:background .2s,transform .2s;}
.tf-btn:hover{background:#2846c4;transform:translateY(-1px);}
.tf-btn:disabled{opacity:.6;cursor:not-allowed;transform:none;}
.results-wrap{max-width:600px;margin:0 auto;padding-top:.5rem;}
.result-card{background:var(--white);border-radius:14px;padding:2rem;margin-top:1.5rem;box-shadow:var(--card-sh);}
.result-header{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:.75rem;margin-bottom:1.25rem;}
.result-title{font-family:'Nunito',sans-serif;font-size:1.1rem;font-weight:800;color:var(--text);}
.result-meta{color:var(--muted);font-size:.82rem;margin-top:.25rem;}
.status-pill{display:inline-flex;padding:.3rem .9rem;border-radius:999px;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;}
.status-pending{background:#fff9e6;color:#b7791f;}
.status-reviewed{background:#ebf4ff;color:#2b6cb0;}
.status-shortlisted{background:#f0fff4;color:#276749;}
.status-rejected{background:#fff5f5;color:#c53030;}
.score-section{margin-bottom:1.25rem;}
.score-label{font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.5rem;}
.score-row{display:flex;align-items:center;gap:1rem;}
.score-bar-outer{height:6px;background:var(--border);border-radius:3px;overflow:hidden;flex:1;max-width:180px;}
.score-bar-inner{height:100%;background:linear-gradient(90deg,#3b5bdb,#7048e8);border-radius:3px;transition:width 1.2s ease;}
.score-val{font-size:.82rem;font-weight:700;color:#3b5bdb;}
.tl{position:relative;padding-left:1.4rem;margin-top:1.25rem;}
.tl::before{content:'';position:absolute;left:0;top:6px;bottom:6px;width:2px;background:var(--border);}
.tl-ev{position:relative;margin-bottom:.9rem;}
.tl-ev::before{content:'';position:absolute;left:-1.4rem;top:6px;width:8px;height:8px;border-radius:50%;background:#3b5bdb;border:2px solid #fff;}
.tl-ev-title{font-size:.875rem;font-weight:700;color:var(--text);}
.tl-ev-date{font-size:.76rem;color:var(--muted);margin-top:.15rem;}
.offer-banner{background:#f0fff4;border:1px solid #9ae6b4;border-radius:10px;padding:1.25rem 1.5rem;margin-bottom:1.5rem;}
.offer-banner-title{font-family:'Nunito',sans-serif;font-size:1rem;font-weight:800;color:#276749;margin-bottom:.5rem;}
.offer-banner p{font-size:.875rem;color:#2f855a;line-height:1.7;}
.err-box{background:#fff9e6;border:1px solid #f6e05e;border-radius:10px;padding:1.25rem 1.5rem;margin-top:1.5rem;}
.err-box h4{font-size:.92rem;font-weight:800;color:#744210;margin-bottom:.5rem;}
.err-box p{font-size:.82rem;color:#744210;line-height:1.7;}
.err-box code{background:#fef3c7;padding:.1rem .35rem;border-radius:3px;font-family:monospace;}
.site-footer{background:#1a1f36;padding:2.5rem 4rem;color:rgba(255,255,255,.65);margin-top:0;}
.footer-bottom{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;}
.footer-copy{font-size:.8rem;}
@media(max-width:768px){nav{padding:.9rem 1.5rem;}.nav-links-list{display:none;}.tracker-hero,.tracker-body{padding-left:1.5rem;padding-right:1.5rem;}}
</style>
</head>
<body>

<div class="page-loader"><div class="loader-logo">TalentFlow</div><div class="loader-spin"></div></div>

<nav>
  <a href="/" class="nav-logo"><span class="nav-logo-dot"></span> TalentFlow</a>
  <ul class="nav-links-list">
    <li><a href="/">Home</a></li>
    <li><a href="/#services">Service</a></li>
    <li><a href="/#about">About</a></li>
    <li><a href="/jobs">Jobs</a></li>
    <li><a href="/#contact">Contact</a></li>
  </ul>
  <a href="http://localhost:8003" class="nav-signin">Sign In</a>
</nav>

<div class="tracker-hero">
  <a href="/" style="display:inline-flex;align-items:center;gap:.5rem;color:rgba(255,255,255,.75);text-decoration:none;font-size:.85rem;font-weight:600;margin-bottom:1.5rem;">&larr; Home</a>
  <h1>Track your Application</h1>
  <p>Enter the email address you used to apply and we'll show you exactly where you stand.</p>
</div>

<div class="tracker-body">
  <div class="tracker-form-card">
    <label class="tf-label" for="trackEmail">Your Email Address</label>
    <input type="email" id="trackEmail" class="tf-input" placeholder="your.email@example.com">
    <button id="trackBtn" class="tf-btn">Track Applications &rarr;</button>
  </div>
  <div class="results-wrap" id="trackerResults"></div>
</div>

<div class="site-footer">
  <div class="footer-bottom">
    <div class="footer-copy">Copyright &copy; 2026 Talent Flow Recruitment &mdash; All Rights Reserved.</div>
    <a href="/" style="color:rgba(255,255,255,.6);text-decoration:none;font-size:.85rem;">&larr; Back to Home</a>
  </div>
</div>

<script>
// trackApps is a plain global function — no IIFE, no wrapper
function trackApps() {
  var emailInput = document.getElementById('trackEmail');
  var btn        = document.getElementById('trackBtn');
  var el         = document.getElementById('trackerResults');
  var email      = emailInput.value.trim();

  if (!email) {
    emailInput.style.borderColor = '#fa5252';
    emailInput.focus();
    return;
  }
  emailInput.style.borderColor = '#e8edf5';

  btn.disabled    = true;
  btn.textContent = 'Searching...';
  el.innerHTML    = '<div style="text-align:center;padding:3rem;color:#718096;">Looking up your applications...</div>';

  fetch('/applications-by-email?email=' + encodeURIComponent(email))
    .then(function(res) {
      if (!res.ok) {
        return res.text().then(function(t) { throw new Error('Server error ' + res.status + ': ' + t.slice(0,200)); });
      }
      return res.json();
    })
    .then(function(data) {
      btn.disabled    = false;
      btn.textContent = 'Track Applications \u2192';

      if (data && !Array.isArray(data) && data.error) {
        throw new Error('DB error: ' + data.error);
      }
      if (!Array.isArray(data)) {
        throw new Error('Unexpected response: ' + JSON.stringify(data).slice(0,120));
      }
      if (data.length === 0) {
        el.innerHTML = '<div class="result-card" style="text-align:center;padding:2.5rem;">'
          + '<div style="font-size:2.5rem;margin-bottom:1rem;">&#128269;</div>'
          + '<div style="font-family:Nunito,sans-serif;font-size:1.1rem;font-weight:800;margin-bottom:.5rem;">No applications found</div>'
          + '<div style="color:#718096;font-size:.9rem;">No applications found for <strong>' + email + '</strong>.<br>Make sure you use the same email you applied with.</div>'
          + '</div>';
        return;
      }

      el.innerHTML = data.map(function(app) {
        var status = ((app.status || 'pending') + '').toLowerCase();

        var offerBanner = '';
        if (app.offer_status === 'sent') {
          offerBanner = '<div class="offer-banner">'
            + '<div class="offer-banner-title">&#127881; Congratulations &mdash; You have an offer!</div>'
            + '<p><strong>Position:</strong> ' + (app.offer_position || app.job_title || 'N/A')
            + ' | <strong>Salary:</strong> ' + (app.offer_salary || 'TBD')
            + ' | <strong>Start:</strong> ' + (app.offer_start_date || 'TBD') + '</p>'
            + '</div>';
        }

        var scoreHtml = '';
        if (app.resume_score) {
          var pct = Math.min(parseFloat(app.resume_score) || 0, 100);
          scoreHtml = '<div class="score-section">'
            + '<div class="score-label">Resume Score</div>'
            + '<div class="score-row">'
            + '<div class="score-bar-outer"><div class="score-bar-inner" style="width:' + pct + '%"></div></div>'
            + '<span class="score-val">' + pct.toFixed(1) + '/100</span>'
            + '</div></div>';
        }

        function fmt(d) {
          try { return new Date(d).toLocaleDateString('en-GB', {day:'numeric',month:'long',year:'numeric'}); }
          catch(e) { return d || ''; }
        }
        function fmtShort(d) {
          try { return new Date(d).toLocaleDateString('en-GB', {day:'numeric',month:'long'}); }
          catch(e) { return d || ''; }
        }

        var tl = '<div class="tl-ev"><div class="tl-ev-title">Application submitted</div>'
          + '<div class="tl-ev-date">' + (app.application_date ? fmt(app.application_date) : 'Unknown') + '</div></div>';

        if (app.resume_score) {
          tl += '<div class="tl-ev"><div class="tl-ev-title">Resume reviewed &amp; scored</div>'
            + '<div class="tl-ev-date">' + parseFloat(app.resume_score).toFixed(1) + ' / 100</div></div>';
        }
        if (app.interview_status) {
          tl += '<div class="tl-ev"><div class="tl-ev-title">Interview scheduled &mdash; ' + app.interview_status + '</div>'
            + '<div class="tl-ev-date">' + (app.scheduled_date ? fmtShort(app.scheduled_date) : '') + ' ' + (app.scheduled_time || '') + '</div></div>';
        }
        if (app.overall_score) {
          tl += '<div class="tl-ev"><div class="tl-ev-title">Evaluation completed</div>'
            + '<div class="tl-ev-date">Score: ' + app.overall_score + '/10</div></div>';
        }
        if (app.offer_status) {
          tl += '<div class="tl-ev"><div class="tl-ev-title" style="color:#276749;">&#127881; Offer ' + app.offer_status + '</div>'
            + '<div class="tl-ev-date">' + (app.offer_salary || '') + ' | Starts ' + (app.offer_start_date || 'TBD') + '</div></div>';
        }

        var appliedStr = app.application_date ? 'Applied ' + new Date(app.application_date).toLocaleDateString('en-GB') : '';

        return '<div class="result-card">'
          + offerBanner
          + '<div class="result-header"><div>'
          + '<div class="result-title">' + (app.job_title || 'Application') + '</div>'
          + '<div class="result-meta">' + (app.department || '') + (app.department && appliedStr ? ' &middot; ' : '') + appliedStr + '</div>'
          + '</div><span class="status-pill status-' + status + '">' + status + '</span></div>'
          + scoreHtml
          + '<div class="tl">' + tl + '</div>'
          + '</div>';
      }).join('');
    })
    .catch(function(err) {
      btn.disabled    = false;
      btn.textContent = 'Track Applications \u2192';
      el.innerHTML = '<div class="err-box">'
        + '<h4>&#9888; Something went wrong</h4>'
        + '<p><strong>Error:</strong> ' + err.message + '</p>'
        + '<p style="margin-top:.5rem;">Open this URL in your browser to see the raw data:</p>'
        + '<p><code>/applications-by-email?email=' + encodeURIComponent(email) + '</code></p>'
        + '</div>';
    });
}

// Wire up button and Enter key after DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  var btn = document.getElementById('trackBtn');
  var inp = document.getElementById('trackEmail');
  if (btn) btn.addEventListener('click', trackApps);
  if (inp) inp.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') { e.preventDefault(); trackApps(); }
  });
});
</script>

</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def modern_landing_page(request: Request):
    jobs = db.get_all_jobs()
    from jinja2 import Template
    html = Template(modern_landing_template).render(jobs=jobs)
    return HTMLResponse(content=html)


@app.get("/jobs", response_class=HTMLResponse)
async def jobs_list(request: Request):
    jobs = db.get_all_jobs()
    from job_portal import job_portal_template
    from jinja2 import Template
    html = Template(job_portal_template).render(jobs=jobs, job=None)
    return HTMLResponse(content=html)


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_details(request: Request, job_id: int):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    from job_portal import job_portal_template
    from jinja2 import Template
    html = Template(job_portal_template).render(job=job, jobs=[])
    return HTMLResponse(content=html)


@app.get("/track-application", response_class=HTMLResponse)
async def track_application(request: Request):
    # Build fresh each time — no string concatenation, no template engine
    return HTMLResponse(content=build_tracker_page())


@app.get("/hr-login")
async def hr_login_redirect():
    return RedirectResponse(url="http://localhost:8003", status_code=302)


@app.get("/applications-by-email")
async def get_applications_by_email(email: str):
    try:
        applications = db.get_applications_by_email(email)
        result = []
        for app in applications:
            if isinstance(app, dict):
                result.append(app)
            elif hasattr(app, '__dict__'):
                result.append({k: v for k, v in app.__dict__.items() if not k.startswith('_')})
            else:
                result.append(dict(app))
        return JSONResponse(content=result)
    except Exception as e:
        import traceback
        return JSONResponse(
            content={"error": str(e), "traceback": traceback.format_exc()},
            status_code=500
        )


@app.post("/apply/{job_id}")
async def submit_application(job_id: int, request: Request):
    """Handle job application submission"""
    try:
        data = await request.json()
        
        # Add applicant to database
        applicant_id = db.add_applicant(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            position=data.get('position', '')
        )
        
        # Score the resume
        result = scorer.score_resume(data['resume_text'])
        
        # Save the score
        db.save_resume_score(
            applicant_id=applicant_id,
            resume_text=data['resume_text'],
            score=result['score'],
            features=result['features'],
            recommendations=result['recommendations']
        )
        
        # Create job application
        db.add_job_application(
            job_id=job_id,
            applicant_id=applicant_id,
            cover_letter=data.get('cover_letter', '')
        )
        
        return JSONResponse(content={
            'success': True,
            'message': 'Application submitted successfully'
        })
        
    except Exception as e:
        return JSONResponse(content={
            'success': False,
            'error': str(e)
        }, status_code=500)


if __name__ == "__main__":
    import uvicorn
    print("Starting TalentFlow Portal...")
    print("Open http://localhost:8005 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8005)