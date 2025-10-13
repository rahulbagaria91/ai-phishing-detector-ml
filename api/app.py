from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
import sys
import os
from urllib.parse import urlparse

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from feature_extraction import extract_features_from_url

app = Flask(__name__)
CORS(app)

# Load model components
print("Loading model components...")
base_path = os.path.join(os.path.dirname(__file__), '..', 'models')

try:
    with open(os.path.join(base_path, 'phishing_model_balanced.pkl'), 'rb') as f:
        model = pickle.load(f)
    with open(os.path.join(base_path, 'scaler.pkl'), 'rb') as f:
        scaler = pickle.load(f)
    with open(os.path.join(base_path, 'feature_names.pkl'), 'rb') as f:
        feature_names = pickle.load(f)
except:
    # Fallback to original model
    with open(os.path.join(base_path, 'phishing_model.pkl'), 'rb') as f:
        model = pickle.load(f)
    with open(os.path.join(base_path, 'feature_names.pkl'), 'rb') as f:
        feature_names = pickle.load(f)
    scaler = None

print("✅ Model loaded successfully!")

# Extended whitelist
TRUSTED_DOMAINS = [
    'google.com', 'youtube.com', 'facebook.com', 'twitter.com', 'instagram.com',
    'amazon.com', 'microsoft.com', 'apple.com', 'wikipedia.org', 'reddit.com',
    'github.com', 'stackoverflow.com', 'linkedin.com', 'w3schools.com',
    'netflix.com', 'adobe.com', 'paypal.com', 'ebay.com', 'yahoo.com',
    'gov.in', 'nic.in', 'india.gov.in', 'indiapost.gov.in', 'mygov.in',
    'uidai.gov.in', 'incometax.gov.in', 'gst.gov.in', 'epfindia.gov.in',
    'sbi.co.in', 'onlinesbi.sbi', 'hdfcbank.com', 'icicibank.com',
    'flipkart.com', 'amazon.in', 'paytm.com', 'phonepe.com',
    'irctc.co.in', 'moneycontrol.com', 'ndtv.com', 'timesofindia.com'
]

# Trusted TLDs
TRUSTED_TLDS = ['.gov.in', '.nic.in', '.ac.in', '.edu.in', '.res.in', '.mil.in']

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'message': 'AI-Powered Phishing Detector API v2.1',
        'version': '2.1',
        'features': ['Whitelist', 'Government domain trust', 'Adjusted threshold']
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'model_loaded': True})

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        # Parse domain
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            has_https = url.startswith('https://')
        except:
            domain = ''
            has_https = False
        
        # Check 1: Trusted domain whitelist
        is_whitelisted = any(trusted in domain.lower() for trusted in TRUSTED_DOMAINS)
        
        if is_whitelisted:
            return jsonify({
                'url': url,
                'prediction': 'Legitimate',
                'is_safe': True,
                'confidence': {'phishing': 0.0, 'legitimate': 100.0},
                'risk_level': 'Very Low',
                'note': 'Trusted domain'
            })
        
        # Check 2: Government/Educational TLD
        is_trusted_tld = any(tld in domain.lower() for tld in TRUSTED_TLDS)
        
        if is_trusted_tld and has_https:
            return jsonify({
                'url': url,
                'prediction': 'Legitimate',
                'is_safe': True,
                'confidence': {'phishing': 5.0, 'legitimate': 95.0},
                'risk_level': 'Very Low',
                'note': 'Government/Educational domain'
            })
        
        # Extract features
        features = extract_features_from_url(url)
        
        if features is None:
            return jsonify({'error': 'Failed to extract features'}), 500
        
        # Prepare features
        feature_df = pd.DataFrame([features])
        feature_df = feature_df[feature_names]
        
        # Scale if scaler exists
        if scaler:
            feature_scaled = scaler.transform(feature_df)
        else:
            feature_scaled = feature_df
        
        # Get prediction probabilities
        probability = model.predict_proba(feature_scaled)[0]
        
        # Adjust probabilities based on domain characteristics
        prob_phishing = float(probability[0])
        prob_legitimate = float(probability[1])
        
        # Boost legitimate score for certain indicators
        boost_score = 0
        
        if has_https:
            boost_score += 0.15  # HTTPS adds 15% to legitimate
        
        if not features.get('IsDomainIP', 0):  # Not an IP address
            boost_score += 0.1  # Add 10%
        
        if '.co.in' in domain or '.org.in' in domain or '.net.in' in domain:
            boost_score += 0.1  # Indian domains get 10% boost
        
        if features.get('HasSocialNet', 0) == 1:
            boost_score += 0.05  # Has social links, +5%
        
        # Apply boost
        prob_legitimate = min(prob_legitimate + boost_score, 0.95)
        prob_phishing = 1.0 - prob_legitimate
        
        # Decision with adjusted threshold (0.4 instead of 0.5)
        # If legitimate probability > 40%, consider it safe
        is_safe = prob_legitimate > 0.4
        
        confidence_phishing = round(prob_phishing * 100, 1)
        confidence_legitimate = round(prob_legitimate * 100, 1)
        
        # Risk level
        if is_safe:
            if confidence_legitimate > 80:
                risk_level = 'Very Low'
            elif confidence_legitimate > 60:
                risk_level = 'Low'
            else:
                risk_level = 'Medium'
        else:
            if confidence_phishing > 80:
                risk_level = 'Very High'
            elif confidence_phishing > 60:
                risk_level = 'High'
            else:
                risk_level = 'Medium-High'
        
        result = {
            'url': url,
            'prediction': 'Legitimate' if is_safe else 'Phishing',
            'is_safe': is_safe,
            'confidence': {
                'phishing': confidence_phishing,
                'legitimate': confidence_legitimate
            },
            'risk_level': risk_level
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 PHISHING DETECTOR API v2.1")
    print("="*70)
    print("Features:")
    print("  ✓ Extended whitelist")
    print("  ✓ Government domain trust")
    print("  ✓ Adjusted decision threshold")
    print("  ✓ Indian domain boost")
    print("="*70)
    print("API: http://localhost:5000")
    print("="*70 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
