const API_URL      = 'http://localhost:5000/predict';
const CACHE_TTL    = 3600000; // 1 hour
const checkedUrls  = new Map();

const SKIP_PREFIXES = [
  'chrome://', 'chrome-extension://', 'about:',
  'edge://', 'moz-extension://', 'file://'
];

// ── Tab updated listener ──────────────────────────────────────
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status !== 'complete' || !tab.url) return;
  if (SKIP_PREFIXES.some(p => tab.url.startsWith(p))) return;

  const cached = checkedUrls.get(tab.url);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    updateBadge(tabId, cached.is_safe);
    if (!cached.is_safe) injectWarning(tabId, cached);
    return;
  }

  checkUrl(tab.url, tabId);
});

// ── Fetch prediction ──────────────────────────────────────────
async function checkUrl(url, tabId) {
  try {
    const ctrl = new AbortController();
    setTimeout(() => ctrl.abort(), 10000);
    const res  = await fetch(API_URL, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ url }),
      signal:  ctrl.signal
    });
    const data = await res.json();

    checkedUrls.set(url, { ...data, timestamp: Date.now() });
    updateBadge(tabId, data.is_safe);

    if (!data.is_safe) {
      injectWarning(tabId, data);
      showNotification(data);
    }
  } catch {
    updateBadge(tabId, null);
  }
}

// ── Badge ─────────────────────────────────────────────────────
function updateBadge(tabId, isSafe) {
  const text  = isSafe === true ? '✓' : isSafe === false ? '!' : '';
  const color = isSafe === true ? '#00cc66' : isSafe === false ? '#ff4466' : '#64748b';
  chrome.action.setBadgeText({ text, tabId });
  chrome.action.setBadgeBackgroundColor({ color, tabId });
}

// ── Warning banner injected into page ────────────────────────
function injectWarning(tabId, data) {
  chrome.scripting.executeScript({
    target: { tabId },
    func:   showWarningBanner,
    args:   [data]
  }).catch(() => {});
}

function showWarningBanner(data) {
  if (document.getElementById('ai-phishing-banner')) return;

  const style = document.createElement('style');
  style.textContent = `
    #ai-phishing-banner {
      position: fixed; top: 0; left: 0; right: 0; z-index: 2147483647;
      background: linear-gradient(135deg, #1a0a0f 0%, #2d0f1a 100%);
      border-bottom: 2px solid #ff4466;
      color: #fff;
      padding: 12px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      font-size: 13px;
      box-shadow: 0 4px 30px rgba(255,68,102,0.3);
      animation: slideIn 0.3s ease;
    }
    @keyframes slideIn {
      from { transform: translateY(-100%); opacity: 0; }
      to   { transform: translateY(0);     opacity: 1; }
    }
    #ai-phishing-banner .b-icon { font-size: 22px; flex-shrink: 0; }
    #ai-phishing-banner .b-text .b-title {
      font-weight: 700; font-size: 14px;
      color: #ff7799; margin-bottom: 2px;
    }
    #ai-phishing-banner .b-text .b-sub {
      font-size: 11px; color: #ffaabb;
    }
    #ai-phishing-banner .b-close {
      background: rgba(255,68,102,0.2);
      border: 1px solid #ff446660;
      color: #ff7799;
      padding: 5px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 12px;
      font-weight: 600;
      flex-shrink: 0;
      transition: background 0.2s;
    }
    #ai-phishing-banner .b-close:hover { background: rgba(255,68,102,0.35); }
  `;
  document.head.appendChild(style);

  const banner = document.createElement('div');
  banner.id = 'ai-phishing-banner';
  banner.innerHTML = `
    <span class="b-icon">⛔</span>
    <div class="b-text">
      <div class="b-title">Phishing Website Detected!</div>
      <div class="b-sub">Risk: ${data.risk_level} &nbsp;|&nbsp; Confidence: ${(data.confidence?.phishing || 0).toFixed(1)}% &nbsp;|&nbsp; AI Phishing Detector</div>
    </div>
    <button class="b-close" id="ai-close-btn">Dismiss</button>
  `;
  document.body.prepend(banner);

  document.getElementById('ai-close-btn').onclick = () => {
    banner.style.animation = 'slideIn 0.25s ease reverse';
    setTimeout(() => banner.remove(), 250);
  };
  setTimeout(() => {
    if (banner.isConnected) {
      banner.style.animation = 'slideIn 0.25s ease reverse';
      setTimeout(() => banner.remove(), 250);
    }
  }, 12000);
}

// ── Desktop notification ──────────────────────────────────────
function showNotification(data) {
  chrome.notifications.create(`phish-${Date.now()}`, {
    type:               'basic',
    iconUrl:            'icon.png',
    title:              '⛔ Phishing Website Detected!',
    message:            `Risk: ${data.risk_level} | Confidence: ${(data.confidence?.phishing || 0).toFixed(1)}%`,
    priority:           2,
    requireInteraction: true
  });
}

// ── Message listener (from popup) ────────────────────────────
chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
  if (req.action === 'getResult') {
    const result = checkedUrls.get(req.url) || null;
    sendResponse(result);
  }
  return true;
});
