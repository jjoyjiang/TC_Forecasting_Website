from scipy.stats import pearsonr
import numpy as np
import pandas as pd
import os
import calendar

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


from datetime import datetime
def skill_score_generate_graph(basin, origin, month, start_year, end_year):
    if isinstance(month, str):
        month = datetime.strptime(month, "%B").month  # 'June' -> 6
    origin = origin.lower()

    print('CHECK1')
    skill_scores = {}
    
    csv_path = os.path.join('static', 'downloads', 'observation_lambda.csv')
    observed_df = pd.read_csv(csv_path)
    print('CHECK2')

    csv_path = os.path.join('static', 'downloads', f'predicted_{basin}_{origin}.csv')
    predicted_df = pd.read_csv(csv_path)
    print('CHECK3')

    if predicted_df['init_month'].dtype == 'object':
        # Quick check if it looks like a date string (e.g., contains a dash and length matches)
        sample_val = predicted_df['init_month'].dropna().iloc[0]
        if isinstance(sample_val, str) and len(sample_val) >= 10 and '-' in sample_val:
            predicted_df['init_month'] = pd.to_datetime(
                predicted_df['init_month'],
                format="%Y-%m-%d",
                errors="coerce"
            )
    print('CHECK4')
    
    predicted_subset_df = predicted_df[predicted_df['year'] >= 2006].copy()
    if pd.api.types.is_datetime64_any_dtype(predicted_subset_df['init_month']):
        predicted_subset_df['init_month'] = predicted_subset_df['init_month'].dt.month
    else:
        predicted_subset_df['init_month'] = predicted_subset_df['init_month'].astype(int)
    predicted_subset_df = predicted_subset_df[predicted_subset_df['init_month'] == month]
    print('CHECK5')

    observed_subset_df = observed_df[observed_df['year'] >= 2006].copy()
    basin_col = f'ANOMALY_{basin.upper()}'
    observed_subset_df = observed_subset_df[['year', basin_col]]

    print('CHECK6')
    for year in range(2015, 2025):
        if year not in predicted_subset_df['year'].values:
            ss = np.nan
        else:
            predicted_temp_df = predicted_subset_df[predicted_subset_df['year'] <= year]
            observed_temp_df = observed_subset_df[observed_subset_df['year'] <= year]

            merged = pd.merge(
            predicted_temp_df[['year', 'rel_sst']],
            observed_temp_df[['year', basin_col]],
            on='year',
            how='inner'
            )
            if len(merged) >= 2:
                # Correlation Coefficient
                rho = np.corrcoef(merged['rel_sst'], merged[basin_col])[0, 1]


                # Potential Skill
                ps = rho**2

                # Unconditional Bias
                ub = ((merged['rel_sst'].mean() - merged[basin_col].mean()) / merged[basin_col].std(ddof=1))**2

                # Conditional Bias
                cb = (rho - (merged[basin_col].std(ddof=1) / merged['rel_sst'].std(ddof=1)))**2

                 # Skill Score
                ss = ps - ub - cb
                
            else:
                ss = np.nan
                
            if year not in skill_scores:
                skill_scores[year] = {}
            skill_scores[year][origin] = ss
    print('CHECK7')
    ss_df = pd.DataFrame.from_dict(skill_scores, orient='index')
    ss_df.index.name = 'year'
    ss_df.reset_index(inplace=True)
    ss_df.sort_values(by='year', inplace=True)
    print('CHECK8')
    
    ss_df.rename(columns=MONTH_MAP, inplace=True)
    print('CHECK9')
    month_title = calendar.month_name[int(month)]
    print('CHECK10')
    print(ss_df.head())
    
    img_bytes = skill_score_graph(ss_df, basin, start_year, end_year, month_title, origin)
    print('CHECK11')
    return img_bytes



import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os
import numpy as np
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter
import io
# month is passed as a string with title case
# basin is passed as a string with lower case
def skill_score_graph(df, basin, start_year, end_year, month = None, origin = None):
    print('hi0')
    # Filter to year range
    df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    print('hi0.75')
    if df.empty:
        print("No data available for the specified origin, month, and year range.")
        return None
    # Drop origin and init_month columns for plotting
    print('hi1')


    df = df.sort_values(by='year')

    models = [col for col in df.columns if col != 'year']
    colors = cm.get_cmap('tab20', len(models))

    y_min = min(df[model].min() for model in models)
    y_max = max(df[model].max() for model in models)
    y_max_rounded = min(np.ceil(y_max * 4) / 4, 1.0)  # cap positive max at 1.0
    print('hi2')
    plt.figure(figsize=(12, 6))

    for idx, model in enumerate(models):
        plt.plot(df['year'], df[model], marker='o', label=model, color=colors(idx))

    # Set symmetric log scale on y-axis with linthresh=1 to keep linear spacing near zero
    plt.yscale('symlog', linthresh=1)

    ax = plt.gca()  # get current axes

    # Use ScalarFormatter to force plain numbers instead of scientific notation
    ax.yaxis.set_major_formatter(ScalarFormatter())

    # Optional: force fixed-point format for nicer decimal ticks
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

    print('hi3')
    # Set y-limits with some padding
    lower_limit = y_min if y_min < -1 else -1
    upper_limit = 1.0  # force y-axis to go to 1.0
    plt.ylim(lower_limit, upper_limit)

    #tick_step = 0.25
    #lower_limit = np.floor(y_min / tick_step) * tick_step if y_min < -1 else -1
    #upper_limit = 1.0  # force y-axis to go to 1.0
    #plt.ylim(lower_limit, upper_limit)

    # Define custom ticks (numeric values, but symlog will space them evenly)
    neg_ticks = [y_min] if y_min < -2 else []
    neg_ticks += [-2, -1] if y_min < -1 else [-1]
    pos_ticks = [0, 0.25, 0.5, 0.75, 1]
    
    # Round down y_min and up y_max to nearest 0.25 outside the range
    #y_min_tick = np.floor(y_min / tick_step) * tick_step
    #y_max_tick = np.ceil(y_max / tick_step) * tick_step

    # Ensure y_max_tick is at most 1.0, and y_min_tick at least -1.0
    #y_min_tick = max(y_min_tick, -1.0)
    #y_max_tick = min(y_max_tick, 1.0)

    # Create symmetric ticks from y_min_tick to y_max_tick
    #all_ticks = np.arange(lower_limit, upper_limit + tick_step, tick_step)

    # Combine and filter ticks inside limits
    # Always include 1.0 in ticks
    if 1.0 not in pos_ticks:
        pos_ticks.append(1.0)

    print('hi4)')
    all_ticks = neg_ticks + pos_ticks
    plt.yscale('symlog', linthresh=1)
    plt.yticks(all_ticks, fontsize=18)
    plt.ylim(lower_limit, upper_limit)

    ax = plt.gca()
    ax.yaxis.set_major_formatter(ScalarFormatter())
    # or if you want two decimals
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    print('hi5')

    plt.axhline(0, color='black', linewidth=2)  # thick black line at y=0

    plt.xticks((df['year'].dropna().unique())[::2], fontsize=18)
    plt.xlabel('Year', fontsize=22)
    plt.ylabel('Skill Score', fontsize=22)

    print('hi6')
    plt.title(f'Skill Scores by Initialization Month and Origin\n({basin.upper()}, {month}, {origin.replace("_", " ").upper()})',
              fontsize=24,
              color='black',
              fontweight='bold',
              loc='center'  # 'center', 'left', or 'right'
              )
    print('hi7')
    plt.legend(
        title='Model',
        title_fontsize=20,     # size of the legend title
        fontsize=18,           # size of the legend labels
        bbox_to_anchor=(1.05, 1),
        loc='upper left'
    )
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()


    print('hi8')
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
