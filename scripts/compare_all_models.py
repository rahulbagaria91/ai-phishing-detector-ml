import pandas as pd
import numpy as np
import pickle
import os
import re
from urllib.parse import urlparse
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.ensemble import RandomForestClassifier

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except:
    HAS_XGB = False

print("=" * 70)
print("  MODEL COMPARISON - HAR DATASET PE ALAG TRAIN")
print("=" * 70)

FEATURES = [
    'URLLength','DomainLength','IsDomainIP','URLSimilarityIndex',
    'CharContinuationRate','TLDLegitimateProb','URLCharProb','TLDLength',
    'NoOfSubDomain','HasObfuscation','NoOfObfuscatedChar','ObfuscationRatio',
    'NoOfLettersInURL','LetterRatioInURL','NoOfDegitsInURL','DegitRatioInURL',
    'NoOfEqualsInURL','NoOfQMarkInURL','NoOfAmpersandInURL',
    'NoOfOtherSpecialCharsInURL','SpacialCharRatioInURL','IsHTTPS',
    'LineOfCode','LargestLineLength','HasTitle','DomainTitleMatchScore',
    'URLTitleMatchScore','HasFavicon','Robots','IsResponsive',
    'NoOfURLRedirect','NoOfSelfRedirect','HasDescription','NoOfPopup',
    'NoOfiFrame','HasExternalFormSubmit','HasSocialNet','HasSubmitButton',
    'HasHiddenFields','HasPasswordField','Bank','Pay','Crypto',
    'HasCopyrightInfo','NoOfImage','NoOfCSS','NoOfJS',
    'NoOfSelfRef','NoOfEmptyRef','NoOfExternalRef'
]

def url_to_features(url):
    f = {feat: 0 for feat in FEATURES}
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        tld = domain.split('.')[-1].lower() if '.' in domain else ''
        f['URLLength']    = len(url)
        f['DomainLength'] = len(domain)
        f['IsDomainIP']   = 1 if re.match(r'^\d+\.\d+\.\d+\.\d+$', domain) else 0
        brands = ['paypal','google','facebook','amazon','apple','microsoft',
                  'netflix','bank','secure','update','verify','login','signin']
        f['URLSimilarityIndex'] = min(sum(b in url.lower() for b in brands)*15, 100)
        cont = sum(1 for i in range(1, len(url)) if url[i] == url[i-1])
        f['CharContinuationRate'] = round(cont / max(len(url), 1), 4)
        legit = {'com':0.8,'org':0.75,'net':0.7,'edu':0.9,'gov':0.95,'in':0.7}
        risky = {'tk':0.1,'ml':0.1,'ga':0.1,'cf':0.1,'xyz':0.2,'top':0.2}
        f['TLDLegitimateProb'] = legit.get(tld, risky.get(tld, 0.4))
        alphanum = sum(c.isalnum() for c in url)
        f['URLCharProb']  = round(alphanum / max(len(url), 1), 4)
        f['TLDLength']    = len(tld)
        parts = domain.split('.')
        f['NoOfSubDomain'] = max(len(parts) - 2, 0)
        f['HasObfuscation']     = 1 if ('@' in url or '%' in url) else 0
        f['NoOfObfuscatedChar'] = url.count('%')
        f['ObfuscationRatio']   = round(f['NoOfObfuscatedChar'] / max(len(url), 1), 4)
        letters = sum(c.isalpha() for c in url)
        digits  = sum(c.isdigit() for c in url)
        f['NoOfLettersInURL']  = letters
        f['LetterRatioInURL']  = round(letters / max(len(url), 1), 4)
        f['NoOfDegitsInURL']   = digits
        f['DegitRatioInURL']   = round(digits / max(len(url), 1), 4)
        f['NoOfEqualsInURL']    = url.count('=')
        f['NoOfQMarkInURL']     = url.count('?')
        f['NoOfAmpersandInURL'] = url.count('&')
        special = sum(c in '!#$^*()[]{}|<>,~`\'"' for c in url)
        f['NoOfOtherSpecialCharsInURL'] = special
        total_sp = f['NoOfEqualsInURL']+f['NoOfQMarkInURL']+f['NoOfAmpersandInURL']+special
        f['SpacialCharRatioInURL'] = round(total_sp / max(len(url), 1), 4)
        f['IsHTTPS'] = 1 if url.startswith('https://') else 0
        url_lower = url.lower()
        f['Bank']   = 1 if any(w in url_lower for w in ['bank','sbi','hdfc']) else 0
        f['Pay']    = 1 if any(w in url_lower for w in ['pay','payment','paypal']) else 0
        f['Crypto'] = 1 if any(w in url_lower for w in ['crypto','bitcoin','wallet']) else 0
    except:
        pass
    return f

def to_label(val):
    val = str(val).strip().lower()
    if val in ['1', 'legitimate', 'good', 'benign']:
        return 1
    return 0

def train_and_evaluate(df, avail, dataset_name):
    """Ek dataset pe dono models train karo aur compare karo"""
    print(f"\n{'─'*70}")
    print(f"Dataset: {dataset_name}  ({len(df):,} rows)")
    print(f"{'─'*70}")

    X = df[avail]
    y = df['label']

    if len(y.unique()) < 2:
        print("  ⚠️  Sirf ek class hai — skip!")
        return None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    scaler     = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    results = {}

    # ── Random Forest ────────────────────────────────────────
    print("  Random Forest train ho raha hai...")
    rf = RandomForestClassifier(
        n_estimators=100, max_depth=12, min_samples_split=50,
        min_samples_leaf=20, class_weight='balanced',
        random_state=42, n_jobs=-1
    )
    rf.fit(X_train_sc, y_train)
    rf_pred = rf.predict(X_test_sc)
    results['Random Forest'] = {
        'accuracy':  round(accuracy_score(y_test, rf_pred)*100, 2),
        'precision': round(precision_score(y_test, rf_pred, zero_division=0)*100, 2),
        'recall':    round(recall_score(y_test, rf_pred, zero_division=0)*100, 2),
        'f1':        round(f1_score(y_test, rf_pred, zero_division=0)*100, 2),
        'model':     rf,
        'scaler':    scaler,
    }
    print(f"  RF Accuracy: {results['Random Forest']['accuracy']}%")

    # ── XGBoost ──────────────────────────────────────────────
    if HAS_XGB:
        print("  XGBoost train ho raha hai...")
        xgb = XGBClassifier(
            n_estimators=100, max_depth=8, learning_rate=0.1,
            random_state=42, n_jobs=-1, eval_metric='logloss', verbosity=0
        )
        xgb.fit(X_train_sc, y_train)
        xgb_pred = xgb.predict(X_test_sc)
        results['XGBoost'] = {
            'accuracy':  round(accuracy_score(y_test, xgb_pred)*100, 2),
            'precision': round(precision_score(y_test, xgb_pred, zero_division=0)*100, 2),
            'recall':    round(recall_score(y_test, xgb_pred, zero_division=0)*100, 2),
            'f1':        round(f1_score(y_test, xgb_pred, zero_division=0)*100, 2),
            'model':     xgb,
            'scaler':    scaler,
        }
        print(f"  XGB Accuracy: {results['XGBoost']['accuracy']}%")

    return results

# ════════════════════════════════════════════════════════════
# Saare datasets load karo
# ════════════════════════════════════════════════════════════
print("\nSaare datasets load ho rahe hain...")

df_orig = pd.read_csv('../dataset/PhiUSIIL_Phishing_URL_Dataset.csv')
avail   = [c for c in FEATURES if c in df_orig.columns]
df_orig_clean = df_orig[avail + ['label']].copy()
df_orig_clean['label'] = df_orig_clean['label'].apply(to_label)

url_files = [
    ('data.csv',                              'url', 'label'),
    ('dataset_phishing.csv',                  'url', 'status'),
    ('dataset_with_all_features v2.csv',      'url', 'type'),
    ('final_dataset_with_all_features_v3.1.csv','url','type'),
    ('malicious_phish.csv',                   'url', 'type'),
    ('phishing_url_dataset_unique.csv',       'url', 'label'),
]

loaded = {'PhiUSIIL (Original)': df_orig_clean}

for fname, url_col, lbl_col in url_files:
    fpath = f'../dataset/{fname}'
    if not os.path.exists(fpath):
        continue
    print(f"  Loading {fname}...")
    df_raw = pd.read_csv(fpath)
    rows = []
    for i, row in df_raw.iterrows():
        feat = url_to_features(str(row[url_col]))
        feat['label'] = to_label(row[lbl_col])
        rows.append(feat)
    df_new = pd.DataFrame(rows)[avail + ['label']]
    loaded[fname.replace('.csv','')] = df_new
    print(f"  {fname}: {len(df_new):,} rows ✅")

# ════════════════════════════════════════════════════════════
# Har dataset pe train karo
# ════════════════════════════════════════════════════════════
all_results = {}
best_model_info = {'accuracy': 0}

for ds_name, df in loaded.items():
    res = train_and_evaluate(df.fillna(0), avail, ds_name)
    if res:
        all_results[ds_name] = res
        for algo, metrics in res.items():
            if metrics['accuracy'] > best_model_info['accuracy']:
                best_model_info = {
                    'accuracy': metrics['accuracy'],
                    'algo':     algo,
                    'dataset':  ds_name,
                    'model':    metrics['model'],
                    'scaler':   metrics['scaler'],
                }

# ════════════════════════════════════════════════════════════
# Final comparison table
# ════════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print("  FINAL COMPARISON TABLE")
print(f"{'='*70}")
print(f"{'Dataset':<40} {'Algorithm':<15} {'Accuracy':>9} {'F1':>8}")
print(f"{'─'*70}")
for ds_name, res in all_results.items():
    for algo, metrics in res.items():
        marker = " ⭐" if (ds_name == best_model_info['dataset'] and algo == best_model_info['algo']) else ""
        print(f"{ds_name[:38]:<40} {algo:<15} {metrics['accuracy']:>8}% {metrics['f1']:>7}%{marker}")

print(f"\n  WINNER: {best_model_info['algo']} on {best_model_info['dataset']}")
print(f"  BEST ACCURACY: {best_model_info['accuracy']}%")

# ── Best model save karo ─────────────────────────────────────
os.makedirs('../models', exist_ok=True)
with open('../models/phishing_model_balanced.pkl', 'wb') as f:
    pickle.dump(best_model_info['model'], f)
with open('../models/scaler.pkl', 'wb') as f:
    pickle.dump(best_model_info['scaler'], f)
with open('../models/feature_names.pkl', 'wb') as f:
    pickle.dump(avail, f)

print(f"\n  Best model save ho gaya!")
print(f"  Ab: cd ..\\api  -->  python app.py")
print(f"{'='*70}")