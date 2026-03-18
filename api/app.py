from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
import sys
import os
from urllib.parse import urlparse
import re

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from feature_extraction import extract_features_from_url

app = Flask(__name__)
CORS(app)

# ── Load model ───────────────────────────────────────────────
print("Loading model components...")
BASE = os.path.join(os.path.dirname(__file__), '..', 'models')

try:
    with open(os.path.join(BASE, 'phishing_model_balanced.pkl'), 'rb') as f:
        model = pickle.load(f)
    with open(os.path.join(BASE, 'scaler.pkl'), 'rb') as f:
        scaler = pickle.load(f)
    with open(os.path.join(BASE, 'feature_names.pkl'), 'rb') as f:
        feature_names = pickle.load(f)
    print("✅ Balanced model loaded!")
except Exception as e:
    print(f"⚠️  Balanced model failed ({e}), trying original...")
    with open(os.path.join(BASE, 'phishing_model.pkl'), 'rb') as f:
        model = pickle.load(f)
    with open(os.path.join(BASE, 'feature_names.pkl'), 'rb') as f:
        feature_names = pickle.load(f)
    scaler = None
    print("✅ Original model loaded!")

# ── Trusted domains (exact match + subdomain match) ──────────
TRUSTED_DOMAINS = [
    'google.com', 'youtube.com', 'facebook.com', 'twitter.com',
    'instagram.com', 'amazon.com', 'microsoft.com', 'apple.com',
    'wikipedia.org', 'reddit.com', 'github.com', 'stackoverflow.com',
    'linkedin.com', 'w3schools.com', 'netflix.com', 'adobe.com',
    'paypal.com', 'ebay.com', 'yahoo.com',
    # Indian trusted domains
    'india.gov.in', 'indiapost.gov.in', 'mygov.in', 'uidai.gov.in',
    'incometax.gov.in', 'gst.gov.in', 'epfindia.gov.in',
    'sbi.co.in', 'onlinesbi.sbi', 'hdfcbank.com', 'icicibank.com',
    'flipkart.com', 'amazon.in', 'paytm.com', 'phonepe.com',
    'irctc.co.in', 'ndtv.com', 'timesofindia.com', 'moneycontrol.com',
]

# Trusted TLDs
TRUSTED_TLDS = ['.gov.in', '.nic.in', '.ac.in', '.edu.in', '.res.in', '.mil.in']

def is_trusted_domain(domain):
    """Exact match OR subdomain match — prevents bypass attacks"""
    domain = domain.lower().replace('www.', '')
    for trusted in TRUSTED_DOMAINS:
        if domain == trusted or domain.endswith('.' + trusted):
            return True
    return False

def get_risk_level(is_safe, conf_legit, conf_phish):
    if is_safe:
        if conf_legit >= 90: return 'Very Low'
        if conf_legit >= 70: return 'Low'
        return 'Medium'
    else:
        if conf_phish >= 85: return 'Very High'
        if conf_phish >= 65: return 'High'
        return 'Medium-High'

# ── Routes ───────────────────────────────────────────────────
@app.route('/')
def home():
    return jsonify({
        'status':  'running',
        'message': 'AI Phishing Detector API v3.0',
        'version': '3.0',
        'model':   str(type(model).__name__),
    })

@app.route('/health')
def health():
    return jsonify({
        'status':       'healthy',
        'model_loaded': True,
        'version':      '3.0'
    })

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json(silent=True) or {}
        url  = data.get('url', '').strip()

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Parse domain
        try:
            parsed     = urlparse(url)
            domain     = parsed.netloc.replace('www.', '').lower()
            has_https  = url.startswith('https://')
        except Exception:
            domain    = ''
            has_https = False

        # ── Level 1: Trusted domain whitelist ─────────────────
        if is_trusted_domain(domain):
            return jsonify({
                'url':        url,
                'prediction': 'Legitimate',
                'is_safe':    True,
                'confidence': {'phishing': 0.0, 'legitimate': 100.0},
                'risk_level': 'Very Low',
                'note':       'Trusted domain'
            })

        # ── Level 2: Trusted TLD + HTTPS ──────────────────────
        if has_https and any(domain.endswith(tld) for tld in TRUSTED_TLDS):
            return jsonify({
                'url':        url,
                'prediction': 'Legitimate',
                'is_safe':    True,
                'confidence': {'phishing': 4.0, 'legitimate': 96.0},
                'risk_level': 'Very Low',
                'note':       'Government/Educational domain'
            })

        # ── Level 3: ML model ──────────────────────────────────
        features = extract_features_from_url(url)
        if features is None:
            return jsonify({'error': 'Feature extraction failed'}), 500

        df = pd.DataFrame([features])
        # Align columns — fill missing with 0
        for col in feature_names:
            if col not in df.columns:
                df[col] = 0
        df = df[feature_names]

        if scaler:
            X = scaler.transform(df)
        else:
            X = df.values

        prob         = model.predict_proba(X)[0]
        prob_phish   = float(prob[0])
        prob_legit   = float(prob[1])

        is_safe      = prob_legit >= 0.50   # Standard 50% threshold
        conf_phish   = round(prob_phish * 100, 1)
        conf_legit   = round(prob_legit * 100, 1)
        risk_level   = get_risk_level(is_safe, conf_legit, conf_phish)

        return jsonify({
            'url':        url,
            'prediction': 'Legitimate' if is_safe else 'Phishing',
            'is_safe':    is_safe,
            'confidence': {
                'phishing':   conf_phish,
                'legitimate': conf_legit,
            },
            'risk_level': risk_level,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀  AI PHISHING DETECTOR API  v3.0")
    print("=" * 60)
    print(f"  Model   : {type(model).__name__}")
    print(f"  Features: {len(feature_names)}")
    print(f"  API     : http://localhost:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
