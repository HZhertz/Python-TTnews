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

all_news_collection = db['ALL_news']
videos_collection = db['videos']
authors_collection = db['authors']
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
        'signature': 'finance_sig',
        'collection': 'finance_news'
    },
    'technology': {
        'name': 'technology',
        'channel_id': '3189398999',
        'signature': 'technology_sig',
        'collection': 'technology_news'
    },
    'hot': {
        'name': 'hot',
        'channel_id': '3189398996',
        'signature': 'hot_sig',
        'collection': 'hot_news'
    },
    'international': {
        'name': 'international',
        'channel_id': '3189398968',
        'signature': 'international_sig',
        'collection': 'international_news'
    },
    'military': {
        'name': 'military',
        'channel_id': '3189398960',
        'signature': 'military_sig',
        'collection': 'military_news'
    },
    'sports': {
        'name': 'sports',
        'channel_id': '3189398957',
        'signature': 'sports_sig',
        'collection': 'sports_news'
    },
    'entertainment': {
        'name': 'entertainment',
        'channel_id': '3189398972',
        'signature': 'entertainment_sig',
        'collection': 'entertainment_news'
    },
    'digital': {
        'name': 'digital',
        'channel_id': '3189398981',
        'signature': 'digital_sig',
        'collection': 'digital_news'
    },
    'history': {
        'name': 'history',
        'channel_id': '3189398965',
        'signature': 'history_sig',
        'collection': 'history_news'
    },
    'food': {
        'name': 'food',
        'channel_id': '3189399002',
        'signature': 'food_sig',
        'collection': 'food_news'
    },
    'games': {
        'name': 'games',
        'channel_id': '3189398995',
        'signature': 'games_sig',
        'collection': 'games_news'
    },
    'travel': {
        'name': 'travel',
        'channel_id': '3189398983',
        'signature': 'travel_sig',
        'collection': 'travel_news'
    },
    'health': {
        'name': 'health',
        'channel_id': '3189398959',
        'signature': 'health_sig',
        'collection': 'health_news'
    },
    'fashion': {
        'name': 'fashion',
        'channel_id': '3189398984',
        'signature': 'fashion_sig',
        'collection': 'fashion_news'
    },
    'parenting': {
        'name': 'parenting',
        'channel_id': '3189399004',
        'signature': 'parenting_sig',
        'collection': 'parenting_news'
    },
    'video': {
        'name': 'video',
        'channel_id': '3431225546',
        'signature': 'video_sig',
        'collection': 'videos'
    },
}


# 运行js脚本获得_signature参数
def get_signature():
    output = subprocess.check_output(['node', 'get_signature.js'])
    signature = output.decode('utf-8').strip()
    signature_str = re.sub(r'(\w+)(?=:)', r"'\1'", signature)
    signature_dict = ast.literal_eval(signature_str)
    return signature_dict


# 获得作者主页url
def get_author_url(url, type):
    print('----从article/video详情页网页结构中获取作者主页url信息,article/video Url:', url)
    res = requests.get(url, headers=HEADERS_)
    soup = BeautifulSoup(res.text, 'html.parser')
    if type == 'article':
        div = soup.find('div', class_='media-info')
    if type == 'video':
        div = soup.find('div', class_='author-card-wrapper')
    first_a = div.find('a')
    href = first_a['href']
    if not href.startswith("https://www.toutiao.com"):
        href = "https://www.toutiao.com" + href
    print('href:', href)
    return href


# 获得article信息
def get_article_info(url):
    print('----从article详情页id为RENDER_DATA的script标签中获取信息,articleUrl:', url)
    res = requests.get(url, headers=HEADERS_)
    soup = BeautifulSoup(res.text, 'html.parser')
    h1 = soup.find('h1')
    article = soup.find('article')
    encoded_str = soup.find('script', {'id': 'RENDER_DATA'}).string
    render_data = json.loads(unquote(encoded_str))
    try:
        seo_info = render_data['data']['seoTDK']
    except KeyError:
        return
    print('articleH1:', h1)
    return {
        'h1': str(h1),
        'article': str(article),
        'title': seo_info['title'],
        'description': seo_info['description'],
        'keywords': seo_info['keywords'],
        'publish_time': int(seo_info['publishTimestamp']),
        'type': 'article'
    }


# 获得作者信息
def get_author_info(author_url):
    print('----从author详情页id为RENDER_DATA的script标签中获取信息,authorUrl:', author_url)
    res = requests.get(author_url, headers=HEADERS_)
    soup = BeautifulSoup(res.text, 'html.parser')
    encoded_str = soup.find('script', {'id': 'RENDER_DATA'}).string
    render_data = json.loads(unquote(encoded_str))
    media_info = render_data['data']['profileUserInfo']
    print('avatar_url', media_info['avatarUrl'])
    avatar_url = ''
    save_path = 'D:\\TT_news\\TTnews-Api\\public\\author_avatar'
    filename = download_image(media_info['avatarUrl'], save_path)
    if filename is not None:
        avatar_url = 'http://127.0.0.1:3007/author_avatar/' + filename
    if media_info['userVerified']:
        verified_content = media_info['userAuthInfo']['auth_info']
    else:
        verified_content = ''
    print('author:', media_info['name'])
    # 生成一个唯一的author_name
    while True:
        author_name = ''.join(random.choices(string.ascii_letters, k=8))
        if not authors_collection.find_one({'author_name': author_name}):
            break
    return {
        'author_id': media_info['userId'],
        'avatar_url': avatar_url,
        'description': media_info['description'],
        'author_name': author_name,
        'password': '$2a$10$NESWQAk4mCgU1WqNLtX0Gu6w1tSrFDEQY68LxHi2A1.m/R.vIe4/u',
        'nickname': media_info['name'],
        'token': media_info['userId'],
        'author_verified': media_info['userVerified'],
        'verified_content': verified_content
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
    if render_data['data']['initialVideo']['videoPlayInfo']['video_duration'] > 2400:
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
            'publish_time': render_data['data']['initialVideo']['publishTime'],
            'src': src,
            'image_url': render_data['data']['initialVideo']['coverUrl'],
            'type': 'video',
            'vid': render_data['data']['initialVideo']['videoPlayInfo']['video_id'],
            'video_style': video_style
        }
    else:
        return


# 如果作者信息不在数据库，则添加作者
def add_author(author_info):
    if not authors_collection.find_one({'author_id': author_info['author_id']}):
        authors_collection.insert_one(author_info)
        print('新增作者')
    else:
        print('已有作者')


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
    article_id = item['group_id']
    article_url = f"https://www.toutiao.com/article/{article_id}/"
    news_type = 'article'
    style = ui_style.split('|')[1]
    image_list = []
    save_path = 'D:\\TT_news\\TTnews-Api\\public\\article_images'
    if ui_style == 'avatar_hide|image_right':
        filename = download_image(item['middle_image']["url"], save_path)
        if filename is not None:
            image_list = [{'url': 'http://127.0.0.1:3007/article_images/' + filename}]
    elif ui_style == 'avatar_hide|image_list':
        for element in item['image_list']:
            filename = download_image(element['url'], save_path)
            if filename is not None:
                image_list.append({'url': 'http://127.0.0.1:3007/article_images/' + filename})
    article_info = get_article_info(article_url)
    author_url = f"https://www.toutiao.com/c/user/token/{item['user_info']['user_id']}/"
    author_info = get_author_info(author_url)
    # 添加作者
    add_author(author_info)

    news_data = {
        'channel_id': channel_item['channel_id'],
        'article_id': item['group_id'],
        'title': item['title'],
        'url': article_url,
        'type': news_type,
        'ui_style': style,
        'image_list': image_list,
        'publish_time': item['publish_time'],
        'take_time': int(time.time()),
        'article_info': article_info,
        'author_info': author_info,
        'comment_count': 0,
        'comment': []
    }

    news_list.append(news_data)
    print(f"---->第{len(news_list)}条article数据:{news_data}")
    print('@———————————————————————————————————————————————————————————————————————————————————————————————')


def take_video(video_list, item, channel_item, ui_style):
    video_id = item['group_id']
    video_url = f"https://www.toutiao.com/video/{video_id}/"
    news_type = 'video'
    style = ui_style.split('|', 1)[1]
    image_src = ''
    save_path = 'D:\\TT_news\\TTnews-Api\\public\\video_images'
    filename = download_image(item['video_detail_info']['detail_video_large_image']['url'], save_path)
    if filename is not None:
        image_src = 'http://127.0.0.1:3007/video_images/' + filename
    video_info = get_video_info(video_url)
    if not video_info:
        print('The video is too long')
        return
    author_url = f"https://www.toutiao.com/c/user/token/{item['user_info']['user_id']}/"
    author_info = get_author_info(author_url)
    # 添加作者
    add_author(author_info)

    # 设置保存位置
    video_save_path = 'D:\\TT_news\\TTnews-Api\\public\\videos'
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
        video_info['src']['src'] = f'http://127.0.0.1:3007/videos/{video_info["video_id"]}.mp4'
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
        video_info['src']['src'] = f'http://127.0.0.1:3007/videos/{video_info["video_id"]}.mp4'

    video_data = {
        'channel_id': channel_item['channel_id'],
        'video_id': video_id,
        'title': item['title'],
        'url': video_url,
        'type': news_type,
        'ui_style': style,
        'image_src': image_src,
        'publish_time': item['publish_time'],
        'take_time': int(time.time()),
        'video_info': video_info,
        'author_info': author_info,
        'collect_count': 0,
        'comment_count': 0,
        'like_count': 0,
        'comment': []
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
    news_list = []
    video_list = []
    # 一次获取14~16条数据
    for i in range(2):
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
                        take_article(news_list, item, channel_item, ui_style)
                    elif item['log_pb']['ui_style'] == 'avatar_hide|image_right':
                        print('类型:文章image_right')
                        ui_style = item['log_pb']['ui_style']
                        take_article(news_list, item, channel_item, ui_style)
                    elif item['log_pb']['ui_style'] == 'avatar_hide|image_list':
                        print('类型:文章image_list')
                        ui_style = item['log_pb']['ui_style']
                        take_article(news_list, item, channel_item, ui_style)
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
        if news_list:
            result_all = all_news_collection.insert_many(news_list, ordered=False)
            inserted_count_all = len(result_all.inserted_ids)
            print(f"Successfully inserted {inserted_count_all} {channel_item['name']} documents to ALL_news.")
        if video_list:
            result_video = videos_collection.insert_many(video_list, ordered=False)
            inserted_count_video = len(result_video.inserted_ids)
            print(f"Successfully inserted {inserted_count_video} video documents to videos from {channel_item['name']} channel.")
        print('\n')
    except errors.BulkWriteError as e:
        # 处理错误
        print(f"Bulk write error: {e.details}")


# 得到热点事件url
def take_hot_event_url(url):
    print('----从热点trending页获取页面结构信息，trending页url:', url)
    res = requests.get(url, headers=HEADERS_)
    soup = BeautifulSoup(res.text, 'html.parser')
    encoded_str = soup.find('script', {'id': 'RENDER_DATA'}).string
    render_data = json.loads(unquote(encoded_str))
    topic_feed_list = render_data['data']['topicFeedList']
    title_list = []
    for item in topic_feed_list:
        title_list.append(item['title'])
    print(title_list)
    if '事件详情' in title_list:
        print('有事件详情')
        block_title = soup.find('div', class_='block-title', string='事件详情')
        href = block_title.find_next('div', class_='block-content').find('a')['href']
        return href
    elif '官方通报' in title_list:
        print('有官方通报')
        block_title = soup.find('div', class_='block-title', string='官方通报')
        href = block_title.find_next('div', class_='block-content').find('a')['href']
        return href
    else:
        return 'other'


# 得到热点事件信息
def take_hot_event(item):
    if item['Url'].startswith("https://www.toutiao.com/trending/"):
        url = take_hot_event_url(item['Url'])
    else:
        url = item['Url']
    print('----得到热点信息url:', url)
    if url.startswith("https://www.toutiao.com/article/"):
        news_type = 'article'
        article_info = get_article_info(url)
        author_url = get_author_url(url, news_type)
        author_info = get_author_info(author_url)
        # 如果作者信息不在数据库，则添加作者
        add_author(author_info)
        return {
            'ClusterId': item['ClusterId'],
            'Title': item['Title'],
            'LabelUrl': item['LabelUrl'],
            'Label': item['Label'],
            'Url': url,
            'HotValue': item['HotValue'],
            'ImageUrl': item['Image']['url'],
            'LabelDesc': item.get('LabelDesc', ''),
            'Type': news_type,
            'ArticleInfo': article_info,
            'AuthorInfo': author_info
        }
    elif url.startswith("https://www.toutiao.com/video/"):
        news_type = 'video'
        video_info = get_video_info(url)
        if not video_info:
            return
        author_url = get_author_url(url, news_type)
        author_info = get_author_info(author_url)
        # 如果作者信息不在数据库，则添加作者
        add_author(author_info)
        return {
            'ClusterId': item['ClusterId'],
            'Title': item['Title'],
            'LabelUrl': item['LabelUrl'],
            'Label': item['Label'],
            'Url': url,
            'HotValue': item['HotValue'],
            'ImageUrl': item['Image']['url'],
            'LabelDesc': item.get('LabelDesc', ''),
            'Type': news_type,
            'VideoInfo': video_info,
            'AuthorInfo': author_info
        }
    else:
        return None


# 获取热点列表
def get_hot_event():
    # 清理数据库
    hot_list_collection.delete_many({})
    signature_dict = get_signature()
    signature = signature_dict['hot_event_sig']
    url = f"https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc&_signature={signature}"
    print('###热点列表请求URL:', url)
    hot_event_list = []
    response = requests.get(url)
    data = response.json()
    data_list = data["data"]
    size = len(data_list)
    print(f"获取到{size}条热点列表数据")
    for item in data_list:
        print('<----newItem:', item)
        hot_event_data = take_hot_event(item)
        if hot_event_data:
            hot_event_list.append(hot_event_data)
            print(f"---->第{len(hot_event_list)}条{hot_event_data['Type']}热点数据:{hot_event_data}")
    # 将获取到的数据更新到数据库
    try:
        result = hot_list_collection.insert_many(hot_event_list, ordered=False)
        inserted_count = len(result.inserted_ids)
        print(f"Successfully inserted {inserted_count} hot_event documents to hot_list.")
        print('\n')
    except errors.BulkWriteError as e:
        # 处理错误
        print(e.details)


# # 获取财经新闻
# get_news(CHANNEL['finance'])
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
# # # 获取旅游新闻
# get_news(CHANNEL['travel'])
# # 获取养生新闻
# get_news(CHANNEL['health'])
# # 获取时尚新闻
# get_news(CHANNEL['fashion'])
# # 获取育儿新闻
# get_news(CHANNEL['parenting'])
# 获取热点列表
# get_hot_event()

# 获取视频
get_news(CHANNEL['video'])