import requests
from bs4 import BeautifulSoup
import os
import shutil
from urllib.parse import urlparse, urlunparse
import time
import random
import json
from threading import Thread

# List of User-Agents to rotate
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def download_video(video_url, save_path, retries=3):
    for attempt in range(1, retries + 1):
        try:
            headers = {'User-Agent': get_random_user_agent()}
            response = requests.get(video_url, headers=headers, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            file.write(chunk)
                return True
            time.sleep(15)
        except requests.exceptions.RequestException:
            time.sleep(15)
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

def save_progress(progress_data, filename='progress.json'):
    with open(filename, 'w') as f:
        json.dump(progress_data, f, indent=4)

def load_progress(filename='progress.json'):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def print_progress(total, success, fail):
    while success + fail < total:
        print(f"[INFO] Download progress: {success + fail}/{total} videos downloaded")
        time.sleep(10)

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
    total_urls = len(cleaned_urls)
    print(f"[INFO] Total URLs: {total_urls}")

    progress_data = load_progress()
    for url in cleaned_urls:
        if url not in progress_data:
            progress_data[url] = {'status': 'pending', 'attempts': 0}

    download_success = 0
    download_fail = 0

    progress_thread = Thread(target=print_progress, args=(total_urls, download_success, download_fail))
    progress_thread.start()

    for url in cleaned_urls:
        if progress_data[url]['status'] != 'success':
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
                    description_text = description_tag['content'].strip() if description_tag else "no_title"
                    description_text = "".join([c if c.isalnum() or c in (' ', '_', '-') else '_' for c in description_text])

                    date_tag = soup.find('span', class_='time')
                    date_text = date_tag.find('a').get_text().strip().replace(' ', '_') if date_tag and date_tag.find('a') else "unknown_date"

                    video_name = f"{date_text}_{description_text}.mp4"
                    save_path = os.path.join(save_dir, video_name)

                    if download_video(video_url, save_path):
                        download_success += 1
                        progress_data[url] = {'status': 'success', 'attempts': progress_data[url]['attempts'] + 1}
                    else:
                        download_fail += 1
                        progress_data[url] = {'status': 'fail', 'attempts': progress_data[url]['attempts'] + 1}
                else:
                    download_fail += 1
                    progress_data[url] = {'status': 'fail', 'attempts': progress_data[url]['attempts'] + 1}
            else:
                download_fail += 1
                progress_data[url] = {'status': 'fail', 'attempts': progress_data[url]['attempts'] + 1}
            save_progress(progress_data)

    progress_thread.join()

    print("[INFO] Downloading archive complete")
    print(f"[INFO] Total successful downloads: {download_success}")
    print(f"[INFO] Total failed downloads: {download_fail}")

    with open('failed_urls.txt', 'w') as f:
        for url, data in progress_data.items():
            if data['status'] == 'fail':
                f.write(f"{url}\n")

    print("[INFO] Failed URLs saved to failed_urls.txt")
