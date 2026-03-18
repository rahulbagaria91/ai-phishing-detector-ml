// AI Phishing Detector — Content Script
// Runs on every webpage — listens for background messages

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'ping') {
    sendResponse({ status: 'active' });
  }
});
