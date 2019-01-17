# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import pymysql
from zhihuscrapy.settings import MYSQL_HOST, MYSQL_DBNAME, MYSQL_USER, MYSQL_PASSWD
from zhihuscrapy.items import ZhihuPeopleItem, ZhihuRelationItem
# from zhihu.tools.async import download_pic



# class ZhihuscrapyPipeline(object):
#     def process_item(self, item, spider):
#         return item

class ZhihuPipeline(object):
    """
    存储数据
    """

    def __init__(self):
        # 连接数据库
        self.connect = pymysql.connect(
            host=MYSQL_HOST,
            db=MYSQL_DBNAME,
            user=MYSQL_USER,
            passwd=MYSQL_PASSWD,
            # charset='utf8',
            use_unicode=True)

        # 通过cursor执行增删查改
        self.cursor = self.connect.cursor()


    # @classmethod
    # def from_crawler(cls, crawler):
    #     return cls(
    #         mongo_uri=MONGO_URI,
    #         mongo_db='zhihu',
    #         image_dir=os.path.join(PROJECT_DIR, 'images')
    #     )

    # def open_spider(self, spider):
    #     self.client = MongoClient(self.mongo_uri)
    #     self.db = self.client[self.mongo_db]
    #     if not os.path.exists(self.image_dir):
    #         os.mkdir(self.image_dir)
    #
    # def close_spider(self, spider):
    #     self.client.close()

    def _process_people(self, item):
        """
        存储用户信息
        """

        try:
            # 插入数据
            sql = """replace into zhihu_user(nickname,zhihu_id, gender, image_url, location, business, employment, 
                position, education, school_name, major, followee_count, follower_count) 
                values('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s, %s);""" %\
                (item['nickname'],
                 item['zhihu_id'],
                 item['gender'],
                 pymysql.escape_string(item['image_url']),
                 item['location'],
                 item['business'],
                 item['employment'],
                 item['position'],
                 item['education'],
                 item['school_name'],
                 item['major'],
                 item['followee_count'],
                 item['follower_count']
                 )
            self.cursor.execute(sql
                )

            # 提交sql语句
            self.connect.commit()

        except Exception as error:
            # 出现错误时打印错误日志
            print(error, '存储用户信息出错')
            print(sql)


    def _process_relation(self, item):
        """
        存储人际拓扑关系
        """
        try:
            # select * from focus where zhihu_id=
            # 插入数据
            self.cursor.execute(
                """replace into focus(zhihu_id,user_list,user_type) values(%s, %s, %s);""",
                (item['zhihu_id'],
                 item['user_list'],
                 item['user_type']
                 ))
            # 提交sql语句
            self.connect.commit()
        except Exception as error:
            # 出现错误时打印错误日志
           print(error, '存储人际关系出错')

    def process_item(self, item, spider):
        """
        处理item
        """
        if isinstance(item, ZhihuPeopleItem):
            self._process_people(item)
        elif isinstance(item, ZhihuRelationItem):
            self._process_relation(item)
        return item