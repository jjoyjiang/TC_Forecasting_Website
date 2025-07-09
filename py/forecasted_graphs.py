import pandas as pd
from py import generate_graphs_helper as ggh
import calendar
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from datetime import datetime
import os

def panel_predicted_graph(quantity_of_interest, start_year, end_year, month, center):
    if isinstance(month, str):
        month = datetime.strptime(month, "%B").month  # 'June' -> 6

    center = center.lower()

    print('Hello, World!')

    # Load file containing MDR data
    mdr_file = f"predicted_mdr_{center}.csv"
    mdr_full = os.path.join('static', 'downloads', mdr_file)
    print("zero")

    if not os.path.isfile(mdr_full):
        print("1")
        raise FileNotFoundError(f"MDR file not found: {mdr_full}")
    else:
        print("2")
        print(f"Loading MDR data from: {mdr_full}")
    print("one")

    mdr_df = pd.read_csv(mdr_full, parse_dates=["init_month"])
    print("two")

    # Load file containing TROP data
    trop_file = f"predicted_trop_{center}.csv"
    trop_full = os.path.join('static', 'downloads', trop_file)
    if not os.path.isfile(trop_full):
        raise FileNotFoundError(f"TROP file not found: {trop_full}")
    else:
        print(f"Loading TROP data from: {trop_full}")
    trop_df = pd.read_csv(trop_full, parse_dates=["init_month"])

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
    print("========FILTERED========")
    print(filtered_df.head())



    if quantity_of_interest == 'Hurricane':
        # Hurricane
        hurricane_df = filtered_df.copy()
        ggh.hurricane_count(hurricane_df)
        lam_hur = ggh.lam_hurricane(hurricane_df)
        ggh.poisson_ppf(lam_hur)
        lam_hur = lam_hur[(lam_hur['year'] >= start_year) & (lam_hur['year'] <= end_year)]
        img_bytes = ggh.new_hurricane_graph(lam_hur, 'Annual Hurricane Count Predictions')
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

