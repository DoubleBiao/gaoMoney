import pandas as pd

df = pd.read_csv('portfolio.csv')
print("DataFrame content:")
print(df)
print("\nDataFrame info:")
print(df.info())
print("\nUnique benchmarks:")
print(df['benchmark'].unique()) 