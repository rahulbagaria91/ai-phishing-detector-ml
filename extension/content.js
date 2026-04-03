// AI Phishing Detector — Content Script
// Runs on every webpage — handles warning banners

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'ping') {
    sendResponse({ status: 'active' });
  }
});

// showWarningBanner function - called by background script
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
</xai:function_call name="edit_file">

<xai:function_call name="edit_file">
<parameter name="path">c:/4th year/new project/TODO.md
