const API = 'http://localhost:5000';

function $(id) { return document.getElementById(id); }

// ── On load ───────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  // Check API online
  fetch(API + '/health')
    .then(r => r.json())
    .then(() => {
      $('dot').style.background = '#3fb950';
    })
    .catch(() => {
      $('dot').style.background = '#f85149';
      $('dot').title = 'API Offline!';
    });

  // Get current tab URL
  chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
    const url = tabs[0]?.url || '';
    $('urlDisplay').textContent = url.replace(/^https?:\/\//, '').substring(0, 45) + (url.length > 50 ? '...' : '');

    // Show cached result
    chrome.runtime.sendMessage({ action: 'getResult', url }, result => {
      if (result) showResult(result);
    });
  });
});

// ── Scan button ───────────────────────────────────────────────
$('checkBtn').addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
    const url = tabs[0]?.url || '';

    if (url.startsWith('chrome://') || url.startsWith('chrome-extension://')) {
      showResult({ error: 'Cannot check internal browser pages.' });
      return;
    }

    $('checkBtn').disabled = true;
    $('loading').style.display = 'block';
    $('result').style.display = 'none';

    // Rotating messages
    const msgs = ['Extracting features...', 'Running ML model...', 'Calculating risk...'];
    let i = 0;
    const t = setInterval(() => { $('loadMsg').textContent = msgs[i++ % msgs.length]; }, 700);

    fetch(API + '/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    })
    .then(r => r.json())
    .then(data => {
      clearInterval(t);
      $('loading').style.display = 'none';
      $('checkBtn').disabled = false;
      showResult(data);
    })
    .catch(() => {
      clearInterval(t);
      $('loading').style.display = 'none';
      $('checkBtn').disabled = false;
      showResult({ error: 'API offline! Please run: python app.py' });
    });
  });
});

// ── Show result ───────────────────────────────────────────────
function showResult(data) {
  const div = $('result');

  // Error state
  if (data.error) {
    div.className = 'result info';
    div.innerHTML = `
      <div class="result-top">
        <span class="result-icon">⚠️</span>
        <div>
          <div class="result-title" style="color:#e3b341">Error</div>
          <div class="result-sub">${data.error}</div>
        </div>
      </div>`;
    div.style.display = 'block';
    return;
  }

  const safe  = data.is_safe;
  const conf  = safe ? (data.confidence?.legitimate || 0) : (data.confidence?.phishing || 0);
  const risk  = data.risk_level || (safe ? 'Low' : 'High');

  const riskTag = risk.toLowerCase().includes('low')  ? 'tag-safe'
                : risk.toLowerCase().includes('high') ? 'tag-danger'
                : 'tag-warn';

  div.className = `result ${safe ? 'safe' : 'danger'}`;
  div.innerHTML = `
    <div class="result-top">
      <span class="result-icon">${safe ? '✅' : '⛔'}</span>
      <div>
        <div class="result-title" style="color:${safe ? '#3fb950' : '#f85149'}">
          ${safe ? 'Safe Website' : 'Phishing Detected!'}
        </div>
        <div class="result-sub">${safe ? 'This website appears legitimate and safe.' : 'This may be a phishing attempt!'}</div>
      </div>
    </div>

    <div class="conf-row">
      <span>Confidence</span>
      <span style="color:${safe ? '#3fb950' : '#f85149'}">${conf.toFixed(1)}%</span>
    </div>
    <div class="conf-track">
      <div class="conf-fill ${safe ? 'safe' : 'danger'}" style="width:${conf}%"></div>
    </div>

    <div class="tags">
      <span class="tag ${safe ? 'tag-safe' : 'tag-danger'}">${safe ? 'Legitimate' : 'Phishing'}</span>
      <span class="tag ${riskTag}">Risk: ${risk}</span>
      ${data.note ? `<span class="tag tag-warn">${data.note}</span>` : ''}
    </div>

    <div class="checked-url">🔗 ${data.url || ''}</div>
  `;
  div.style.display = 'block';
}
