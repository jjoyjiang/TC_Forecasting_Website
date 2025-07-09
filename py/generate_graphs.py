# observational_data.py

import xarray as xr
import dotenv
import os
from py import generate_graphs_helper as ggh
import pandas as pd
import matplotlib.pyplot as plt
import io


def get_new_data():
    ds = ggh.get_hadisst()
    observed_df = ggh.clean_observation(ds)


hurricane_df = pd.DataFrame()
TC_df = pd.DataFrame()
PDI_df = pd.DataFrame()
ACE_df = pd.DataFrame()
def update_calculations(start_year = None, end_year= None, user_id = None):
    global hurricane_df, TC_df, PDI_df, ACE_df

    observed_df = pd.read_csv("static/downloads/sst_observational.csv")

    mdr_mean, trop_mean = ggh.reference_means(observed_df)

    ggh.anomalies(observed_df, mdr_mean, trop_mean)

    hurricane_df = ggh.lam_hurricane(observed_df).copy()
    # print(hurricane_df.head())

    ggh.poisson_ppf(hurricane_df)
    # print(hurricane_df.head())

    ggh.hurricane_count(hurricane_df)

    csv_path = os.path.join('static', 'downloads', 'hurricane_df.csv')
    hurricane_df.to_csv(csv_path, index=False)

    TC_df = ggh.TC_regression(observed_df).copy()
    ggh.lam_other(TC_df)
    ggh.poisson_ppf(TC_df)

    csv_path = os.path.join('static', 'downloads', 'TC_df.csv')
    TC_df.to_csv(csv_path, index=False)
    
    PDI_df = ggh.PDI_regression(observed_df).copy()
    ggh.lam_other(PDI_df)
    ggh.poisson_ppf(PDI_df)
    csv_path = os.path.join('static', 'downloads', 'PDI_df.csv')
    PDI_df.to_csv(csv_path, index=False)

    ACE_df = ggh.ACE_regression(observed_df).copy()
    ggh.lam_other(ACE_df)
    ggh.poisson_ppf(ACE_df)
    csv_path = os.path.join('static', 'downloads', 'ACE_df.csv')
    ACE_df.to_csv(csv_path, index=False)


    # -----------------------

    # ggh.actual_vs_predicted_graph(PDI_df, 'PDI_median_actual')
    # ggh.actual_vs_predicted_graph(hurricane_df, 'hurricane_median_actual')

def update_graphs(start_year = None, end_year= None, user_id = None):
    ggh.hurricane_graph(hurricane_df, 'hurricane_percentiles.png', user_id, start_year, end_year)
    ggh.TC_params_graph(TC_df, 'tc_regression.png', user_id, start_year, end_year)
    ggh.params_graph_dual_axis(TC_df, 'tc_superimposed.png', user_id, start_year, end_year)
    ggh.TC_graph(TC_df, 'tc_percentiles.png', user_id, start_year, end_year)
    ggh.params_graph_dual_axis(PDI_df, 'pdi_superimposed.png', user_id, start_year, end_year)
    ggh.PDI_graph(PDI_df, 'pdi_percentiles.png', user_id, start_year, end_year)
    ggh.params_graph_dual_axis(ACE_df, 'pdi_superimposed.png', user_id, start_year, end_year)
    ggh.ACE_graph(ACE_df, 'pdi_percentiles.png', user_id, start_year, end_year)


user_images_cache = {}

def generate_image_for_user(start_year, end_year, user_id, type_data):
    global user_images_cache

    # 1. Filter your dataset based on year range
    if type_data == 'Hurricane':
        csv_path = os.path.join('static', 'downloads', 'hurricane_df.csv')
        df = pd.read_csv(csv_path)
        img_bytes = ggh.new_hurricane_graph(df, 'Hurricane Occurences', user_id, start_year, end_year)
    elif type_data == 'Tropical Cyclone':
        csv_path = os.path.join('static', 'downloads', 'TC_df.csv')
        df = pd.read_csv(csv_path)
        img_bytes = ggh.new_TC_graph(df, 'Tropical Cyclone Occurences', user_id, start_year, end_year)
    elif type_data == 'PDI':
        csv_path = os.path.join('static', 'downloads', 'PDI_df.csv')
        df = pd.read_csv(csv_path)
        img_bytes = ggh.new_PDI_graph(df, 'Power Dissipation Index (PDI)', user_id, start_year, end_year)
    elif type_data == 'ACE':
        csv_path = os.path.join('static', 'downloads', 'ACE_df.csv')
        df = pd.read_csv(csv_path)
        img_bytes = ggh.new_ACE_graph(df, 'Accumulated Cyclone Energy (ACE)', user_id, start_year, end_year)
    else:
        return TypeError

    # Cache image bytes per user_id
    user_images_cache[user_id] = img_bytes

    # Return image bytes
    return img_bytes