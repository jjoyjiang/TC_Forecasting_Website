# observational_data.py

import xarray as xr
import dotenv
import os
from . import generate_graphs_helper as ggh


def update_graphs():
    ds = ggh.get_hadisst()
    observed_df = ggh.clean_observation(ds)

    print('-------------')
    print(observed_df.head())

    mdr_mean, trop_mean = ggh.reference_means(observed_df)
    print(mdr_mean)
    print(trop_mean)

    ggh.anomalies(observed_df, mdr_mean, trop_mean)

    hurricane_df = ggh.lam_hurricane(observed_df)
    # print(hurricane_df.head())

    ggh.poisson_ppf(hurricane_df)
    # print(hurricane_df.head())

    ggh.hurricane_count(hurricane_df)

    csv_path = os.path.join('static', 'downloads', 'hurricane_df.csv')
    hurricane_df.to_csv(csv_path, index=False)

    TC_df = ggh.TC_regression(observed_df)
    ggh.lam_other(TC_df)
    ggh.poisson_ppf(TC_df)

    csv_path = os.path.join('static', 'downloads', 'TC_df.csv')
    TC_df.to_csv(csv_path, index=False)

    ggh.hurricane_graph(hurricane_df, 'hurricane_percentiles.png')
    ggh.TC_params_graph(TC_df, 'TC_regression.png')
    ggh.params_graph_dual_axis(TC_df, 'TC_superimposed.png')

    ggh.TC_graph(TC_df, 'TC_percentiles.png')

    PDI_df = ggh.PDI_regression(observed_df)
    ggh.lam_other(PDI_df)
    ggh.poisson_ppf(PDI_df)
    csv_path = os.path.join('static', 'downloads', 'PDI_df.csv')
    PDI_df.to_csv(csv_path, index=False)
    ggh.params_graph_dual_axis(PDI_df, 'PDI_superimposed.png')
    ggh.PDI_graph(PDI_df, 'PDI_percentiles.png')

    ACE_df = ggh.ACE_regression(observed_df)
    ggh.lam_other(ACE_df)
    ggh.poisson_ppf(ACE_df)
    csv_path = os.path.join('static', 'downloads', 'ACE_df.csv')
    ACE_df.to_csv(csv_path, index=False)
    ggh.params_graph_dual_axis(ACE_df, 'ACE_superimposed.png')
    ggh.ACE_graph(ACE_df, 'ACE_percentiles.png')

    # -----------------------

    # ggh.actual_vs_predicted_graph(PDI_df, 'PDI_median_actual')
    # ggh.actual_vs_predicted_graph(hurricane_df, 'hurricane_median_actual')


