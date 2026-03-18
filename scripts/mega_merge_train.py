import pandas as pd
import numpy as np
import pickle
import os
import re
from urllib.parse import urlparse
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

print("=" * 60)
print("  MEGA MERGE - SAARE DATASETS EK SAATH")
print("=" * 60)

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
        f['NoOfEqualsInURL']   = url.count('=')
        f['NoOfQMarkInURL']    = url.count('?')
        f['NoOfAmpersandInURL']= url.count('&')

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

# ── 1. Original dataset (features pehle se hain) ────────────
print("\n[1/7] PhiUSIIL original dataset...")
df_orig = pd.read_csv('../dataset/PhiUSIIL_Phishing_URL_Dataset.csv')
avail   = [c for c in FEATURES if c in df_orig.columns]
df1     = df_orig[avail + ['label']].copy()
df1['label'] = df1['label'].apply(to_label)
print(f"      {len(df1):,} rows ✅")

# ── 2-7. Baaki datasets (URL se features nikalo) ────────────
url_datasets = [
    ('[2/7] data.csv',                              'data.csv',                             'url', 'label'),
    ('[3/7] dataset_phishing.csv',                  'dataset_phishing.csv',                 'url', 'status'),
    ('[4/7] dataset_with_all_features v2.csv',      'dataset_with_all_features v2.csv',     'url', 'type'),
    ('[5/7] final_dataset_with_all_features_v3.1',  'final_dataset_with_all_features_v3.1.csv', 'url', 'type'),
    ('[6/7] malicious_phish.csv',                   'malicious_phish.csv',                  'url', 'type'),
    ('[7/7] phishing_url_dataset_unique.csv',       'phishing_url_dataset_unique.csv',      'url', 'label'),
]

all_dfs = [df1]

for label_name, fname, url_col, lbl_col in url_datasets:
    fpath = f'../dataset/{fname}'
    if not os.path.exists(fpath):
        print(f"\n{label_name} - FILE NAHI MILI, SKIP!")
        continue
    print(f"\n{label_name} - features nikal rahe hain...")
    df_raw = pd.read_csv(fpath)
    rows = []
    for i, row in df_raw.iterrows():
        if i % 50000 == 0:
            print(f"      {i:,}/{len(df_raw):,}...")
        feat = url_to_features(str(row[url_col]))
        feat['label'] = to_label(row[lbl_col])
        rows.append(feat)
    df_new = pd.DataFrame(rows)[avail + ['label']]
    all_dfs.append(df_new)
    print(f"      {len(df_new):,} rows ✅")

# ── Merge + deduplicate ──────────────────────────────────────
print("\nSab merge ho rahe hain...")
df_combined = pd.concat(all_dfs, ignore_index=True)
before = len(df_combined)
df_combined = df_combined.drop_duplicates()
df_combined = df_combined.fillna(0)
after = len(df_combined)

print(f"\n{'='*60}")
print(f"TOTAL (before dedup) : {before:,}")
print(f"Duplicates removed   : {before - after:,}")
print(f"FINAL TOTAL          : {after:,}  URLS!")
print(f"Legitimate           : {(df_combined['label']==1).sum():,}")
print(f"Phishing             : {(df_combined['label']==0).sum():,}")
print(f"{'='*60}")

# ── Train ────────────────────────────────────────────────────
print("\nModel train ho raha hai... (~10-15 min)")
X = df_combined[avail]
y = df_combined['label']
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Training: {len(X_train):,}  Testing: {len(X_test):,}")

scaler     = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

try:
    from xgboost import XGBClassifier
    print("XGBoost use ho raha hai...")
    model = XGBClassifier(
        n_estimators=100, max_depth=8, learning_rate=0.1,
        random_state=42, n_jobs=-1, eval_metric='logloss', verbosity=0
    )
    algo = "XGBoost"
except ImportError:
    from sklearn.ensemble import RandomForestClassifier
    print("Random Forest use ho raha hai...")
    model = RandomForestClassifier(
        n_estimators=100, max_depth=12, min_samples_split=50,
        min_samples_leaf=20, class_weight='balanced', random_state=42, n_jobs=-1
    )
    algo = "Random Forest"

model.fit(X_train_sc, y_train)
acc = accuracy_score(y_test, model.predict(X_test_sc))

# ── Save ─────────────────────────────────────────────────────
os.makedirs('../models', exist_ok=True)
with open('../models/phishing_model_balanced.pkl', 'wb') as f:
    pickle.dump(model, f)
with open('../models/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
with open('../models/feature_names.pkl', 'wb') as f:
    pickle.dump(avail, f)

print(f"\n{'='*60}")
print(f"  COMPLETE!")
print(f"  Algorithm : {algo}")
print(f"  Accuracy  : {acc*100:.2f}%")
print(f"  Dataset   : {after:,} URLs")
print(f"  Ab API restart karo:")
print(f"  cd ..\\api  -->  python app.py")
print(f"{'='*60}")