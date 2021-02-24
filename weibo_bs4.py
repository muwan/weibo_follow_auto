# -*- coding: utf-8 -*-
"""
Description:
Author:henly
Date:2020/12/24
Change Activity:2020/12/24:
"""
__author__ = 'henly'

import random
import asyncio
import pymongo
import sys
import time
import os
import json

from pyppeteer import launch
from pyppeteer.page import Page
from pyppeteer.errors import TimeoutError
from bson.objectid import ObjectId
from chaoying import Chaojiying_Client

from weibo_follow import MONGO_CONNECTION_STRING
from weibo_follow import collection

WINDOW_WIDTH, WINDOW_HEIGHT = 1366, 768
client = pymongo.MongoClient(MONGO_CONNECTION_STRING)


class Follow(object):
    def __init__(self, username, password):
        self.last_follow = None
        self.follow_json = None
        self.username = username
        self.password = password
        self.real_count = 0
        self.cjy = Chaojiying_Client("sunbofu", "awgmRFEHbKSe.u7", "909639")
        self.repeat = False
        self.validate_follow()

    def validate_follow(self):
        config_path = os.path.split(os.path.realpath(__file__))[0] + os.sep + 'follow.json'
        if not os.path.isfile(config_path):
            sys.exit(u'当前路径：%s 不存在关注文件config.json' %
                     (os.path.split(os.path.realpath(__file__))[0] + os.sep))
        with open(config_path) as f:
            try:
                self.follow_json = json.loads(f.read())
            except ValueError:
                sys.exit(u'follow.json 格式不正确')



    async def web_brownser(self) -> Page:
        browser = await launch({'headless': True,
                                'userDataDir': './userData',
                                'args': [
                                    '--disable-infobars',
                                    f'--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}',
                                    '--no-sandbox'
                                ]})
        page = await browser.newPage()
        return page

    async def query_page(self, url, selecter, page: Page) -> Page:
        try:
            await page.setViewport({'width': WINDOW_WIDTH, 'height': WINDOW_HEIGHT})
            await page.evaluateOnNewDocument('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')
            await page.goto(url, options={"timeout": 1000 * 60})
            await asyncio.wait(
                [
                    asyncio.sleep(3),
                    page.waitForSelector(selecter, options={"timeout": 1000 * 60})
                ]
            )
            return page
        except TimeoutError:
            print('timeout error')

    async def run_browser(self, uri, page: Page):
        status = False
        url = f"https://weibo.com/{uri}"
        web_page = await self.query_page(url, '.WB_frame_c', page)
        await asyncio.sleep(1)
        sexElement = await web_page.querySelector("i.icon_pf_male")
        if sexElement:
            element = await web_page.querySelector('div[node-type="focusLink"]')
            if not await element.querySelectorEval('a', 'element => element.getAttribute("action-type")') == "unFollow":
                await element.click()
                await asyncio.sleep(random.randint(1, 3))
                yzm_frame = await web_page.querySelector('input.yzm_input')
                if yzm_frame:
                    print("%s 阿哦，遇到验证码了" % time.strftime("%H:%M:%S", time.localtime()))
                    # await asyncio.sleep(300)
                    if self.real_count % 100 > 0 or self.real_count == 0 or self.repeat:
                        await asyncio.sleep(1)
                        yzm_img = await web_page.waitForSelector("img.yzm_img")
                        img = await yzm_img.screenshot()
                        yzm_res = self.cjy.PostPic(img, "6004")
                        error_no = yzm_res.get("err_no")
                        pic_id = yzm_res.get("pic_id")
                        input_text = yzm_res.get("pic_str")
                        if input_text and error_no == 0:
                            self.repeat = False
                            await web_page.type("input[action-type='yzm_input']", input_text)
                            submit_btn = await web_page.querySelector("[action-type='yzm_submit']")
                            await asyncio.sleep(1)
                            await submit_btn.click()
                            await asyncio.sleep(1)
                            yzm_frame_new = await web_page.querySelector('div.layer_verification')
                            status = True
                            if yzm_frame_new:
                                self.cjy.ReportError(pic_id)
                                print("现在时间: %s , 验证码未通过" % (time.strftime("%H:%M:%S", time.localtime())))
                                png_name = f"{time.strftime('%Y%m%d%H%M%S', time.localtime())}.png"
                                await web_page.screenshot({'path': f'./errImg/{png_name}'})
                                status = False
                            else:
                                print("验证成功")
                    else:
                        status = False
                        self.repeat = True
                        sleep_time = random.randint(0.1 * 60, 0.5 * 60)
                        print("现在时间: %s , 休息时间 : %s 小时 %s 分 %s 秒" % (
                            time.strftime("%H:%M:%S", time.localtime()), int(sleep_time / 3600),
                            int((sleep_time % 3600) / 60), (sleep_time % 3600) % 60))
                        await asyncio.sleep(sleep_time)
                else:
                    print('finish follow')
                    status = True
                    self.repeat = False
            else:
                self.repeat = False
                print("pass followed")
            return status
        else:
            self.repeat = False
            print("skip female")
            status = False
            return status

    async def pyppeteer_get(self):
        page = await self.web_brownser()
        try:
            user_id = None
            sys_user_list = []

            if sys.platform == "darwin":
                if self.follow_json["mac_id"]:
                    user_id = self.follow_json["mac_id"]
                    user_list = list(collection.find({"_id": {"$gte": ObjectId(user_id)}}))
                    sys_user_list = user_list[::2]
                else:
                    user_id = self.follow_json["win_id"]
                    user_list = list(collection.find({"_id": {"$gte": ObjectId(user_id)}}))
                    sys_user_list = user_list[1::2]
            else:
                if self.follow_json["win_id"]:
                    user_id = self.follow_json["win_id"]
                    user_list = list(collection.find({"_id": {"$gte": ObjectId(user_id)}}))
                    sys_user_list = user_list[::2]
                else:
                    user_id = self.follow_json["mac_id"]
                    user_list = list(collection.find({"_id": {"$gte": ObjectId(user_id)}}))
                    sys_user_list = user_list[1::2]

            for index, user in enumerate(sys_user_list):
                self.last_follow = str(user["_id"])
                self.write_to_txt()
                print("user : %s,\nindex : %s" % (user, index))
                status = await self.run_browser(user["uri"], page)
                self.real_count = self.real_count + 1 if status else self.real_count
                print("已经关注 %s 人,当前时间：%s" % (self.real_count, time.strftime("%H:%M:%S", time.localtime())))
                if self.real_count > 500:
                    break
        finally:
            print("ok 今天的关注结束啦")

    def write_to_txt(self):
        if sys.platform == "darwin":
            self.follow_json["mac_id"] = self.last_follow
        else:
            self.follow_json["win_id"] = self.last_follow

        with open('follow.json', 'w') as f:
            json.dump(self.follow_json, f)


if __name__ == '__main__':
    password = ''
    account = ''
    login = Follow(account, password)
    asyncio.get_event_loop().run_until_complete(login.pyppeteer_get())
