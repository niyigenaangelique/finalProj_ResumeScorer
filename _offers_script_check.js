
// ── AV COLOURS ────────────────────────────────────────
const AV_COLS = [
  ['#4776E6','#8E54E9'],['#F05252','#FF7B7B'],
  ['#0BB5B5','#36D1C4'],['#F4A83A','#F7CB6A'],
  ['#27AE60','#52C87A'],['#6B4FDB','#9B6FFF'],
];
function avGrad(name) {
  const i = (name||'?').charCodeAt(0)%AV_COLS.length;
  return `linear-gradient(135deg,${AV_COLS[i][0]},${AV_COLS[i][1]})`;
}

// ── AUTO-FILL ─────────────────────────────────────────
function autoFill() {
  const id = document.getElementById('applicationSelect').value;
  if (!id) return;
  fetch('/api/application-details/'+id)
    .then(r=>r.json())
    .then(d=>{
      if (d.success) {
        const a = d.application;
        document.getElementById('positionTitle').value = a.job_title    || '';
        document.getElementById('department').value    = a.department   || '';
      }
    }).catch(()=>{});
}

function updateSalaryPlaceholder() {
  const t = document.getElementById('offerType').value;
  const ph = {internship:'e.g. 2,000/month or 20/hr',contract:'e.g. 120,000/year or 75/hr',
               'part-time':'e.g. 40,000 – 60,000/year'}[t] || 'e.g. 80,000 – 120,000/year';
  document.getElementById('salary').placeholder = ph;
}

function scrollToForm() {
  document.getElementById('offerForm').scrollIntoView({behavior:'smooth',block:'start'});
}

// ── PREVIEW ───────────────────────────────────────────
function openPreview() {
  const pos = gv('positionTitle');
  const sal = gv('salary');
  if (!pos || !sal) { showToast('Missing','Fill in Position and Salary first.','warning'); return; }

  const today = new Date().toLocaleDateString('en-US',{year:'numeric',month:'long',day:'numeric'});
  const ben   = gv('benefits');
  const det   = gv('offerDetails');
  const dead  = gv('responseDeadline');
  const start = gv('startDate');

  document.getElementById('previewContent').innerHTML = `
    <div style="border:1.5px solid var(--border);border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#3B6FE8,#6B4FDB);padding:20px 24px;text-align:center;">
        <div style="font-family:'Sora',sans-serif;font-size:22px;font-weight:800;color:#fff;">ZIBITECH</div>
        <div style="font-size:12px;color:rgba(255,255,255,.7);margin-top:3px;">Confidential Offer Letter</div>
      </div>
      <div style="padding:24px 28px;background:var(--white);">
        <p style="font-size:13px;color:var(--ink3);margin-bottom:16px;">${today}</p>
        <p style="font-size:14px;color:var(--ink);line-height:1.7;margin-bottom:16px;">
          Dear <strong>[Applicant Name]</strong>,<br><br>
          We are delighted to offer you the position of <strong style="color:var(--blue);">${escHtml(pos)}</strong> at ZIBITECH.
        </p>
        <div style="background:var(--bg);border-radius:10px;padding:16px 20px;margin-bottom:16px;">
          <div style="font-family:'Sora',sans-serif;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);margin-bottom:12px;">Offer Details</div>
          ${_dtrow2('Position',    pos)}
          ${_dtrow2('Department',  gv('department'))}
          ${_dtrow2('Type',        gv('offerType').replace('-',' ').replace(/\\b\\w/g,c=>c.toUpperCase()))}
          ${_dtrow2('Salary',      '$'+escHtml(gv('salary')))}
          ${_dtrow2('Start Date',  start||'TBD')}
          ${_dtrow2('Location',    gv('location')||'—')}
          ${_dtrow2('Reports To',  gv('reportingTo')||'—')}
        </div>
        ${ben?`<div style="margin-bottom:14px;"><div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);margin-bottom:6px;">Benefits & Perks</div><div style="font-size:13.5px;color:var(--ink2);white-space:pre-wrap;line-height:1.65;">${escHtml(ben)}</div></div>`:''}
        ${det?`<div style="margin-bottom:14px;"><div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3);margin-bottom:6px;">Additional Terms</div><div style="font-size:13.5px;color:var(--ink2);white-space:pre-wrap;line-height:1.65;">${escHtml(det)}</div></div>`:''}
        <p style="font-size:13.5px;color:var(--ink2);line-height:1.7;">
          Please respond by <strong style="color:${dead?'var(--red)':'var(--ink)'}">${dead||'as soon as possible'}</strong>.
          If you have any questions, don't hesitate to reach out.
        </p>
        <p style="margin-top:16px;font-size:13.5px;color:var(--ink2);">Best regards,<br><strong>ZIBITECH HR Team</strong></p>
      </div>
    </div>`;
  document.getElementById('previewModal').style.display = 'flex';
}

function _dtrow2(label, val) {
  return `<div style="display:flex;gap:8px;padding:6px 0;border-bottom:1px solid var(--border);">
    <span style="font-size:12.5px;font-weight:700;color:var(--ink2);min-width:100px;">${label}</span>
    <span style="font-size:13px;color:var(--ink);">${val||'—'}</span>
  </div>`;
}

function closePreview() { document.getElementById('previewModal').style.display='none'; }

// ── DRAFT ─────────────────────────────────────────────
const DRAFT_IDS = ['applicationSelect','offerType','positionTitle','department','salary',
  'startDate','location','reportingTo','benefits','offerDetails','responseDeadline'];

function saveDraft() {
  const d = {};
  DRAFT_IDS.forEach(id => { const el=document.getElementById(id); if(el) d[id]=el.value; });
  localStorage.setItem('offerDraft', JSON.stringify(d));
  showToast('Draft Saved','Form saved locally.','success',2000);
}
function clearForm() {
  DRAFT_IDS.forEach(id => { const el=document.getElementById(id); if(el) el.value=''; });
  localStorage.removeItem('offerDraft');
  showToast('Cleared','Form reset.','info',1500);
}

// ── SUBMIT ────────────────────────────────────────────
function gv(id) { return (document.getElementById(id)?.value||'').trim(); }

function submitOffer() {
  const required = ['applicationSelect','positionTitle','department','salary','startDate','location','reportingTo'];
  for (const id of required) {
    if (!gv(id)) {
      showToast('Required', id.replace(/([A-Z])/g,' $1').replace(/^./,c=>c.toUpperCase())+' is required.','warning');
      document.getElementById(id)?.focus(); return;
    }
  }
  const btn = document.getElementById('createBtn');
  const lbl = document.getElementById('createBtnLabel');
  btn.disabled = true;
  lbl.innerHTML = '<div class="spin" style="width:13px;height:13px;border-width:2px;border-top-color:#fff;display:inline-block;vertical-align:-2px;"></div> Creating…';

  const data = {
    application_id:   gv('applicationSelect'),
    offer_type:       gv('offerType'),
    position_title:   gv('positionTitle'),
    department:       gv('department'),
    salary:           gv('salary'),
    start_date:       gv('startDate'),
    location:         gv('location'),
    reporting_to:     gv('reportingTo'),
    benefits:         gv('benefits'),
    offer_details:    gv('offerDetails'),
    response_deadline:gv('responseDeadline'),
  };

  fetch('/api/create-offer', {
    method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)
  })
  .then(r=>r.json())
  .then(d=>{
    btn.disabled=false; lbl.textContent='Create Offer';
    if (d.success) {
      showToast('Offer Created','Offer letter generated successfully.','success');
      clearForm();
      localStorage.removeItem('offerDraft');
      setTimeout(()=>location.reload(), 1300);
    } else showToast('Error', d.error||'Failed.','error');
  })
  .catch(err=>{ btn.disabled=false; lbl.textContent='Create Offer'; showToast('Network Error',err.message,'error'); });
}

// ── VIEW OFFER ────────────────────────────────────────
function viewOffer(id) {
  document.getElementById('viewOfferContent').innerHTML =
    '<div style="text-align:center;padding:32px;"><div class="spin" style="margin:0 auto 10px;"></div><div style="font-size:13px;color:var(--ink3);">Loading…</div></div>';
  document.getElementById('viewOfferModal').style.display = 'flex';

  fetch('/api/offer-details/'+id)
    .then(r=>r.json())
    .then(d=>{
      if (!d.success) { document.getElementById('viewOfferContent').innerHTML=`<p style="color:var(--red);">${d.error}</p>`; return; }
      const o = d.offer;
      const s = (o.status||'pending').toLowerCase();
      const statusMeta = {
        pending:  ['var(--amber-lt)','#C67C00','Pending'],
        sent:     ['var(--blue-lt)','var(--blue)','Sent'],
        accepted: ['#E8F8F0','var(--green)','Accepted'],
        rejected: ['var(--red-lt)','var(--red)','Rejected'],
        withdrawn:['var(--bg)','var(--ink3)','Withdrawn'],
      };
      const [sbg,scol,slbl] = statusMeta[s]||['var(--bg)','var(--ink3)',s];
      document.getElementById('viewOfferContent').innerHTML = `
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
          <div style="width:44px;height:44px;border-radius:11px;flex-shrink:0;
            background:${avGrad(o.applicant_name)};
            display:flex;align-items:center;justify-content:center;
            font-family:'Sora',sans-serif;font-weight:800;font-size:16px;color:#fff;">
            ${(o.applicant_name||'?')[0].toUpperCase()}
          </div>
          <div style="flex:1;">
            <div style="font-family:'Sora',sans-serif;font-weight:700;font-size:15px;color:var(--ink);">${escHtml(o.applicant_name||'N/A')}</div>
            <div style="font-size:12.5px;color:var(--ink3);">${escHtml(o.position_title||'N/A')}</div>
          </div>
          <span style="display:inline-flex;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700;background:${sbg};color:${scol};">${slbl}</span>
        </div>
        <table class="od-table">
          <tr><td>Position</td><td style="font-weight:600;">${escHtml(o.position_title||'—')}</td></tr>
          <tr><td>Department</td><td>${escHtml(o.department||'—')}</td></tr>
          <tr><td>Offer Type</td><td>${escHtml(o.offer_type||'—')}</td></tr>
          <tr><td>Salary</td><td style="font-weight:700;color:var(--blue);">${escHtml(o.salary||'—')}</td></tr>
          <tr><td>Start Date</td><td>${escHtml(o.start_date||'—')}</td></tr>
          <tr><td>Location</td><td>${escHtml(o.location||'—')}</td></tr>
          <tr><td>Reports To</td><td>${escHtml(o.reporting_to||'—')}</td></tr>
          <tr><td>Deadline</td><td>${escHtml(o.response_deadline||'No deadline')}</td></tr>
        </table>
        ${o.benefits?`<div style="font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--ink3);margin-bottom:6px;">Benefits</div><div class="od-notes">${escHtml(o.benefits)}</div>`:''}
        <div style="margin-top:20px; padding-top:16px; border-top:1px solid var(--border);">
          <div style="font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--ink3);margin-bottom:8px;">Update Status</div>
          <div style="display:flex; gap:10px; align-items:center;">
            <select class="form-ctrl" id="offerStatusSelect" style="flex:1;">
              <option value="draft" ${s==='draft'?'selected':''}>Draft</option>
              <option value="sent" ${s==='sent'?'selected':''}>Sent</option>
              <option value="accepted" ${s==='accepted'?'selected':''}>Accepted</option>
              <option value="rejected" ${s==='rejected'?'selected':''}>Rejected</option>
              <option value="hired" ${s==='hired'?'selected':''}>Hired (Sync to HRMS)</option>
              <option value="withdrawn" ${s==='withdrawn'?'selected':''}>Withdrawn</option>
            </select>
            <button class="btn btn-primary" onclick="updateOfferStatus(${id})">Update</button>
          </div>
          ${s === 'hired' ? '<div style="margin-top:8px; font-size:11px; color:var(--green); font-weight:700;">✓ Synced to TalentFlow HRMS</div>' : ''}
        </div>

        <div style="display:flex;gap:8px;margin-top:24px;flex-wrap:wrap;">
          ${s==='accepted' ? `<button class="btn btn-success" onclick="closeViewOffer();updateOfferStatus(${o.id}, 'hired')"><svg width='13' height='13' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2.5'><path d='M22 11.08V12a10 10 0 1 1-5.93-9.14'/><polyline points='22 4 12 14.01 9 11.01'/></svg> Finalize Hire & Sync</button>` : ''}
          ${s==='draft' || s==='pending' ?`<button class="btn btn-primary" onclick="closeViewOffer();sendOffer(${id})"><svg width='13' height='13' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><line x1='22' y1='2' x2='11' y2='13'/><polygon points='22 2 15 22 11 13 2 9 22 2'/></svg> Send Offer</button>`
            : s==='sent'?`<button class="btn btn-danger" onclick="closeViewOffer();withdrawOffer(${id})"><svg width='13' height='13' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><polyline points='9 14 4 9 9 4'/><path d='M20 20v-7a4 4 0 0 0-4-4H4'/></svg> Withdraw</button>`:''}
          <button class="btn btn-outline" onclick="closeViewOffer()">Close</button>
        </div>`;
    })
    .catch(()=>{ document.getElementById('viewOfferContent').innerHTML='<p style="color:var(--red);">Network error.</p>'; });
}
function closeViewOffer() { document.getElementById('viewOfferModal').style.display='none'; }

// ── SEND / WITHDRAW / DELETE ───────────────────────────
function updateOfferStatus(id, manualStatus = null) {
  const status = manualStatus || document.getElementById('offerStatusSelect').value;
  if (!confirm(`Update offer status to "${status}"?` + (status === 'hired' ? '\n\nIMPORTANT: This will finalize the recruitment and push the new employee data to the TalentFlow HRMS.' : ''))) return;
  
  fetch('/api/update-offer-status', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ offer_id: id, status: status })
  })
  .then(r => r.json())
  .then(d => {
    if (d.success) {
      showToast('Status Updated', `Offer is now ${status}.`, 'success');
      closeViewOffer();
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast('Update Failed', d.error || 'Failed to update.', 'error');
    }
  })
  .catch(err => showToast('Network Error', err.message, 'error'));
}

function sendOffer(id) {
  if (!confirm('Send this offer to the candidate now?')) return;
  fetch('/api/send-offer/'+id, {method:'POST'})
    .then(r=>r.json())
    .then(d=>{ if(d.success){ showToast('Offer Sent','Email dispatched to candidate.','success'); setTimeout(()=>location.reload(),1200); }
      else showToast('Error', d.error||'Failed.','error'); })
    .catch(()=>showToast('Error','Network error.','error'));
}
function withdrawOffer(id) {
  if (!confirm('Withdraw this offer?')) return;
  fetch('/api/withdraw-offer/'+id, {method:'POST'})
    .then(r=>r.json())
    .then(d=>{ if(d.success){ showToast('Withdrawn','Offer has been withdrawn.','warning'); setTimeout(()=>location.reload(),1200); }
      else showToast('Error', d.error||'Failed.','error'); })
    .catch(()=>showToast('Error','Network error.','error'));
}
function deleteOffer(id) {
  if (!confirm('Delete this offer permanently?')) return;
  fetch('/api/delete-offer/'+id, {method:'DELETE'})
    .then(r=>r.json())
    .then(d=>{ if(d.success){ showToast('Deleted','Offer removed.','warning'); setTimeout(()=>location.reload(),1200); }
      else showToast('Error', d.error||'Failed.','error'); })
    .catch(()=>showToast('Error','Network error.','error'));
}

// ── HISTORY ──────────────────────────────────────────
function loadOfferHistory() {
  const div = document.getElementById('offersHistory');
  div.innerHTML = '<div style="text-align:center;padding:32px;"><div class="spin" style="margin:0 auto 10px;"></div><div style="font-size:13px;color:var(--ink3);">Loading…</div></div>';
  fetch('/api/offer-history')
    .then(r=>r.json())
    .then(d=>{
      if (!d.success||!d.offers.length) {
        div.innerHTML = `<div style="text-align:center;padding:40px;color:var(--ink3);">
          <div style="margin-bottom:12px;"><svg width='20' height='20' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='1.8'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/><polyline points='14 2 14 8 20 8'/><line x1='16' y1='13' x2='8' y2='13'/><line x1='16' y1='17' x2='8' y2='17'/></svg></div>
          <div style="font-family:'Sora',sans-serif;font-weight:700;font-size:14px;color:var(--ink2);">No offer history yet</div>
        </div>`; return;
      }
      div.innerHTML = d.offers.map((o,i) => {
        const s = (o.status||'pending').toLowerCase();
        const statusMeta = {
          pending:  ['var(--amber-lt)','#C67C00','Pending'],
          sent:     ['var(--blue-lt)','var(--blue)','Sent'],
          accepted: ['#E8F8F0','var(--green)','Accepted'],
          rejected: ['var(--red-lt)','var(--red)','Rejected'],
          withdrawn:['var(--bg)','var(--ink3)','Withdrawn'],
        };
        const [sbg,scol,slbl] = statusMeta[s]||['var(--bg)','var(--ink3)',s];
        return `<div class="offer-card" style="animation-delay:${i*0.04}s;">
          <div class="offer-av" style="background:${avGrad(o.applicant_name||'?')}">${(o.applicant_name||'?')[0].toUpperCase()}</div>
          <div class="offer-body">
            <div class="offer-name">${escHtml(o.applicant_name||'N/A')} — ${escHtml(o.position_title||'N/A')}</div>
            <div class="offer-meta">
              <span><svg width='11' height='11' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><line x1='12' y1='1' x2='12' y2='23'/><path d='M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6'/></svg> ${escHtml(o.salary||'—')}</span>
              <span><svg width='11' height='11' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><path d='M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/><polyline points='9 22 9 12 15 12 15 22'/></svg> ${escHtml(o.department||'—')}</span>
              <span><svg width='11' height='11' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2'><rect x='3' y='4' width='18' height='18' rx='2'/><line x1='16' y1='2' x2='16' y2='6'/><line x1='8' y1='2' x2='8' y2='6'/><line x1='3' y1='10' x2='21' y2='10'/></svg> ${escHtml(o.start_date||'—')}</span>
              <span style="display:inline-flex;padding:2px 9px;border-radius:20px;font-size:11.5px;font-weight:700;background:${sbg};color:${scol};">${slbl}</span>
            </div>
          </div>
          <div class="offer-actions">
            <button class="btn btn-outline btn-sm" onclick="viewOffer(${o.id})">View</button>
            ${s==='draft' || s==='pending'?`<button class="btn btn-primary btn-sm" onclick="sendOffer(${o.id})">Send</button>`:''}
            ${s==='sent'?`<button class="btn btn-warn btn-sm" onclick="withdrawOffer(${o.id})">Withdraw</button>`:''}
            <button class="btn btn-danger btn-sm" onclick="deleteOffer(${o.id})">Delete</button>
          </div>
        </div>`;
      }).join('');
    })
    .catch(()=>{
      div.innerHTML='<div style="text-align:center;padding:32px;color:var(--red);">Error loading history. <button class="btn btn-outline" style="margin-top:10px;" onclick="loadOfferHistory()">Retry</button></div>';
    });
}

// ── UTILS ─────────────────────────────────────────────
function escHtml(s) {
  if(!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/\'/g,'&#39;');
}

// Backdrop close
['previewModal','viewOfferModal'].forEach(id=>{
  document.getElementById(id).addEventListener('click', function(e){ if(e.target===this) this.style.display='none'; });
});

// Init
window.addEventListener('load', () => {
  loadOfferHistory();
  const draft = localStorage.getItem('offerDraft');
  if (draft) {
    try {
      const data = JSON.parse(draft);
      Object.keys(data).forEach(id => { const el=document.getElementById(id); if(el&&data[id]) el.value=data[id]; });
      showToast('Draft Restored','Last saved draft loaded.','info',2500);
    } catch(e) { localStorage.removeItem('offerDraft'); }
  }
});
