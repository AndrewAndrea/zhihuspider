# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import pymysql
from zhihuscrapy.settings import MYSQL_HOST, MYSQL_DBNAME, MYSQL_USER, MYSQL_PASSWD
from zhihuscrapy.items import ZhihuPeopleItem, ZhihuRelationItem
from scrapy import log
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
    #
    # def close_spider(self, spider):
    #     self.client.close()

    def _process_people(self, item):
        """
        存储用户信息
        """
        self.connect.ping(reconnect=True)
        try:
            select_sql = """select * from zhihu_user where (zhihu_id='%s');""" % \
                         (item['zhihu_id'])
            data = self.cursor.execute(select_sql)
            if not data:
                # 插入数据
                sql = """replace into zhihu_user(nickname,zhihu_id, gender, image_url, location, business, employment, 
                    position, education, school_name, major, followee_count, follower_count) 
                    values('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s, %s);""" %\
                    (item['nickname'],
                     item['zhihu_id'],
                     item['gender'],
                     pymysql.escape_string(item['image_url']),
                     pymysql.escape_string(item['location']),
                     item['business'],
                     item['employment'],
                     item['position'],
                     item['education'],
                     item['school_name'],
                     item['major'],
                     item['followee_count'],
                     item['follower_count']
                     )

                self.cursor.execute(sql)
                # 提交sql语句
                self.connect.commit()
        except pymysql.err.ProgrammingError as error:
            # 出现错误时打印错误日志
            print(error, data, sql)
            log.ERROR('保存用户时出错'+str(error))
        except pymysql.err.InterfaceError as error:
            print(error, data, sql)
            log.ERROR('数据连接已断掉，正在重连。。。')
            self.__init__()
            self.process_item(item, "zhihu")
        except Exception as e:
            print(e)
            print('插入用户数据出错')



    def _process_relation(self, item):
        """
        存储人际拓扑关系
        """
        self.connect.ping(reconnect=True)
        try:
            select_sql = """select user_list from focus where (zhihu_id='%s' and user_type=%d);""" % \
                         (item['zhihu_id'], item['user_type'])
            self.cursor.execute(select_sql)
            old_list = self.cursor.fetchall()
            if not old_list:
                # 插入数据
                self.cursor.execute("""replace into focus(zhihu_id,user_list,user_type) values(%s, %s, %s);""",
                                    (item['zhihu_id'], item['user_list'], item['user_type']))
            else:
                # 数据库中的user_list
                old_list = old_list[0][0].split(',')
                # item中的user_list
                new_list = item['user_list'].split(',')
                # new_list = list(set(old_list) | set(new_list))
                # 两个列表相加，通过set去重，再转为list
                new_list = list(set(old_list + new_list))
                user_list = ','.join(new_list)
                # 更新
                update_sql = """UPDATE focus SET user_list = '%s' WHERE (zhihu_id='%s' and user_type=%s);""" %\
                 (user_list, item['zhihu_id'], item['user_type'])
                # 更新
                self.cursor.execute(update_sql)
            # 提交sql语句
            self.connect.commit()
        except pymysql.err.ProgrammingError as error:
            # 出现错误时打印错误日志
            print(error)
            log.ERROR('存储人际关系出错')
            self.connect.rollback()
        except pymysql.err.InterfaceError as error:
            print(error)
            log.ERROR('数据连接已断掉，正在重连。。。')
            self.__init__()
            self.process_item(item, "zhihu")
        except Exception as e:
            print(e)
            print('插入数据出错')



    def process_item(self, item, spider):
        """
        处理item
        """
        if isinstance(item, ZhihuPeopleItem):
            self._process_people(item)
        elif isinstance(item, ZhihuRelationItem):
            self._process_relation(item)
        return item