// Store checked URLs to avoid re-checking
const checkedUrls = new Map();
const CACHE_DURATION = 3600000; // 1 hour in milliseconds

// Listen for tab updates (when user navigates to new page)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Only check when page is completely loaded
  if (changeInfo.status === 'complete' && tab.url) {
    const url = tab.url;
    
    // Skip internal Chrome pages
    if (url.startsWith('chrome://') || 
        url.startsWith('chrome-extension://') ||
        url.startsWith('about:') ||
        url.startsWith('edge://')) {
      return;
    }
    
    // Check if URL was recently checked
    const cached = checkedUrls.get(url);
    if (cached && (Date.now() - cached.timestamp < CACHE_DURATION)) {
      // Use cached result
      if (!cached.is_safe) {
        showWarning(tabId, cached);
      }
      updateBadge(tabId, cached.is_safe);
      return;
    }
    
    // Check URL with API
    checkUrl(url, tabId);
  }
});

// Function to check URL with API
async function checkUrl(url, tabId) {
  try {
    const response = await fetch('http://localhost:5000/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url: url })
    });
    
    const data = await response.json();
    
    // Cache result
    checkedUrls.set(url, {
      ...data,
      timestamp: Date.now()
    });
    
    // Update badge
    updateBadge(tabId, data.is_safe);
    
    // Show warning if phishing detected
    if (!data.is_safe) {
      showWarning(tabId, data);
      showNotification(data);
    }
    
  } catch (error) {
    console.error('Error checking URL:', error);
    // If API is down, show neutral badge
    updateBadge(tabId, null);
  }
}

// Update extension badge (icon indicator)
function updateBadge(tabId, isSafe) {
  if (isSafe === true) {
    chrome.action.setBadgeText({ text: '✓', tabId: tabId });
    chrome.action.setBadgeBackgroundColor({ color: '#28a745', tabId: tabId });
  } else if (isSafe === false) {
    chrome.action.setBadgeText({ text: '!', tabId: tabId });
    chrome.action.setBadgeBackgroundColor({ color: '#dc3545', tabId: tabId });
  } else {
    chrome.action.setBadgeText({ text: '', tabId: tabId });
  }
}

// Show warning overlay on page
function showWarning(tabId, data) {
  chrome.scripting.executeScript({
    target: { tabId: tabId },
    func: displayWarningBanner,
    args: [data]
  });
}

// Function injected into page to show warning
function displayWarningBanner(data) {
  // Check if banner already exists
  if (document.getElementById('phishing-warning-banner')) {
    return;
  }
  
  // Create warning banner
  const banner = document.createElement('div');
  banner.id = 'phishing-warning-banner';
  banner.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 999999;
    background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%);
    color: white;
    padding: 15px 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    font-family: Arial, sans-serif;
    display: flex;
    align-items: center;
    justify-content: space-between;
    animation: slideDown 0.3s ease;
  `;
  
  banner.innerHTML = `
    <div style="display: flex; align-items: center; gap: 15px;">
      <div style="font-size: 28px;">⚠️</div>
      <div>
        <div style="font-weight: bold; font-size: 16px; margin-bottom: 5px;">
          🛡️ Phishing Warning!
        </div>
        <div style="font-size: 13px;">
          This website may be a phishing attempt. 
          Confidence: ${data.confidence.phishing.toFixed(1)}% | 
          Risk Level: ${data.risk_level}
        </div>
      </div>
    </div>
    <button id="close-warning-btn" style="
      background: white;
      color: #cc0000;
      border: none;
      padding: 8px 16px;
      border-radius: 5px;
      cursor: pointer;
      font-weight: bold;
      font-size: 14px;
    ">
      Dismiss
    </button>
  `;
  
  // Add animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideDown {
      from {
        transform: translateY(-100%);
        opacity: 0;
      }
      to {
        transform: translateY(0);
        opacity: 1;
      }
    }
  `;
  document.head.appendChild(style);
  
  // Insert banner at top of page
  document.body.insertBefore(banner, document.body.firstChild);
  
  // Close button functionality
  document.getElementById('close-warning-btn').addEventListener('click', () => {
    banner.style.animation = 'slideDown 0.3s ease reverse';
    setTimeout(() => banner.remove(), 300);
  });
  
  // Auto-hide after 10 seconds
  setTimeout(() => {
    if (banner.parentElement) {
      banner.style.animation = 'slideDown 0.3s ease reverse';
      setTimeout(() => banner.remove(), 300);
    }
  }, 10000);
}

// Show desktop notification
function showNotification(data) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icon.png',
    title: '⚠️ Phishing Website Detected!',
    message: `This website may be dangerous.\nRisk Level: ${data.risk_level}\nConfidence: ${data.confidence.phishing.toFixed(1)}%`,
    priority: 2,
    requireInteraction: true
  });
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getResult') {
    const result = checkedUrls.get(request.url);
    sendResponse(result || null);
  }
});
