# storms.py

import tropycal.tracks as tracks
from collections import defaultdict
import pandas as pd

def storm_count(df):
    basin = tracks.TrackDataset(basin='north_atlantic', source='hurdat', include_btk=False)

    min_wind = 33  # knots
    min_time_steps = 9
    allowed_types = {'HU', 'SS', 'TS'}

    storm_years = defaultdict(list)
    for storm_id in basin.keys:
        year = int(storm_id[-4:])
        storm_years[year].append(storm_id)

    # Build a dict {year: count}
    storm_counts = {}
    for year in df['year'].unique():
        count = 0
        for storm_id in storm_years.get(year, []):
            storm = basin.data[storm_id]
            vmax_list = storm['vmax']
            type_list = storm['type']
            steps = 0

            for vmax, t in zip(vmax_list, type_list):
                if vmax >= min_wind and t in allowed_types:
                    steps += 1
            if steps >= min_time_steps:
                count += 1
        storm_counts[year] = count

    # Map counts back to the dataframe by year
    df['count'] = df['year'].map(storm_counts)

    return df


def hurricane_count(df):
    print('hurricane5')
    basin = tracks.TrackDataset(basin='north_atlantic', source='hurdat', include_btk=False)
    print('hurricane5')
    allowed_types = {'HU'}
    storm_years = defaultdict(list)
    print('hurricane5')
    for storm_id in basin.keys:
        year=int(storm_id[-4:])
        storm_years[year].append(storm_id)
    print('hurricane5')
    year_counts = {
        year: sum(
            any(t in allowed_types for t in basin.data[storm_id]['type'])
            for storm_id in storm_years.get(year, [])
        )
        for year in df['year'].unique()
    }
    df['count'] = df['year'].map(year_counts)
    print('done-ish')
    print(df.head())

def pdi_count(df):
    basin = tracks.TrackDataset(basin='north_atlantic', source='hurdat', include_btk=False)
    storm_years = defaultdict(list)
    for storm_id in basin.keys:
        year=int(storm_id[-4:])
        storm_years[year].append(storm_id)
    pdi = []
    for year in df['year']:
        pdi_total = 0
        for storm_id in storm_years.get(year, []):
            wind_speeds = basin.data[storm_id]['vmax']  # in knots
            for v in wind_speeds:
                v_ms = v * 0.514444  # convert knots to m/s
                if v_ms > 17:
                    pdi_total += (v_ms ** 3) * 6 * 3600  # 6 hours = 21600 s

        pdi.append(pdi_total / 1e11)
    df['count'] = pdi
    print(df.head(10))

def ace_count(df):
    basin = tracks.TrackDataset(basin='north_atlantic', source='hurdat', include_btk=False)
    storm_years = defaultdict(list)
    for storm_id in basin.keys:
        year=int(storm_id[-4:])
        storm_years[year].append(storm_id)
    ace = []
    for year in df['year']:
        ace_total = 0
        for storm_id in storm_years.get(year, []):
            wind_speeds = basin.data[storm_id]['vmax']  # in knots
            for v in wind_speeds:
                v_ms = v * 0.514444  # convert knots to m/s
                if v_ms > 17:
                    ace_total += (v_ms ** 2) * 6 * 3600  # 6 hours = 21600 s

        ace.append(ace_total / 1e9)
    df['count'] = ace




# graphs.py

import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend for background/thread-safe image generation
import matplotlib.pyplot as plt

import os
import numpy as np

# graphs lambda as a function of time. Also includes percentiles for visualization
# file_name should be the name of the image or pdf you wish to save.
# ex: percentiles.png or percentiles.pdf
def hurricane_graph(df, file_name, user_id = None, start_year = None, end_year = None):
    df = df.copy()
    if start_year and end_year:
        df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    plt.figure(figsize=(12, 6))

    # plt.plot(df['year'], df['percentile_05'], label='5th percentile', linestyle='--')
    # plt.plot(df['year'], df['percentile_25'], label='25th percentile', linestyle='--')
    plt.plot(df['year'], df['p_50'],color='gainsboro', label='50th percentile (median)')
    # plt.plot(df['year'], df['percentile_75'], label='75th percentile', linestyle='--')
    # plt.plot(df['year'], df['percentile_95'], label='95th percentile', linestyle='--')

    # plt.step(df['year'], df['lambda'], where='mid', label='Lambda (mean)', color='black', linewidth=2)

    plt.fill_between(df['year'], df['p_05'], df['p_25'], 
                     color='gray', alpha=0.5)
    plt.fill_between(df['year'], df['p_25'], df['p_75'], 
                     color='gray', alpha=0.8)
    plt.fill_between(df['year'], df['p_75'], df['p_95'], 
                     color='gray', alpha=0.5)

    plt.scatter(df['year'], df['count'], color='red', zorder=5)

    plt.xlabel('Year')
    plt.xticks(df['year'][::2])  # Show every second year
    plt.ylabel('# of Hurricanes')
    plt.yticks([2, 4, 6, 8, 10, 12, 14, 16, 18, 20])
    plt.title('Poisson Lambda and Percentiles')
    # Use the 'label' paramter in the previous functions to make legend
    # plt.legend()
    plt.grid(True)
    plt.tight_layout()

    if user_id: 
        download_dir = os.path.abspath(os.path.join("static", "images", "user_sessions", user_id))
    else: 
        download_dir = os.path.abspath(os.path.join("static", "images", "default"))

    os.makedirs(download_dir, exist_ok=True)
    output_path = os.path.join(download_dir, file_name)
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"Removed old image: {output_path}")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    # Uncomment to show the image on your screen as a popup window
    # plt.show()

def TC_params_graph(df, file_name, user_id = None, start_year = None, end_year = None):
    df = df.copy()
    if start_year and end_year:
        df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    plt.figure(figsize=(12, 6))

    plt.plot(df['year'], df['beta'],color='red', label='beta')
    plt.plot(df['year'], df['gamma'],color='blue', label='gamma')

    plt.xlabel('Year')
    plt.xticks(df['year'][::2])  # Show every second year
    plt.ylabel('Beta and Gamma')
    plt.title('TC Poisson Regression Over Time')
    plt.grid(True)
    plt.tight_layout()
    plt.legend()

    if user_id: 
        download_dir = os.path.abspath(os.path.join("static", "images", "user_sessions", user_id))
    else: 
        download_dir = os.path.abspath(os.path.join("static", "images", "default"))
    
    os.makedirs(download_dir, exist_ok=True)
    output_path = os.path.join(download_dir, file_name)
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"Removed old image: {output_path}")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')

#via ChatGPT
def params_graph_dual_axis(df, file_name, user_id = None, start_year = None, end_year = None):
    df = df.copy()
    if start_year and end_year:
        df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # First axis for beta (left y-axis)
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Beta', color='red')
    ax1.plot(df['year'], df['beta'], color='red', label='Beta')
    ax1.tick_params(axis='y', labelcolor='red')
    ax1.set_xticks(df['year'][::2])
    ax1.grid(True)

    # Second axis for gamma (right y-axis)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Gamma', color='blue')
    ax2.plot(df['year'], df['gamma'], color='blue', label='Gamma')
    ax2.tick_params(axis='y', labelcolor='blue')
    # ax2.invert_yaxis()

    # Title and layout
    plt.title('Regression Parameters Over Time')
    fig.tight_layout()

    # Save the figure
    if user_id: 
        download_dir = os.path.abspath(os.path.join("static", "images", "user_sessions", user_id))
    else: 
        download_dir = os.path.abspath(os.path.join("static", "images", "default"))

    os.makedirs(download_dir, exist_ok=True)
    output_path = os.path.join(download_dir, file_name)
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"Removed old image: {output_path}")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')

def TC_graph(df, file_name, user_id = None, start_year = None, end_year = None):
    df = df.copy()
    if start_year and end_year:
        df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    plt.figure(figsize=(12, 6))

    plt.plot(df['year'], df['p_50'],color='gainsboro', label='50th percentile (median)')

    plt.fill_between(df['year'], df['p_05'], df['p_25'], 
                     color='gray', alpha=0.5)
    plt.fill_between(df['year'], df['p_25'], df['p_75'], 
                     color='gray', alpha=0.8)
    plt.fill_between(df['year'], df['p_75'], df['p_95'], 
                     color='gray', alpha=0.5)

    plt.scatter(df['year'], df['count'], color='red', zorder=5)

    plt.xlabel('Year')
    plt.xticks(df['year'][::2])  # Show every second year
    plt.ylabel('# of Tropical Cyclones')
    plt.yticks([4, 8, 12, 16, 20, 24])
    plt.title('Poisson Lambda and Percentiles')
    # Use the 'label' paramter in the previous functions to make legend
    # plt.legend()
    plt.grid(True)
    plt.tight_layout()

    if user_id: 
        download_dir = os.path.abspath(os.path.join("static", "images", "user_sessions", user_id))
    else: 
        download_dir = os.path.abspath(os.path.join("static", "images", "default"))
    
    os.makedirs(download_dir, exist_ok=True)
    output_path = os.path.join(download_dir, file_name)
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"Removed old image: {output_path}")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    # Uncomment to show the image on your screen as a popup window
    # plt.show()

# --------------------------------------------
# EXACT SAME AS TC_graph. REFACTOR LATER
def PDI_graph(df, file_name, user_id = None, start_year = None, end_year = None):
    df = df.copy()
    if start_year and end_year:
        df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    plt.figure(figsize=(12, 6))

    plt.plot(df['year'], df['p_50'],color='gainsboro', label='50th percentile (median)')

    plt.fill_between(df['year'], df['p_05'], df['p_25'], 
                     color='gray', alpha=0.5)
    plt.fill_between(df['year'], df['p_25'], df['p_75'], 
                     color='gray', alpha=0.8)
    plt.fill_between(df['year'], df['p_75'], df['p_95'], 
                     color='gray', alpha=0.5)

    plt.scatter(df['year'], df['count'], color='red', zorder=5)

    plt.xlabel('Year')
    plt.xticks(df['year'][::2])  # Show every second year
    plt.ylabel('PDI')
    plt.yticks([2, 4, 6, 8, 10, 12, 14])
    plt.title('Gamma Lambda and Percentiles')
    # Use the 'label' paramter in the previous functions to make legend
    # plt.legend()
    plt.grid(True)
    plt.tight_layout()

    if user_id: 
        download_dir = os.path.abspath(os.path.join("static", "images", "user_sessions", user_id))
    else: 
        download_dir = os.path.abspath(os.path.join("static", "images", "default"))

    os.makedirs(download_dir, exist_ok=True)
    output_path = os.path.join(download_dir, file_name)
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"Removed old image: {output_path}")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    # Uncomment to show the image on your screen as a popup window
    # plt.show()

def ACE_graph(df, file_name, user_id = None, start_year = None, end_year = None):
    df = df.copy()
    if start_year and end_year:
        df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    plt.figure(figsize=(12, 6))

    plt.plot(df['year'], df['p_50'],color='gainsboro', label='50th percentile (median)')

    plt.fill_between(df['year'], df['p_05'], df['p_25'], 
                     color='gray', alpha=0.5)
    plt.fill_between(df['year'], df['p_25'], df['p_75'], 
                     color='gray', alpha=0.8)
    plt.fill_between(df['year'], df['p_75'], df['p_95'], 
                     color='gray', alpha=0.5)

    plt.scatter(df['year'], df['count'], color='red', zorder=5)

    plt.xlabel('Year')
    plt.xticks(df['year'][::2])  # Show every second year
    plt.ylabel('ACE')
    plt.yticks([4, 8, 12, 16, 20, 24])
    plt.title('Gamma Lambda and Percentiles')
    # Use the 'label' paramter in the previous functions to make legend
    # plt.legend()
    plt.grid(True)
    plt.tight_layout()

    if user_id: 
        download_dir = os.path.abspath(os.path.join("static", "images", "user_sessions", user_id))
    else: 
        download_dir = os.path.abspath(os.path.join("static", "images", "default"))
    
    os.makedirs(download_dir, exist_ok=True)
    output_path = os.path.join(download_dir, file_name)
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"Removed old image: {output_path}")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')



# ------------------------------------------------------------------
# download hadISST data for the observed ssts and anomalies

import os
import time
import glob
import gzip
import shutil
import xarray as xr
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def get_hadisst():  # returns xarray.Dataset
    # === SETUP DOWNLOAD DIRECTORY ===
    download_dir = os.path.abspath(os.path.join("static", "downloads"))
    os.makedirs(download_dir, exist_ok=True)

    # === Clean up old files ===
    gz_path = os.path.join(download_dir, "HadISST_sst.nc.gz")
    nc_path = os.path.join(download_dir, "HadISST_sst.nc")

    for file_path in [gz_path, nc_path]:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed old file: {file_path}")


    # === SETUP CHROME OPTIONS ===
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "directory_upgrade": True
    })

    # === START SELENIUM BROWSER ===
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.metoffice.gov.uk/hadobs/hadisst/data/download.html")
    time.sleep(2)

    # === Click the .nc.gz download link ===
    driver.find_element(By.LINK_TEXT, "HadISST_sst.nc.gz").click()

    # === Wait for download to finish ===
    timeout = 60
    latest_file = None
    while timeout > 0:
        list_of_files = glob.glob(os.path.join(download_dir, '*.nc.gz'))
        if list_of_files:
            latest_file = max(list_of_files, key=os.path.getctime)
            if not latest_file.endswith(".crdownload") and os.path.getsize(latest_file) > 10000:
                break
        time.sleep(1)
        timeout -= 1

    driver.quit()

    # === Decompress .gz file to .nc ===
    if latest_file and os.path.exists(latest_file):
        nc_path = latest_file[:-3]  # remove .gz
        try:
            with gzip.open(latest_file, 'rb') as f_in:
                with open(nc_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        except EOFError:
            print("ERROR: Corrupted gzip file. Removing and exiting.")
            os.remove(latest_file)
            return None

        # === Load with xarray ===
        try: 
            ds = xr.open_dataset(nc_path)
            print(ds)
            return ds
        except Exception as e:
            print(f"Failed to load NetCDF file: {e}")
            return None

    else:
        print("Download failed or file not found.")
        return None



import pandas as pd
import os
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature

def clean_observation(ds):
    # # Show variables and dimensions
    # print('-------variables and dimensions---------')
    # print(ds)

    print('-------variable names---------')
    # See variable names
    print(ds.data_vars)

    # See dimensions
    print('-------dimensions---------')
    print(ds.dims)

    # Access a specific variable (e.g. SST)
    # print('--------SST--------')
    sst = ds['sst']
    # print(sst)

    # print('--------SST Summer--------')
    # changed to 1958 for now for testing purposes CHANGE BACK!!!!!!!!!!!
    sst_1981 = sst.sel(time=slice("1958-01-01", None))
    sst_summer = sst_1981.sel(time=sst_1981['time'].dt.month.isin([8, 9, 10]))
    # print(sst_summer)

    # print('--------SST MDR--------')
    sst_mdr = sst_summer.sel(latitude=slice(25, 10), longitude=slice(-80, -20))
    # print(sst_mdr)

    # print('--------SST TROP--------')
    sst_trop = sst_summer.sel(latitude=slice(30, -30))
    
    # # Plot to ensure points are correct
    # plot_sst_region_global(sst_mdr, "MDR Region on Global Map", color='red')
    # plot_sst_region_global(sst_trop, "Tropical Region on Global Map", color='blue')

    # Means by location and then by year
    mdr_mean = sst_mdr.mean(dim=["latitude", "longitude"])
    trop_mean = sst_trop.mean(dim=["latitude", "longitude"])

    mdr_yearly = mdr_mean.groupby('time.year').mean(dim='time')
    trop_yearly = trop_mean.groupby('time.year').mean(dim='time')

    # dataframe
    df = pd.DataFrame({
        'year': mdr_yearly['year'].values,
        'SST_MDR': mdr_yearly.values,
        'SST_TROP': trop_yearly.values
    })

    # print(df.head())

    csv_path = os.path.join('static', 'downloads', 'sst_observational.csv')
    df.to_csv(csv_path, index=False)
    return df



from scipy.stats import poisson
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
# IMPORTANT!:
# The pandas dataframe used as a parameter must have the following column names:
# year, SST_MDR, SST_TROP, ANOMALY_MDR, ANOMALY_TROP

def reference_means(df):
    df_filtered = df[(df['year'] >= 1982) & (df['year'] <= 2005)].copy()
    df_filtered = df_filtered.reset_index(drop=True)
    # print(df_filtered.head())

    # These means may be constant once calculated. 
    # Keep here for now so that these values can be
    # calculated for various models
    mdr_mean = df_filtered['SST_MDR'].mean()
    trop_mean = df_filtered['SST_TROP'].mean()
    return mdr_mean, trop_mean

def anomalies(df, mdr_mean, trop_mean):
    df['ANOMALY_MDR']=df['SST_MDR'] - mdr_mean
    df['ANOMALY_TROP']=df['SST_TROP'] - trop_mean

# creates and fills a new column 'lambda' in the provided dataframe
# using the statistcal model provided in 2019 paper
def lam_hurricane(df):
    filtered_df = df[(df['year'] >= 1981) & (df['year'] <= get_current_year())].copy()
    filtered_df['lambda']=np.exp(1.707 + (1.388 * filtered_df['ANOMALY_MDR']) - (1.521 * filtered_df['ANOMALY_TROP']))
    return filtered_df

def lam_other(df):
    df['lambda']=np.exp(df['alpha'] + (df['beta'] * df['ANOMALY_MDR']) 
                        + (df['gamma'] * df['ANOMALY_TROP']))

# Inverse CDF, provides values given percentile and lambda
# creates and fills new columns in the dataframe:
# percentile_05, percentile_25, percentile_50, percentile_75, percentile_95
# poisson.ppf takes in values (q, lam)
def poisson_ppf(df):
    df['p_05']=poisson.ppf(0.05, df['lambda'])
    df['p_25']=poisson.ppf(0.25, df['lambda'])
    df['p_50']=poisson.ppf(0.50, df['lambda'])
    df['p_75']=poisson.ppf(0.75, df['lambda'])
    df['p_95']=poisson.ppf(0.95, df['lambda'])

# CDF (cumulative distribution function)
# Will make more useful later
def poisson_cdf(k, lam):
    return poisson.cdf(k, lam)

def TC_regression(df):
    new_df = df.copy()
    storm_count(new_df)   

    models = {}
    # range excludes final value
    for year in range(1981, get_current_year() + 1):
        df_subset = new_df[new_df['year'] <= year]

        model = smf.glm(formula='count ~ ANOMALY_MDR + ANOMALY_TROP', data=df_subset, family=sm.families.Poisson())
        results = model.fit()

        models[year] = {
        'alpha': results.params['Intercept'],
        'beta': results.params['ANOMALY_MDR'],
        'gamma': results.params['ANOMALY_TROP']
    }
    coeff_df = pd.DataFrame.from_dict(models, orient='index')
    coeff_df.index.name = 'year'
    coeff_df.reset_index(inplace=True)

    coeff_df = coeff_df.merge(
        new_df[['year', 'SST_MDR', 'SST_TROP', 'ANOMALY_MDR', 'ANOMALY_TROP', 'count']],
        on='year',
        how='left'
    )

    print(coeff_df.head())

    return coeff_df

def PDI_regression(df):
    new_df = df.copy()
    pdi_count(new_df)   

    models = {}
    # range excludes final value
    for year in range(1981, get_current_year() + 1):
        df_subset = new_df[new_df['year'] <= year]

        model = smf.glm(formula='count ~ ANOMALY_MDR + ANOMALY_TROP', data=df_subset, family=sm.families.Gamma(link=sm.families.links.Log()))
        results = model.fit()

        models[year] = {
        'alpha': results.params['Intercept'],
        'beta': results.params['ANOMALY_MDR'],
        'gamma': results.params['ANOMALY_TROP']
    }
    coeff_df = pd.DataFrame.from_dict(models, orient='index')
    coeff_df.index.name = 'year'
    coeff_df.reset_index(inplace=True)

    coeff_df = coeff_df.merge(
        new_df[['year', 'SST_MDR', 'SST_TROP', 'ANOMALY_MDR', 'ANOMALY_TROP', 'count']],
        on='year',
        how='left'
    )

    print(coeff_df.head())

    return coeff_df

def ACE_regression(df):
    new_df = df.copy()
    ace_count(new_df)   

    models = {}
    # range excludes final value
    for year in range(1981, get_current_year() + 1):
        df_subset = new_df[new_df['year'] <= year]

        model = smf.glm(formula='count ~ ANOMALY_MDR + ANOMALY_TROP', data=df_subset, family=sm.families.Gamma(link=sm.families.links.Log()))
        results = model.fit()

        models[year] = {
        'alpha': results.params['Intercept'],
        'beta': results.params['ANOMALY_MDR'],
        'gamma': results.params['ANOMALY_TROP']
    }
    coeff_df = pd.DataFrame.from_dict(models, orient='index')
    coeff_df.index.name = 'year'
    coeff_df.reset_index(inplace=True)

    coeff_df = coeff_df.merge(
        new_df[['year', 'SST_MDR', 'SST_TROP', 'ANOMALY_MDR', 'ANOMALY_TROP', 'count']],
        on='year',
        how='left'
    )

    print(coeff_df.head())

    return coeff_df


from datetime import datetime
def get_current_year():
    current_year = datetime.now().year
    return current_year




import io

from matplotlib.ticker import MaxNLocator

def new_hurricane_graph(df, title, user_id = None, start_year = None, end_year = None):
    df = df.copy()
    if start_year and end_year:
        df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    plt.figure(figsize=(12, 6))

    # plt.plot(df['year'], df['percentile_05'], label='5th percentile', linestyle='--')
    # plt.plot(df['year'], df['percentile_25'], label='25th percentile', linestyle='--')
    # plt.plot(df['year'], df['p_50'],color='red', label='50th percentile (median)')
    # plt.plot(df['year'], df['percentile_75'], label='75th percentile', linestyle='--')
    # plt.plot(df['year'], df['percentile_95'], label='95th percentile', linestyle='--')

    # plt.step(df['year'], df['lambda'], where='mid', label='Lambda (mean)', color='black', linewidth=2)

    plt.plot(df['year'], df['p_50'], color='red', linewidth=3, label='50th percentile (median)')

    # Add shaded percentile bands with labels
    plt.fill_between(df['year'], df['p_05'], df['p_25'], 
                    color='blue', alpha=0.3, label='5th–25th percentile')
    plt.fill_between(df['year'], df['p_25'], df['p_75'], 
                    color='blue', alpha=0.5, label='25th–75th percentile')
    plt.fill_between(df['year'], df['p_75'], df['p_95'], 
                    color='blue', alpha=0.3, label='75th–95th percentile')

    # Add observed points
    plt.scatter(df['year'], df['count'], s=120, facecolors='lightgray', edgecolors='black', zorder=5, label='Observed')


    plt.xlabel('Year', fontsize=24)
    # plt.xticks(df['year'][::5], fontsize = 21)  # Show every second year
    plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=8, integer = True))
    plt.tick_params(axis='x', labelsize=21)
    plt.ylabel('# of Hurricanes', fontsize = 24)
    plt.yticks([2, 4, 6, 8, 10, 12, 14, 16, 18, 20], fontsize=21)
    plt.title(title,
            fontsize=26,
            color='black',
            fontweight='bold',
            loc='center'  # 'center', 'left', or 'right'
            )
    # Use the 'label' paramter in the previous functions to make legend
    # plt.legend()
    plt.grid(True)
    plt.legend(fontsize=16, loc='upper left', frameon=True)
    plt.tight_layout()

    # Get current figure
    fig = plt.gcf()

    # 3. Save to in-memory buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    img_bytes = buf.read()

    # 5. Return image bytes
    return img_bytes



def new_TC_graph(df, title, user_id = None, start_year = None, end_year = None):
    df = df.copy()
    if start_year and end_year:
        df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    plt.figure(figsize=(12, 6))

    plt.plot(df['year'], df['p_50'], color='red', linewidth=3, label='50th percentile (median)')

    # Add shaded percentile bands with labels
    plt.fill_between(df['year'], df['p_05'], df['p_25'], 
                    color='blue', alpha=0.3, label='5th–25th percentile')
    plt.fill_between(df['year'], df['p_25'], df['p_75'], 
                    color='blue', alpha=0.5, label='25th–75th percentile')
    plt.fill_between(df['year'], df['p_75'], df['p_95'], 
                    color='blue', alpha=0.3, label='75th–95th percentile')

    # Add observed points
    plt.scatter(df['year'], df['count'], s=120, facecolors='lightgray', edgecolors='black', zorder=5, label='Observed')


    plt.xlabel('Year', fontsize=24)
    plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=8, integer = True))
    plt.tick_params(axis='x', labelsize=21)
    plt.ylabel('# of Tropical Cyclones', fontsize = 24)
    plt.yticks([4, 8, 12, 16, 20, 24], fontsize=21)
    plt.title(title,
            fontsize=26,
            color='black',
            fontweight='bold',
            loc='center'  # 'center', 'left', or 'right'
            )
    # Use the 'label' paramter in the previous functions to make legend
    # plt.legend()
    plt.grid(True)
    plt.legend(fontsize=16, loc='upper left', frameon=True)
    plt.tight_layout()

    # Get current figure
    fig = plt.gcf()

    # 3. Save to in-memory buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    img_bytes = buf.read()

    # 5. Return image bytes
    return img_bytes

# --------------------------------------------
# EXACT SAME AS TC_graph. REFACTOR LATER
def new_PDI_graph(df, title, user_id = None, start_year = None, end_year = None):
    df = df.copy()
    if start_year and end_year:
        df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    plt.figure(figsize=(12, 6))

    plt.plot(df['year'], df['p_50'], color='red', linewidth=3, label='50th percentile (median)')

    # Add shaded percentile bands with labels
    plt.fill_between(df['year'], df['p_05'], df['p_25'], 
                    color='blue', alpha=0.3, label='5th–25th percentile')
    plt.fill_between(df['year'], df['p_25'], df['p_75'], 
                    color='blue', alpha=0.5, label='25th–75th percentile')
    plt.fill_between(df['year'], df['p_75'], df['p_95'], 
                    color='blue', alpha=0.3, label='75th–95th percentile')

    # Add observed points
    plt.scatter(df['year'], df['count'], s=120, facecolors='lightgray', edgecolors='black', zorder=5, label='Observed')


    plt.xlabel('Year', fontsize=24)
    plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=8, integer = True))
    plt.tick_params(axis='x', labelsize=21)
    plt.ylabel(r'PDI ($10^{10}$ knots$^3$)', fontsize=24)
    plt.yticks([2, 4, 6, 8, 10, 12, 14], fontsize=21)
    plt.title(title, 
            fontsize=26,
            color='black',
            fontweight='bold',
            loc='center'  # 'center', 'left', or 'right'
            )
    # Use the 'label' paramter in the previous functions to make legend
    # plt.legend()
    plt.grid(True)
    plt.legend(fontsize=16, loc='upper left', frameon=True)
    plt.tight_layout()

    # Get current figure
    fig = plt.gcf()

    # 3. Save to in-memory buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    img_bytes = buf.read()

    # 5. Return image bytes
    return img_bytes

def new_ACE_graph(df, title, user_id = None, start_year = None, end_year = None):
    df = df.copy()
    if start_year and end_year:
        df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    plt.figure(figsize=(12, 6))

    plt.plot(df['year'], df['p_50'], color='red', linewidth=3, label='50th percentile (median)')

    # Add shaded percentile bands with labels
    plt.fill_between(df['year'], df['p_05'], df['p_25'], 
                    color='blue', alpha=0.3, label='5th–25th percentile')
    plt.fill_between(df['year'], df['p_25'], df['p_75'], 
                    color='blue', alpha=0.5, label='25th–75th percentile')
    plt.fill_between(df['year'], df['p_75'], df['p_95'], 
                    color='blue', alpha=0.3, label='75th–95th percentile')

    # Add observed points
    plt.scatter(df['year'], df['count'], s=120, facecolors='lightgray', edgecolors='black', zorder=5, label='Observed')

    plt.xlabel('Year', fontsize=24)
    plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=8, integer = True))
    plt.tick_params(axis='x', labelsize=21)
    plt.ylabel(r'ACE ($10^4$ knots$^2$)', fontsize=24)
    plt.yticks([4, 8, 12, 16, 20, 24], fontsize=21)
    plt.title(title, 
            fontsize=26,
            color='black',
            fontweight='bold',
            loc='center'  # 'center', 'left', or 'right'
            )
    # Use the 'label' paramter in the previous functions to make legend
    # plt.legend()
    plt.grid(True)
    plt.legend(fontsize=16, loc='upper left', frameon=True)
    plt.tight_layout()

    # Get current figure
    fig = plt.gcf()

    # 3. Save to in-memory buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    img_bytes = buf.read()

    # 5. Return image bytes
    return img_bytes



def lam_hurricane(df):
    filtered_df = df[(df['year'] >= 1981) & (df['year'] <= 2025)].copy()
    filtered_df['lambda']=np.exp(1.707 + (1.388 * filtered_df['ANOMALY_MDR']) - (1.521 * filtered_df['ANOMALY_TROP']))
    return filtered_df


def lam_other(df):
    df['lambda']=np.exp(df['alpha'] + (df['beta'] * df['ANOMALY_MDR']) 
                        + (df['gamma'] * df['ANOMALY_TROP']))

def poisson_ppf(df):
    df['p_05']=poisson.ppf(0.05, df['lambda'])
    df['p_25']=poisson.ppf(0.25, df['lambda'])
    df['p_50']=poisson.ppf(0.50, df['lambda'])
    df['p_75']=poisson.ppf(0.75, df['lambda'])
    df['p_95']=poisson.ppf(0.95, df['lambda'])


def new_TC_regression(df):
    print('test1')
    new_df = df.copy()
    storm_count(new_df)
    print('test1')   

    models = {}
    # range excludes final value
    print('test1')
    for year in range(2005, get_current_year() + 1):
        df_subset = new_df[new_df['year'] <= year]

        model = smf.glm(formula='count ~ ANOMALY_MDR + ANOMALY_TROP', data=df_subset, family=sm.families.Poisson())
        results = model.fit()

        models[year] = {
        'alpha': results.params['Intercept'],
        'beta': results.params['ANOMALY_MDR'],
        'gamma': results.params['ANOMALY_TROP']
    }
    print('test1')
    coeff_df = pd.DataFrame.from_dict(models, orient='index')
    coeff_df.index.name = 'year'
    coeff_df.reset_index(inplace=True)
    print('test2')

    
    coeff_df = coeff_df.merge(
       new_df[['year', 'ANOMALY_MDR', 'ANOMALY_TROP', 'count']],
       on='year',
       how='left'
    )
    print('test3')

    print(coeff_df.head())

    return coeff_df



def new_PDI_regression(df):
    print('test1')
    new_df = df.copy()
    pdi_count(new_df)   
    print('test2')

    models = {}
    # range excludes final value
    for year in range(2005, get_current_year() + 1):
        df_subset = new_df[new_df['year'] <= year]

        model = smf.glm(formula='count ~ ANOMALY_MDR + ANOMALY_TROP', data=df_subset, family=sm.families.Gamma(link=sm.families.links.Log()))
        results = model.fit()

        models[year] = {
        'alpha': results.params['Intercept'],
        'beta': results.params['ANOMALY_MDR'],
        'gamma': results.params['ANOMALY_TROP']
    }
    print('test3')
    coeff_df = pd.DataFrame.from_dict(models, orient='index')
    print('test4')
    coeff_df.index.name = 'year'
    coeff_df.reset_index(inplace=True)
    print('test5')
    print(coeff_df.head())

    coeff_df = coeff_df.merge(
        new_df[['year', 'ANOMALY_MDR', 'ANOMALY_TROP', 'count']],
        on='year',
        how='left'
    )
    print('test6')
    print(coeff_df.head())

    return coeff_df


def new_ACE_regression(df):
    new_df = df.copy()
    ace_count(new_df)   

    models = {}
    # range excludes final value
    for year in range(2005, get_current_year() + 1):
        df_subset = new_df[new_df['year'] <= year]

        model = smf.glm(formula='count ~ ANOMALY_MDR + ANOMALY_TROP', data=df_subset, family=sm.families.Gamma(link=sm.families.links.Log()))
        results = model.fit()

        models[year] = {
        'alpha': results.params['Intercept'],
        'beta': results.params['ANOMALY_MDR'],
        'gamma': results.params['ANOMALY_TROP']
    }
    coeff_df = pd.DataFrame.from_dict(models, orient='index')
    coeff_df.index.name = 'year'
    coeff_df.reset_index(inplace=True)

    coeff_df = coeff_df.merge(
        new_df[['year', 'ANOMALY_MDR', 'ANOMALY_TROP', 'count']],
        on='year',
        how='left'
    )

    print(coeff_df.head())

    return coeff_df