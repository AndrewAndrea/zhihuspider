#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# @Time : 2019/1/23 10:25 
# @Author : Aries 
# @Site :  
# @File : login.py 
# @Software: PyCharm


import json
import scrapy, time, hmac, base64
from hashlib import sha1


class ZhihuComSpider(scrapy.Spider):

    agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
    headers = {
        'Connection': 'keep-alive',
        'Host': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com/signin',
        'User-Agent': agent
        # 'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20'
    }
    client_id = 'c3cef7c66a1843f8b3a9e6a1e3160e20'
    grant_type = 'password'
    source = 'com.zhihu.web'
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
        yield scrapy.Request('https://www.zhihu.com/api/v3/oauth/captcha?lang=en', headers=self.headers,
                             callback=self.start_login, meta={'cookiejar': 1},)


    def start_login(self,response):
        # 判断是否需要验证码
        need_cap=json.loads(response.body)['show_captcha']
        print(need_cap)
        if need_cap:
            print('需要验证码')
            yield scrapy.Request('https://www.zhihu.com/api/v3/oauth/captcha?lang=en', headers=self.headers,
                                 callback=self.capture, method='PUT', meta={'cookiejar': response.meta['cookiejar']})

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
            yield scrapy.FormRequest(url=post_url, formdata=post_data, headers=self.headers,
                                     meta={'cookiejar': response.meta['cookiejar']},)

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
            Cookie2 = response.request.headers.getlist('Cookie')
        else:
            print("登录失败")