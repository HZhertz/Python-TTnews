import json
import string
import subprocess
import re
import ast
import requests
import time
import random
import os
from bs4 import BeautifulSoup
from pymongo import MongoClient, errors
from urllib.parse import unquote, urlparse

# 连接到MongoDB服务器
client = MongoClient('mongodb://localhost:27017/')
# 选择数据库
db = client['TT_news']

articles_collection = db['articles']
videos_collection = db['videos']
users_collection = db['users']
hot_list_collection = db['hot_list']

# 设置请求头信息
HEADERS = {
    "Cookie": "tt_webid=7312092887481959973",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}
HEADERS_ = {
    "Cookie": "ttwid=1%7Ctl1VFtYWJj3stLmKsWVg-ZfD7GpsUkBe18GanjhfZKY%7C1702479662%7C58d34dfbb056ede9cc6f0e57640c23c4a61f7f0ce0b15ba2da3c28423967a8c7",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

# 频道信息
CHANNEL = {
    'finance': {
        'name': 'finance',
        'channel_id': '3189399007',
        'signature': 'finance_sig'
    },
    'technology': {
        'name': 'technology',
        'channel_id': '3189398999',
        'signature': 'technology_sig'
    },
    'hot': {
        'name': 'hot',
        'channel_id': '3189398996',
        'signature': 'hot_sig'
    },
    'international': {
        'name': 'international',
        'channel_id': '3189398968',
        'signature': 'international_sig'
    },
    'military': {
        'name': 'military',
        'channel_id': '3189398960',
        'signature': 'military_sig'
    },
    'sports': {
        'name': 'sports',
        'channel_id': '3189398957',
        'signature': 'sports_sig'
    },
    'entertainment': {
        'name': 'entertainment',
        'channel_id': '3189398972',
        'signature': 'entertainment_sig'
    },
    'digital': {
        'name': 'digital',
        'channel_id': '3189398981',
        'signature': 'digital_sig'
    },
    'history': {
        'name': 'history',
        'channel_id': '3189398965',
        'signature': 'history_sig'
    },
    'food': {
        'name': 'food',
        'channel_id': '3189399002',
        'signature': 'food_sig'
    },
    'games': {
        'name': 'games',
        'channel_id': '3189398995',
        'signature': 'games_sig'
    },
    'travel': {
        'name': 'travel',
        'channel_id': '3189398983',
        'signature': 'travel_sig'
    },
    'health': {
        'name': 'health',
        'channel_id': '3189398959',
        'signature': 'health_sig'
    },
    'fashion': {
        'name': 'fashion',
        'channel_id': '3189398984',
        'signature': 'fashion_sig'
    },
    'parenting': {
        'name': 'parenting',
        'channel_id': '3189399004',
        'signature': 'parenting_sig'
    },
    'video': {
        'name': 'video',
        'channel_id': '3431225546',
        'signature': 'video_sig'
    },
}


# 运行js脚本获得_signature参数
def get_signature():
    output = subprocess.check_output(['node', 'get_signature.js'])
    signature = output.decode('utf-8').strip()
    signature_str = re.sub(r'(\w+)(?=:)', r"'\1'", signature)
    signature_dict = ast.literal_eval(signature_str)
    return signature_dict


def get_image_list(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    image_list = [img['src'] for img in soup.find_all('img') if 'src' in img.attrs]
    return image_list


# 获得article信息
def get_article_info(url):
    print('----从article详情页id为RENDER_DATA的script标签中获取信息,articleUrl:', url)
    res = requests.get(url, headers=HEADERS_)
    if res.history:
        print('注意: 请求的URL已重定向到', res.url)
        return
    soup = BeautifulSoup(res.text, 'html.parser')
    encoded_str = soup.find('script', {'id': 'RENDER_DATA'}).string
    render_data = json.loads(unquote(encoded_str))
    try:
        seo_info = render_data['data']['seoTDK']
    except KeyError:
        return
    print('title:', seo_info['title'])
    content = render_data['data']['content']
    image_list = get_image_list(content)
    # print(image_list)
    return {
        'content': content,
        'title': seo_info['title'],
        'description': seo_info['description'],
        'keywords': seo_info['keywords'],
        'publish_time': int(seo_info['publishTimestamp']) * 1000,
        'type': 'article',
        # 'image_list': render_data['data'].get('imageList', [])
        'image_list': image_list
    }


# 获得作者信息
def get_author_info(author_url):
    print('----从author详情页id为RENDER_DATA的script标签中获取信息,authorUrl:', author_url)
    res = requests.get(author_url, headers=HEADERS_)
    soup = BeautifulSoup(res.text, 'html.parser')
    encoded_str = soup.find('script', {'id': 'RENDER_DATA'}).string
    render_data = json.loads(unquote(encoded_str))
    media_info = render_data['data']['profileUserInfo']
    if not media_info.get('mediaId'):
        return
    print('avatar_url', media_info['avatarUrl'])
    avatar_url = ''
    save_path = 'D:\\work\\TTnews\\Vue3-TT-news-api\\public\\user_avatar'
    filename = download_image(media_info['avatarUrl'], save_path)
    if filename is not None:
        avatar_url = 'http://127.0.0.1:3007/user_avatar/' + filename
    if media_info['userVerified']:
        print('media_info', media_info)
        verified_content = media_info['userAuthInfo']['auth_info']
    else:
        verified_content = ''
    print('author:', media_info['name'])

    user_id = int(media_info['mediaId'])

    while True:
        user_name = ''.join(random.choices(string.ascii_letters, k=8))
        if not users_collection.find_one({'user_name': user_name}):
            break
    return {
        'user_id': user_id,
        'source_id': media_info['userId'],
        'user_name': user_name,
        'user_nickname': media_info['name'],
        'user_avatar': avatar_url,
        'user_gender': 0,
        'user_intro': media_info['description'],
        'user_verified': media_info['userVerified'],
        'verified_content': verified_content,
        'user_password': '$2a$10$NESWQAk4mCgU1WqNLtX0Gu6w1tSrFDEQY68LxHi2A1.m/R.vIe4/u',
        'user_email': '',
        'user_phone': '',
        'user_state': 0,
        'browse': {'article': [], 'video': []},
        'like': {'article': [], 'video': [], 'comment': []},
        'collect': {'article': [], 'video': []},
        'fans': [],
        'followers': [],
        'comment': [],
        'message': [],
        'works_count': 1,
        'fans_count': 0,
        'followers_count': 0,
        'comment_count': 0,
        'likes_count': 0,
        'channel': {
            'selected': [0, 1, 2, 3, 4, 5, 6, 7],
            'unselected': [8, 9, 10, 11, 12, 13, 14, 15],
        },

    }


# 获得video信息
def get_video_info(url):
    print('----从video详情页id为RENDER_DATA的script标签中获取信息,videoUrl:', url)
    res = requests.get(url, headers=HEADERS_)
    soup = BeautifulSoup(res.text, 'html.parser')
    encoded_str = soup.find('script', {'id': 'RENDER_DATA'}).string
    render_data = json.loads(unquote(encoded_str))
    try:
        seo_info = render_data['data']['seoTDK']
    except KeyError:
        return
    if render_data['data']['initialVideo']['videoPlayInfo']['video_duration'] < 2400:
        if 'video_list' in render_data['data']['initialVideo']['videoPlayInfo']:
            src = {
                'video_src': render_data['data']['initialVideo']['videoPlayInfo']['video_list'][0]['main_url']
            }
            video_style = 'audio'
        elif 'dynamic_video' in render_data['data']['initialVideo']['videoPlayInfo']:
            src = {
                'video_src': render_data['data']['initialVideo']['videoPlayInfo']['dynamic_video']['dynamic_video_list'][0]['main_url'],
                'audio_src': render_data['data']['initialVideo']['videoPlayInfo']['dynamic_video']['dynamic_audio_list'][0]['main_url']
            }
            video_style = 'noaudio'
        print('videoTitle:', seo_info['title'])
        print('videoStyle:', video_style)
        return {
            'video_id': render_data['data']['initialVideo']['group_id'],
            'title': seo_info['title'],
            'description': seo_info['description'],
            'keywords': seo_info['keywords'],
            'publish_time': render_data['data']['initialVideo']['publishTime'] * 1000,
            'duration': render_data['data']['initialVideo']['videoPlayInfo']['video_duration'],
            'src': src,
            'image_url': render_data['data']['initialVideo']['coverUrl'],
            'type': 'video',
            'video_style': video_style
        }
    else:
        return


# 如果作者信息不在数据库，则添加作者
def add_author(author_info):
    if not users_collection.find_one({'user_id': author_info['user_id']}):
        users_collection.insert_one(author_info)
        print('新增作者')
    else:
        users_collection.update_one({'user_id': author_info['user_id']}, {'$inc': {'works_count': 1}})
        print('已有作者，作品数量+1')


# 下载图片
def download_image(url, save_dir):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        # 解析URL以获取文件名
        a = urlparse(url)
        filename = os.path.basename(a.path)
        # 检查并更改文件扩展名
        file_ext = filename.split('.')[-1]
        if file_ext.lower() == 'image':
            file_ext = 'jpg'
        # 创建唯一的文件名
        filename = ''.join(random.choices(string.ascii_letters + string.digits, k=16)) + '.' + file_ext
        # 创建完整的保存路径
        save_path = os.path.join(save_dir, filename)
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return filename
    else:
        print(f"Failed to download image from {url}")
        return None


# 得到article信息
def take_article(news_list, item, channel_item, ui_style):
    author_url = f"https://www.toutiao.com/c/user/token/{item['user_info']['user_id']}/"
    author_info = get_author_info(author_url)
    if not author_info:
        print('no media_id')
        return
    # 添加作者
    add_author(author_info)

    article_id = item['group_id']
    article_url = f"https://www.toutiao.com/article/{article_id}/"
    style = ui_style.split('|')[1]
    article_info = get_article_info(article_url)
    if not article_info:
        print('no seo_info or redirection')
        return
    content = article_info['content']
    image_list = []
    save_path = 'D:\\work\\TTnews\\Vue3-TT-news-api\\public\\article_images'
    if not article_info['image_list'] == []:
        for element in article_info['image_list']:
            filename = download_image(element, save_path)
            if filename is not None:
                new_url = 'http://127.0.0.1:3007/article_images/' + filename
                image_list.append(new_url)
                content = content.replace(element, new_url)
    article_info['content'] = content
    article_info['image_list'] = image_list

    news_data = {
        'channel_id': channel_item['channel_id'],
        'type': 'article',
        'article_id': item['group_id'],
        'title': article_info['title'],
        'description': article_info['description'],
        'content': article_info['content'],
        'image_list': image_list,
        'cover_list': image_list,
        'publish_time': article_info['publish_time'],
        'keywords': article_info['keywords'],
        'ui_style': style,
        'user_id': author_info['user_id'],
        'view_count': 0,
        'collect_count': 0,
        'comment_count': 0,
        'like_count': 0
    }

    news_list.append(news_data)
    print(f"---->第{len(news_list)}条article数据:{news_data}")
    print('@———————————————————————————————————————————————————————————————————————————————————————————————')


def take_video(video_list, item, channel_item, ui_style):
    author_url = f"https://www.toutiao.com/c/user/token/{item['user_info']['user_id']}/"
    author_info = get_author_info(author_url)
    if not author_info:
        print('no media_id')
        return
    # 添加作者
    add_author(author_info)

    video_id = item['group_id']
    video_url = f"https://www.toutiao.com/video/{video_id}/"
    video_info = get_video_info(video_url)
    if not video_info:
        print('The video is too long')
        return
    style = ui_style.split('|', 1)[1]
    image_src = ''
    save_path = 'D:\\work\\TTnews\\Vue3-TT-news-api\\public\\video_images'
    filename = download_image(video_info['image_url'], save_path)
    if filename is not None:
        image_src = 'http://127.0.0.1:3007/video_images/' + filename

    # 设置保存位置
    video_save_path = 'D:\\work\\TTnews\\Vue3-TT-news-api\\public\\videos'
    # 设置 ffmpeg 可执行文件的绝对路径
    ffmpeg_path = 'D:\\develop\\ffmpeg-6.0-full_build\\bin\\ffmpeg.exe'
    # 输入文件的路径
    video_file = f'{video_save_path}\\video.mp4'
    audio_file = f'{video_save_path}\\audio.mp3'
    if video_info['video_style'] == 'audio':
        # 保存视频,无需合并
        video_src = video_info['src']['video_src']
        video_content = requests.get(video_src).content
        print('保存视频,无需合并', video_info["video_id"])
        with open(f'{video_save_path}/{video_info["video_id"]}.mp4', 'wb') as f:
            f.write(video_content)
        # 更新 video_info
        # video_info['src']['src'] = f'http://127.0.0.1:3007/videos/{video_info["video_id"]}.mp4'
        video_info['video_src'] = f'http://127.0.0.1:3007/videos/{video_info["video_id"]}.mp4'
    elif video_info['video_style'] == 'noaudio':
        # 需要合并视频和音频
        video_src = video_info['src']['video_src']
        audio_src = video_info['src']['audio_src']
        video_content = requests.get(video_src).content
        print('需要合并视频和音频', video_info["video_id"])
        with open(video_file, 'wb') as f:
            f.write(video_content)
        audio_content = requests.get(audio_src).content
        with open(audio_file, 'wb') as f:
            f.write(audio_content)
        # 调用 ffmpeg 命令合并视频和音频
        cmd = f'{ffmpeg_path} -i {video_file} -i {audio_file} -c:v copy -c:a aac {video_save_path}\\{video_info["video_id"]}.mp4'
        subprocess.call(cmd, shell=True)
        # 删除临时文件
        os.remove(video_file)
        os.remove(audio_file)
        # 更新 video_info
        video_info['video_src'] = f'http://127.0.0.1:3007/videos/{video_info["video_id"]}.mp4'

    video_data = {
        'channel_id': channel_item['channel_id'],
        'type': 'video',
        'video_id': video_id,
        'title': video_info['title'],
        'description': video_info['description'],
        'duration': video_info['duration'],
        'video_src': video_info['video_src'],
        'cover_src': image_src,
        'publish_time': video_info['publish_time'],
        'keywords': video_info['keywords'],
        'ui_style': style,
        'user_id': author_info['user_id'],
        'play_count': 0,
        'collect_count': 0,
        'comment_count': 0,
        'like_count': 0,
    }

    video_list.append(video_data)
    print(f"---->第{len(video_list)}条video数据:{video_data}")
    print('@———————————————————————————————————————————————————————————————————————————————————————————————')


# 获取新闻信息
def get_news(channel_item):
    signature_dict = get_signature()
    signature = signature_dict[channel_item['signature']]
    url = f"https://www.toutiao.com/api/pc/list/feed?channel_id={channel_item['channel_id']}&min_behot_time=0&offset=0&category=pc_profile_channel&client_extra_params=%7B" \
          f"%22short_video_item%22:%22filter%22%7D&aid=24&app_name=toutiao_web&_signature={signature}"
    print(f"@@@{channel_item['name']}新闻请求URL:{url}")
    article_list = []
    video_list = []
    # 一次获取14~16条数据
    for i in range(1):
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        data_list = data["data"]
        if channel_item['name'] == 'hot':
            data_list = data["data"][3:]
        size = len(data_list)
        print(f"第{i + 1}次获取到{size}条{channel_item['name']}数据,请求到的数据:{data_list}")

        for item in data_list:
            print('<----newItem:', item)
            if 'card_label' in item and item['card_label'] == '小视频':
                print('小视频')
            elif 'log_pb' in item and 'author_id' in item['log_pb']:
                if 'article_type' in item['log_pb'] and item['log_pb']['article_type'] == 'weitoutiao':
                    print('微头条')
                elif 'ui_style' in item['log_pb']:
                    if item['log_pb']['ui_style'] == 'avatar_hide|image_none':
                        print('类型:文章image_none')
                        ui_style = item['log_pb']['ui_style']
                        take_article(article_list, item, channel_item, ui_style)
                    elif item['log_pb']['ui_style'] == 'avatar_hide|image_right':
                        print('类型:文章image_right')
                        ui_style = item['log_pb']['ui_style']
                        take_article(article_list, item, channel_item, ui_style)
                    elif item['log_pb']['ui_style'] == 'avatar_hide|image_list':
                        print('类型:文章image_list')
                        ui_style = item['log_pb']['ui_style']
                        take_article(article_list, item, channel_item, ui_style)
                    elif item['log_pb']['ui_style'] == 'avatar_hide|image_right|video':
                        print('类型:视频image_right|video')
                        ui_style = item['log_pb']['ui_style']
                        take_video(video_list, item, channel_item, ui_style)
                    elif item['log_pb']['ui_style'] == 'avatar_hide|image_large|video':
                        print('类型:视频image_large|video')
                        ui_style = item['log_pb']['ui_style']
                        take_video(video_list, item, channel_item, ui_style)
                    else:
                        print('other')
                else:
                    print('other')
            else:
                print('other')

        # 每次获取后间隔2~4秒
        time.sleep(random.uniform(2, 4))
    # 将获取到的数据更新到数据库
    try:
        if article_list:
            result_all = articles_collection.insert_many(article_list, ordered=False)
            inserted_count_all = len(result_all.inserted_ids)
            print(f"Successfully inserted {inserted_count_all} {channel_item['name']} documents to articles.")
        if video_list:
            result_video = videos_collection.insert_many(video_list, ordered=False)
            inserted_count_video = len(result_video.inserted_ids)
            print(f"Successfully inserted {inserted_count_video} video documents to videos from {channel_item['name']} channel.")
        print('\n')
    except errors.BulkWriteError as e:
        # 处理错误
        print(f"Bulk write error: {e.details}")


# # 获取财经新闻
get_news(CHANNEL['finance'])
# # 获取科技新闻
# get_news(CHANNEL['technology'])
# # 获取热点新闻
# get_news(CHANNEL['hot'])
# # 获取国际新闻
# get_news(CHANNEL['international'])
# # 获取军事新闻
# get_news(CHANNEL['military'])
# # 获取体育新
# get_news(CHANNEL['sports'])
# # 获取娱乐新闻
# get_news(CHANNEL['entertainment'])
# # 获取数码新闻
# get_news(CHANNEL['digital'])
# # 获取历史新闻
# get_news(CHANNEL['history'])
# # 获取美食新闻
# get_news(CHANNEL['food'])
# # 获取游戏新闻
# get_news(CHANNEL['games'])
# # 获取旅游新闻
# get_news(CHANNEL['travel'])
# # 获取养生新闻
# get_news(CHANNEL['health'])
# # 获取时尚新闻
# get_news(CHANNEL['fashion'])
# # 获取育儿新闻
# get_news(CHANNEL['parenting'])
#
# # 获取视频
get_news(CHANNEL['video'])
