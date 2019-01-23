# -*- coding=utf8 -*-
from scrapy import cmdline
import datetime

today = datetime.datetime.now()
cmdline.execute("scrapy crawl zhihutest -s LOG_FILE=log/spider_0.log".split())