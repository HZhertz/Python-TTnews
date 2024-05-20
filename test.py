import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote

# 传入url，查看从id为RENDER_DATA的script标签中获取的数据结构
HEADERS_ = {
    "Cookie": "ttwid=1%7Ctl1VFtYWJj3stLmKsWVg-ZfD7GpsUkBe18GanjhfZKY%7C1702479662%7C58d34dfbb056ede9cc6f0e57640c23c4a61f7f0ce0b15ba2da3c28423967a8c7",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

url = "https://www.toutiao.com/c/user/token/MS4wLjABAAAAquxMiIRojSXeDqoE1oo6MnwTCAfdPSN1rvvHrjzEHls/"

res = requests.get(url, headers=HEADERS_)
soup = BeautifulSoup(res.text, 'html.parser')
encoded_str = soup.find('script', {'id': 'RENDER_DATA'}).string
render_data = json.loads(unquote(encoded_str))

print(render_data)
