import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pickle
import os

print("="*70)
print("TRAINING IMPROVED PHISHING DETECTOR")
print("="*70)

# Load dataset
print("\n[1/7] Loading dataset...")
df = pd.read_csv('../dataset/PhiUSIIL_Phishing_URL_Dataset.csv')
print(f"✅ Loaded {len(df)} URLs")

# Drop unnecessary columns
print("\n[2/7] Preprocessing...")
df = df.drop(['URL', 'Domain', 'Title', 'TLD'], axis=1, errors='ignore')
df = df.fillna(df.median())

# Handle outliers - cap extreme values
print("\n[3/7] Handling outliers...")
numeric_cols = df.select_dtypes(include=[np.number]).columns.drop('label')

for col in numeric_cols:
    q1 = df[col].quantile(0.01)
    q99 = df[col].quantile(0.99)
    df[col] = df[col].clip(q1, q99)

print("✅ Outliers handled")

# Separate features and labels
X = df.drop('label', axis=1)
y = df['label']

print(f"✅ Features: {X.shape[1]} columns")
print(f"✅ Samples: {X.shape[0]} URLs")

# Split data
print("\n[4/7] Splitting dataset...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)
print(f"✅ Training: {len(X_train)}")
print(f"✅ Testing: {len(X_test)}")

# Scale features
print("\n[5/7] Scaling features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
print("✅ Features scaled")

# Train model with better parameters to avoid overfitting
print("\n[6/7] Training Random Forest...")
print("(Using regularization to prevent overfitting)")

model = RandomForestClassifier(
    n_estimators=100,           # Reduced from 200
    max_depth=12,               # Limited depth to prevent overfitting
    min_samples_split=50,       # Require more samples to split
    min_samples_leaf=20,        # Require more samples in leaf nodes
    max_features='sqrt',        # Use subset of features
    random_state=42,
    n_jobs=-1,
    class_weight='balanced'     # Handle class imbalance
)

model.fit(X_train_scaled, y_train)
print("✅ Training complete!")

# Cross-validation
print("\n[7/7] Cross-validating...")
cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
print(f"✅ Cross-validation scores: {cv_scores}")
print(f"✅ Average CV accuracy: {cv_scores.mean()*100:.2f}% (+/- {cv_scores.std()*2*100:.2f}%)")

# Evaluate on test set
y_pred = model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)

print("\n" + "="*70)
print("MODEL PERFORMANCE")
print("="*70)
print(f"Test Accuracy: {accuracy*100:.2f}%")
print("\n" + classification_report(y_test, y_pred, target_names=['Phishing', 'Legitimate']))

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix:")
print(f"True Negatives:  {cm[0][0]:,}")
print(f"False Positives: {cm[0][1]:,}")
print(f"False Negatives: {cm[1][0]:,}")
print(f"True Positives:  {cm[1][1]:,}")

# Feature importance
print("\n" + "="*70)
print("TOP 15 MOST IMPORTANT FEATURES")
print("="*70)
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

for idx, row in feature_importance.head(15).iterrows():
    print(f"{row['feature']:35s}: {row['importance']:.4f}")

# Save model and scaler
print("\n" + "="*70)
os.makedirs('../models', exist_ok=True)

model_path = '../models/phishing_model_balanced.pkl'
scaler_path = '../models/scaler.pkl'
features_path = '../models/feature_names.pkl'

with open(model_path, 'wb') as f:
    pickle.dump(model, f)

with open(scaler_path, 'wb') as f:
    pickle.dump(scaler, f)

with open(features_path, 'wb') as f:
    pickle.dump(X.columns.tolist(), f)

print(f"✅ Model saved: {model_path}")
print(f"✅ Scaler saved: {scaler_path}")
print(f"✅ Features saved: {features_path}")

print("\n" + "="*70)
print("✅ TRAINING COMPLETE - Model ready for deployment!")
print("="*70)
print("\nThis model has regularization to avoid overfitting.")
print("It should work better on real-world websites.")
