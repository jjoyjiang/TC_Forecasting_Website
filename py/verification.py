# verification.py

import xarray as xr
import dotenv
import os
import generate_graphs_helper as ggh
import pandas as pd

origins = ('bom', 'cmcc', 'dwd', 'eccc', 'ecmwf',
          'jma', 'mf', 'ncep', 'ukmo',
          'nmme_nasa', 'nmme_ncep')

MONTH_MAP = {
    1: 'Jan',
    2: 'Feb',
    3: 'Mar',
    4: 'Apr',
    5: 'May',
    6: 'Jun',
    7: 'Jul',
    8: 'Aug'
}

# To use dotenv for our NetCDF file, you must have a separate file named ".env" (note the period)
# Within the file, have the line "NETCDF=[file_path_name]"
dotenv.load_dotenv()
NETCDF = os.getenv("NETCDF")

# Load the NetCDF file
ds = xr.open_dataset(NETCDF)

import os
# Ensure the directory exists
os.makedirs("csv_files", exist_ok=True)
observed_df = ggh.clean_observation(ds)
print('-------------')
print(observed_df.head())

mdr_mean, trop_mean = ggh.reference_means(observed_df)
# print(mdr_mean)
# print(trop_mean)

# regression.anomalies(observed_df, mdr_mean, trop_mean)

# hurricane_df = regression.lam_hurricane(observed_df)


# Median counts for each year for the previous 21 years

# regression.poisson_ppf(hurricane_df)
ggh.hurricane_count(observed_df)
observed_df['median_21yr'] = (
    observed_df
    .set_index('year')['count']
    .rolling(window=21, min_periods=21)
    .median()
    .reset_index(drop=True)
)
print(observed_df.tail())

observed_df = observed_df[['year', 'count', 'median_21yr']]


# hurricane_df = hurricane_df[['year', 'count', 'p_50']]
# print(hurricane_df.head())

##############################################
def reliability_prep(origin, month):
    # Load file containing MDR data
    #mdr_file = f"predicted_mdr_{origin}.csv"
    #mdr_full = rf"C:\Users\simti\Documents\GitHub\TC_Forecasting\csv_files\{mdr_file}"
    #mdr_df = pd.read_csv(mdr_full, parse_dates=["init_month"])
    csv_path = os.path.join('static', 'downloads', f'predicted_mdr_{origin}.csv')
    mdr_df = pd.read_csv(csv_path, parse_dates=["init_month"])

    # Load file containing TROP data
    #trop_file = f"predicted_trop_{origin}.csv"
    #trop_full = rf"C:\Users\simti\Documents\GitHub\TC_Forecasting\csv_files\{trop_file}"
    #trop_df = pd.read_csv(trop_full, parse_dates=["init_month"])
    csv_path = os.path.join('static', 'downloads', f'predicted_trop_{origin}.csv')
    trop_df = pd.read_csv(csv_path, parse_dates=["init_month"])

    print("TESTING 1")
    print(trop_df.head())

    # Setup the MDR data for graphing
    sub_mdr = mdr_df[['year', 'init_month', 'rel_sst']].copy()
    if pd.api.types.is_datetime64_any_dtype(sub_mdr['init_month']):
        sub_mdr['init_month'] = sub_mdr['init_month'].dt.month
    else:
        sub_mdr['init_month'] = sub_mdr['init_month'].astype(int)
    sub_mdr.rename(columns={'rel_sst': 'ANOMALY_MDR'}, inplace=True)

    # Setup the TROP data for graphing
    sub_trop = trop_df[['year', 'init_month', 'rel_sst']].copy()
    if pd.api.types.is_datetime64_any_dtype(sub_trop['init_month']):
        sub_trop['init_month'] = sub_trop['init_month'].dt.month
    else:
        sub_trop['init_month'] = sub_trop['init_month'].astype(int)
    sub_trop.rename(columns={'rel_sst': 'ANOMALY_TROP'}, inplace=True)

    print("TESTING 2")
    print(sub_trop.head())

    merged_df = (pd.merge(sub_mdr, sub_trop, on=['year', 'init_month'])).dropna()

    print("TESTING 3")
    print(merged_df.head())

    filtered_df = merged_df[merged_df['init_month'] == month].reset_index()

    if filtered_df.empty:
        print(f"No data for month {month}, skipping.")
        return  # Or `continue` if inside a loop
    else:
        print("========FILTERED========")
        print(filtered_df.head())

    # Hurricane
    hurr_df = filtered_df.copy()
    lam_hur = ggh.lam_hurricane(hurr_df)
    lam_hur = lam_hur[['year', 'lambda']]
    print(lam_hur.head())
    merge_df = pd.merge(observed_df, lam_hur, on='year', how='inner')

    base_dir = 'csv_files'
    os.makedirs(base_dir, exist_ok=True)

    
    sub_dir = os.path.join(base_dir, 'reliability')
    os.makedirs(sub_dir, exist_ok=True)
    file_name = f"reliability_{origin}_{MONTH_MAP[month].lower()}.csv"
    output_path = os.path.join(sub_dir, file_name)

    merge_df.to_csv(output_path, index=False)

######################################

if __name__ == "__main__":
    for origin in origins:
        for month in range(1, 9):
            reliability_prep(origin, month)

# subprocess.run([r"C:\Program Files\R\R-4.4.1\bin\Rscript.exe", "attribute.R"], check=True)
