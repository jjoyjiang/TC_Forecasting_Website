from threading import Thread
import time
from datetime import datetime
from flask import Flask, render_template, request, session, send_file
from py import generate_graphs as gg
from py import utils
import panel as pn
import py.panel_widget as pw
import os
import uuid
import io


app = Flask(__name__)
app.secret_key = "joix"

def background_updater():
    last_run_date = None
    while True:
        now = datetime.now()
        # Check if it's the 1st or 15th of the month
        if now.day in [0, 15] and (last_run_date is None or last_run_date.date() != now.date()):
            print(f"Running update on {now}")
            gg.get_new_data()
            gg.update_calculations()
            gg.update_graphs()
            print("Done updating!")
            last_run_date = now
        else:
            print(f"No update needed at {now}")
        time.sleep(3600)  # Sleep for an hour to check again

@app.before_request
def assign_session():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        print(f"Assigned new session: {session['user_id']}")



@app.context_processor
def utility_processor():
    def file_exists(filepath):
    # Remove leading slash if present
        if filepath.startswith('/'):
            filepath = filepath[1:]
        return os.path.isfile(os.path.join(app.static_folder, filepath))
    return dict(file_exists=file_exists)




@app.route('/api/get_image')
def get_image():
    user_id = session.get('user_id')
    start_year = int(request.args.get('start_year', 1981))
    end_year = int(request.args.get('end_year', 2025))
    type_data = request.args.get('type') # FIX THIS. grab some element from the widget instead once you figure
                        # out how to do diff updates for each graph


    # Generate image bytes for the given year range
    try:
        image_bytes = gg.generate_image_for_user(start_year, end_year, user_id, type_data)
        if not image_bytes:
                raise ValueError("Image generation failed or returned None.")
        return send_file(io.BytesIO(image_bytes), mimetype='image/png')
    except Exception as e:
        print(f"[❌] Failed to generate {type_data} image for user {user_id}: {e}")
        fallback_path = os.path.join(app.static_folder, 'images', 'default', f'{type_data}_percentiles.png')
        return send_file(fallback_path, mimetype='image/png')






# --- Panel in a thread ---
def run_panel():
    pn.serve({
        "/observed": pw.get_panel_layout,
        "/forecast": pw.get_forecast_layout,
        }, port=5010, show=False,
             websocket_origin=["localhost:5000", "localhost:5010", "127.0.0.1:5000", "127.0.0.1:5010"])


@app.route('/')
def home():

    user_id = session['user_id']
    img1 = f'images/user_sessions/{user_id}/hurricane_percentiles.png'
    img2 = f'images/user_sessions/{user_id}/TC_percentiles.png'
    img3 = f'images/user_sessions/{user_id}/ACE_percentiles.png'
    img4 = f'images/user_sessions/{user_id}/PDI_percentiles.png'

    return render_template(
        'observed_page.html',
        user_id=user_id,
        img1=img1,
        img2=img2,
        img3=img3,
        img4=img4
    )
#make one of these homepages


@app.route('/observed', methods = ["GET", "POST"])
def observed():
    if request.method == "POST":
        start_year = int(request.form["start_year"])
        end_year = int(request.form["end_year"])
        gg.update_graphs(start_year, end_year)
        utils.update_session_timestamp(user_id = session['user_id'])
    
    user_id = session['user_id']
    img1 = f'images/user_sessions/{user_id}/hurricane_percentiles.png'
    img2 = f'images/user_sessions/{user_id}/TC_percentiles.png'
    img3 = f'images/user_sessions/{user_id}/ACE_percentiles.png'
    img4 = f'images/user_sessions/{user_id}/PDI_percentiles.png'

    return render_template(
        'observed_page.html',
        user_id=session['user_id'],
        img1=img1,
        img2=img2,
        img3=img3,
        img4=img4
    )


@app.route('/forecast')
def forecast():
    return render_template('forecast_page.html', user_id=session['user_id']) 


if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        # Only run these once in the reloaded process
        Thread(target=background_updater, daemon=True).start()
        Thread(target=run_panel, daemon=True).start()

    app.run(port=5000, debug=True)