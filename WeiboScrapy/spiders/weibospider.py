import scrapy
import re
import json
from html.parser import HTMLParser
import logging
from datetime import datetime
logger = logging.getLogger(__name__)


class Blog(scrapy.Item):
    '''
    定义需要爬取的字段及类型
    '''
    _id = scrapy.Field(serializer=str)          # 微博id
    uid = scrapy.Field(serializer=str)          # 用户id
    uname = scrapy.Field(serializer=str)        # 用户名称
    city = scrapy.Field(serializer=str)         # 用户地址(精确到城市或省份)
    gender = scrapy.Field(serializer=str)       # 用户性别
    time = scrapy.Field(serializer=str)         # blog创建时间
    text = scrapy.Field(serializer=str)         # 微博文本
    # location = scrapy.Field(serializer=str)     # 微博地址


class WeibospiderSpider(scrapy.Spider):
    name = 'weibospider'

    start_urls = [
        'https://m.weibo.cn'
    ]

    def parse(self, response):
        '''
        初始化Item：Blog
        :param response:
        :return:
        '''
        blog = Blog()
        # 筛选要爬取的数据, response为字符串格式
        # traverse each page
        for page in json.loads(response.body):
            page = json.loads(page)
            for card in page["data"]["cards"]:
                if "card_group" in card:
                    mblog = card["card_group"][0]["mblog"]
                    itemid = card["card_group"][1]["itemid"]
                elif "card_group" not in card:
                    mblog = card["mblog"]
                    itemid = card["itemid"]
                # fill items
                blog['_id'] = mblog['mid']
                blog['uid'] = mblog["user"]["id"]
                blog['uname'] = mblog["user"]["screen_name"]
                blog['city'] = mblog["user"]["city"]  # 后补
                blog['gender'] = mblog["user"]["gender"]
                time = re.findall(
                    r'qtime=\d{10}', itemid)[0][-10:]
                blog['time'] = datetime.fromtimestamp(int(time))
                # 处理字符串
                if mblog["isLongText"] is True:
                    text = mblog["longText"]["longTextContent"]
                else:
                    text = HTMLParser().unescape(mblog["text"])
                blog['text'] = re.sub(r'<span class="url-icon".*?span>|<a.*?</a>|<br />|\n',
                                      '', text)  # 除去emoji, 链接, 换行符
                # # 处理微博地址信息
                # location=re.findall(r'<span class="surl-text">[^#].*?span>', text)
                # if len(location) > 0:
                #     blog['location']=location[0]
                # else:
                #     blog['location']=""

                yield blog

        # # 下一页
        # # https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D61%26q%3D%E5%8D%97%E4%BA%AC%26t%3D0&page_type=searchall&page=2
        # index = int(re.findall(r'page=\d*', response.url)[0][5:]) + 1
        # start_url = re.findall(r'https:.*page=', response.url)
        # url = start_url + index
        # if url:
        #     yield scrapy.Request(url, callback=self.parse)

        # /html/body/div/div[1]/div[1]/div[2]/div[2]/div[1]/div/div/div/ul/li[1]/span
        # /html/body/div/div[1]/div[1]/div[2]/div[2]/div[1]/div/div/div/ul/li[3]/span

        # https://m.weibo.cn/p/index?containerid=230283<1553000681>_-_INFO
