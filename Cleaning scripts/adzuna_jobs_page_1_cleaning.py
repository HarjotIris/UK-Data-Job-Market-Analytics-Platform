import numpy as np
import pandas as pd
import os
print(os.getcwd())
os.chdir(r'C:\Desktop\UK Jobs Project')
print(os.getcwd())
path = r"C:\Desktop\UK Jobs Project\adzuna_jobs_page_1.xlsx"

df = pd.read_excel(path)

#print(df.head())
print(df.columns)

df = df.drop(["Job_Health_Insurance", "Skills", "Salary", "Degree", "Remote Work"], axis=1)

#print(df.columns)

for col in df.columns:
    if col.endswith("Cleaned"):
        continue
    df = df.rename(columns={f'{col}': f'{col}_Cleaned'})

print(df.columns) 

df.to_excel('adzuna_jobs_page_1_cleaned.xlsx', index=False)