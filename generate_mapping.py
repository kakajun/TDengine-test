import pandas as pd
import json
import re

try:
    # Read CSV
    df = pd.read_csv('d:\\git\\TDengine-test\\靳家梁.csv', encoding='gbk')
    
    # Filter for G16 (verified to match DB schema)
    df_g16 = df[df['turbineName'] == 'G16']
    
    # Create mapping dictionary
    mapping = {}
    valid_cols = []
    
    for _, row in df_g16.iterrows():
        idx = str(row['index']).strip()
        # Check if index is alphabetic (e.g., A, AA, etc.)
        if re.match(r'^[a-zA-Z]+$', idx):
            col_name = idx.lower()
            desc = str(row['chinese_name']).strip()
            mapping[col_name] = desc
            valid_cols.append(col_name)
            
    # Save to JSON
    with open('d:\\git\\TDengine-test\\column_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
        
    print(f"Mapping saved to column_mapping.json. Found {len(mapping)} columns.")
    
except Exception as e:
    print(f"Error: {e}")
