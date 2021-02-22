#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import random
import sys
import traceback
import requests
import re
import pymongo
import os
from lxml import etree
from tqdm import tqdm
from bs4 import BeautifulSoup
from time import sleep
from os import makedirs
from os.path import exists


RESULTS_DIR = 'results'
exists(RESULTS_DIR) or makedirs(RESULTS_DIR)

MONGO_CONNECTION_STRING = 'mongodb://localhost:27017'
MONGO_DB_NAME = 'weibo_follow'
MONGO_COLLECTION_NAME = 'WO_YUE_SHUAI_GE_WU_SHU'

client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
db = client[MONGO_DB_NAME]
fansdb = client['weibo_fans']
collection = db[MONGO_COLLECTION_NAME]
fanscollection = fansdb[MONGO_COLLECTION_NAME]

class Follow(object):
    def __init__(self, config):
        """Follow类初始化"""
        self.validate_config(config)
        self.cookie = config['cookie']
        # user_id_list = config['user_id_list']
        user_id_list = self.get_userId_from_mongo()
        if not isinstance(user_id_list, list):
            if not os.path.isabs(user_id_list):
                user_id_list = os.path.split(
                    os.path.realpath(__file__))[0] + os.sep + user_id_list
            user_id_list = self.get_user_list(user_id_list)
        self.user_id_list = user_id_list  # 要爬取的微博用户的user_id列表
        self.user_id = ''
        self.follow_list = []  # 存储爬取到的所有关注微博的uri和用户昵称

    def get_userId_from_mongo(self):
        result = list(fanscollection.find({},{'uri':1,'_id':0}))
        user_list = []
        [user_list.append(item['uri']) for item in result]
        return user_list

    def validate_config(self, config):
        """验证配置是否正确"""
        user_id_list = config['user_id_list']
        if (not isinstance(user_id_list,
                           list)) and (not user_id_list.endswith('.txt')):
            sys.exit(u'user_id_list值应为list类型或txt文件路径')
        if not isinstance(user_id_list, list):
            if not os.path.isabs(user_id_list):
                user_id_list = os.path.split(
                    os.path.realpath(__file__))[0] + os.sep + user_id_list
            if not os.path.isfile(user_id_list):
                sys.exit(u'不存在%s文件' % user_id_list)

    def deal_html(self, url):
        """处理html"""
        try:
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'
            headers = {
                'User_Agent': user_agent,
                'Cookie': self.cookie,
                'Connection': 'close'
            }
            html = requests.get(url, headers=headers).text
            selector = etree.HTML(html.encode('utf-8'))
            # bs = BeautifulSoup(html, "html.parser")
            return selector
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_page_num(self):
        """获取关注列表页数"""
        url = "https://weibo.cn/%s/fans" % self.user_id
        selector = self.deal_html(url)
        if selector.xpath("//input[@name='mp']") == []:
            page_num = 1
        else:
            page_num = (int)(
                selector.xpath("//input[@name='mp']")[0].attrib['value'])
        return page_num

    def get_one_page(self, page):
        """获取第page页的user_id"""
        print(u'%s第%d页%s' % ('-' * 30, page, '-' * 30))
        url = 'https://weibo.cn/%s/fans?page=%d' % (self.user_id, page)
        selector = self.deal_html(url)
        table_list = selector.xpath('//table')
        if (page == 1 and len(table_list) == 0):
            print(u'cookie无效或提供的user_id无效')
        else:
            for t in table_list:
                im = t.xpath('.//a/@href')[-1]
                uri = im.split('uid=')[-1].split('&')[0].split('/')[-1]
                nickname = t.xpath('.//a/text()')[0]
                followTd = t.xpath('.//td')[-1]
                fansNum = re.search('.*<br />粉丝(\d+)人<br />', etree.tostring(followTd,encoding='unicode')).group(1)
                if {'uri': uri, 'nickname': nickname,'fans':fansNum} not in self.follow_list:
                    self.follow_list.append({'uri': uri, 'nickname': nickname,'fans': fansNum})
                    print(u'%s %s 粉丝 %s 人' % (nickname, uri, fansNum))

    def get_follow_list(self):
        """获取关注用户主页地址"""
        page_num = self.get_page_num()
        print(u'用户关注页数：' + str(page_num))
        page1 = 0
        random_pages = random.randint(1, 5)
        for page in tqdm(range(1, page_num + 1), desc=u'关注列表爬取进度'):
            self.get_one_page(page)

            if page - page1 == random_pages and page < page_num:
                sleep(random.randint(6, 10))
                page1 = page
                random_pages = random.randint(1, 5)

        print(u'用户关注列表爬取完毕')

    def save_to_mongodb(self):
        self.follow_list.sort(key=lambda x :(int(x['fans']),x['uri']),reverse=False)
        for user in self.follow_list:
            collection.update_one(
                {'uri':user.get('uri')},
                {'$set':user},
                upsert=True)

    def write_to_txt(self):
        # sorted(self.follow_list,key = lambda x :x['fans'],reverse=True)
        self.follow_list.sort(key=lambda x :int(x['fans']),reverse=False)
        with open('user_id_list.txt', 'ab') as f:
            for user in self.follow_list:
                f.write((user['uri'] + ' ' + user['nickname'] + ' ' + user['fans'] + '\n').encode(
                    sys.stdout.encoding))

    def get_user_list(self, file_name):
        """获取文件中的微博id信息"""
        with open(file_name, 'rb') as f:
            try:
                lines = f.read().splitlines()
                lines = [line.decode('utf-8-sig') for line in lines]
            except UnicodeDecodeError:
                sys.exit(u'%s文件应为utf-8编码，请先将文件编码转为utf-8再运行程序' % file_name)
            user_id_list = []
            for line in lines:
                info = line.split(' ')
                if len(info) > 0 and info[0].isdigit():
                    user_id = info[0]
                    if user_id not in user_id_list:
                        user_id_list.append(user_id)
        return user_id_list

    def initialize_info(self, user_id):
        """初始化爬虫信息"""
        self.follow_list = []
        self.user_id = user_id

    def start(self):
        """运行爬虫"""
        try:
            for user_id in self.user_id_list:
                self.initialize_info(user_id)
                print('*' * 100)
                self.get_follow_list()  # 爬取微博信息
                self.save_to_mongodb()
                print(u'信息抓取完毕')
                print('*' * 100)
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()


def main():
    try:
        config_path = os.path.split(
            os.path.realpath(__file__))[0] + os.sep + 'config.json'
        if not os.path.isfile(config_path):
            sys.exit(u'当前路径：%s 不存在配置文件config.json' %
                     (os.path.split(os.path.realpath(__file__))[0] + os.sep))
        with open(config_path) as f:
            try:
                config = json.loads(f.read())
            except ValueError:
                sys.exit(u'config.json 格式不正确，请参考 '
                         u'https://github.com/dataabc/weiboSpider#3程序设置')
        wb = Follow(config)
        wb.start()  # 爬取微博信息

    except Exception as e:
        print('Error: ', e)
        traceback.print_exc()


if __name__ == '__main__':
    main()
