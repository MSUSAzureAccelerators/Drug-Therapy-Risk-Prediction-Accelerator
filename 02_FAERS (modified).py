# Databricks notebook source
# MAGIC %md #Part 2: EDA & Preprocessing for AutoML

# COMMAND ----------

# https://docs.microsoft.com/en-us/azure/machine-learning/how-to-understand-automated-ml
# https://towardsdatascience.com/feature-engineering-for-machine-learning-3a5e293a5114
# https://matthewrocklin.com/blog/work/2017/10/16/streaming-dataframes-1

# COMMAND ----------

# check python version

# https://vincentlauzon.com/2018/04/18/python-version-in-databricks
import sys

sys.version

# COMMAND ----------

pip install missingno pandasql pycaret[full]

# COMMAND ----------

# import libraries needed
import pandas as pd # for data analysis
import numpy as np # for numeric calculation
import matplotlib.pyplot as plt # for data visualization
import seaborn as sns #for data visualization
from statistics import mode
import scipy as sp

# library settings
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

from matplotlib.colors import ListedColormap

# COMMAND ----------

# MAGIC %md #Load data

# COMMAND ----------

df = spark.read.csv("/mnt/adls/FAERS_CSteroid_preprocess1.csv", header="true", nullValue = "NA", inferSchema="true")

display(df)

# COMMAND ----------

# how many rows, columns

print((df.count(), len(df.columns)))

# COMMAND ----------

# MAGIC %md #Explore data

# COMMAND ----------

# Exploratory Data Analysis

# convert to pandas

df1 = df.toPandas()

# COMMAND ----------



# COMMAND ----------

# data distribution of numerical variables

# https://thecleverprogrammer.com/2021/02/05/what-is-exploratory-data-analysis-eda/

# https://towardsdatascience.com/building-a-simple-machine-learning-model-on-breast-cancer-data-eca4b3b99fa3

df1.hist(figsize=(12, 12))

# COMMAND ----------

# run dataframe statistics

df1.describe()

# COMMAND ----------

# MAGIC %md #Preprocess data

# COMMAND ----------

# MAGIC %md ##Create target variable

# COMMAND ----------

# outcome values

df1['outc_cod'].value_counts()

# COMMAND ----------

# new column - outcome code = DE

df1.insert(loc = 52, 
          column = 'outc_cod_DE', 
          value = 0)

display(df1)

# COMMAND ----------

# target will be binary classification - did a patient die?

df1['outc_cod_DE'] = np.where(df1['outc_cod']=='DE',1,0)

# COMMAND ----------

# outcome values = DE only

df1['outc_cod_DE'].value_counts()

# COMMAND ----------

# MAGIC %md ###Merge dup caseid

# COMMAND ----------

# merge dup caseid where outc_cod = DE is present

# return some records where outcome of death = 1

df1.loc[df1['outc_cod_DE'] == 1].head(5)

# COMMAND ----------

# collapse multiple caseid (FAERS case)

# where there are multiple AEs for the same caseid, collapse these records by taking the max record where outc_code = DE (1)

#https://stackoverflow.com/questions/49343860/how-to-drop-duplicate-values-based-in-specific-columns-using-pandas

df2 = df1.sort_values(by=['outc_cod_DE'], ascending = False) \
        .drop_duplicates(subset=['caseid'], keep = 'first')

# COMMAND ----------

# re-inspect case

df2[df2['caseid'] == 18322071].head(5)

# COMMAND ----------

# how many records after removing dups

df2.shape

# COMMAND ----------

# count distinct cases

# https://datascienceparichay.com/article/pandas-count-of-unique-values-in-each-column

print(df2.nunique())

# COMMAND ----------

# value counts now

df2['outc_cod_DE'].value_counts()

# COMMAND ----------

# MAGIC %md ### Check for imbalance

# COMMAND ----------

# Are the target classes imbalanced?

# https://dataaspirant.com/handle-imbalanced-data-machine-learning/

# 0 is majority class
# 1 is minority class

sns.countplot(x='outc_cod_DE', data=df2) # data already looks wildly imbalanced but let us continue

# COMMAND ----------

# MAGIC %md ##Recode variables

# COMMAND ----------

# age code

# https://www.statology.org/pandas-drop-rows-with-value

df2['age_cod'].value_counts(dropna = False)

# COMMAND ----------

# age in years - insert new column next to 'age' column

df2.insert(loc = 15, 
  column = 'age_in_yrs', 
  value = '0')

# COMMAND ----------

# convert to years

# DEC DECADE
# YR YEAR
# MON MONTH
# WK WEEK
# DY DAY
# HR HOUR

for index, row in df2.iterrows():
  if (row['age_cod'] == "YR"):
    df2.loc[index, 'age_in_yrs'] = df2.loc[index, 'age']
  elif (row['age_cod'] == "DEC"):
     df2.loc[index, 'age_in_yrs'] = df2.loc[index, 'age'] / 10
  elif (row['age_cod'] == "MON"):
    df2.loc[index, 'age_in_yrs'] = df2.loc[index, 'age'] / 12
  elif (row['age_cod'] == "WK"):
    df2.loc[index, 'age_in_yrs'] = df2.loc[index, 'age'] / 52
  elif (row['age_cod'] == "DY"):
    df2.loc[index, 'age_in_yrs']  = df2.loc[index, 'age'] / 365
  else:
    df2.loc[index, 'age_in_yrs'] = 0

# COMMAND ----------

df2[df2['age_cod'] == "DY"].head(5)

# COMMAND ----------

# weight code

df2['wt_cod'].value_counts()

# COMMAND ----------

# spot inspect

df2[df2['wt_cod'] == "LBS"].head(5)

# COMMAND ----------

# weight in lbs - insert new column next to 'wt' column

df2.insert(loc = 21, 
  column = 'wt_in_lbs', 
  value = 0)

# COMMAND ----------

# convert to lbs

for index, row in df2.iterrows():
  if (df2['wt_cod'] == "KG").any(): # https://www.learndatasci.com/solutions/python-valueerror-truth-value-series-ambiguous-use-empty-bool-item-any-or-all/
    df2['wt_in_lbs'] = df2['wt']*2.20462262
  else:
    df2['wt_in_lbs'] = df2['wt']

df2.head(1)

# COMMAND ----------

# MAGIC %md ##Drop NULL values

# COMMAND ----------

# MAGIC %md ###NULL columns

# COMMAND ----------

# display all null values per column

# https://www.analyticsvidhya.com/blog/2021/10/a-beginners-guide-to-feature-engineering-everything-you-need-to-know/

df2.isnull().sum()

# COMMAND ----------

# drop columns with > 90% missing values

threshold = 0.9
df3 = df2[df2.columns[df2.isnull().mean() < threshold]]

df3.columns

# COMMAND ----------

df3.shape

# COMMAND ----------

# inspect remaining missing values in data

import missingno as msno

msno.matrix(df3)

# COMMAND ----------

# MAGIC %md ###NULL rows

# COMMAND ----------

# drop rows where age, weight = 0

df4 = df3[(df3['age_in_yrs'] > 0 & (df3['wt_in_lbs'] > 0))]

display(df4)

# COMMAND ----------

df4.shape

# COMMAND ----------

# MAGIC %md ##Remove outliers

# COMMAND ----------

df4.dtypes

# COMMAND ----------

# detect outliers

# https://www.kaggle.com/agrawaladitya/step-by-step-data-preprocessing-eda
# https://www.machinelearningplus.com/plots/python-boxplot

# select numerical variables of interest
num_cols = ['age_in_yrs','wt_in_lbs','drug_seq','dose_amt','dsg_drug_seq']

plt.figure(figsize=(18,9))
df4[num_cols].boxplot()
plt.title("Numerical variables in the Corticosteroid dataset", fontsize=20)
plt.show()

# COMMAND ----------

import seaborn as sns

sns.boxplot(x=df4['age_in_yrs'])

# COMMAND ----------

import seaborn as sns

sns.boxplot(x=df4['wt_in_lbs'])

# COMMAND ----------

df5 = df4.query("wt_in_lbs <=700")

# COMMAND ----------

# MAGIC %md ##Drop irrelevant variables

# COMMAND ----------

# 2022-02-04 Drop columns that will not be used for training and inference

df5.dtypes

# COMMAND ----------

df6 = df5.drop(['primaryid', 'caseid', 'caseversion', 'i_f_code', \
                'event_dt', 'mfr_dt', 'init_fda_dt', 'fda_dt', \
                'rept_cod', 'auth_num', 'mfr_num', \
                #'age', 'age_cod', 
                'age_grp', 'e_sub', \
                'wt', 'wt_cod', 'rept_dt', \
                'occp_cod', 'reporter_country', 'last_case_version', \
                'role_cod', 'prod_ai', 'val_vbm', 'dose_vbm', 'lot_num', 'nda_num', \
                'pt','outc_cod', 'start_dt', 'end_dt'], axis=1)


# COMMAND ----------

df6.dtypes

# COMMAND ----------

df6.shape

# COMMAND ----------

display(df6)

# COMMAND ----------

# MAGIC %md #Export for AML

# COMMAND ----------

# save data to ADLS Gen2

df6.to_csv('/dbfs/mnt/adls/FAERS_CSteroid_preprocess2.csv', index=False)