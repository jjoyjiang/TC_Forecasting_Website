# attribute.py

import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import poisson
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss, roc_curve, auc
import io
from datetime import datetime

# Forecasting origins and months
origins = [
    "bom", "cmcc", "dwd", "eccc", "ecmwf",
    "jma", "mf", "ncep", "ukmo",
    "nmme_nasa", "nmme_ncep"
]

months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug"]

# Create output directory
output_dir = Path("reliability_graphs")
output_dir.mkdir(exist_ok=True)

# Store Brier scores
brier_scores = []

# Plotting functions
#def reliability_plot(y_true, y_prob, title, path):
#    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)
 #   plt.figure(figsize=(8, 6))
#    plt.plot(prob_pred, prob_true, marker='o', label='Reliability Curve')
#    plt.plot([0, 1], [0, 1], linestyle='--', color='gray')
 #   plt.title(title)
  #  plt.xlabel('Forecast Probability')
   # plt.ylabel('Observed Frequency')
    #plt.grid()
#    plt.legend()
 #   plt.savefig(path)
  #  plt.close()


def reliability_plot(y_true, y_prob, title, path):
    import numpy as np
    import matplotlib.pyplot as plt
    from sklearn.calibration import calibration_curve

    # Compute reliability curve
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)

    # Histogram data
    bins = np.linspace(0, 1, 11)
    hist, _ = np.histogram(y_prob, bins=bins)

    # Main plot
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(prob_pred, prob_true, marker='o', label='Reliability Curve')
    ax.plot([0, 1], [0, 1], linestyle='--', color='gray')
    ax.set_title(title, fontsize=22,
              color='black',
              fontweight='bold',
              loc='center')
    ax.set_xlabel('Forecast Probability', fontsize=20)
    ax.set_ylabel('Observed Frequency', fontsize=20)
    ax.tick_params(axis='both', which='major', labelsize=17)
    ax.legend(loc='upper left', fontsize = 16)
    ax.grid(False)

    # Draw canvas to get transforms
    fig.canvas.draw()
    trans_data_to_fig = ax.transData + fig.transFigure.inverted()
    xaxis_y_fig = trans_data_to_fig.transform((0, 0))[1]

    # Square inset size
    inset_size = 0.15  # both width and height

    # Bottom-right position
    bbox = ax.get_position()
    inset_left = bbox.x0 + bbox.width - inset_size - 0.02  # right padding

    # Inset axes
    inset_ax = fig.add_axes([inset_left, xaxis_y_fig, inset_size, inset_size])

    # Transparent background, black border
    inset_ax.patch.set_alpha(0.0)
    for spine in inset_ax.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(0.8)

    # Semi-transparent histogram bars
    inset_ax.bar(
        bins[:-1],
        hist,
        width=0.09,
        align='edge',
        color='gray',
        alpha=0.5,
        edgecolor='black',
        linewidth=0.6
    )

    inset_ax.set_xlim(0, 1)
    inset_ax.set_xticks([0, 0.5, 1])
    inset_ax.set_yticks([])
    inset_ax.tick_params(axis='both', labelsize=8)

    
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







def attribute_plot(y_true, y_prob, title, path):
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)
    confidence = 2 * np.abs(prob_pred - 0.5)
    resolution = np.var(prob_true)
    plt.figure(figsize=(8, 6))
    plt.plot(prob_pred, prob_true, 'o-', label='Attribute Curve')
    plt.plot([0, 1], [0, 1], '--', label='Perfect Reliability')
    plt.title(f"{title}\nResolution: {resolution:.3f}, Confidence: {np.mean(confidence):.3f}", fontsize=22,
              color='black',
              fontweight='bold',
              loc='center')
    plt.xlabel('Forecast Probability', fontsize=20)
    plt.ylabel('Observed Frequency', fontsize=20)
    plt.tick_params(axis='both', which='major', labelsize=17)
    plt.grid()
    plt.legend(fontsize = 16)
    
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






def roc_plot(y_true, y_prob, title, path):
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, label=f'AUC = {roc_auc:.2f}')
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray')
    plt.title(title, fontsize=23,
              color='black',
              fontweight='bold',
              loc='center')
    plt.xlabel('False Positive Rate', fontsize=21)
    plt.ylabel('True Positive Rate', fontsize=21)
    plt.tick_params(axis='both', which='major', labelsize=18)
    plt.legend(fontsize=16)
    plt.grid()

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





def generate_attribute_graph(origin, month, graph_type):

    #MONTH_MAP = {
    #    'January': 'jan',
    #    'February': 'feb',
    #    'March': 'mar',
    #    'April': 'apr',
    #    'May': 'may',
    #    'June': 'jun',
    #    'July': 'jul',
    #    'August': 'aug'
    #}
    MONTH_MAP = {
        1: 'jan',
        2: 'feb',
        3: 'mar',
        4: 'apr',
        5: 'may',
        6: 'jun',
        7: 'jul',
        8: 'aug'
    }
    MONTH_MAP_2 = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August'
    }
    MONTH_MAP_3 = {
        'jan': 'January',
        'feb': 'February',
        'mar': 'March',
        'apr': 'April',
        'may': 'May',
        'jun': 'June',
        'jul': 'July',
        'aug': 'August'
    }
    month = MONTH_MAP[month]
    origin = origin.lower()

    # Loop through all model/month combinations
    print(f"Processing: {origin} {month}")

    csv_file = Path("csv_files/reliability") / f"reliability_{origin}_{month}.csv"
    if not csv_file.exists():
        print(f"File not found: {csv_file}")
        return f"No data available for center {origin.upper()} during month {MONTH_MAP_3[month]}."

    df = pd.read_csv(csv_file)

    required_cols = ["count", "median_21yr", "lambda"]
    if not all(col in df.columns for col in required_cols):
        print(f"Missing required columns in: {csv_file}")
        return None

    # Binary outcome: did it exceed the median?
    df["event_observed"] = (df["count"] >= df["median_21yr"]).astype(int)

    # Forecast probability using Poisson CDF
    df["forecast_prob"] = 1 - poisson.cdf(df["median_21yr"] - 1, df["lambda"])

    # Compute Brier score
    y_true = df["event_observed"]
    y_prob = df["forecast_prob"]
    brier = brier_score_loss(y_true, y_prob)
    print("Brier Score:", round(brier, 4))

    brier_scores.append({
        "origin": origin,
        "month": month,
        "brier_score": brier
    })

    # Generate plots
    title_label = f"{origin.replace('_', ' ').upper()} {MONTH_MAP_3[month]}"

    if graph_type == 'reliability':
        img_bytes = reliability_plot(
            y_true, y_prob,
            title=f"Reliability Plot - {title_label}",
            path=output_dir / f"reliability_{origin}_{month}.png"
        )
    elif graph_type == 'attribute':
        img_bytes = attribute_plot(
            y_true, y_prob,
            title=f"Attribute Diagram - {title_label}",
            path=output_dir / f"attribute_{origin}_{month}.png"
        )
    elif graph_type == 'roc':
        img_bytes = roc_plot(
            y_true, y_prob,
            title=f"ROC Curve - {title_label}",
            path=output_dir / f"roc_{origin}_{month}.png"
        )
    else:
        print('Attribute Graph Type Error')
        return None

    # Save Brier scores to CSV
    # pd.DataFrame(brier_scores).to_csv("brier_scores.csv", index=False)

    return img_bytes