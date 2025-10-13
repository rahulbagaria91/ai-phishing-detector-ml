import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
import pickle
import os

print("=" * 60)
print("AI-POWERED PHISHING DETECTOR - MODEL TRAINING")
print("=" * 60)

# Load dataset
print("\n[1/6] Loading dataset...")
df = pd.read_csv('../dataset/PhiUSIIL_Phishing_URL_Dataset.csv')
print(f"✅ Loaded {len(df)} URLs successfully")

# Handle missing values
print("\n[2/6] Preprocessing data...")
# Drop URL, Domain, Title columns (text data, not needed for ML)
df = df.drop(['URL', 'Domain', 'Title', 'TLD'], axis=1, errors='ignore')

# Fill missing values with median
df = df.fillna(df.median())

# Separate features and labels
X = df.drop('label', axis=1)
y = df['label']

print(f"✅ Features: {X.shape[1]} columns")
print(f"✅ Samples: {X.shape[0]} URLs")

# Split dataset
print("\n[3/6] Splitting dataset...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"✅ Training set: {len(X_train)} samples")
print(f"✅ Testing set: {len(X_test)} samples")

# Train model
print("\n[4/6] Training Random Forest model...")
print("(This may take 2-3 minutes...)")
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=20,
    random_state=42,
    n_jobs=-1  # Use all CPU cores
)
model.fit(X_train, y_train)
print("✅ Model training complete!")

# Make predictions
print("\n[5/6] Evaluating model...")
y_pred = model.predict(X_test)

# Calculate metrics
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print("\n" + "=" * 60)
print("MODEL PERFORMANCE METRICS")
print("=" * 60)
print(f"Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"Precision: {precision:.4f} ({precision*100:.2f}%)")
print(f"Recall:    {recall:.4f} ({recall*100:.2f}%)")
print(f"F1-Score:  {f1:.4f} ({f1*100:.2f}%)")

# Confusion Matrix
print("\n" + "=" * 60)
print("CONFUSION MATRIX")
print("=" * 60)
cm = confusion_matrix(y_test, y_pred)
print(f"True Negatives:  {cm[0][0]}")
print(f"False Positives: {cm[0][1]}")
print(f"False Negatives: {cm[1][0]}")
print(f"True Positives:  {cm[1][1]}")

# Classification Report
print("\n" + "=" * 60)
print("DETAILED CLASSIFICATION REPORT")
print("=" * 60)
print(classification_report(y_test, y_pred, target_names=['Phishing', 'Legitimate']))

# Feature Importance (Top 10)
print("\n" + "=" * 60)
print("TOP 10 MOST IMPORTANT FEATURES")
print("=" * 60)
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

for idx, row in feature_importance.head(10).iterrows():
    print(f"{row['feature']:30s} : {row['importance']:.4f}")

# Save the model
print("\n[6/6] Saving model...")
os.makedirs('../models', exist_ok=True)
model_path = '../models/phishing_model.pkl'
with open(model_path, 'wb') as f:
    pickle.dump(model, f)
print(f"✅ Model saved to: {model_path}")

# Save feature names for later use
feature_names = X.columns.tolist()
with open('../models/feature_names.pkl', 'wb') as f:
    pickle.dump(feature_names, f)
print(f"✅ Feature names saved")

print("\n" + "=" * 60)
print("✅ TRAINING COMPLETE!")
print("=" * 60)
print(f"\nModel saved at: C:\\y\\4th year\\new project\\models\\phishing_model.pkl")
print("Next step: Create Flask API to use this model")
