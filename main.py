from threading import Thread
import time
from datetime import datetime
from flask import Flask, render_template
from py import generate_graphs as gg


app = Flask(__name__)

def background_updater():
    last_run_date = None
    while True:
        now = datetime.now()
        # Check if it's the 1st or 15th of the month
        if now.day in [1, 12] and (last_run_date is None or last_run_date.date() != now.date()):
            print(f"Running update on {now}")
            gg.update_graphs()
            print("Done updating!")
            last_run_date = now
        else:
            print(f"No update needed at {now}")
        time.sleep(3600)  # Sleep for an hour to check again

@app.route('/')
def home():
    return render_template('observed_page.html') #make one of these homepages

@app.route('/observed')
def observed():
    return render_template('observed_page.html') 

@app.route('/verification')
def verification():
    return render_template('verification_page.html') 


if __name__ == "__main__":
    updater_thread = Thread(target=background_updater)
    updater_thread.daemon = True
    updater_thread.start()
    app.run(debug=True)