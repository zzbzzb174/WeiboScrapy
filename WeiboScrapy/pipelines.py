# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from pymongo import MongoClient
from scrapy.utils.project import get_project_settings
settings = get_project_settings()


class DuplicatesPipeline(object):
    def __init__(self):
        self.ids_seen = set()
        self.texts_seen = set()

    def process_item(self, item, spider):
        '''
        用于去重的过滤器
        '''
        if item['_id'] in self.ids_seen:
            raise DropItem("Duplicate id item found: %s" % item)
        else:
            self.ids_seen.add(item['_id'])
            if item['text'][0:20] in self.texts_seen:
                raise DropItem("Duplicate text item found: %s" % item)
            else:
                self.ids_seen.add(item['_id'][0:20])
                return item


class MongoPipeline(object):
    def __init__(self):
        client = MongoClient(
            host=settings['MONGO_HOST'], port=settings['MONGO_PORT'])
        self.db = client[settings['MONGO_DB']]
        self.coll = self.db[settings['MONGO_COLL']]  # 获得collection的句柄
        # 数据库登录需要帐号密码的话
        self.db.authenticate(settings['MONGO_USER'], settings['MONGO_PSW'])

    def process_item(self, item, spider):
        if item['city'] != "" and item['city'] != "其他" and item['city'].startswith('海外') != True:
            postItem = dict(item)  # 把item转化成字典形式
            self.db.scrapy.insert(postItem)  # 向数据库插入一条记录
            return item  # 会在控制台输出原item数据，可以选择不写
        else:
            raise DropItem("City invalid in %s" % item)
