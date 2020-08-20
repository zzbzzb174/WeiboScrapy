# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

# import scrapy


# class Blog(scrapy.Item):
#     '''
#     定义需要爬取的字段及类型
#     '''
#     uid = scrapy.Field(serializer=str)          # 用户id
#     uname = scrapy.Field(serializer=str)        # 用户名称
#     city = scrapy.Field(serializer=str)         # 用户地址(精确到城市或省份)
#     gender = scrapy.Field(serializer=str)       # 用户性别
#     time = scrapy.Field(serializer=str)         # blog创建时间
#     text = scrapy.Field(serializer=str)         # 微博文本
#     location = scrapy.Field(serializer=str)     # 微博地址
