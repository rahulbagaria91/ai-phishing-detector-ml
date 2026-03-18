import pandas as pd
import os
import glob

print("=" * 60)
print("SAARE DATASETS CHECK HO RAHE HAIN...")
print("=" * 60)

# Dataset folder ke saare CSV files
csv_files = glob.glob('../dataset/*.csv')

if not csv_files:
    print("Koi CSV file nahi mili dataset folder mein!")
else:
    total_urls = 0
    for f in sorted(csv_files):
        try:
            df = pd.read_csv(f, nrows=5)
            full = pd.read_csv(f)
            rows = len(full)
            total_urls += rows
            
            # Label column dhundo
            label_col = 'NOT FOUND'
            for col in full.columns:
                if col.lower() in ['label','status','class_label','type','class']:
                    label_col = col
                    break
            
            # URL column dhundo
            url_col = 'NOT FOUND'
            for col in full.columns:
                if col.lower() in ['url','urls']:
                    url_col = col
                    break

            print(f"\n FILE: {os.path.basename(f)}")
            print(f"  Rows      : {rows:,}")
            print(f"  URL col   : {url_col}")
            print(f"  Label col : {label_col}")
            if label_col != 'NOT FOUND':
                print(f"  Labels    : {full[label_col].value_counts().to_dict()}")
            print(f"  Columns   : {list(full.columns[:8])}")
            print(f"  {'✅ ADD HO SAKTA HAI!' if url_col != 'NOT FOUND' else '❌ URL column nahi hai!'}")

        except Exception as e:
            print(f"\n❌ {os.path.basename(f)} ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"TOTAL FILES   : {len(csv_files)}")
    print(f"TOTAL URLs    : {total_urls:,}")
    print("=" * 60)