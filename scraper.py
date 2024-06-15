import requests
from bs4 import BeautifulSoup
import os
import shutil
from urllib.parse import urlparse, urlunparse
import time
import random

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def download_video(video_url, save_path, retries=5, backoff_factor=1):
    attempt = 0
    while attempt < retries:
        try:
            headers = {'User-Agent': get_random_user_agent()}
            response = requests.get(video_url, headers=headers, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            file.write(chunk)
                time.sleep(5)
                print(f"[SUCCESS] Downloaded: {save_path}")
                return True
            else:
                time.sleep(2)
                print(f"[ERROR] Failed to download (status code {response.status_code}): {video_url}")
                return False
        except requests.exceptions.RequestException as e:
            attempt += 1
            wait_time = backoff_factor * (2 ** (attempt - 1))
            print(f"[WARNING] Attempt {attempt} failed: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    print(f"[ERROR] All retries failed for: {video_url}")
    return False

def find_txt_file():
    current_dir = os.getcwd()
    files = os.listdir(current_dir)
    
    for file in files:
        if file.endswith('.txt'):
            return file

def parse_url(url_txt_file):
    cleaned_urls = set()
    with open(url_txt_file, "r") as file:
        for url in file:
            cleaned_urls.add(remove_query_params(url.strip()))
    return cleaned_urls

def remove_query_params(url):
    parsed_url = urlparse(url)
    cleaned_url = parsed_url._replace(query="")
    return urlunparse(cleaned_url)

if "__main__" == __name__:
    url_txt_file = find_txt_file()
    print("[INFO] Loaded URL file")
    save_dir = 'downloaded_videos'
    if os.path.exists(save_dir):
        shutil.rmtree(save_dir)
        print("[INFO] Removed existing download folder")
    
    os.makedirs(save_dir, exist_ok=True)
    print("[INFO] Created new download folder")
    
    cleaned_urls = parse_url(url_txt_file)

    print(f"[INFO] Total URLs: {len(cleaned_urls)}")

    download_success = 0
    download_fail = 0

    for url in cleaned_urls:
        try:
            headers = {'User-Agent': get_random_user_agent()}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                content = response.content
                soup = BeautifulSoup(content, 'html.parser')
                
                video_tag = soup.find('source', type='video/mp4')
                if video_tag:
                    video_url = video_tag['src']
                    if video_url.startswith('//'):
                        video_url = 'https:' + video_url
                    if "/processed/" in video_url:
                        video_url = video_url.replace("/480.mp4", "/720.mp4")
                    
                    description_tag = soup.find('meta', property='og:title')
                    if description_tag:
                        description_text = description_tag['content'].strip()
                        description_text = "".join([c if c.isalnum() or c in (' ', '_', '-') else '_' for c in description_text])
                    else:
                        description_text = "video"

                    date_tag = soup.find('span', class_='time')
                    if date_tag and date_tag.find('a'):
                        date_text = date_tag.find('a').get_text().strip().replace(' ', '_')
                    else:
                        date_text = "unknown_date"
                    
                    video_name = f"{date_text}_{description_text}.mp4"
                    
                    save_path = os.path.join(save_dir, video_name)
                    state = download_video(video_url, save_path)
                    if state:
                        download_success += 1
                    else:
                        download_fail += 1
                else:
                    print(f"[WARNING] No video tag found in: {url}")
            else:
                print(f"[ERROR] Failed to fetch the page (status code {response.status_code}): {url}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Error fetching page {url}: {e}")

    print("[INFO] Downloading archive complete")
    print(f"[INFO] Total successful downloads: {download_success}")
    print(f"[INFO] Total failed downloads: {download_fail}")
