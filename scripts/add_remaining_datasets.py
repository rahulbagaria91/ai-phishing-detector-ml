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
print("BAAKI 2 DATASETS ADD HO RAHE HAIN")
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

def url_se_features(url):
    f = {}
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        tld = domain.split('.')[-1] if '.' in domain else ''

        f['URLLength'] = len(url)
        f['DomainLength'] = len(domain)
        f['IsDomainIP'] = 1 if re.match(r'^\d+\.\d+\.\d+\.\d+$', domain) else 0
        brands = ['paypal','google','facebook','amazon','apple','microsoft',
                  'netflix','bank','secure','update','verify','login','signin']
        f['URLSimilarityIndex'] = min(sum(b in url.lower() for b in brands)*15, 100)
        cont = sum(1 for i in range(1, len(url)) if url[i] == url[i-1])
        f['CharContinuationRate'] = cont / max(len(url), 1)
        legit = {'com':0.8,'org':0.75,'net':0.7,'edu':0.9,'gov':0.95,'in':0.7}
        risky = {'tk':0.1,'ml':0.1,'ga':0.1,'cf':0.1,'xyz':0.2,'top':0.2}
        f['TLDLegitimateProb'] = legit.get(tld, risky.get(tld, 0.4))
        alphanum = sum(c.isalnum() for c in url)
        f['URLCharProb'] = alphanum / max(len(url), 1)
        f['TLDLength'] = len(tld)
        parts = domain.split('.')
        f['NoOfSubDomain'] = max(len(parts)-2, 0)
        f['HasObfuscation'] = 1 if ('@' in url or '%' in url) else 0
        f['NoOfObfuscatedChar'] = url.count('%')
        f['ObfuscationRatio'] = f['NoOfObfuscatedChar'] / max(len(url), 1)
        letters = sum(c.isalpha() for c in url)
        digits = sum(c.isdigit() for c in url)
        f['NoOfLettersInURL'] = letters
        f['LetterRatioInURL'] = letters / max(len(url), 1)
        f['NoOfDegitsInURL'] = digits
        f['DegitRatioInURL'] = digits / max(len(url), 1)
        f['NoOfEqualsInURL'] = url.count('=')
        f['NoOfQMarkInURL'] = url.count('?')
        f['NoOfAmpersandInURL'] = url.count('&')
        special = sum(c in '!#$^*()[]{}|<>,~`\'"' for c in url)
        f['NoOfOtherSpecialCharsInURL'] = special
        total_sp = f['NoOfEqualsInURL']+f['NoOfQMarkInURL']+f['NoOfAmpersandInURL']+special
        f['SpacialCharRatioInURL'] = total_sp / max(len(url), 1)
        f['IsHTTPS'] = 1 if url.startswith('https://') else 0
        url_lower = url.lower()
        f['Bank'] = 1 if any(w in url_lower for w in ['bank','sbi','hdfc']) else 0
        f['Pay']  = 1 if any(w in url_lower for w in ['pay','payment','paypal']) else 0
        f['Crypto'] = 1 if any(w in url_lower for w in ['crypto','bitcoin','wallet']) else 0
        for feat in FEATURES:
            if feat not in f:
                f[feat] = 0
    except:
        for feat in FEATURES:
            if feat not in f:
                f[feat] = 0
    return f

# ── Step 1: Pichla merged dataset load karo ─────────────────────────────────
print("\nStep 1: Pichla combined model ka scaler aur features load ho rahe hain...")
with open('../models/feature_names.pkl', 'rb') as f:
    saved_features = pickle.load(f)

# Original + phishing_url_dataset_unique (jo pehle merge kiya)
df_main = pd.read_csv('../dataset/PhiUSIIL_Phishing_URL_Dataset.csv')
df_url  = pd.read_csv('../dataset/phishing_url_dataset_unique.csv')

available = [c for c in FEATURES if c in df_main.columns]
df_orig_clean = df_main[available + ['label']].copy()

print(f"  Original dataset: {len(df_orig_clean):,} rows")

# URL dataset features
print("  phishing_url_dataset_unique se features nikal rahe hain...")
rows1 = []
for i, row in df_url.iterrows():
    if i % 10000 == 0:
        print(f"    {i:,}/{len(df_url):,}...")
    feat = url_se_features(str(row['url']))
    feat['label'] = int(row['label'])
    rows1.append(feat)
df_url_feat = pd.DataFrame(rows1)[available + ['label']]
print(f"  phishing_url_dataset_unique: {len(df_url_feat):,} rows")

# ── Step 2: dataset_phishing.csv (URL column hai) ───────────────────────────
print("\nStep 2: dataset_phishing.csv se features nikal rahe hain...")
df_ph = pd.read_csv('../dataset/dataset_phishing.csv')
rows2 = []
for i, row in df_ph.iterrows():
    if i % 2000 == 0:
        print(f"  {i:,}/{len(df_ph):,}...")
    feat = url_se_features(str(row['url']))
    # status: 'legitimate'=1, 'phishing'=0
    feat['label'] = 1 if str(row['status']).strip().lower() == 'legitimate' else 0
    rows2.append(feat)
df_ph_feat = pd.DataFrame(rows2)[available + ['label']]
print(f"  dataset_phishing: {len(df_ph_feat):,} rows added!")

# ── Step 3: Phishing_Legitimate_full.csv (column mapping) ───────────────────
print("\nStep 3: Phishing_Legitimate_full.csv columns map ho rahe hain...")
df_pl = pd.read_csv('../dataset/Phishing_Legitimate_full.csv')

col_map = {
    'UrlLength':          'URLLength',
    'HostnameLength':     'DomainLength',
    'IpAddress':          'IsDomainIP',
    'NumQueryComponents': 'NoOfQMarkInURL',
    'NumAmpersand':       'NoOfAmpersandInURL',
    'NumPercent':         'NoOfObfuscatedChar',
    'AtSymbol':           'HasObfuscation',
    'SubdomainLevel':     'NoOfSubDomain',
    'PopUpWindow':        'NoOfPopup',
    'IframeOrFrame':      'NoOfiFrame',
    'ExtFormAction':      'HasExternalFormSubmit',
    'SubmitInfoToEmail':  'HasSubmitButton',
    'RightClickDisabled': 'HasHiddenFields',
}

df_pl_mapped = pd.DataFrame(0, index=df_pl.index, columns=available + ['label'])
for old_col, new_col in col_map.items():
    if old_col in df_pl.columns and new_col in available:
        df_pl_mapped[new_col] = df_pl[old_col]

# IsHTTPS = NOT NoHttps
if 'NoHttps' in df_pl.columns and 'IsHTTPS' in available:
    df_pl_mapped['IsHTTPS'] = df_pl['NoHttps'].apply(lambda x: 0 if x == 1 else 1)

# HasTitle = NOT MissingTitle
if 'MissingTitle' in df_pl.columns and 'HasTitle' in available:
    df_pl_mapped['HasTitle'] = df_pl['MissingTitle'].apply(lambda x: 0 if x == 1 else 1)

df_pl_mapped['label'] = df_pl['CLASS_LABEL']
print(f"  Phishing_Legitimate_full: {len(df_pl_mapped):,} rows added!")

# ── Step 4: Sab merge karo ──────────────────────────────────────────────────
print("\nStep 4: Sab datasets merge ho rahe hain...")
df_combined = pd.concat([
    df_orig_clean,
    df_url_feat,
    df_ph_feat,
    df_pl_mapped
], ignore_index=True)
df_combined = df_combined.drop_duplicates()
df_combined = df_combined.fillna(0)

print(f"\n{'='*60}")
print(f"TOTAL DATASET:")
print(f"  Original:                  {len(df_orig_clean):>8,} rows")
print(f"  + phishing_url_unique:     {len(df_url_feat):>8,} rows")
print(f"  + dataset_phishing:        {len(df_ph_feat):>8,} rows")
print(f"  + Phishing_Legitimate:     {len(df_pl_mapped):>8,} rows")
print(f"  = COMBINED TOTAL:          {len(df_combined):>8,} rows")
print(f"  Phishing:   {(df_combined['label']==0).sum():,}")
print(f"  Legitimate: {(df_combined['label']==1).sum():,}")
print(f"{'='*60}")

# ── Step 5: Train ────────────────────────────────────────────────────────────
print("\nStep 5: Model train ho raha hai...")
X = df_combined[available]
y = df_combined['label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

print("XGBoost train ho raha hai...")
try:
    from xgboost import XGBClassifier
    model = XGBClassifier(
        n_estimators=100, max_depth=8,
        learning_rate=0.1, random_state=42,
        n_jobs=-1, eval_metric='logloss', verbosity=0
    )
    model.fit(X_train_sc, y_train)
    acc = accuracy_score(y_test, model.predict(X_test_sc))
    print(f"XGBoost Accuracy: {acc*100:.2f}%")
except:
    from sklearn.ensemble import RandomForestClassifier
    print("XGBoost nahi mila, Random Forest use ho raha hai...")
    model = RandomForestClassifier(
        n_estimators=100, max_depth=12,
        min_samples_split=50, min_samples_leaf=20,
        class_weight='balanced', random_state=42, n_jobs=-1
    )
    model.fit(X_train_sc, y_train)
    acc = accuracy_score(y_test, model.predict(X_test_sc))
    print(f"Random Forest Accuracy: {acc*100:.2f}%")

# ── Step 6: Save ─────────────────────────────────────────────────────────────
print("\nStep 6: Model save ho raha hai...")
os.makedirs('../models', exist_ok=True)
with open('../models/phishing_model_balanced.pkl', 'wb') as f:
    pickle.dump(model, f)
with open('../models/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
with open('../models/feature_names.pkl', 'wb') as f:
    pickle.dump(available, f)

print(f"\n{'='*60}")
print(f"COMPLETE! Final accuracy: {acc*100:.2f}%")
print(f"Total dataset: {len(df_combined):,} URLs")
print("Ab api folder mein jao aur: python app.py chalao!")
print(f"{'='*60}")