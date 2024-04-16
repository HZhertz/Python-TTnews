import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote

HEADERS_ = {
    "Cookie": "ttwid=1%7Ctl1VFtYWJj3stLmKsWVg-ZfD7GpsUkBe18GanjhfZKY%7C1702479662%7C58d34dfbb056ede9cc6f0e57640c23c4a61f7f0ce0b15ba2da3c28423967a8c7",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

url = "https://www.toutiao.com/trending/7357733068578226216/?category_name=topic_innerflow&event_type=hot_board&log_pb=%7B%22category_name%22%3A%22topic_innerflow%22%2C%22cluster_type%22%3A%222%22%2C%22enter_from%22%3A%22click_category%22%2C%22entrance_hotspot%22%3A%22outside%22%2C%22event_type%22%3A%22hot_board%22%2C%22hot_board_cluster_id%22%3A%227357733068578226216%22%2C%22hot_board_impr_id%22%3A%2220240416110519150621CD4E943B0D9133%22%2C%22jump_page%22%3A%22hot_board_page%22%2C%22location%22%3A%22news_hot_card%22%2C%22page_location%22%3A%22hot_board_page%22%2C%22rank%22%3A%221%22%2C%22source%22%3A%22trending_tab%22%2C%22style_id%22%3A%2240132%22%2C%22title%22%3A%22%E4%B8%8E%E9%86%89%E6%B1%89%E5%86%B2%E7%AA%81%E8%A2%AB%E5%88%91%E6%8B%98%E7%94%B7%E7%94%9F%E7%88%B6%E4%BA%B2%E7%A7%B0%E6%84%BF%E5%92%8C%E8%A7%A3%22%7D&rank=1&style_id=40132&topic_id=7357733068578226216"

res = requests.get(url, headers=HEADERS_)
soup = BeautifulSoup(res.text, 'html.parser')
encoded_str = soup.find('script', {'id': 'RENDER_DATA'}).string
render_data = json.loads(unquote(encoded_str))

print(render_data)