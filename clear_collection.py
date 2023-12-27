from pymongo import MongoClient

# 连接到MongoDB数据库
client = MongoClient('mongodb://localhost:27017/')
db = client['TT_news']

# ！！！清空数据库
db['articles'].delete_many({})
db['hot_list'].delete_many({})
db['users'].delete_many({})
db['videos'].delete_many({})

# db['administrators'].delete_many({})


