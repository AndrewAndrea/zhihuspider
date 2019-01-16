# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


# class ZhihuscrapyItem(scrapy.Item):
#     # define the fields for your item here like:
#     # name = scrapy.Field()
#     pass

class ZhihuPeopleItem(Item):
    """知乎用户属性
    Attributes:
        nickname 用户名
        zhihu_id 用户id
        location 位置
        business 行业
        gender 性别
        employment 公司
        position 职位
        education 教育情况
        major 专业
        image_url 头像图片url
        followee_count 关注了
        follower_count 关注者
    """
    nickname = Field()
    zhihu_id = Field()
    location = Field()
    business = Field()
    gender = Field()
    employment = Field()
    position = Field()
    education = Field()
    school_name = Field()
    major = Field()
    followee_count = Field()
    follower_count = Field()
    image_url = Field()


class ZhihuRelationItem(Item):
    """知乎用户关系
    Attributes:
        zhihu_id 知乎id
        user_list 用户列表
        user_type 用户类型（1关注的人 2粉丝）

    """
    zhihu_id = Field()
    user_list = Field()
    user_type = Field()

