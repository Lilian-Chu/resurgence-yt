from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
import sys
sys.path.append('C:\\Users\\lilia\\OneDrive\\Documents\\Resume Projects\\scrape_youtube\\resurgence')
import get_video_info
import pandas as pd
import sqlite3

from resurgence.db import get_db

bp = Blueprint('home', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/tools', methods=('GET', 'POST'))
def video_analysis():
    if request.method == 'GET':
        return render_template('video_analysis.html')
    else:
        url = request.form['url']
        error = None
        if not url or url == "blank":
            error = 'Error: Please enter a valid URL'
        
        if error is None:
            playlist_name = get_video_info.get_playlist_name(url)
            dataframe = get_video_info.playlist_info(url)
            db = get_db()
            dataframe.to_sql('pd_df', db)
            
            html_df = dataframe.to_html(index=False,justify="center", classes='table table-striped', render_links=True)
            print(playlist_name)
            html_df = html_df.replace("<th>URL</th>", "<th id='url' onclick='sortTable(0)'>URL</th>")
            html_df = html_df.replace("<th>Title</th>", "<th id='title' onclick='sortTable(1)'>Title</th>")
            html_df = html_df.replace("<th>Channel Name</th>", "<th id='channel' onclick='sortTable(2)'>Channel Name</th>")
            html_df = html_df.replace("<th>Sub Count</th>", "<th id='sub' onclick='sortTable(3)'>Sub Count</th>")
            html_df = html_df.replace("<th>Date</th>", "<th id='date' onclick='sortTable(4)'>Date</th>")
            html_df = html_df.replace("<th>Views</th>", "<th id='views' onclick='sortTable(5)'>Views</th>")
            html_df = html_df.replace("<th>Tags</th>", "<th id='tags' onclick='sortTable(6)'>Tags</th>")
            print(html_df.find("<th id='url' onclick='sortTable(0)'>URL</th>"))

            with open("text.txt", "w") as text_file:
                text_file.write(html_df)

            if g.user:
                db = get_db()
                db.execute(
                    "INSERT INTO info (playlist_title, html_df, owner_id)"
                    " VALUES (?, ?, ?)",
                    (playlist_name, html_df, g.user['id'])
                )
                db.commit()

            return render_template('results.html', playlist_name=playlist_name, dataframe=html_df)
        
        flash(error)

    return render_template('video_analysis.html')
