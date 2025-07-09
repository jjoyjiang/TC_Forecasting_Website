import os
import io
import matplotlib.pyplot as plt
from py import generate_graphs as gg
import pandas as pd

def update_session_timestamp(user_id):
    try:
        session_folder = os.path.abspath(os.path.join("static", "images", "user_sessions", user_id))
        os.utime(session_folder, None)
    except Exception as e:
        print(f"Could not update timestamp on {session_folder}: {e}")



def generate_image_for_user(start_year, end_year, user_id, type_data):
    csv_path = os.path.join('static', 'downloads', 'hurricane_df.csv')
    hurricane_df = pd.read_csv(csv_path)

    # 1. Filter your dataset based on year range
    # Assuming you have a DataFrame `hurricane_df` with a 'year' column
    filtered_data = hurricane_df[
        (hurricane_df['year'] >= start_year) & 
        (hurricane_df['year'] <= end_year)
    ]

    # 2. Create the plot
    fig, ax = plt.subplots(figsize=(6,4))
    
    # Example: plot count of hurricanes per year
    counts = filtered_data.groupby('year').size()
    counts.plot(kind='bar', ax=ax)
    ax.set_title(f"Hurricane counts from {start_year} to {end_year}")
    ax.set_xlabel("Year")
    ax.set_ylabel("Count")

    # 3. Save to in-memory buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    # 4. Return image bytes
    return buf.read()












    fig, ax = plt.subplots()
    ax.plot([start_year, end_year], [0, 1])  # example plot
    ax.set_title(f"Years: {start_year}–{end_year}")

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return buf.read()