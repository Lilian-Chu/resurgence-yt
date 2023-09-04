from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

import pandas as pd
from googleapiclient.discovery import build
import json
from db import get_db

from dotenv import load_dotenv
import os

bp = Blueprint('get_video_info', __name__)

load_dotenv()
api_key = os.getenv('api_key')

# Uses the YOuTube API to return video details
# Input: video ID YouTube uses to identify a video
# Input: playlist ID used by SQL table
# ID can be obtained from the URL or from playlistitems
# If user is logged in, inserts video and tags into SQL tables
def api_get_video_info(video_id, playlist_sql_id):

    with build('youtube', 'v3', developerKey=api_key) as service:

        request = service.videos().list(
            part='statistics, snippet',
            id=video_id
        )
        response = request.execute()['items'][0]

        title = response['snippet']['title']
        channel = response['snippet']['channelTitle']
        channel_id = response['snippet']['channelId']
        vid_date = response['snippet']['publishedAt']
        # Format publication date + time
        vid_date = vid_date.replace('T', ' ')
        vid_date = vid_date.replace('Z', '')
        vid_views = response['statistics']['viewCount']
        tags = []
        # This conditional is here because tags are optional; field can be empty
        if 'tags' in response['snippet']:
            tags = response['snippet']['tags']

        # We need to make a second request to get the sub count of the
        # channel that posted the video
        request = service.channels().list(
            part='statistics',
            id = channel_id
        )
        response = request.execute()
        sub_count = response['items'][0]['statistics']['subscriberCount']

        # Check if user is logged in; if so, insert one new entry in video
        # and i entries in tag, where i = number of tags this video has
        # We do this here so we don't have to iterate through the dataframe later
        # Can't use to_sql because we also want to add to the tag table
        if False and g.user:
            vid_url = "https://youtu.be/" + video_id
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO video (playlist_id, video_title, video_url, channel_name, sub_count, video_date, views)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (playlist_sql_id, title, vid_url, channel, sub_count, vid_date, vid_views)
            )
            video_sql_id = cursor.lastrowid
            for t in tags:
                cursor.execute(
                    "INSERT INTO tag (tag_text, video_id)"
                    " VALUES (?, ?)",
                    (t, video_sql_id)
                )
            db.commit()

        tags_string = ", "
        tags_string = tags_string.join(tags)
        return title,channel,sub_count,vid_date,vid_views,tags_string


# Uses the YouTube API to return title of a playlist
# We need a separate function to get the title because we need
# sql_id in api_get_playlist_info and need the playlist title
# to insert the entry in playlist before getting the sql_id
def api_get_playlist_title(playlist_id):

    with build('youtube', 'v3', developerKey=api_key) as service:

        request = service.playlists().list(
            part='snippet',
            id=playlist_id
        )
        response = request.execute()
        playlist_title = response['items'][0]['snippet']['title']

        return playlist_title


# Uses the YouTube API to return details of all videos in a playlist
# Input: playlist ID YouTube uses to identify a playlist
# Note: There are two "id"'s here: one id refers to the unique ID used by YoUTube
# sql_id refers to the id used to store SQL information
# We add it at this step to save time later
def api_get_playlist_info(playlist_id, sql_id):
    
    with build('youtube', 'v3', developerKey=api_key) as service:

        # playlistItems retrieves list of videoIDs
        request = service.playlistItems().list(
            part='contentDetails, snippet',
            playlistId = playlist_id,
            maxResults = '20'
        )
        response = request.execute()
        # Store all video id's in video_list
        video_list = []
        for item in response['items']:
            video_list.append(item['contentDetails']['videoId'])
        # Could be multi-page; continuing fetching from next page until we've reached last page
        while ('nextPageToken' in response):
            next_page = response['nextPageToken']
            request = service.playlistItems().list(
                part='contentDetails, snippet',
                playlistId = playlist_id,
                maxResults = '20',
                pageToken = next_page
            )
            response = request.execute()
            for item in response['items']:
                video_list.append(item['contentDetails']['videoId'])

        # Make dataframe to send information to website for display
        playlist_df = pd.DataFrame(columns = ['playlist_id', 'video_url', 'video_title', 'channel_name', 'sub_count', 'video_date', 'views', 'tags'])
        playlist_df['tags'] = playlist_df['tags'].astype(object)

        for video in video_list:
            title, channel, sub_count, vid_date, views, vid_tags = api_get_video_info(video, sql_id)
            # Contruct a YouTube URL for display
            vid_url = "https://youtu.be/" + video
            dict1 = {'playlist_id': sql_id, 'video_url':vid_url, 'video_title':title, 'channel_name':channel, 'sub_count':sub_count, 'video_date':vid_date, 'views':views, 'tags':vid_tags}
            df_dict = pd.DataFrame([dict1])

            playlist_df = pd.concat([playlist_df, df_dict], ignore_index=True)

        return playlist_df


# Returns the k most common tags, given the primary key for a playlist in the playlist table
# Parameters:
#   playlist_sql_id (int) is the key for a playlist in the playlist table
#   k (int) sets how many tags to return. Optional: if not specified, default to 3
# Returns:
#   top_vals (array of strings)
def top_k_frequent_tags(playlist_sql_id, k=3):
    # Get list of videos
    db = get_db()
    videos = db.execute(
        "SELECT * FROM video WHERE playlist_id = ?", (playlist_sql_id,)
    ).fetchall()
    
    # Make list of tags
    tag_list = []
    for v in videos:
        current_tags = db.execute(
            "SELECT tag_text FROM tag WHERE video_id = ?", (v['video_id'],)
        ).fetchall()
        current_tags = [tag[0] for tag in current_tags]
        tag_list.extend(current_tags)
    
    # dict counter uses tags as keys and occurrences as values
    counter = {}
    for tag in tag_list:
        if tag in counter:
            counter[tag] += 1
        else:
            counter[tag] = 1
    
    # sorted_by_value is a list of tuples, where first item is the tag and 
    # second item is the number of occurrences - sort by second item
    sorted_by_value = reversed(sorted(counter.items(), key=lambda kv: kv[1]))
    # Select first k tuples and isolates the tag from each tuple
    top_vals = [item[0] for item in sorted_by_value][:k]

    return top_vals
    
    

def main():

    title,channel,sub_count,vid_date,vid_views,tags = api_get_video_info('BPSh5r2xF_U', 1)
    print(title)
    print(channel)
    print(sub_count)
    print(vid_date)
    print(vid_views)
    print(tags)

    # test_playlist_id = 'PL9qQXSjI-WOqgtYxpBlrJn8d__xzzb8mN'
    # dataframe = api_get_playlist_info(test_playlist_id, 1)
    # title = api_get_playlist_title(test_playlist_id)
    # print(title)
    # print(dataframe)



if __name__ == '__main__':
    main()