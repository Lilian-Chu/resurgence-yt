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

bp = Blueprint('get_video_info', __name__)

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


def frequent_tags(dataframe):
    tag_col = dataframe.loc[:,"Tags"]
    


def main():

    playlist = "https://www.youtube.com/playlist?list=PLER_tGgYixxlJgDAu94M5X29ze9x8koml"
    title = get_playlist_name(playlist)
    print(title)

    dataframe = playlist_info(playlist)
    print(dataframe.size)

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