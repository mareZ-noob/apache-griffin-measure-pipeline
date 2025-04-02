import json
import csv
from datetime import datetime, timezone

def extract_urls(data: list) -> list:
    posts = []
    
    for user_dict in data:
        for username, user_data in user_dict.items():
            if 'threads' in user_data:
                for thread in user_data['threads']:
                    if 'url' in user_data['user']:
                        len_images = len(thread['images']) if type(thread['images']) == list else None
                        len_videos = len(thread['videos']) if type(thread['videos']) == list else None
                        post = [
                            thread['id'],
                            thread['user_id'],
                            thread['user_verified'],
                            thread['username'],
                            thread['url'],
                            datetime.fromtimestamp(int(thread['published_on']), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z'),
                            thread['text'].replace('\n', ' ').replace('\r', ' ') if thread['text'] else None,
                            len_images,
                            len_videos,
                            thread['has_audio']
                        ]
                        posts.append(post)
    return posts

with open('data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

all_urls = extract_urls(data)

headers = ['id', 'user_id', 'user_verified', 'username', 'url', 'published_on', 'text', \
           'image_count', 'video_count', 'has_audio']


with open('bigdata.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(headers)
    writer.writerows(all_urls)
