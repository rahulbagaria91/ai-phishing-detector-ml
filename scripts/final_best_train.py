import pandas as pd
import numpy as np
import pickle
import os
import re
from urllib.parse import urlparse
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, precision_score,
                              recall_score, f1_score, confusion_matrix)

print("=" * 65)
print("  FINAL MODEL - TOP 2 BEST DATASETS")
print("=" * 65)

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

# ── Dataset 1: PhiUSIIL (best dataset - 50 features ready) ──
print("\n[1/2] PhiUSIIL dataset load ho raha hai...")
df_orig = pd.read_csv('../dataset/PhiUSIIL_Phishing_URL_Dataset.csv')
avail   = [c for c in FEATURES if c in df_orig.columns]
df1     = df_orig[avail + ['label']].copy()
df1['label'] = df1['label'].apply(to_label)
print(f"      {len(df1):,} rows ✅")
print(f"      Legitimate: {(df1['label']==1).sum():,}")
print(f"      Phishing:   {(df1['label']==0).sum():,}")

# ── Dataset 2: phishing_url_unique (99.91% accuracy tha) ────
print("\n[2/2] phishing_url_dataset_unique features nikal rahe hain...")
df_url = pd.read_csv('../dataset/phishing_url_dataset_unique.csv')
rows = []
for i, row in df_url.iterrows():
    if i % 10000 == 0:
        print(f"      {i:,}/{len(df_url):,}...")
    feat = url_to_features(str(row['url']))
    feat['label'] = to_label(row['label'])
    rows.append(feat)
df2 = pd.DataFrame(rows)[avail + ['label']]
print(f"      {len(df2):,} rows ✅")
print(f"      Legitimate: {(df2['label']==1).sum():,}")
print(f"      Phishing:   {(df2['label']==0).sum():,}")

# ── Merge ────────────────────────────────────────────────────
print("\nDono datasets merge ho rahe hain...")
df_combined = pd.concat([df1, df2], ignore_index=True)
df_combined = df_combined.drop_duplicates()
df_combined = df_combined.fillna(0)

print(f"\n{'='*65}")
print(f"  Dataset 1 (PhiUSIIL)      : {len(df1):,} rows")
print(f"  Dataset 2 (phishing_url)  : {len(df2):,} rows")
print(f"  FINAL TOTAL               : {len(df_combined):,} rows!")
print(f"  Legitimate                : {(df_combined['label']==1).sum():,}")
print(f"  Phishing                  : {(df_combined['label']==0).sum():,}")
print(f"{'='*65}")

# ── Train/Test Split ─────────────────────────────────────────
print("\nTrain/Test split ho raha hai...")
X = df_combined[avail]
y = df_combined['label']
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Training: {len(X_train):,}  |  Testing: {len(X_test):,}")

scaler     = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

# ── Random Forest ────────────────────────────────────────────
print("\nRandom Forest train ho raha hai...")
from sklearn.ensemble import RandomForestClassifier
rf = RandomForestClassifier(
    n_estimators=100, max_depth=12,
    min_samples_split=50, min_samples_leaf=20,
    class_weight='balanced', random_state=42, n_jobs=-1
)
rf.fit(X_train_sc, y_train)
rf_pred = rf.predict(X_test_sc)
rf_acc  = accuracy_score(y_test, rf_pred)
rf_f1   = f1_score(y_test, rf_pred)
print(f"Random Forest - Accuracy: {rf_acc*100:.2f}%  F1: {rf_f1*100:.2f}%")

# ── XGBoost ──────────────────────────────────────────────────
best_model = rf
best_acc   = rf_acc
best_algo  = "Random Forest"
best_pred  = rf_pred

try:
    from xgboost import XGBClassifier
    print("\nXGBoost train ho raha hai...")
    xgb = XGBClassifier(
        n_estimators=100, max_depth=8, learning_rate=0.1,
        random_state=42, n_jobs=-1,
        eval_metric='logloss', verbosity=0
    )
    xgb.fit(X_train_sc, y_train)
    xgb_pred = xgb.predict(X_test_sc)
    xgb_acc  = accuracy_score(y_test, xgb_pred)
    xgb_f1   = f1_score(y_test, xgb_pred)
    print(f"XGBoost       - Accuracy: {xgb_acc*100:.2f}%  F1: {xgb_f1*100:.2f}%")
    if xgb_acc > best_acc:
        best_model = xgb
        best_acc   = xgb_acc
        best_algo  = "XGBoost"
        best_pred  = xgb_pred
except ImportError:
    print("XGBoost nahi mila — Random Forest use ho raha hai")

# ── Final metrics ────────────────────────────────────────────
cm = confusion_matrix(y_test, best_pred)
print(f"\n{'='*65}")
print(f"  WINNER: {best_algo}")
print(f"{'='*65}")
print(f"  Accuracy  : {best_acc*100:.2f}%")
print(f"  Precision : {precision_score(y_test, best_pred)*100:.2f}%")
print(f"  Recall    : {recall_score(y_test, best_pred)*100:.2f}%")
print(f"  F1-Score  : {f1_score(y_test, best_pred)*100:.2f}%")
print(f"\n  Confusion Matrix:")
print(f"  True Negatives  (Phishing sahi pakda)  : {cm[0][0]:,}")
print(f"  False Positives (Safe ko phishing bola): {cm[0][1]:,}")
print(f"  False Negatives (Phishing miss kiya)   : {cm[1][0]:,}")
print(f"  True Positives  (Safe sahi bola)       : {cm[1][1]:,}")
print(f"{'='*65}")

# ── Save ─────────────────────────────────────────────────────
os.makedirs('../models', exist_ok=True)
with open('../models/phishing_model_balanced.pkl', 'wb') as f:
    pickle.dump(best_model, f)
with open('../models/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
with open('../models/feature_names.pkl', 'wb') as f:
    pickle.dump(avail, f)

print(f"\n  Model save ho gaya!")
print(f"  Total Dataset : {len(df_combined):,} URLs")
print(f"  Algorithm     : {best_algo}")
print(f"  Accuracy      : {best_acc*100:.2f}%")
print(f"\n  Ab chalao:")
print(f"  cd ..\\api")
print(f"  python app.py")
print(f"{'='*65}")