// Content script runs on every webpage
// Currently just listens for commands from background script
// Can be extended for additional page analysis

console.log('AI Phishing Detector: Active');

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'showWarning') {
    // Warning is injected by background.js
  }
});
