# CREATE TABLE gcm (
#     gcm_id SERIAL PRIMARY KEY,
#     name TEXT NOT NULL
# );

# CREATE TABLE mean_sst (
#     mean_sst_id SERIAL PRIMARY KEY,
#     gcm_id INT NOT NULL REFERENCES gcm(gcm_id) ON DELETE CASCADE,
#     year INT NOT NULL,
#     init_month INT NOT NULL,
#     sst_mdr FLOAT NOT NULL,
#     sst_trop FLOAT NOT NULL,
#     anomaly_mdr FLOAT NOT NULL,
#     anomaly_trop FLOAT NOT NULL
# );

# CREATE TABLE rmse_weights (
#     weights_id SERIAL PRIMARY KEY,
#     gcm_id INT NOT NULL REFERENCES gcm(gcm_id) ON DELETE CASCADE,
#     rmse_mdr FLOAT NOT NULL,
#     rmse_trop FLOAT NOT NULL,
#     w_mdr FLOAT NOT NULL,
#     w_trop FLOAT NOT NULL
# );

import pandas as pd
from sqlalchemy import create_engine
import dotenv
import os

dotenv.load_dotenv(override=True)
DATABASE_URL = os.getenv("DATABASE_URL")

def model_sql(origin, id):
    mdr_df = pd.read_csv(f'static\\downloads\\predicted_mdr_{origin}.csv')
    trop_df = pd.read_csv(f'static\\downloads\\predicted_trop_{origin}.csv')

    mdr_df.rename(columns={
        'sst': 'sst_mdr',
        'rel_sst': 'anomaly_mdr',
    }, inplace=True)

    trop_df.rename(columns={
        'sst': 'sst_trop',
        'rel_sst': 'anomaly_trop',
    }, inplace=True)

    merged_df = pd.merge(mdr_df, trop_df, on=["year", "init_month"], how="inner")
    merged_df["gcm_id"] = id

    # print(merged_df.head())
    return merged_df


if __name__ == "__main__":
    print("Hello, World!")
    all_dfs = []
    id = 1
    for origin in ('bom', 'cmcc', 'dwd', 'eccc', 'ecmwf',
                   'jma', 'meteo_france', 'ncep', 'ukmo',
                   'nmme_nasa', 'nmme_ncep'):
        df = model_sql(origin, id)
        all_dfs.append(df)
        id = id + 1
    big_df = pd.concat(all_dfs, ignore_index=True)
    #big_df.to_csv('cleaning\\cleaned_gcm.csv', index=False)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)
    big_df.to_sql("mean_sst", engine, if_exists="append", index=False)
