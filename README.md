# Python-TTnews
python爬虫文件，爬取今日头条首页各频道新闻信息（文章与视频），用于 [Vue3-TT-news-user](https://github.com/HZhertz-JXjrtyx/Vue3-TT-news-user) 添加新闻数据。
图片与视频资源会下载到本地文件夹，新闻信息会存储到mongoDB数据库。

需要安装node.js环境以及 ffmpeg 并进行相关环境配置，
今日头条的请求需要携带 _signature 参数，此参数可以通过运行 get_signature.js 脚本文件获得，
获取的视频信息中音频与视频资源是分开的，需要通过 ffmpeg 合并音频与视频
