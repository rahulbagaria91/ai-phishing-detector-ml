import pandas as pd
import numpy as np
import pickle
import os
import re
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

print("=" * 60)
print("STEP 1: Original dataset load ho raha hai...")
print("=" * 60)

# Original dataset
df_main = pd.read_csv('../dataset/PhiUSIIL_Phishing_URL_Dataset.csv')
print(f"Original dataset: {len(df_main):,} URLs")

# Feature names jo model use karta hai
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

print("\n" + "=" * 60)
print("STEP 2: Naye URLs se features nikal rahe hain...")
print("(48,812 URLs - sirf URL se, scraping nahi)")
print("=" * 60)

def url_se_features(url):
    """URL string se features nikalta hai"""
    f = {}
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        tld = domain.split('.')[-1] if '.' in domain else ''
        
        f['URLLength'] = len(url)
        f['DomainLength'] = len(domain)
        f['IsDomainIP'] = 1 if re.match(r'^\d+\.\d+\.\d+\.\d+$', domain) else 0
        
        brands = ['paypal','google','facebook','amazon','apple','microsoft',
                  'netflix','bank','secure','update','verify','login','signin']
        f['URLSimilarityIndex'] = min(sum(b in url.lower() for b in brands) * 15, 100)
        
        cont = sum(1 for i in range(1, len(url)) if url[i] == url[i-1])
        f['CharContinuationRate'] = cont / max(len(url), 1)
        
        legit = {'com':0.8,'org':0.75,'net':0.7,'edu':0.9,'gov':0.95,'in':0.7}
        risky = {'tk':0.1,'ml':0.1,'ga':0.1,'cf':0.1,'xyz':0.2,'top':0.2}
        f['TLDLegitimateProb'] = legit.get(tld, risky.get(tld, 0.4))
        
        alphanum = sum(c.isalnum() for c in url)
        f['URLCharProb'] = alphanum / max(len(url), 1)
        f['TLDLength'] = len(tld)
        
        parts = domain.split('.')
        f['NoOfSubDomain'] = max(len(parts) - 2, 0)
        
        obf = 1 if ('@' in url or '%' in url or '0x' in url.lower()) else 0
        f['HasObfuscation'] = obf
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
        total_sp = f['NoOfEqualsInURL'] + f['NoOfQMarkInURL'] + f['NoOfAmpersandInURL'] + special
        f['SpacialCharRatioInURL'] = total_sp / max(len(url), 1)
        f['IsHTTPS'] = 1 if url.startswith('https://') else 0
        
        # Webpage features - default values (scraping nahi karunga)
        f['LineOfCode'] = 0
        f['LargestLineLength'] = 0
        f['HasTitle'] = 0
        f['DomainTitleMatchScore'] = 0
        f['URLTitleMatchScore'] = 0
        f['HasFavicon'] = 0
        f['Robots'] = 0
        f['IsResponsive'] = 0
        f['NoOfURLRedirect'] = 0
        f['NoOfSelfRedirect'] = 0
        f['HasDescription'] = 0
        f['NoOfPopup'] = 0
        f['NoOfiFrame'] = 0
        f['HasExternalFormSubmit'] = 0
        f['HasSocialNet'] = 0
        f['HasSubmitButton'] = 0
        f['HasHiddenFields'] = 0
        f['HasPasswordField'] = 0
        
        url_lower = url.lower()
        f['Bank'] = 1 if any(w in url_lower for w in ['bank','banking','sbi','hdfc']) else 0
        f['Pay'] = 1 if any(w in url_lower for w in ['pay','payment','paypal']) else 0
        f['Crypto'] = 1 if any(w in url_lower for w in ['crypto','bitcoin','wallet']) else 0
        
        f['HasCopyrightInfo'] = 0
        f['NoOfImage'] = 0
        f['NoOfCSS'] = 0
        f['NoOfJS'] = 0
        f['NoOfSelfRef'] = 0
        f['NoOfEmptyRef'] = 0
        f['NoOfExternalRef'] = 0
        
    except:
        for feat in FEATURES:
            if feat not in f:
                f[feat] = 0
    return f

# Naya dataset load karo
df_new_urls = pd.read_csv('../dataset/phishing_url_dataset_unique.csv')
print(f"Naye URLs: {len(df_new_urls):,}")

# Features extract karo
print("Features extract ho rahi hain...")
new_rows = []
for i, row in df_new_urls.iterrows():
    if i % 5000 == 0:
        print(f"  {i:,}/{len(df_new_urls):,} done...")
    feat = url_se_features(str(row['url']))
    feat['label'] = int(row['label'])
    new_rows.append(feat)

df_new = pd.DataFrame(new_rows)
print(f"Naye features extract ho gaye: {len(df_new):,} rows")

print("\n" + "=" * 60)
print("STEP 3: Dono datasets merge ho rahe hain...")
print("=" * 60)

# Original dataset ke sirf wahi columns jo FEATURES mein hain + label
available = [c for c in FEATURES if c in df_main.columns]
df_orig_clean = df_main[available + ['label']].copy()

# Naya data ka same structure
df_new_clean = df_new[available + ['label']].copy()

# Merge!
df_combined = pd.concat([df_orig_clean, df_new_clean], ignore_index=True)
df_combined = df_combined.drop_duplicates()
df_combined = df_combined.fillna(0)

print(f"Original: {len(df_orig_clean):,} rows")
print(f"Naya:     {len(df_new_clean):,} rows")
print(f"Combined: {len(df_combined):,} rows TOTAL!")
print(f"Phishing:   {(df_combined['label']==0).sum():,}")
print(f"Legitimate: {(df_combined['label']==1).sum():,}")

print("\n" + "=" * 60)
print("STEP 4: Train/Test split ho raha hai...")
print("=" * 60)

X = df_combined[available]
y = df_combined['label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Training: {len(X_train):,} | Testing: {len(X_test):,}")

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

print("\n" + "=" * 60)
print("STEP 5: Random Forest train ho raha hai...")
print("=" * 60)

rf = RandomForestClassifier(
    n_estimators=100, max_depth=12,
    min_samples_split=50, min_samples_leaf=20,
    max_features='sqrt', class_weight='balanced',
    random_state=42, n_jobs=-1
)
rf.fit(X_train_sc, y_train)
rf_acc = accuracy_score(y_test, rf.predict(X_test_sc))
print(f"Random Forest Accuracy: {rf_acc*100:.2f}%")

print("\n" + "=" * 60)
print("STEP 6: XGBoost train ho raha hai...")
print("=" * 60)

try:
    from xgboost import XGBClassifier
    xgb = XGBClassifier(
        n_estimators=100, max_depth=8,
        learning_rate=0.1, random_state=42,
        n_jobs=-1, eval_metric='logloss',
        verbosity=0
    )
    xgb.fit(X_train_sc, y_train)
    xgb_acc = accuracy_score(y_test, xgb.predict(X_test_sc))
    print(f"XGBoost Accuracy: {xgb_acc*100:.2f}%")
    use_xgb = xgb_acc > rf_acc
except:
    print("XGBoost install nahi hai — Random Forest use karenge")
    use_xgb = False

print("\n" + "=" * 60)
print("RESULTS COMPARISON")
print("=" * 60)
print(f"Random Forest: {rf_acc*100:.2f}%")
if 'xgb_acc' in dir():
    print(f"XGBoost:       {xgb_acc*100:.2f}%")
    if use_xgb:
        print("Winner: XGBoost")
    else:
        print("Winner: Random Forest")

print("\n" + "=" * 60)
print("STEP 7: Best model save ho raha hai...")
print("=" * 60)

os.makedirs('../models', exist_ok=True)

best_model = xgb if (use_xgb and 'xgb' in dir()) else rf

with open('../models/phishing_model_balanced.pkl', 'wb') as f:
    pickle.dump(best_model, f)
with open('../models/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
with open('../models/feature_names.pkl', 'wb') as f:
    pickle.dump(available, f)

print("Model save ho gaya!")
print("\n" + "=" * 60)
print("SAB COMPLETE! Ab python app.py se API restart karo!")
print("=" * 60)