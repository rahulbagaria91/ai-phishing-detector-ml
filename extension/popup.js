// Check if we have a cached result when popup opens
window.addEventListener('DOMContentLoaded', function() {
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    const currentUrl = tabs[0].url;
    
    // Ask background script for cached result
    chrome.runtime.sendMessage(
      { action: 'getResult', url: currentUrl },
      function(result) {
        if (result) {
          displayResult(result);
        }
      }
    );
  });
});

document.getElementById('checkBtn').addEventListener('click', function() {
  const button = document.getElementById('checkBtn');
  const loading = document.getElementById('loading');
  const resultDiv = document.getElementById('result');
  
  button.disabled = true;
  loading.style.display = 'block';
  resultDiv.style.display = 'none';
  
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    const currentUrl = tabs[0].url;
    
    // Skip chrome:// URLs
    if (currentUrl.startsWith('chrome://') || 
        currentUrl.startsWith('chrome-extension://')) {
      loading.style.display = 'none';
      button.disabled = false;
      resultDiv.innerHTML = `
        <div class="result-title">
          <span class="result-icon">ℹ️</span>
          Cannot Check
        </div>
        <p>Internal browser pages cannot be checked.</p>
      `;
      resultDiv.className = '';
      resultDiv.style.display = 'block';
      return;
    }
    
    fetch('http://localhost:5000/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({url: currentUrl})
    })
    .then(response => response.json())
    .then(data => {
      loading.style.display = 'none';
      button.disabled = false;
      displayResult(data);
    })
    .catch(error => {
      loading.style.display = 'none';
      button.disabled = false;
      
      resultDiv.innerHTML = `
        <div class="result-title">
          <span class="result-icon">⚠️</span>
          Error
        </div>
        <p>Could not connect to detection service. Make sure the API is running at localhost:5000</p>
      `;
      resultDiv.className = 'danger';
      resultDiv.style.display = 'block';
    });
  });
});

function displayResult(data) {
  const resultDiv = document.getElementById('result');
  const isSafe = data.is_safe;
  const confidence = isSafe ? data.confidence.legitimate : data.confidence.phishing;
  
  const icon = isSafe ? '✅' : '⚠️';
  const statusText = isSafe ? 'Safe Website' : 'Phishing Detected!';
  const message = isSafe 
    ? 'This website appears to be legitimate and safe to use.' 
    : 'This website may be a phishing attempt. Exercise extreme caution!';
  
  resultDiv.innerHTML = `
    <div class="result-title">
      <span class="result-icon">${icon}</span>
      ${statusText}
    </div>
    <p>${message}</p>
    <div class="result-details">
      <strong>Risk Level:</strong> ${data.risk_level}<br>
      <strong>Confidence:</strong> ${confidence.toFixed(1)}%
      <div class="confidence-bar">
        <div class="confidence-fill" style="width: ${confidence}%; background: ${isSafe ? '#28a745' : '#dc3545'}">
          ${confidence.toFixed(0)}%
        </div>
      </div>
    </div>
    <div class="url-display">
      <strong>Checked URL:</strong><br>${data.url}
    </div>
    ${data.note ? `<div style="margin-top: 10px; font-size: 12px; color: #666;"><em>Note: ${data.note}</em></div>` : ''}
  `;
  
  resultDiv.className = isSafe ? 'safe' : 'danger';
  resultDiv.style.display = 'block';
}
