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

        # Make sure URL is valid
        error = None
        if not url or url == "blank":
            error = 'Error: Please enter a valid URL'
        
        if error is None:

            dataframe = ""

            playlist_name = get_video_info.api_get_playlist_title(url)
            # If user is logged in, we need to make a new playlist entry
            # and associate each video in the playlist with that entry
            # If not logged in, just make the playlist 0 (it won't be used)
            if g.user:
                db = get_db()
                cursor = db.cursor()
                cursor.execute(
                    "INSERT INTO playlist (owner_id, playlist_title, playlist_url)"
                    " VALUES (?, ?, ?)",
                    (g.user['id'], playlist_name, url)
                )
                playlist_id = cursor.lastrowid
                print(playlist_id)
                db.commit()
                dataframe = get_video_info.api_get_playlist_info(url, playlist_id)
            else:
                dataframe = get_video_info.api_get_playlist_info(url, 0)
            

            # Add HTML id tags to make formatting easier            
            html_df = dataframe.to_html(columns=['video_url', 'video_title', 'channel_name', 'sub_count', 'video_date', 'views', 'tags'], 
                                        index=False,justify="center", classes='table table-striped', render_links=True)
            
            html_df = html_df.replace("<th>video_url</th>", "<th id='url' onclick='sortTable(0)'>URL</th>")
            html_df = html_df.replace("<th>video_title</th>", "<th id='title' onclick='sortTable(1)'>Title</th>")
            html_df = html_df.replace("<th>channel_name</th>", "<th id='channel' onclick='sortTable(2)'>Channel Name</th>")
            html_df = html_df.replace("<th>sub_count</th>", "<th id='sub' onclick='sortTable(3)'>Sub Count</th>")
            html_df = html_df.replace("<th>video_date</th>", "<th id='date' onclick='sortTable(4)'>Date</th>")
            html_df = html_df.replace("<th>views</th>", "<th id='views' onclick='sortTable(5)'>Views</th>")
            html_df = html_df.replace("<th>tags</th>", "<th id='tags' onclick='sortTable(6)'>Tags</th>")

            # If user is not logged in, simply display results
            # if not g.user:
            #     return render_template('results.html', playlist_name=playlist_name, dataframe=html_df)

            # If user is logged in, convert dataframe to sql and append it to the videos table
            # db = get_db()
            # cursor = db.cursor()
            # rows_affected = dataframe.to_sql('video', con=cursor, if_exists="append", index=False)
            # print(rows_affected)
            # db.commit()

            return render_template('results.html', playlist_name=playlist_name, dataframe=html_df)
        
        flash(error)

    return render_template('video_analysis.html')
