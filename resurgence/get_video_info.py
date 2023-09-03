from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
import re
import time

from googleapiclient.discovery import build
import json

from db import get_db

bp = Blueprint('get_video_info', __name__)

api_key = 'AIzaSyCFk_r-Jo70qntW0FBfaRAV_Rr1b14X0kc'

def single_video_info(url, driver):

    driver.get(url)
    time.sleep(2)
    driver.execute_script("window.scrollBy(0,700)","")
    clickable = driver.find_element(By.ID, 'expand')
    clickable.click()
    # wait = WebDriverWait(driver, 20)
    # wait.until(EC.element_to_be_clickable((By.ID, 'snippet'))).click()

    title = driver.find_element(By.XPATH, '//div[@id="title"]/h1[1]/yt-formatted-string').text
    re.sub(r'\W+', '', title)
    channel = driver.find_element(By.XPATH, '//ytd-channel-name[@id="channel-name"]/div/div/yt-formatted-string/a').text
    sub_count = driver.find_element(By.XPATH, '//yt-formatted-string[@id="owner-sub-count"]').text
    sub_count = sub_count.replace(' subscribers', '')
    vid_date = driver.find_element(By.XPATH, '//yt-formatted-string[@id="info"]/span[3]').text
    vid_views = driver.find_element(By.XPATH, '//yt-formatted-string[@id="info"]/span[1]').text
    vid_views = vid_views.replace(' views', '')
    tags = driver.find_element(By.NAME, "keywords").get_attribute("content")

    return title,channel,sub_count,vid_date,vid_views,tags


def playlist_info(playlist, id):
    df2 = pd.DataFrame(columns = ['playlist_id', 'video_url', 'video_title', 'channel_name', 'sub_count', 'video_date', 'views', 'tags'])
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(playlist)
    time.sleep(3)
    list_of_vids = driver.find_elements(By.ID, "video-title")
    list_of_vids = driver.find_elements(By.XPATH, '//a[@id="video-title"]')
    list_of_urls = [i.get_attribute("href") for i in list_of_vids]
    for url in list_of_urls:
        title,channel,sub_count,vid_date,views,vid_tags = single_video_info(url, driver)
        dict1 = {'playlist_id': id, 'video_url':url, 'video_title':title, 'channel_name':channel, 'sub_count':sub_count, 'video_date':vid_date, 'views':views, 'tags':vid_tags}
        # Add information to a dataframe
        df_dict = pd.DataFrame([dict1])

        df2 = pd.concat([df2, df_dict], ignore_index=True)
    
    return df2


def get_playlist_name(playlist):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(playlist)

    title = driver.find_element(By.XPATH, "//*[@name='title']").get_attribute("content")
    return title


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
        vid_date = vid_date.replace('T', ' ')
        vid_date = vid_date.replace('Z', '')
        vid_views = response['statistics']['viewCount']
        tags = []
        if 'tags' in response['snippet']:
            tags = response['snippet']['tags']

        # We need to make another request to get the sub count of the channel that
        # posted the video
        request = service.channels().list(
            part='statistics',
            id = channel_id
        )
        response = request.execute()
        sub_count = response['items'][0]['statistics']['subscriberCount']

        # Check if user is logged in; if so, insert one new entry in video
        # and i entries in tag, where i = number of tags this video has
        if g.user:
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
            playlistId = playlist_id
        )
        response = request.execute()
        video_list = []
        for item in response['items']:
            video_list.append(item['contentDetails']['videoId'])

        playlist_df = pd.DataFrame(columns = ['playlist_id', 'video_url', 'video_title', 'channel_name', 'sub_count', 'video_date', 'views', 'tags'])
        playlist_df['tags'] = playlist_df['tags'].astype(object)

        for video in video_list:
            title, channel, sub_count, vid_date, views, vid_tags = api_get_video_info(video, sql_id)
            vid_url = "https://youtu.be/" + video
            dict1 = {'playlist_id': sql_id, 'video_url':vid_url, 'video_title':title, 'channel_name':channel, 'sub_count':sub_count, 'video_date':vid_date, 'views':views, 'tags':vid_tags}
            df_dict = pd.DataFrame([dict1])

            playlist_df = pd.concat([playlist_df, df_dict], ignore_index=True)

        return playlist_df



def frequent_tags(dataframe):
    tag_col = dataframe.loc[:,"Tags"]
    


def main():

    # playlist = "https://www.youtube.com/playlist?list=PLER_tGgYixxlJgDAu94M5X29ze9x8koml"
    # title = get_playlist_name(playlist)
    # print(title)

    # dataframe = playlist_info(playlist)
    # print(dataframe.size)

    title,channel,sub_count,vid_date,vid_views,tags = api_get_video_info('BPSh5r2xF_U', 1)
    print(title)
    print(channel)
    print(sub_count)
    print(vid_date)
    print(vid_views)
    print(tags)

    test_playlist_id = 'PLxn4rjamqFgj8m8tvKgjRRz6Kx6DLqunI'
    dataframe = api_get_playlist_info(test_playlist_id, 1)
    title = api_get_playlist_title(test_playlist_id)
    print(title)
    print(dataframe)

    return

    df = pd.read_csv("videos.csv", encoding='ISO-8859-1')
    urls_list = df['urls'].to_list()

    # Go through list of URLs
    df2 = pd.DataFrame(columns = ['URL', 'Title', 'Channel Name', 'Sub Count', 'Date', 'Views', 'Tags'])
    for x in urls_list:
        # Extract information for each URL
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        title,channel,sub_count,vid_date,views,vid_tags = single_video_info(x, driver)
        
        dict1 = {'URL':x, 'Title':title, 'Channel Name':channel, 'Sub Count':sub_count, 'Date':vid_date, 'Views':views, 'Tags':vid_tags}
        # Add information to a dataframe
        df_dict = pd.DataFrame([dict1])

        df2 = pd.concat([df2, df_dict], ignore_index=True)

    # Dataframe is converted to CSV for readability
    df2.to_csv("vid-list.csv")

if __name__ == '__main__':
    main()