import pandas as pd
try:
    df = pd.read_csv('d:\\git\\TDengine-test\\靳家梁.csv', encoding='gbk')
    print("Columns:", df.columns.tolist())
    print("Head (first 5 rows):")
    print(df.head())
    print(f"Total rows: {len(df)}")
    
    # Check if 'aa', 'ab' etc are in any column
    found = False
    for col in df.columns:
        if df[col].astype(str).str.contains('aa').any():
            print(f"Found 'aa' in column {col}")
            found = True
            
    if not found:
        print("Did not find 'aa' in any column. Might be sequential mapping.")
        
except Exception as e:
    print(f"Error: {e}")
