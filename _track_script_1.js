
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
      btn.textContent = 'Track Applications →';

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

        var offerStatus = ((app.offer_status || '') + '').toLowerCase();
        var offerBanner = '';
        if (offerStatus === 'sent') {
          offerBanner = '<div class="offer-banner">'
            + '<div class="offer-banner-title">&#127881; Congratulations &mdash; You have an offer!</div>'
            + '<p><strong>Position:</strong> ' + (app.offer_position || app.job_title || 'N/A')
            + ' | <strong>Salary:</strong> ' + (app.offer_salary || 'TBD')
            + ' | <strong>Start:</strong> ' + (app.offer_start_date || 'TBD') + '</p>'
            + '</div>';
        } else if (offerStatus === 'accepted') {
          offerBanner = '<div class="offer-banner">'
            + '<div class="offer-banner-title">&#9989; Offer accepted successfully</div>'
            + '<p>Your offer response was received. HR will now complete final hiring steps.</p>'
            + '</div>';
        } else if (offerStatus === 'rejected') {
          offerBanner = '<div class="offer-banner" style="background:#fff5f5;border-color:#fecaca;">'
            + '<div class="offer-banner-title" style="color:#b91c1c;">Offer declined</div>'
            + '<p style="color:#991b1b;">You have declined this offer. Contact HR if this was a mistake.</p>'
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
        if (status === 'interview_failed') {
          tl += '<div class="tl-ev"><div class="tl-ev-title" style="color:#b91c1c;">Interview result: Not selected</div>'
            + '<div class="tl-ev-date">Thank you for your time and effort during the interview process.</div></div>';
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

        var actions = '';
        if (offerStatus === 'sent' && app.offer_id) {
          actions = '<div style="margin-top:1.5rem;display:flex;gap:1rem;">'
            + '<button onclick="respondToOffer(' + app.id + ', ' + app.offer_id + ', \'accepted\')" class="tf-btn" style="background:#276749;">Accept Offer</button>'
            + '<button onclick="respondToOffer(' + app.id + ', ' + app.offer_id + ', \'rejected\')" class="tf-btn" style="background:#fa5252;">Reject Offer</button>'
            + '</div>';
        }

        return '<div class="result-card">'
          + offerBanner
          + '<div class="result-header"><div>'
          + '<div class="result-title">' + (app.job_title || 'Application') + '</div>'
          + '<div class="result-meta">' + (app.department || '') + (app.department && appliedStr ? ' &middot; ' : '') + appliedStr + '</div>'
          + '</div><span class="status-pill status-' + status.replace(/_/g, '-') + '">' + status.replace(/_/g, ' ') + '</span></div>'
          + scoreHtml
          + '<div class="tl">' + tl + '</div>'
          + actions
          + '</div>';
      }).join('');
    })
    .catch(function(err) {
      btn.disabled    = false;
      btn.textContent = 'Track Applications →';
      el.innerHTML = '<div class="err-box">'
        + '<h4>&#9888; Something went wrong</h4>'
        + '<p><strong>Error:</strong> ' + err.message + '</p>'
        + '<p style="margin-top:.5rem;">Open this URL in your browser to see the raw data:</p>'
        + '<p><code>/applications-by-email?email=' + encodeURIComponent(email) + '</code></p>'
        + '</div>';
    });
}

function respondToOffer(appId, offerId, response) {
  if (!confirm('Are you sure you want to ' + response + ' this offer?')) return;
  
  fetch('/api/respond-to-offer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ application_id: appId, offer_id: offerId, response: response })
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.success) {
      alert('Your response has been recorded.');
      trackApps();
    } else {
      alert('Error: ' + data.error);
    }
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
