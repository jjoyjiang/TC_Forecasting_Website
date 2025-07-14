import pandas as pd
from py import generate_graphs_helper as ggh
import calendar
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from datetime import datetime
import os

def parse_month_column(col):
    if pd.api.types.is_numeric_dtype(col):
        return col.astype(int)
    else:
        return pd.to_datetime(col, errors='coerce').dt.month
    

def panel_predicted_graph(quantity_of_interest, start_year, end_year, month, centers):
    if isinstance(month, str):
        month = datetime.strptime(month, "%B").month  # 'June' -> 6

    all_filtered_dfs = []
    print(centers)

    for center in centers:
        center = center.lower()
        print(center)

        # Load MDR data
        mdr_file = f"predicted_mdr_{center}.csv"
        mdr_full = os.path.join('static', 'downloads', mdr_file)
        if not os.path.isfile(mdr_full):
            raise FileNotFoundError(f"MDR file not found: {mdr_full}")
        #mdr_df = pd.read_csv(mdr_full, parse_dates=["init_month"])
        mdr_df = pd.read_csv(mdr_full)

        print('hi1')

        # Load TROP data
        trop_file = f"predicted_trop_{center}.csv"
        trop_full = os.path.join('static', 'downloads', trop_file)
        if not os.path.isfile(trop_full):
            raise FileNotFoundError(f"TROP file not found: {trop_full}")
        #trop_df = pd.read_csv(trop_full, parse_dates=["init_month"])
        trop_df = pd.read_csv(trop_full)

        print('hi2')

        # Clean MDR
        #sub_mdr = mdr_df[['year', 'init_month', 'rel_sst']].copy()
        #sub_mdr['init_month'] = pd.to_datetime(sub_mdr['init_month']).dt.month
        #sub_mdr.rename(columns={'rel_sst': 'ANOMALY_MDR'}, inplace=True)
        sub_mdr = mdr_df[['year', 'init_month', 'rel_sst']].copy()
        sub_mdr['init_month'] = parse_month_column(sub_mdr['init_month'])
        sub_mdr.rename(columns={'rel_sst': 'ANOMALY_MDR'}, inplace=True)
        print('hi3')

        # Clean TROP
        #sub_trop = trop_df[['year', 'init_month', 'rel_sst']].copy()
        #sub_trop['init_month'] = pd.to_datetime(sub_trop['init_month']).dt.month
        #sub_trop.rename(columns={'rel_sst': 'ANOMALY_TROP'}, inplace=True)
        sub_trop = trop_df[['year', 'init_month', 'rel_sst']].copy()
        sub_trop['init_month'] = parse_month_column(sub_trop['init_month'])
        sub_trop.rename(columns={'rel_sst': 'ANOMALY_TROP'}, inplace=True)
        
        print('hi4')

        # Merge
        merged_df = pd.merge(sub_mdr, sub_trop, on=['year', 'init_month']).dropna()
        filtered_df = merged_df[merged_df['init_month'] == month].reset_index().copy()
        filtered_df['center'] = center.upper()
        print(filtered_df.tail())
        print('hi5')
        all_filtered_dfs.append(filtered_df)
        print(all_filtered_dfs[-1].tail())

    # Combine all center data
    filtered_df = pd.concat(all_filtered_dfs, ignore_index=True)
    # Limit to year range


    if quantity_of_interest == 'Hurricane':
        # Hurricane
        hurricane_df = filtered_df.copy()
        print('hi')
        ggh.hurricane_count(hurricane_df)
        lam_hur = ggh.lam_hurricane(hurricane_df)
        ggh.poisson_ppf(lam_hur)
        print('hi')
        lam_hur = lam_hur[(lam_hur['year'] >= start_year) & (lam_hur['year'] <= end_year)]
        print('hi again')
        img_bytes = multi_hurricane_graph(lam_hur, 'Annual Hurricane Count Predictions')
    elif quantity_of_interest == 'Tropical Cyclone':
        # Tropical Cyclone
        print('test')
        TC_df = (ggh.new_TC_regression(filtered_df)).dropna()
        print('test')
        ggh.lam_other(TC_df)
        print('test')
        ggh.poisson_ppf(TC_df)
        print('test')
        TC_df = TC_df[(TC_df['year'] >= start_year) & (TC_df['year'] <= end_year)]
        img_bytes = ggh.new_TC_graph(TC_df, 'Annual Tropical Cyclone Count Predictions')
    elif quantity_of_interest == 'PDI':
        # PDI
        print('pdi')
        PDI_df = (ggh.new_PDI_regression(filtered_df)).dropna()
        print('pdi')
        ggh.lam_other(PDI_df)
        print('pdi')
        ggh.poisson_ppf(PDI_df)
        print('pdi')
        PDI_df = PDI_df[(PDI_df['year'] >= start_year) & (PDI_df['year'] <= end_year)]
        img_bytes = ggh.new_PDI_graph(PDI_df, 'Power Dissipation Index (PDI) Predictions')
    elif quantity_of_interest == 'ACE':
        ACE_df = (ggh.new_ACE_regression(filtered_df)).dropna()
        ggh.lam_other(ACE_df)
        ggh.poisson_ppf(ACE_df)
        ACE_df = ACE_df[(ACE_df['year'] >= start_year) & (ACE_df['year'] <= end_year)]
        img_bytes = ggh.new_ACE_graph(ACE_df, 'Accumulated Cyclone Energy (ACE) Predictions')
    else:
        print("ERROR")
        return TypeError

    print("DONE")
    return img_bytes






import io

from matplotlib.ticker import MaxNLocator


import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend for background/thread-safe image generation
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import io
from matplotlib.ticker import MaxNLocator

def multi_hurricane_graph(df, title, user_id=None, start_year=None, end_year=None):
    df = df.copy()
    fig, ax = plt.subplots(figsize=(12, 6))

    print('graph1')
    # Setup color and marker style
    centers = df['center'].unique()
    print(centers)
    colors = plt.cm.get_cmap('tab10', len(centers))
    markers = ['o', 's', 'D', '^', 'v', 'P', '*', 'X', 'H', '>']  # Supports up to 10 styles
    print('graph2')

    print("Columns in df:", df.columns)

    # Plot p_50 lines and dots for each center
    for i, center in enumerate(centers):
        try:
            print(center)
            print(i)
            group = df[df['center'] == center].sort_values('year')
            ax.plot(group['year'], group['p_50'], 
                    label=f"{center} (p₅₀)", 
                    linewidth=2,
                    color=colors(i),
                    marker=markers[i % len(markers)],
                    markersize=6)
        except Exception as e:
            print(f"Error processing center {center}: {e}")

    print('graph3')
    # Overlay actual observed counts as large black outlined dots
    # Note: you may have duplicates across centers so group by year to avoid overlap
    observed = df.groupby('year')['count'].mean().reset_index()  # or .first() or whatever you prefer
    ax.scatter(observed['year'], observed['count'], 
               s=120, facecolors='white', edgecolors='black', linewidths=1.5, label='Observed Count')
    print('graph4')
    # Final styling
    ax.set_title(title, fontsize=24, fontweight='bold')
    ax.set_xlabel('Year', fontsize=22)
    ax.set_ylabel('# of Hurricanes', fontsize=22)
    ax.tick_params(axis='both', which='major', labelsize=18)
    ax.legend(title='Research Center', fontsize=14, title_fontsize=15)
    ax.grid(True)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    fig.tight_layout()

    # Save to buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    return buf.read()


def lam_hurricane(df):
    def compute_lambda(group):
        group = group[(group['year'] >= 1981) & (group['year'] <= get_current_year())].copy()
        group['lambda'] = np.exp(
            1.707 + 1.388 * group['ANOMALY_MDR'] - 1.521 * group['ANOMALY_TROP']
        )
        return group

    return df.groupby('center', group_keys=False).apply(compute_lambda)

from scipy.stats import poisson
def poisson_ppf(df):
    for center in df['center'].unique():
        mask = df['center'] == center
        df.loc[mask, 'p_50'] = poisson.ppf(0.50, df.loc[mask, 'lambda'])


from datetime import datetime
def get_current_year():
    current_year = datetime.now().year
    return current_year