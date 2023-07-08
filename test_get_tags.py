from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import requests
from requests_html import HTMLSession
import pandas as pd
import time
import re
import numpy as np

def get_youtube_info(url, ua, crawl_delay):
    header = {"user-agent": ua.random}
    time.sleep(crawl_delay)

    request = requests.get(url,headers=header,verify=True)
    soup = BeautifulSoup(request.text,"html.parser")
    tags = soup.find_all("meta",property="og:video:tag")
    # titles = soup.find("span", class_="watch-title")
    titles = soup.find("head").text

    # try:
    #     getdesc = re.search('description\":{\"simpleText\":\".*\"',request.text)
    #     desc = getdesc.group(0)
    #     desc = desc.replace('description":{"simpleText":"','')
    #     desc = desc.replace('"','')
    #     desc = desc.replace('\n','')
    # except:
    #     desc = "n/a"
    
    getdate = re.search('[a-zA-z]{3}\s[0-9]{1,2},\s[0-9]{4}',request.text)
    vid_date = getdate.group(0)

    getviews = re.search('[0-9,]+\sviews',request.text)
    vid_views = getviews.group(0)

    return tags,titles,vid_date,vid_views

def main():
    df = pd.read_csv("videos.csv", encoding='ISO-8859-1')
    urls_list = df['urls'].to_list()

    # test_url = "https://youtu.be/2uihTs4D7UU"
    # r = requests.get(test_url)
    # s = BeautifulSoup(r.text, "html.parser")
    # title = s.find("head").text

    ua = UserAgent()
    delays = [*range(10,22,1)]

    df2 = pd.DataFrame(columns = ['URL', 'Title', 'Date', 'Views', 'Tags'])
    for x in urls_list:
        crawl_delay = np.random.choice(delays)
        vid_tags,title,vid_date,views = get_youtube_info(x, ua, crawl_delay)

        vid_tag_list = ""
        for i in vid_tags:
            vid_tag_list += i['content'] + ', '
        
        title = title.replace(' - YouTube', '')
        dict1 = {'URL':x, 'Title':title, 'Date':vid_date, 'Views':views, 'Tags':vid_tag_list}
        df_dict = pd.DataFrame([dict1])
        # df2 = df2.append(dict1, ignore_index=True)
        df2 = pd.concat([df2, df_dict], ignore_index=True)

    df2.to_csv("vid-list.csv")




if __name__ == '__main__':
    main()