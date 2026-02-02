import pandas as pd
df = pd.read_csv('d:\\git\\TDengine-test\\jjl.csv', encoding='gbk')
print(df.iloc[30:50][['index', 'chinese_name', 'var_name']])
