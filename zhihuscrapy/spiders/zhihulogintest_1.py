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
from scrapy import Selector, log


class ZhihuComSpider(scrapy.Spider):
    name = 'zhihutest'
    allowed_domains = ['zhihu.com']
    start_url = 'https://www.zhihu.com/people/mei-li-xiu-xing-nei-ce-zu'

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
    followee_ids = []

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
            post_url = 'https://www.zhihu.com/api/v3/oauth/sign_in'
            post_data ={
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

        try:
            zhihu_id = os.path.split(response.url)[-1]
            userlinks = selector.xpath('//script[@id="js-initialData"]/text()').extract_first()
            userlinks = json.loads(userlinks)
            userlinks = userlinks['initialState']['entities']['users'][zhihu_id]
            nickname = userlinks['name']

            try:
                # 位置
                location = userlinks['locations'][0]['name']
            except (KeyError, IndexError) as e:
                # log.WARNING('未找到位置'+str(e))
                location = "未知"
            try:
                # 公司
                employment = userlinks['employments'][0]['company']['name']
                # # 职位
                position = userlinks['employments'][0]['job']['name']
            except (KeyError, IndexError) as e:
                employment = '未知'
                position = '未知'
            try:
                # 行业
                business = userlinks['business'][0]['name']
            except (KeyError, IndexError) as e:
                business = "未知"
            try:
                # 学校名字
                school_name = userlinks['educations'][0]['school']['name']
                log.logger.info(school_name)
                # 专业
                major = userlinks['educations'][0]['major']['name']
                # 1高中及以下，2大专，3本科， 4硕士，5博士及以上
                edu = userlinks['educations'][0]['diploma']
                if edu == 1:
                    education = '高中及以下'
                elif edu == 2:
                    education = '大专'
                elif edu == 3:
                    education = '本科'
                elif edu == 4:
                    education = '硕士'
                elif edu == 5:
                    education = '博士及以上'
                else:
                    education = '未知'
            except (KeyError, IndexError) as e:
                school_name = "未知"
                major = "未知"
                education = "未知"
            try:
                gender = userlinks['gender']
                gender = '男' if gender == 1 else '女'
            except IndexError as e:
                gender = '未知'
            image_url = selector.xpath(
                '//div[@class="UserAvatar ProfileHeader-avatar"]/img/@src'
            ).extract_first('')[0:-3]
            follow_urls = selector.xpath(
                '//div[@class="NumberBoard FollowshipCard-counts NumberBoard--divider"]/a/@href'
            ).extract()
            followee_count = userlinks['followingCount']
            follower_count = userlinks['followerCount']

            for url in follow_urls:
                complete_url = 'https://{}{}'.format(self.allowed_domains[0], url)
                print(complete_url, '一个是关注者一个是被关注', follower_count, followee_count)
                if follower_count == 0:
                    if url.endswith('followers'):
                        continue
                if followee_count == 0:
                    if url.endswith('following'):
                        continue
                if url.endswith('following'):
                    yield scrapy.Request(complete_url,
                                  meta={
                                      'cookiejar': response.meta['cookiejar'],
                                  },
                                  headers=HEADER,
                                  callback=self.parse_follow,
                                  errback=self.parse_err
                                )
            item = ZhihuPeopleItem(
                nickname=nickname,
                zhihu_id=zhihu_id,
                location=location,
                business=business,
                gender=gender,
                employment=employment,
                position=position,
                education=education,
                school_name=school_name,
                major=major,
                followee_count=followee_count,
                follower_count=follower_count,
                image_url=image_url + 'jpg',
            )
            yield item
        except Exception as e:
            log.logger.error('页面被重定向到登录页' + str(e))
            print(response.meta.get('start_url'), '123')
            if response.meta.get('start_url') == 'None':
                self.start_requests()
            else:
                with open('user_fail.txt', 'a', encoding='utf-8') as f:
                    f.write('\n' + response.meta.get('start_url'))
                self.start_url = response.meta.get('start_url')
                self.start_requests()

            # yield scrapy.Request(response.meta.get('start_url'),
            #                      meta={'cookiejar': response.meta['cookiejar'],
            #                            'start_url': response.meta.get('start_url')
            #                            },
            #                      callback=self.parse_people,
            #                      headers=HEADER,
            #                      errback=self.parse_err)

    def parse_follow(self, response):
        """
        解析follow数据
        """
        url, user_type = os.path.split(response.url)
        type_name = user_type
        user_type = People.Follower if user_type == u'followers' else People.Followee
        zhihu_id = os.path.split(url)[-1]
        # 获取关注的人
        selector = Selector(response)
        # 获取js中的json数据
        userlinks = selector.xpath('//script[@id="js-initialData"]/text()').extract_first()
        # 解析
        userInfos = json.loads(userlinks)
        # 取所有的key
        userKeys = userInfos['initialState']['entities']['users'].keys()
        # 获取当前用户的信息
        userInfos = userInfos['initialState']['entities']['users'][zhihu_id]
        followee_count = userInfos['followingCount']
        follower_count = userInfos['followerCount']
        start = 20
        page = 1
        # 关注了
        # count = followee_count if user_type == 1 else follower_count
        # 由于在前面做了限制，所以只会爬取关注了谁。避免无用的循环
        count = followee_count
        # 请求所有人的信息，每页有20条超过20条请求下一页
        while start < count:
            HEADER.update({'Referer': response.url})
            follow_url = 'https://{}/people/{}/{}?page={}'.format(self.allowed_domains[0], zhihu_id, type_name, page)
            start += 20
            page += 1
            yield scrapy.Request(follow_url,
                          meta={'cookiejar': response.meta['cookiejar']},
                          headers=HEADER,
                          callback=self.parse_post_follow,
                          errback=self.parse_err)
        zhihu_ids = []
        for follow in userKeys:
            if zhihu_id == follow:
                continue
            else:
                zhihu_ids.append(follow)
                follow_url = 'https://{}{}'.format(self.allowed_domains[0], '/people/' + follow)
                yield scrapy.Request(follow_url,
                                     meta={'cookiejar': response.meta['cookiejar'], 'start_url': follow_url},
                                     callback=self.parse_people,
                                     headers=HEADER,
                                     errback=self.parse_err)
        # 返回数据
        item = ZhihuRelationItem(
            zhihu_id=os.path.split(url)[-1],
            user_type=user_type,
            user_list=','.join(zhihu_ids),
        )
        yield item


    def parse_post_follow(self, response):
        """
        获取动态请求拿到的人员
        """

        url, user_type = os.path.split(response.url)
        user_type = People.Follower if 'followers' in user_type else People.Followee
        zhihu_id = os.path.split(url)[-1]
        # 获取关注的人
        selector = Selector(response)
        userlinks = selector.xpath('//script[@id="js-initialData"]/text()').extract_first()
        userlinks = json.loads(userlinks)
        userlinks = userlinks['initialState']['entities']['users'].keys()
        zhihu_ids = []
        for follow in userlinks:
            if zhihu_id == follow:
                continue
            else:
                zhihu_ids.append(follow)
                follow_url = 'https://{}{}'.format(self.allowed_domains[0], '/people/' + follow)
                yield scrapy.Request(follow_url,
                                     meta={'cookiejar': response.meta['cookiejar'], 'start_url': follow_url},
                                     callback=self.parse_people,
                                     headers=HEADER,
                                     errback=self.parse_err)
        # 返回数据
        item = ZhihuRelationItem(
            zhihu_id=os.path.split(url)[-1],
            user_type=user_type,
            user_list=','.join(zhihu_ids),
        )
        yield item

    def parse_err(self, response):
        # print(response.url)
        log.ERROR('crawl {} failed'.format(response.url))


