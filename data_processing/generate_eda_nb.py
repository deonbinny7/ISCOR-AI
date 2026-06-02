import nbformat as nbf

nb = nbf.v4.new_notebook()

text = """\
# Part 1: Exploratory Data Analysis (EDA)
This notebook performs EDA on the cleaned primary training dataset for ISCOR AI.
It includes:
1. Class balance of the target label (Risk_Category)
2. Missingness matrix
3. Correlation heatmap of the unified features
"""

code_imports = """\
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

%matplotlib inline
"""

code_load = """\
# Load the cleaned primary dataset
df = pd.read_csv('../datasets/primary_dataset_clean.csv')
df.head()
"""

text_balance = """\
## 1. Class Balance (Risk Category)
"""

code_balance = """\
plt.figure(figsize=(8, 5))
sns.countplot(data=df, x='Risk_Category', order=['Low', 'Moderate', 'High'])
plt.title('Distribution of Risk Categories')
plt.ylabel('Count')
plt.show()

print(df['Risk_Category'].value_counts(normalize=True) * 100)
"""

text_missing = """\
## 2. Missingness
"""

code_missing = """\
# We already imputed missing values during preprocessing, but let's verify
missing = df.isnull().sum()
print("Missing values per column:\\n", missing[missing > 0])
if missing.sum() == 0:
    print("No missing values found!")
"""

text_corr = """\
## 3. Correlation Heatmap
"""

code_corr = """\
# Compute correlation matrix for numeric features
numeric_cols = df.select_dtypes(include=[np.number]).columns
corr = df[numeric_cols].corr()

plt.figure(figsize=(10, 8))
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
plt.title('Feature Correlation Heatmap')
plt.show()
"""

nb['cells'] = [
    nbf.v4.new_markdown_cell(text),
    nbf.v4.new_code_cell(code_imports),
    nbf.v4.new_code_cell(code_load),
    nbf.v4.new_markdown_cell(text_balance),
    nbf.v4.new_code_cell(code_balance),
    nbf.v4.new_markdown_cell(text_missing),
    nbf.v4.new_code_cell(code_missing),
    nbf.v4.new_markdown_cell(text_corr),
    nbf.v4.new_code_cell(code_corr)
]

with open('notebooks/Part1_EDA.ipynb', 'w') as f:
    nbf.write(nb, f)
print("Notebook created at notebooks/Part1_EDA.ipynb")
