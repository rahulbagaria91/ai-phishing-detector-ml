import pandas as pd
import numpy as np
import pickle
import os
import re
from urllib.parse import urlparse
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

print("=" * 65)
print("  MEGA DATASET - URL FEATURES ONLY (MAX ACCURACY)")
print("=" * 65)

# Sirf URL se nikalne wale features — saare datasets mein hain
URL_FEATURES = [
    'URLLength', 'DomainLength', 'IsDomainIP', 'IsHTTPS',
    'NoOfSubDomain', 'TLDLength', 'TLDLegitimateProb',
    'URLSimilarityIndex', 'CharContinuationRate', 'URLCharProb',
    'HasObfuscation', 'NoOfObfuscatedChar', 'ObfuscationRatio',
    'NoOfLettersInURL', 'LetterRatioInURL',
    'NoOfDegitsInURL', 'DegitRatioInURL',
    'NoOfEqualsInURL', 'NoOfQMarkInURL', 'NoOfAmpersandInURL',
    'NoOfOtherSpecialCharsInURL', 'SpacialCharRatioInURL',
    'Bank', 'Pay', 'Crypto'
]

def url_to_features(url):
    f = {feat: 0 for feat in URL_FEATURES}
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        parsed  = urlparse(url)
        domain  = parsed.netloc.replace('www.', '')
        tld     = domain.split('.')[-1].lower() if '.' in domain else ''

        f['URLLength']    = len(url)
        f['DomainLength'] = len(domain)
        f['IsDomainIP']   = 1 if re.match(r'^\d+\.\d+\.\d+\.\d+$', domain) else 0
        f['IsHTTPS']      = 1 if url.startswith('https://') else 0
        f['TLDLength']    = len(tld)

        parts = domain.split('.')
        f['NoOfSubDomain'] = max(len(parts) - 2, 0)

        brands = ['paypal','google','facebook','amazon','apple','microsoft',
                  'netflix','bank','secure','update','verify','login','signin',
                  'account','password','ebay','chase','wellsfargo']
        f['URLSimilarityIndex'] = min(sum(b in url.lower() for b in brands)*10, 100)

        cont = sum(1 for i in range(1, len(url)) if url[i] == url[i-1])
        f['CharContinuationRate'] = round(cont / max(len(url), 1), 4)

        legit = {'com':0.8,'org':0.75,'net':0.7,'edu':0.9,'gov':0.95,
                 'in':0.7,'co':0.65,'io':0.6,'uk':0.72,'au':0.72}
        risky = {'tk':0.05,'ml':0.05,'ga':0.05,'cf':0.05,'gq':0.05,
                 'xyz':0.15,'top':0.15,'click':0.1,'pw':0.1,'cc':0.2}
        f['TLDLegitimateProb'] = legit.get(tld, risky.get(tld, 0.35))

        alphanum = sum(c.isalnum() for c in url)
        f['URLCharProb'] = round(alphanum / max(len(url), 1), 4)

        f['HasObfuscation']     = 1 if ('@' in url or '%' in url or '0x' in url.lower()) else 0
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
        total_sp = (f['NoOfEqualsInURL'] + f['NoOfQMarkInURL'] +
                    f['NoOfAmpersandInURL'] + special)
        f['SpacialCharRatioInURL'] = round(total_sp / max(len(url), 1), 4)

        url_lower = url.lower()
        f['Bank']   = 1 if any(w in url_lower for w in
                               ['bank','banking','sbi','hdfc','icici','axis']) else 0
        f['Pay']    = 1 if any(w in url_lower for w in
                               ['pay','payment','paypal','paytm','gpay']) else 0
        f['Crypto'] = 1 if any(w in url_lower for w in
                               ['crypto','bitcoin','btc','wallet','ethereum','eth']) else 0
    except:
        pass
    return f

def to_label(val):
    val = str(val).strip().lower()
    if val in ['1', 'legitimate', 'good', 'benign']:
        return 1
    return 0

# ════════════════════════════════════════════════════════════
# 1. Original dataset — URL column se features nikalo
# ════════════════════════════════════════════════════════════
print("\n[1/7] PhiUSIIL original dataset...")
df_orig = pd.read_csv('../dataset/PhiUSIIL_Phishing_URL_Dataset.csv')

# Original dataset mein URL column se fresh features nikalo
rows = []
for i, row in df_orig.iterrows():
    if i % 50000 == 0:
        print(f"      {i:,}/{len(df_orig):,}...")
    feat = url_to_features(str(row.get('URL', '')))
    feat['label'] = to_label(row['label'])
    rows.append(feat)
df1 = pd.DataFrame(rows)
print(f"      {len(df1):,} rows ✅")

# ── Baaki datasets ───────────────────────────────────────────
url_files = [
    ('[2/7] data.csv',                             'data.csv',                              'url',  'label'),
    ('[3/7] dataset_phishing.csv',                 'dataset_phishing.csv',                  'url',  'status'),
    ('[4/7] dataset_with_all_features v2',         'dataset_with_all_features v2.csv',      'url',  'type'),
    ('[5/7] final_dataset_v3.1',                   'final_dataset_with_all_features_v3.1.csv','url','type'),
    ('[6/7] malicious_phish',                      'malicious_phish.csv',                   'url',  'type'),
    ('[7/7] phishing_url_unique',                  'phishing_url_dataset_unique.csv',        'url',  'label'),
]

all_dfs = [df1]

for tag, fname, url_col, lbl_col in url_files:
    fpath = f'../dataset/{fname}'
    if not os.path.exists(fpath):
        print(f"\n{tag} - NAHI MILI, SKIP")
        continue
    print(f"\n{tag}...")
    df_raw = pd.read_csv(fpath)
    rows = []
    for i, row in df_raw.iterrows():
        if i % 50000 == 0:
            print(f"      {i:,}/{len(df_raw):,}...")
        feat = url_to_features(str(row[url_col]))
        feat['label'] = to_label(row[lbl_col])
        rows.append(feat)
    df_new = pd.DataFrame(rows)
    all_dfs.append(df_new)
    print(f"      {len(df_new):,} rows ✅")

# ── Merge ────────────────────────────────────────────────────
print("\nSab merge ho rahe hain...")
df_combined = pd.concat(all_dfs, ignore_index=True)
before = len(df_combined)
df_combined = df_combined.drop_duplicates(subset=URL_FEATURES)
df_combined = df_combined.fillna(0)
after = len(df_combined)

print(f"\n{'='*65}")
print(f"  Total (before dedup) : {before:,}")
print(f"  Duplicates removed   : {before - after:,}")
print(f"  FINAL TOTAL          : {after:,} URLs!")
print(f"  Legitimate           : {(df_combined['label']==1).sum():,}")
print(f"  Phishing             : {(df_combined['label']==0).sum():,}")
print(f"{'='*65}")

# ── Train ────────────────────────────────────────────────────
print("\nModel train ho raha hai...")
X = df_combined[URL_FEATURES]
y = df_combined['label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Training: {len(X_train):,}  |  Testing: {len(X_test):,}")

scaler     = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

# Random Forest
from sklearn.ensemble import RandomForestClassifier
print("\nRandom Forest train ho raha hai...")
rf = RandomForestClassifier(
    n_estimators=200, max_depth=15,
    min_samples_split=30, min_samples_leaf=10,
    class_weight='balanced', random_state=42, n_jobs=-1
)
rf.fit(X_train_sc, y_train)
rf_acc = accuracy_score(y_test, rf.predict(X_test_sc))
rf_f1  = f1_score(y_test, rf.predict(X_test_sc))
print(f"Random Forest - Accuracy: {rf_acc*100:.2f}%  F1: {rf_f1*100:.2f}%")

# XGBoost
best_model  = rf
best_acc    = rf_acc
best_algo   = "Random Forest"

try:
    from xgboost import XGBClassifier
    print("\nXGBoost train ho raha hai...")
    xgb = XGBClassifier(
        n_estimators=200, max_depth=8, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8,
        random_state=42, n_jobs=-1,
        eval_metric='logloss', verbosity=0
    )
    xgb.fit(X_train_sc, y_train)
    xgb_acc = accuracy_score(y_test, xgb.predict(X_test_sc))
    xgb_f1  = f1_score(y_test, xgb.predict(X_test_sc))
    print(f"XGBoost       - Accuracy: {xgb_acc*100:.2f}%  F1: {xgb_f1*100:.2f}%")
    if xgb_acc > best_acc:
        best_model = xgb
        best_acc   = xgb_acc
        best_algo  = "XGBoost"
except ImportError:
    print("XGBoost nahi mila")

# ── Save ─────────────────────────────────────────────────────
os.makedirs('../models', exist_ok=True)
with open('../models/phishing_model_balanced.pkl', 'wb') as f:
    pickle.dump(best_model, f)
with open('../models/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
with open('../models/feature_names.pkl', 'wb') as f:
    pickle.dump(URL_FEATURES, f)

print(f"\n{'='*65}")
print(f"  COMPLETE!")
print(f"  Algorithm : {best_algo}")
print(f"  Accuracy  : {best_acc*100:.2f}%")
print(f"  Dataset   : {after:,} URLs")
print(f"  Ab: cd ..\\api  -->  python app.py")
print(f"{'='*65}")