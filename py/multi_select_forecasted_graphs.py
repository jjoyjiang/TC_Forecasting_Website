import pandas as pd
from py import generate_graphs_helper as ggh
import calendar
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from datetime import datetime
import os
from py import skill_score as ss
from py import attribute as atrb
from py import weights as weights

def parse_month_column(col):
    if pd.api.types.is_numeric_dtype(col):
        return col.astype(int)
    else:
        return pd.to_datetime(col, errors='coerce').dt.month
    

def panel_predicted_graph(quantity_of_interest, start_year, end_year, months, centers):
    print("generating")
    img_bytes_list = []
    section_img_count = [0]*5
    no_data_messages = [[] for _ in range(5)]


    months = sorted([datetime.strptime(m, "%B").month if isinstance(m, str) else m for m in months])
    centers = sorted(centers)
    centers = list (centers)

    if "Total Unweighted Average" in centers:
        centers.remove("Total Unweighted Average")
        print("removed")
        img_bytes_list.append(weights.generate_avg_plot(months, quantity_of_interest,start_year,end_year))
        section_img_count[0] += 1

    if "Total Weighted Average" in centers:
        centers.remove("Total Weighted Average")
        print("removed")
        img_bytes_list.append(weights.generate_weighted_plot(months, quantity_of_interest,start_year,end_year))
        section_img_count[0] += 1

    
    if len(centers) > 0:

        all_filtered_dfs = []
        for center in centers:
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

        if (len(centers) > 1):
            for month in months:
                centers_with_data_this_month_count = len(centers)
                month_df = combined_df[combined_df['init_month'] == month].copy()
                for center in centers:
                    center_month_df = month_df[month_df['center'] == center]
                    if center_month_df.empty:
                        no_data_messages[1].append(f"No data available for center {center.upper()} during month {MONTH_MAP[month]}.")
                        centers_with_data_this_month_count -= 1
                if centers_with_data_this_month_count < 2:
                    continue

                if quantity_of_interest == 'Hurricane':
                    ggh.hurricane_count(month_df)
                    lam_df = ggh.lam_hurricane(month_df)
                elif quantity_of_interest == 'Tropical Cyclone':
                    print("TESTING 1")
                    lam_df = new_TC_regression(month_df).dropna()
                    ggh.lam_other(lam_df)
                elif quantity_of_interest == 'PDI':
                    lam_df = new_PDI_regression(month_df).dropna()
                    ggh.lam_other(lam_df)
                elif quantity_of_interest == 'ACE':
                    lam_df = new_ACE_regression(month_df).dropna()
                    ggh.lam_other(lam_df)
                else:
                    raise TypeError("Invalid quantity_of_interest")

                ggh.poisson_ppf(lam_df)
                lam_df = lam_df[(lam_df['year'] >= start_year) & (lam_df['year'] <= end_year)]

                if quantity_of_interest == 'Hurricane':
                    img_bytes = multi_hurricane_graph(lam_df, f'Annual Hurricane Count\nPredictions from {MONTH_MAP[month]}')
                elif quantity_of_interest == 'Tropical Cyclone':
                    print("TESTING 2")
                    img_bytes = multi_TC_graph(lam_df, f'Annual Tropical Cyclone Count\nPredictions from {MONTH_MAP[month]}')
                elif quantity_of_interest == 'PDI':
                    img_bytes = multi_PDI_graph(lam_df, f'Power Dissipation Index (PDI)\nPredictions from {MONTH_MAP[month]}')
                elif quantity_of_interest == 'ACE':
                    img_bytes = multi_ACE_graph(lam_df, f'Accumulated Cyclone Energy (ACE)\nPredictions from {MONTH_MAP[month]}')

                img_bytes_list.append(img_bytes)
                section_img_count[1] +=1
                

        for center in centers:
            for month in months:
                center_month_df = combined_df[(combined_df['center'] == center.upper()) & (combined_df['init_month'] == month)].copy()

                if center_month_df.empty:
                    no_data_messages[2].append(f"No data available for center {center.upper()} during month {MONTH_MAP[month]}.")
                    continue

                if quantity_of_interest == 'Hurricane':
                    ggh.hurricane_count(center_month_df)
                    lam_df = ggh.lam_hurricane(center_month_df)
                elif quantity_of_interest == 'Tropical Cyclone':
                    lam_df = ggh.new_TC_regression(center_month_df).dropna()
                    ggh.lam_other(lam_df)
                elif quantity_of_interest == 'PDI':
                    lam_df = ggh.new_PDI_regression(center_month_df).dropna()
                    ggh.lam_other(lam_df)
                elif quantity_of_interest == 'ACE':
                    lam_df = ggh.new_ACE_regression(center_month_df).dropna()
                    ggh.lam_other(lam_df)
                else:
                    raise TypeError("Invalid quantity_of_interest")

                ggh.poisson_ppf(lam_df)
                lam_df = lam_df[(lam_df['year'] >= start_year) & (lam_df['year'] <= end_year)]

                title = f"{quantity_of_interest} Predictions\nfor {center.replace('_', ' ').upper()} {MONTH_MAP[month]}"
                if quantity_of_interest == 'Hurricane':
                    img_bytes = ggh.new_hurricane_graph(lam_df, title)
                elif quantity_of_interest == 'Tropical Cyclone':
                    img_bytes = ggh.new_TC_graph(lam_df, title)
                elif quantity_of_interest == 'PDI':
                    img_bytes = ggh.new_PDI_graph(lam_df, title)
                elif quantity_of_interest == 'ACE':
                    img_bytes = ggh.new_ACE_graph(lam_df, title)

                img_bytes_list.append(img_bytes)
                section_img_count[2] +=1
                


        for center in centers:
            for month in months:
                img_bytes = ss.skill_score_generate_graph(center, month, start_year, end_year)
                if isinstance(img_bytes, bytes):
                    img_bytes_list.append(img_bytes)
                    section_img_count[3] +=1
                elif isinstance(img_bytes, str):
                    no_data_messages[3].append(img_bytes)
                else:
                    # Optional: handle unexpected types
                    no_data_messages.append(f"Unexpected return type: {type(img_bytes)}")


        print('LAST SECTION?')
        for center in centers:
            for month in months:
                print(center)
                print(month)
                img_bytes = atrb.generate_attribute_graph(center, month, "attribute")
                if isinstance(img_bytes, bytes):
                    img_bytes_list.append(img_bytes)
                    section_img_count[4] +=1
                elif isinstance(img_bytes, str):
                    print(img_bytes)
                    print("HI ^^")
                    no_data_messages[4].append(img_bytes)
                    continue
                else:
                    # Optional: handle unexpected types
                    no_data_messages.append(f"Unexpected return type: {type(img_bytes)}")

                img_bytes = atrb.generate_attribute_graph(center, month, "reliability")
                if isinstance(img_bytes, bytes):
                    img_bytes_list.append(img_bytes)
                    section_img_count[4] +=1
                elif isinstance(img_bytes, str):
                    #no_data_messages[4].append(img_bytes)
                    continue
                else:
                    # Optional: handle unexpected types
                    no_data_messages.append(f"Unexpected return type: {type(img_bytes)}")

                img_bytes = atrb.generate_attribute_graph(center, month, "roc")
                if isinstance(img_bytes, bytes):
                    img_bytes_list.append(img_bytes)
                    section_img_count[4] +=1
                elif isinstance(img_bytes, str):
                    #no_data_messages[4].append(img_bytes)
                    continue
                else:
                    # Optional: handle unexpected types
                    no_data_messages.append(f"Unexpected return type: {type(img_bytes)}")

                
        
                
    return img_bytes_list, section_img_count, no_data_messages



MONTH_MAP = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August'
}



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


from datetime import datetime
def get_current_year():
    current_year = datetime.now().year
    return current_year




def multi_TC_graph(df, title, user_id = None, start_year = None, end_year = None):
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
    ax.set_ylabel('# of Tropical Cyclones', fontsize=22)
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

import statsmodels.api as sm
import statsmodels.formula.api as smf

def new_TC_regression(df):
    print("Starting grouped TC regression...")
    df = df.copy()
    ggh.storm_count(df)

    results_list = []

    grouped = df.groupby(['center', 'init_month'])
    print(f"Number of groups: {len(grouped)}")

    for (center, month), group in grouped:
        print(f"Processing center={center}, month={month}, group size={len(group)}")
        group = group.copy()
        models = {}

        for year in range(2005, get_current_year() + 1):
            print(f"  Year: {year}")
            df_subset = group[group['year'] <= year]

            if len(df_subset) < 5 or df_subset[['ANOMALY_MDR', 'ANOMALY_TROP']].isnull().any().any():
                print(f"    Skipping year {year} due to insufficient data or NaNs")
                continue  # skip poorly formed or small groups

            try:
                model = smf.glm(formula='count ~ ANOMALY_MDR + ANOMALY_TROP',
                                data=df_subset,
                                family=sm.families.Poisson()).fit()
            except Exception as e:
                print(f"    Regression failed for center={center}, month={month}, year={year}: {e}")
                continue

            models[year] = {
                'center': center,
                'init_month': month,
                'year': year,
                'alpha': model.params['Intercept'],
                'beta': model.params['ANOMALY_MDR'],
                'gamma': model.params['ANOMALY_TROP']
            }

        if models:
            group_df = pd.DataFrame.from_dict(models, orient='index').reset_index(drop=True)
            results_list.append(group_df)
        else:
            print(f"No valid models for center={center}, month={month}")

    if not results_list:
        raise ValueError("No valid regression results generated.")

    coeff_df = pd.concat(results_list, ignore_index=True)

    merged = coeff_df.merge(
        df[['year', 'center', 'init_month', 'ANOMALY_MDR', 'ANOMALY_TROP', 'count']],
        on=['year', 'center', 'init_month'],
        how='left'
    )

    merged['lambda'] = np.exp(
        merged['alpha'] +
        merged['beta'] * merged['ANOMALY_MDR'] +
        merged['gamma'] * merged['ANOMALY_TROP']
    )

    print("DONE")
    print(merged.head())

    return merged



def multi_PDI_graph(df, title, user_id = None, start_year = None, end_year = None):
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



def multi_ACE_graph(df, title, user_id = None, start_year = None, end_year = None):
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

    plt.xlabel('Year', fontsize=24)
    plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=8, integer = True))
    plt.tick_params(axis='x', labelsize=21)
    plt.ylabel(r'ACE ($10^4$ knots$^2$)', fontsize=24)
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


def new_PDI_regression(df):
    df = df.copy()
    ggh.pdi_count(df)

    results_list = []

    grouped = df.groupby(['center', 'init_month'])

    for (center, month), group in grouped:
        group = group.copy()
        models = {}

        for year in range(1981, get_current_year() + 1):
            df_subset = group[group['year'] <= year]

            if len(df_subset) < 5 or df_subset[['ANOMALY_MDR', 'ANOMALY_TROP']].isnull().any().any():
                continue

            model = smf.glm(
                formula='count ~ ANOMALY_MDR + ANOMALY_TROP',
                data=df_subset,
                family=sm.families.Gamma(link=sm.families.links.Log())
            ).fit()

            models[year] = {
                'center': center,
                'init_month': month,
                'year': year,
                'alpha': model.params['Intercept'],
                'beta': model.params['ANOMALY_MDR'],
                'gamma': model.params['ANOMALY_TROP']
            }

        if models:
            group_df = pd.DataFrame.from_dict(models, orient='index').reset_index(drop=True)
            results_list.append(group_df)

    if not results_list:
        raise ValueError("No valid PDI regression results.")

    coeff_df = pd.concat(results_list, ignore_index=True)

    # Merge model coefficients back with input SST anomaly data
    merged = coeff_df.merge(
        df[['year', 'center', 'init_month', 'ANOMALY_MDR', 'ANOMALY_TROP', 'count']],
        on=['year', 'center', 'init_month'],
        how='left'
    )

    merged['lambda'] = np.exp(
        merged['alpha'] +
        merged['beta'] * merged['ANOMALY_MDR'] +
        merged['gamma'] * merged['ANOMALY_TROP']
    )

    return merged

def new_ACE_regression(df):
    df = df.copy()
    ggh.ace_count(df)

    results_list = []

    grouped = df.groupby(['center', 'init_month'])

    for (center, month), group in grouped:
        group = group.copy()
        models = {}

        for year in range(1981, get_current_year() + 1):
            df_subset = group[group['year'] <= year]

            if len(df_subset) < 5 or df_subset[['ANOMALY_MDR', 'ANOMALY_TROP']].isnull().any().any():
                continue

            model = smf.glm(
                formula='count ~ ANOMALY_MDR + ANOMALY_TROP',
                data=df_subset,
                family=sm.families.Gamma(link=sm.families.links.Log())
            ).fit()

            models[year] = {
                'center': center,
                'init_month': month,
                'year': year,
                'alpha': model.params['Intercept'],
                'beta': model.params['ANOMALY_MDR'],
                'gamma': model.params['ANOMALY_TROP']
            }

        if models:
            group_df = pd.DataFrame.from_dict(models, orient='index').reset_index(drop=True)
            results_list.append(group_df)

    if not results_list:
        raise ValueError("No valid ACE regression results.")

    coeff_df = pd.concat(results_list, ignore_index=True)

    # Merge model coefficients back with input SST anomaly data
    merged = coeff_df.merge(
        df[['year', 'center', 'init_month', 'ANOMALY_MDR', 'ANOMALY_TROP', 'count']],
        on=['year', 'center', 'init_month'],
        how='left'
    )

    merged['lambda'] = np.exp(
        merged['alpha'] +
        merged['beta'] * merged['ANOMALY_MDR'] +
        merged['gamma'] * merged['ANOMALY_TROP']
    )

    return merged
