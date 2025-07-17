import pandas as pd
import numpy as np


def compute_weighted_forecast(forecast_df, weights_df, quantity_of_interest):
    """
    Computes weighted forecast per year and init_month, adjusting for dual weights.

    forecast_df: DataFrame with columns ['year', 'init_month', 'center', 'lambda', 'ANOMALY_MDR', 'ANOMALY_TROP']
    weights_df: DataFrame with columns ['center', 'init_month', 'mdr_weight', 'trop_weight']
    """

    print("in weights.py")
    weights_df = weights_df.rename(columns={"origin": "center", "month": "init_month"})  
    print("WEIGHTS DF:")
    print(weights_df.head())

    # Merge forecast data with weights
    forecast_df['center'] = forecast_df['center'].str.lower()
    merged = forecast_df.merge(weights_df, on=['center', 'init_month'], how='left')
    print("MERGED DF:")
    print(merged.head())

    # Fill missing weights with 0
    merged["mdr_weight"] = merged["mdr_weight"].fillna(0)
    merged["trop_weight"] = merged["trop_weight"].fillna(0)
    print("MERGED DF:")
    print(merged.head())
    # Fill missing anomalies with 0 just in case
    merged["ANOMALY_MDR"] = merged["ANOMALY_MDR"].fillna(0)
    merged["ANOMALY_TROP"] = merged["ANOMALY_TROP"].fillna(0)

    # Compute weighted anomalies
    merged['weighted_mdr'] = merged['mdr_weight'] * merged['ANOMALY_MDR']
    merged['weighted_trop'] = merged['trop_weight'] * merged['ANOMALY_TROP']

    # Aggregate by year and month
    anomaly_by_month = (
        merged.groupby(['year', 'init_month'], as_index=False)
        .agg({
            'weighted_mdr': 'sum',
            'weighted_trop': 'sum'
        })
    )

    if quantity_of_interest == 'Hurricane':
        # Compute lambda using the regression formula
        anomaly_by_month['weighted_lambda'] = np.exp(
            1.707 + 1.388 * anomaly_by_month['weighted_mdr'] - 1.521 * anomaly_by_month['weighted_trop']
        )
    else:
        coeffs = (
            merged.groupby(['year', 'init_month'], as_index=False)
            .agg({'alpha': 'mean', 'beta': 'mean', 'gamma': 'mean'})
        )
        anomaly_by_month = anomaly_by_month.merge(coeffs, on=['year', 'init_month'], how='left')

        anomaly_by_month['weighted_lambda']=np.exp(anomaly_by_month['alpha'] + (anomaly_by_month['beta'] * anomaly_by_month['weighted_mdr']) 
                        + (anomaly_by_month['gamma'] * anomaly_by_month['weighted_trop']))

    # Get count per year/init_month from merged
    count_df = (
        merged.groupby(['year', 'init_month'], as_index=False)
        .agg({'count': 'mean'}) 
    )

    # Merge it into anomaly_by_month
    anomaly_by_month = anomaly_by_month.merge(count_df, on=['year', 'init_month'], how='left')

    print("ANOMALY BY MONTH DF:")
    print(anomaly_by_month.head())

    return anomaly_by_month[['year', 'init_month', 'weighted_lambda', 'count']]



import io
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

def plot_weighted_forecast(weighted_df, quantity_of_interest):
    fig, ax = plt.subplots(figsize=(12, 6))  # Use fig, ax explicitly
    
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

    colors = plt.cm.get_cmap('tab10', len(weighted_df['init_month'].unique()))
    markers = ['o', 's', 'D', '^', 'v', 'P', '*', 'X', 'H', '>']  # Supports up to 10 styles
    

    for i, month in enumerate(sorted(weighted_df['init_month'].unique())):
        try:
            month_df = weighted_df[weighted_df['init_month'] == month]
            ax.plot(month_df['year'], month_df['weighted_lambda'], label=f'{MONTH_MAP[month]}',
                    linewidth = 2, color = colors(i), marker=markers[i % len(markers)],
                    markersize=6)
        except Exception as e:
            print(f"Error processing month {month}: {e}")

    observed = weighted_df.groupby('year')['count'].mean().reset_index()  # or .first() or whatever you prefer
    ax.scatter(observed['year'], observed['count'], 
               s=120, facecolors='white', edgecolors='black', linewidths=1.5, label='Observed Count')
    
    print("PLOTTED WEIGHTS")
    if quantity_of_interest == 'Hurricane':
        title = "Weighted Average of Hurricane Forecasts by\nInitialization Month and Year"
    elif quantity_of_interest == 'TC':
        title = "Weighted Average of Tropical Cyclone Forecasts by\nInitialization Month and Year"
    elif quantity_of_interest == 'PDI':
        title = "Weighted Average of PDI Forecasts by\nInitialization Month and Year"
    elif quantity_of_interest == 'ACE':
        title = "Weighted Average of ACE Forecasts by\nInitialization Month and Year"
    else:
        return TypeError
    
    ax.set_title(title, fontsize=24, fontweight='bold')
    ax.set_xlabel('Year', fontsize=22)

    if quantity_of_interest == 'Hurricane':
        caption = "# of Hurricanes"
    elif quantity_of_interest == 'TC':
        caption = "# of Tropical Cyclones"
    elif quantity_of_interest == 'PDI':
        caption = r'PDI ($10^{10}$ knots$^3$)'
    elif quantity_of_interest == 'ACE':
        caption = r'ACE ($10^4$ knots$^2$)'
    else:
        return TypeError

    ax.set_ylabel(caption, fontsize=22)
    ax.legend(title='Initialization Month', fontsize=14, title_fontsize=15)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.tick_params(axis='both', which='major', labelsize=18)
    ax.grid(True)
    fig.tight_layout()
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    return buf.read()



def parse_month_column(col):
    if pd.api.types.is_numeric_dtype(col):
        return col.astype(int)
    else:
        return pd.to_datetime(col, errors='coerce').dt.month

import os
from py import generate_graphs_helper as ggh
from py import multi_select_forecasted_graphs as msfg
def generate_weighted_plot(months, quantity_of_interest, start_year, end_year):
    ALL_CENTERS=['BOM', 'CMCC', 'DWD', 'ECCC', 'ECMWF', 'JMA', 'MF', 'NCEP', 'NMME_NASA', 'NMME_NCEP', 'UKMO']

    all_filtered_dfs = []

    for center in ALL_CENTERS:
        center_lower = center.lower()
        mdr_path = os.path.join('static', 'downloads', f"predicted_mdr_{center_lower}.csv")
        trop_path = os.path.join('static', 'downloads', f"predicted_trop_{center_lower}.csv")

        if not os.path.isfile(mdr_path):
            raise FileNotFoundError(f"MDR file not found: {mdr_path}")
        if not os.path.isfile(trop_path):
            raise FileNotFoundError(f"TROP file not found: {trop_path}")

        mdr_df = pd.read_csv(mdr_path)[['year', 'init_month', 'rel_sst']]
        trop_df = pd.read_csv(trop_path)[['year', 'init_month', 'rel_sst']]

        mdr_df['init_month'] = parse_month_column(mdr_df['init_month'])
        trop_df['init_month'] = parse_month_column(trop_df['init_month'])

        mdr_df.rename(columns={'rel_sst': 'ANOMALY_MDR'}, inplace=True)
        trop_df.rename(columns={'rel_sst': 'ANOMALY_TROP'}, inplace=True)

        merged_df = pd.merge(mdr_df, trop_df, on=['year', 'init_month']).dropna()
        filtered_df = merged_df[merged_df['init_month'].isin(months)].copy()
        filtered_df['center'] = center.upper()
        all_filtered_dfs.append(filtered_df)

    combined_df = pd.concat(all_filtered_dfs, ignore_index=True)


    all_weighted_dfs = []
    # load weights
    weights_path = os.path.join('static', 'downloads', "weights.csv")
    if not os.path.isfile(weights_path):
        raise FileNotFoundError(f"Weights file not found: {weights_path}")
    weights_df = pd.read_csv(weights_path)


    all_lam_dfs = []

    for month in months:
        month_df = combined_df[combined_df['init_month'] == month].copy()

        if quantity_of_interest == 'Hurricane':
            ggh.hurricane_count(month_df)
            lam_df = ggh.lam_hurricane(month_df)
        elif quantity_of_interest == 'Tropical Cyclone':
            lam_df = msfg.new_TC_regression(month_df).dropna()
            ggh.lam_other(lam_df)
        elif quantity_of_interest == 'PDI':
            lam_df = msfg.new_PDI_regression(month_df).dropna()
            ggh.lam_other(lam_df)
        elif quantity_of_interest == 'ACE':
            lam_df = msfg.new_ACE_regression(month_df).dropna()
            ggh.lam_other(lam_df)
        else:
            raise TypeError("Invalid quantity_of_interest")

        ggh.poisson_ppf(lam_df)

        lam_df = lam_df[(lam_df['year'] >= start_year) & (lam_df['year'] <= end_year)]
        all_lam_dfs.append(lam_df)
    combined_lam_df = pd.concat(all_lam_dfs, ignore_index=True)
        
    # generate graph
    for month in months:
        monthly_df = combined_lam_df[combined_lam_df['init_month'] == month].copy()
        weighted_df = compute_weighted_forecast(monthly_df, weights_df, quantity_of_interest)
        all_weighted_dfs.append(weighted_df)

    all_weighted_dfs_combined = pd.concat(all_weighted_dfs, ignore_index=True)
    weighted_avg_bytes = plot_weighted_forecast(all_weighted_dfs_combined, quantity_of_interest)
    print("RETURNING WEIGHT GRAPH")
    return weighted_avg_bytes




def compute_simple_average_forecast(forecast_df, quantity_of_interest):
    """
    Computes simple average forecast per year and init_month (no weights).

    forecast_df: DataFrame with columns ['year', 'init_month', 'center', 'lambda', 'ANOMALY_MDR', 'ANOMALY_TROP']
    """

    if quantity_of_interest == 'Hurricane':
        forecast_df['simple_lambda'] = np.exp(
            1.707 + 1.388 * forecast_df['ANOMALY_MDR'] - 1.521 * forecast_df['ANOMALY_TROP']
        )
    else:
        forecast_df['simple_lambda'] = np.exp(
            forecast_df['alpha'] + forecast_df['beta'] * forecast_df['ANOMALY_MDR'] + forecast_df['gamma'] * forecast_df['ANOMALY_TROP']
        )

    # Average across centers
    avg_df = (
        forecast_df.groupby(['year', 'init_month'], as_index=False)
        .agg({'simple_lambda': 'mean', 'count': 'mean'})  # simple average across centers
    )

    return avg_df


def generate_avg_plot(months, quantity_of_interest, start_year, end_year):
    ALL_CENTERS = ['BOM', 'CMCC', 'DWD', 'ECCC', 'ECMWF', 'JMA', 'MF', 'NCEP', 'NMME_NASA', 'NMME_NCEP', 'UKMO']
    all_filtered_dfs = []

    for center in ALL_CENTERS:
        center_lower = center.lower()
        mdr_path = os.path.join('static', 'downloads', f"predicted_mdr_{center_lower}.csv")
        trop_path = os.path.join('static', 'downloads', f"predicted_trop_{center_lower}.csv")

        if not os.path.isfile(mdr_path) or not os.path.isfile(trop_path):
            raise FileNotFoundError(f"Missing file for center: {center}")

        mdr_df = pd.read_csv(mdr_path)[['year', 'init_month', 'rel_sst']]
        trop_df = pd.read_csv(trop_path)[['year', 'init_month', 'rel_sst']]

        mdr_df['init_month'] = parse_month_column(mdr_df['init_month'])
        trop_df['init_month'] = parse_month_column(trop_df['init_month'])

        mdr_df.rename(columns={'rel_sst': 'ANOMALY_MDR'}, inplace=True)
        trop_df.rename(columns={'rel_sst': 'ANOMALY_TROP'}, inplace=True)

        merged_df = pd.merge(mdr_df, trop_df, on=['year', 'init_month']).dropna()
        merged_df['center'] = center.upper()
        all_filtered_dfs.append(merged_df)

    combined_df = pd.concat(all_filtered_dfs, ignore_index=True)

    all_lam_dfs = []

    for month in months:
        month_df = combined_df[combined_df['init_month'] == month].copy()

        if quantity_of_interest == 'Hurricane':
            ggh.hurricane_count(month_df)
            lam_df = ggh.lam_hurricane(month_df)
        elif quantity_of_interest == 'Tropical Cyclone':
            lam_df = msfg.new_TC_regression(month_df).dropna()
            ggh.lam_other(lam_df)
        elif quantity_of_interest == 'PDI':
            lam_df = msfg.new_PDI_regression(month_df).dropna()
            ggh.lam_other(lam_df)
        elif quantity_of_interest == 'ACE':
            lam_df = msfg.new_ACE_regression(month_df).dropna()
            ggh.lam_other(lam_df)
        else:
            raise TypeError("Invalid quantity_of_interest")

        ggh.poisson_ppf(lam_df)
        lam_df = lam_df[(lam_df['year'] >= start_year) & (lam_df['year'] <= end_year)]
        all_lam_dfs.append(lam_df)

    combined_lam_df = pd.concat(all_lam_dfs, ignore_index=True)

    # Compute simple (equal) averages
    all_avg_dfs = []
    for month in months:
        monthly_df = combined_lam_df[combined_lam_df['init_month'] == month].copy()
        avg_df = compute_simple_average_forecast(monthly_df, quantity_of_interest)
        all_avg_dfs.append(avg_df)

    all_avg_combined = pd.concat(all_avg_dfs, ignore_index=True)
    print("ALL AVG COMBINED:")
    print(all_avg_combined.head())


    # Plot
    avg_bytes = plot_avg_forecast(all_avg_combined, quantity_of_interest)  # you can keep this name or change it
    return avg_bytes




def plot_avg_forecast(weighted_df, quantity_of_interest):
    fig, ax = plt.subplots(figsize=(12, 6))  # Use fig, ax explicitly
    
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

    colors = plt.cm.get_cmap('tab10', len(weighted_df['init_month'].unique()))
    markers = ['o', 's', 'D', '^', 'v', 'P', '*', 'X', 'H', '>']  # Supports up to 10 styles
    

    for i, month in enumerate(sorted(weighted_df['init_month'].unique())):
        try:
            month_df = weighted_df[weighted_df['init_month'] == month]
            ax.plot(month_df['year'], month_df['simple_lambda'], label=f'{MONTH_MAP[month]}',
                    linewidth = 2, color = colors(i), marker=markers[i % len(markers)],
                    markersize=6)
        except Exception as e:
            print(f"Error processing month {month}: {e}")

    observed = weighted_df.groupby('year')['count'].mean().reset_index()  # or .first() or whatever you prefer
    ax.scatter(observed['year'], observed['count'], 
               s=120, facecolors='white', edgecolors='black', linewidths=1.5, label='Observed Count')
    
    print("PLOTTED WEIGHTS")
    if quantity_of_interest == 'Hurricane':
        title = "Unweighted Average of Hurricane Forecasts by\nInitialization Month and Year"
    elif quantity_of_interest == 'TC':
        title = "Unweighted Average of Tropical Cyclone Forecasts by\nInitialization Month and Year"
    elif quantity_of_interest == 'PDI':
        title = "Unweighted Average of PDI Forecasts by\nInitialization Month and Year"
    elif quantity_of_interest == 'ACE':
        title = "Unweighted Average of ACE Forecasts by\nInitialization Month and Year"
    else:
        return TypeError
    
    ax.set_title(title, fontsize=24, fontweight='bold')
    ax.set_xlabel('Year', fontsize=22)

    if quantity_of_interest == 'Hurricane':
        caption = "# of Hurricanes"
    elif quantity_of_interest == 'TC':
        caption = "# of Tropical Cyclones"
    elif quantity_of_interest == 'PDI':
        caption = r'PDI ($10^{10}$ knots$^3$)'
    elif quantity_of_interest == 'ACE':
        caption = r'ACE ($10^4$ knots$^2$)'
    else:
        return TypeError

    ax.set_ylabel(caption, fontsize=22)
    ax.legend(title='Initialization Month', fontsize=14, title_fontsize=15)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.tick_params(axis='both', which='major', labelsize=18)
    ax.grid(True)
    fig.tight_layout()
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    return buf.read()
