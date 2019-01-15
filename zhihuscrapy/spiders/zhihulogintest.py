# -*- coding: utf-8 -*-

import os
import re
import json

import scrapy, time, hmac, base64
from urllib.parse import urlencode
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from zhihuscrapy.constants import Gender, People, HEADER
from zhihuscrapy.items import ZhihuPeopleItem, ZhihuRelationItem
from hashlib import sha1
from scrapy import Selector


class ZhihuComSpider(scrapy.Spider):
    name = 'zhihutest'
    allowed_domains = ['zhihu.com']
    start_url = 'https://www.zhihu.com/people/msnz-12'

    rules = (Rule(LinkExtractor(allow=r'Items/'), callback='parse_item', follow=True),)

    agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
    headers = {
        'Connection': 'keep-alive',
        'Host': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com/signin',
        'User-Agent': agent
        # 'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20'
    }
    client_id='c3cef7c66a1843f8b3a9e6a1e3160e20'
    grant_type= 'password'
    source='com.zhihu.web'
    timestamp = str(int(time.time() * 1000))
    timestamp2 = str(time.time() * 1000)

    # 处理签名
    def get_signnature(self,grant_type,client_id,source,timestamp):
        """
        通过 Hmac 算法计算返回签名
        实际是几个固定字符串加时间戳
        :param timestamp: 时间戳
        :return: 签名
        """
        hm=hmac.new(b'd1b964811afb40118a12068ff74a12f4',None,sha1)
        hm.update(str.encode(grant_type))
        hm.update(str.encode(client_id))
        hm.update(str.encode(source))
        hm.update(str.encode(timestamp))
        return str(hm.hexdigest())


    def start_requests(self):
        # 进入登录页面,回调函数start_login()
        yield scrapy.Request('https://www.zhihu.com/api/v3/oauth/captcha?lang=en',headers=self.headers,callback=self.start_login, meta={'cookiejar': 1},)  # meta={'cookiejar':1}


    def start_login(self,response):
        # 判断是否需要验证码
        need_cap=json.loads(response.body)['show_captcha']
        print(need_cap)
        if need_cap:
            print('需要验证码')
            yield scrapy.Request('https://www.zhihu.com/api/v3/oauth/captcha?lang=en',headers=self.headers,callback=self.capture,method='PUT', meta={'cookiejar': response.meta['cookiejar']})

        else:
            print('不需要验证码')
            post_url='https://www.zhihu.com/api/v3/oauth/sign_in'
            post_data={
                'client_id': self.client_id,
                'grant_type': self.grant_type,
                'timestamp': self.timestamp,
                'source': self.source,
                'signature': self.get_signnature(self.grant_type, self.client_id, self.source, self.timestamp),
                'username': '+8615929799185',
                'password': 'wjzj1217@',
                'captcha': '',
                # 改为'cn'是倒立汉字验证码
                'lang': 'en',
                'ref_source': 'other_',
                'utm_source': ''}
            yield scrapy.FormRequest(url=post_url, formdata=post_data, headers=self.headers, meta={'cookiejar': response.meta['cookiejar']},)

    def capture(self,response):
        try:
            img = json.loads(response.body)['img_base64']
        except ValueError:
            print('获取img_base64的值失败！')
        else:
            img = img.encode('utf8')
            img_data = base64.b64decode(img)

            with open('zhihu.gif', 'wb') as f:
                f.write(img_data)
                f.close()
        captcha = input('请输入验证码：')
        post_data = {
            'client_id': self.client_id,
            'grant_type': self.grant_type,
            'timestamp': self.timestamp,
            'source': self.source,
            'signature': self.get_signnature(self.grant_type, self.client_id, self.source, self.timestamp),
            'username': '+8615929799185',
            'password': 'wjzj1217@',
            'captcha': captcha,
            # 改为'cn'是倒立汉字验证码
            'lang': 'en',
            'ref_source': 'other_',
            'utm_source': '',
            '_xsrf': '0sQhRIVITLlEX8kQWA09VOqsPlSqRJQT'
        }
        yield scrapy.FormRequest(
            url='https://www.zhihu.com/signin',
            formdata=post_data,
            callback=self.after_login,
            headers=self.headers,
            meta={'cookiejar': response.meta['cookiejar']},
        )

    def after_login(self, response):
        if response.status == 200:
            print("登录成功")
            """
                    登陆完成后从第一个用户开始爬数据
                    """
            return [scrapy.Request(
                self.start_url,
                meta={'cookiejar': response.meta['cookiejar']},
                callback=self.parse_people,
                errback=self.parse_err,
            )]
        else:
            print("登录失败")

    def parse_people(self, response):
        """
        解析用户主页
        """

        selector = Selector(response)
        # 昵称
        nickname = selector.xpath(
            '//h1[@class="ProfileHeader-title"]/span[@class="ProfileHeader-name"]/text()'
        ).extract_first()
        zhihu_id = os.path.split(response.url)[-1]
        # location = selector.xpath(
        #     '//span[@class="location item"]/@title'
        # ).extract_first()
        # print(location)
        # business = selector.xpath(
        #     '//span[@class="business item"]/@title'
        # ).extract_first()
        # print(business)
        gender = selector.xpath(
            '//div[@class="ProfileHeader-iconWrapper"]/svg/@class'
        ).extract_first()
        if gender is not None:
            gender = Gender.FEMALE if u'female' in gender else Gender.MALE

        # employment = selector.xpath(
        #     '//span[@class="employment item"]/@title'
        # ).extract_first()
        # position = selector.xpath(
        #     '//span[@class="position item"]/@title'
        # ).extract_first()
        # education = selector.xpath(
        #     '//span[@class="education-extra item"]/@title'
        # ).extract_first()
        # print(education)

        # 关注了，关注者
        # followee_count, follower_count = tuple(selector.xpath(
        #     '//div[@class="NumberBoard-itemInner"]/strong/text()'
        # ).extract())

        # followee_count, follower_count = str(followee_count), str(follower_count)

        image_url = selector.xpath(
            '//div[@class="UserAvatar ProfileHeader-avatar"]/img/@src'
        ).extract_first('')[0:-3]
        follow_urls = selector.xpath(
            '//div[@class="NumberBoard FollowshipCard-counts NumberBoard--divider"]/a/@href'
        ).extract()
        for url in follow_urls:
            complete_url = 'https://{}{}'.format(self.allowed_domains[0], url)
            print(complete_url, '一个是关注者一个是被关注')
            yield scrapy.Request(complete_url,
                          meta={'cookiejar': response.meta['cookiejar']},
                          callback=self.parse_follow,
                          errback=self.parse_err
                        )
        item = ZhihuPeopleItem(
            nickname=nickname,
            zhihu_id=zhihu_id,
            # location=location,
            # business=business,
            gender=gender,
            # employment=employment,
            # position=position,
            # education=education,
            # followee_count=followee_count,
            # follower_count=follower_count,
            image_url=image_url,
        )
        yield item


    def parse_follow(self, response):
        """
        解析follow数据
        """
        url, user_type = os.path.split(response.url)
        zhihu_id = os.path.split(url)[-1]
        zhihu_ids = []
        # 获取关注的人
        selector = Selector(response)
        userlinks = selector.xpath('//script[@id="js-initialData"]/text()').extract_first()
        userlinks = json.loads(userlinks)
        userlinks = userlinks['initialState']['entities']['users'].keys()
        if userlinks == 20:
            yield scrapy.Request(complete_url,
                                 meta={'cookiejar': response.meta['cookiejar']},
                                 callback=self.parse_follow,
                                 errback=self.parse_err
                                 )
        for follow in userlinks:
            if zhihu_id == follow:
                continue
            else:
                zhihu_ids.append(follow)
                follow_url = 'https://{}{}'.format(self.allowed_domains[0], '/people/' + follow)
                yield scrapy.Request(follow_url,
                                     meta={'cookiejar': response.meta['cookiejar']},
                                     callback=self.parse_people,
                                     errback=self.parse_err)

        # 返回数据

        user_type = People.Follower if user_type == u'followers' else People.Followee
        item = ZhihuRelationItem(
            zhihu_id=os.path.split(url)[-1],
            user_type=user_type,
            user_list=','.join(zhihu_ids),
            count=len(zhihu_ids)
        )
        yield item


    # def parse_post_follow(self, response):
    #     """
    #     获取动态请求拿到的人员
    #     """
    #     body = json.loads(response.body)
    #     people_divs = body.get('msg', [])
    #
    #     # 请求所有的人
    #     zhihu_ids = []
    #     for div in people_divs:
    #         selector = Selector(text=div)
    #         link = selector.xpath('//a[@class="zg-link"]/@href').extract_first()
    #         if not link:
    #             continue
    #
    #         zhihu_ids.append(os.path.split(link)[-1])
    #         # yield Request(link,
    #         #               meta={'cookiejar': response.meta['cookiejar']},
    #         #               callback=self.parse_people,
    #         #               errback=self.parse_err)
    #
    #     url, user_type = os.path.split(response.request.headers['Referer'])
    #     user_type = People.Follower if user_type == u'followers' else People.Followee
    #     zhihu_id = os.path.split(url)[-1]
    #     # yield ZhihuRelationItem(
    #     #     zhihu_id=zhihu_id,
    #     #     user_type=user_type,
    #     #     user_list=zhihu_ids,
    #     # )

    def parse_err(self, response):
        print(response.url)
        # log.ERROR('crawl {} failed'.format(response.url))


