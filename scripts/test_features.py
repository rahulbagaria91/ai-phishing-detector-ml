import sys
sys.path.append('.')
from feature_extraction import extract_features_from_url
import pandas as pd

# Test URLs
test_urls = [
    "https://www.google.com",
    "https://www.w3schools.com",
    "http://suspicious-paypal-verify.tk/login",
]

print("Testing Feature Extraction:\n")
print("="*80)

for url in test_urls:
    print(f"\nURL: {url}")
    print("-"*80)
    features = extract_features_from_url(url)
    
    if features:
        # Show top important features
        important = [
            'URLSimilarityIndex', 'NoOfExternalRef', 'LineOfCode',
            'NoOfSelfRef', 'NoOfImage', 'NoOfJS', 'IsHTTPS',
            'HasSocialNet', 'IsDomainIP', 'URLLength'
        ]
        
        for feat in important:
            if feat in features:
                print(f"{feat:25s}: {features[feat]}")
    print("="*80)
