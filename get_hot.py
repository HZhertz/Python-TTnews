import requests
import json
import re
from bs4 import BeautifulSoup
from pymongo import errors
from urllib.parse import unquote
from get_news import get_article_info, get_author_info, add_author, get_video_info, get_signature, take_article, take_video, articles_collection, videos_collection
from get_news import HEADERS_, hot_list_collection


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
        article_id = re.findall(r'\d+', url)[0]
        print(article_id)
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
            'ArticleId': article_id,
            'AuthorInfo': {
                'user_id': author_info['user_id'],
                'source_id': author_info['source_id'],
            }
        }
    elif url.startswith("https://www.toutiao.com/video/"):
        news_type = 'video'
        video_id = re.findall(r'\d+', url)[0]
        print(video_id)
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
            'VideoId': video_id,
            'AuthorInfo': {
                'user_id': author_info['user_id'],
                'source_id': author_info['source_id'],
            }
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
    article_list = []
    video_list = []
    response = requests.get(url)
    data = response.json()
    data_list = data["data"]
    size = len(data_list)
    print(f"获取到{size}条热点列表数据")
    for item in data_list:
        print('<----newItem:', item)
        hot_event_data = take_hot_event(item)
        if hot_event_data:
            print(hot_event_data['Url'], hot_event_data['Type'])
            if hot_event_data['Type'] == 'article':
                take_article(
                    article_list,
                    {
                        'group_id': hot_event_data['ArticleId'],
                        'user_info': {
                            'user_id': hot_event_data['AuthorInfo']['source_id']
                        }
                    },
                    {
                        'name': 'hot',
                        'channel_id': '3189398996',
                        'signature': 'hot_sig'
                    }, 'avatar_hide|image_none')
            if hot_event_data['Type'] == 'video':
                take_video(
                    video_list,
                    {
                        'group_id': hot_event_data['VideoId'],
                        'user_info': {
                            'user_id': hot_event_data['AuthorInfo']['source_id']
                        }
                    },
                    {
                        'name': 'hot',
                        'channel_id': '3189398996',
                        'signature': 'hot_sig'
                    }, 'avatar_hide|image_large|video')
            hot_event_list.append(hot_event_data)

            print(f"---->第{len(hot_event_list)}条{hot_event_data['Type']}热点数据:{hot_event_data}")
    # 将获取到的数据更新到数据库
    try:
        result = hot_list_collection.insert_many(hot_event_list, ordered=False)
        inserted_count = len(result.inserted_ids)
        print(f"Successfully inserted {inserted_count} hot_event documents to hot_list.")
        if article_list:
            result_all = articles_collection.insert_many(article_list, ordered=False)
            inserted_count_all = len(result_all.inserted_ids)
            print(f"Successfully inserted {inserted_count_all} hot_event documents to articles.")
        if video_list:
            result_video = videos_collection.insert_many(video_list, ordered=False)
            inserted_count_video = len(result_video.inserted_ids)
            print(f"Successfully inserted {inserted_count_video} video documents to videos from hot_event.")
        print('\n')
    except errors.BulkWriteError as e:
        # 处理错误
        print(e.details)


# 获取热点列表
get_hot_event()
