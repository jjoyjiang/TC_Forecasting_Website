import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from py import generate_graphs_helper as ggh

# CREATE TABLE observed (
#   observed_id SERIAL PRIMARY KEY,
#   year INT,
#   sst_mdr FLOAT,
#   sst_trop FLOAT,
#   anomaly_mdr FLOAT,
#   anomaly_trop FLOAT,
#   hu INT,
#   tc INT,
#   pdi FLOAT,
#   ace FLOAT
# );

observed_df = pd.read_csv('static\\downloads\\observation_lambda.csv')
# hu_df = pd.read_csv('static\downloads\hurricane_df.csv')
# tc_df = pd.read_csv('static\downloads\TC_df.csv')
# pdi_df = pd.read_csv('static\downloads\PDI_df.csv')
# ace_df = pd.read_csv('static\downloads\ACE_df.csv')

observed_df.rename(columns={
    'SST_MDR': 'sst_mdr',
    'SST_TROP': 'sst_trop',
    'ANOMALY_MDR': 'anomaly_mdr',
    'ANOMALY_TROP': 'anomaly_trop',
    'hurricane_count': 'hu',
    'storm_count': 'tc',
}, inplace=True)

observed_df = observed_df[["year", "sst_mdr", "sst_trop", "anomaly_mdr",
                           "anomaly_trop", "hu", "tc"]]

ggh.pdi_count(observed_df)

observed_df.rename(columns={
    'count': 'pdi'
}, inplace=True)

ggh.ace_count(observed_df)

observed_df.rename(columns={
    'count': 'ace'
}, inplace=True)

print(observed_df.head())

required_cols = ['year', 'sst_mdr', 'sst_trop', 'anomaly_mdr', 'anomaly_trop', 'hu', 'tc', 'pdi', 'ace']

observed_df.to_csv('cleaning\\cleaned_observations.csv', index=False)