import pandas as pd

# Load the dataset
df = pd.read_csv('../dataset/PhiUSIIL_Phishing_URL_Dataset.csv')

# Check basic info
print("Dataset shape:", df.shape)
print("\nColumn names:")
print(df.columns.tolist())
print("\nFirst few rows:")
print(df.head())
print("\nClass distribution:")
print(df['label'].value_counts())
