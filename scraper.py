import requests
from bs4 import BeautifulSoup
import os

url = "https://web.archive.org/web/20191216031501/https://plays.tv/video/5975203c5add88ca21/ez-ace-"

def download_video(video_url, save_path):
    response = requests.get(video_url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        print(f"Downloaded: {save_path}")
    else:
        print(f"Failed to download: {video_url}")


def find_txt_file():

    current_dir = os.getcwd()
    
    files = os.listdir(current_dir)
    
    for file in files:
        if file.endswith('.txt'):
            return file

def parse_url(save_dir):
    pass


if "__main__" == __name__:
    url_txt_file = find_txt_file()
    save_dir = 'downloaded_videos'
    os.makedirs(save_dir, exist_ok=True)

    print(url_txt_file)

    parse_url()

    response = requests.get(url)
    if response.status_code == 200:
        content = response.content
        soup = BeautifulSoup(content, 'html.parser')
        
        for video in soup.find_all('source', type='video/mp4'):
            video_url = video['src']
            
            if video_url.startswith('//'):
                video_url = 'https:' + video_url

            if "/processed/" in video_url:
                video_url = video_url.replace("/480.mp4", "/720.mp4")
            
            video_name = os.path.basename(video_url)
            save_path = os.path.join(save_dir, video_name)
            
            download_video(video_url, save_path)
    else:
        print(f"Failed to fetch the page: {url}")