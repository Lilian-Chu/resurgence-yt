from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

def main():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://www.youtube.com/@RevityRime/videos")

    channel_title = driver.find_element(By.XPATH, '//yt-formatted-string[contains(@class, "ytd-channel-name")]').text
    print(channel_title)
    subscriber_count = driver.find_element(By.XPATH, '//yt-formatted-string[@id="subscriber-count"]').text
    print(subscriber_count)

    titles = driver.find_elements(By.ID, "video-title")
    views = driver.find_elements(By.XPATH,'//div[@id="metadata-line"]/span[1]')

    videos = []
    for title, view in zip(titles, views):
        video_dict = { 
            'title': title.text,
            'views': view.text,
        }
        videos.append(video_dict)
    
    print(videos[0])

if __name__ == '__main__':
    main()