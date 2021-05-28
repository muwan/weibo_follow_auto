# -*- coding: utf-8 -*-
"""
Description:
Author:henly Date:2021/2/6
"""
# import json
import os
import random
import sys
# import traceback
import asyncio
# import requests
import pymongo
from pathlib import Path

from time import sleep
import time
from pyppeteer import launch
from pyppeteer.page import Page
from pyppeteer.browser import Browser
from pyppeteer.errors import TimeoutError
from bson.objectid import ObjectId

WINDOW_WIDTH, WINDOW_HEIGHT = 1366, 768
client = pymongo.MongoClient('localhost')
db = client['weibo_follow']
collection = db['WO_YUE_SHUAI_GE_WU_SHU']


# browser, apage = None, None

class Follow(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    async def web_brownser(self):
        # global browser, apage
        p = Path("./userData").resolve()
        browser = await launch({'headless': True,
                                'userDataDir': p,
                                'userGesture': True,
                                'autoClose': False,
                                'args': [
                                    '--disable-infobars',
                                    f'--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}',
                                    '--no-sandbox'
                                ]})
        apage = await browser.newPage()
        return apage

    async def web_page(self, url, selecter, page: Page) -> Page:
        try:
            await page.setViewport({'width': WINDOW_WIDTH, 'height': WINDOW_HEIGHT})
            await page.evaluateOnNewDocument('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')
            await page.goto(url, options={"timeout": 1000 * 60})
            await asyncio.wait(
                [
                    asyncio.sleep(3),
                    page.waitForSelector(selecter, options={"timeout": 1000 * 30})
                ]
            )

        except TimeoutError:
            print('timeout error')

    async def run_browser(self, uri, page: Page) -> Page:
        status = False
        need_sleep = False
        url = f"https://weibo.com/{uri}"
        await self.web_page(url, '.WB_frame_c', page)
        await asyncio.sleep(1)

        element = await page.querySelector('div[node-type="focusLink"]')
        if element:
            focus = await element.querySelector('a')
            focus_text = await page.evaluate('element => element.getAttribute("action-type")', focus)
            button_text = await page.evaluate('element => element.innerText', focus)

            if focus_text == "unFollow" and "互相关注" not in button_text:
                await element.hover()
                await asyncio.sleep(1)
                await element.click()
                cancle_follow = await page.querySelector('li[action-type="ok"]')
                await cancle_follow.click()
                await asyncio.sleep(2)

                yzm_frame = await page.querySelector('input.yzm_input')
                if yzm_frame:
                    print("阿哦，遇到验证码了，休息一会儿吧")
                    sleep_time = random.randint(70 * 60, 95 * 60)
                    print("现在时间: %s , 休息时间 : %s 秒" % (time.strftime("%H:%M:%S", time.localtime()), sleep_time))
                    await asyncio.sleep(sleep_time)
                    need_sleep = True
                print('finish scrool')
                status = True
                return status, need_sleep
            else:
                print("skip unfollow")
                status = False
                return status, need_sleep
        else:
            print("网页错误")
            status = False
            return status, need_sleep

    async def pyppeteer_get(self):
        page = await self.web_brownser()
        try:
            #                               {"_id": {"$gt": ObjectId("5ff48b902d896ec165b881c3"), "$lt": ObjectId("5ff496bc2d896ec165b8bd19")}}
            userList = list(collection.find({"_id": {"$lte": ObjectId("5ff481ae2d896ec165b84ec7")}}).sort("_id",-1))
            lastObject = userList[-1]
            print(lastObject["_id"])
            # 本次启动已经关注人数ß
            real_count = 0
            status = False

            for index, user in enumerate(userList):
                status, need_sleep = await self.run_browser(user["uri"], page)
                if need_sleep:
                    await self.run_browser(user["uri"], page)

                real_count = real_count + 1 if status else real_count

                print("user : %s,\nindex : %s" % (user, index))
                print("已经取消关注 %s 人" % (real_count))
        finally:
            pass

    async def start_a_page(self):
        url = "https://weibo.com/p/1005051764018647/myfollow?gid=4620402435822182&expand=1#place"
        page: Page = await self.web_brownser()
        await self.web_page(url, ".WB_frame", page)
        await asyncio.sleep(3)
        pages = await page.JJ("[bpfilter='page'].S_txt1.page")
        last_page = await page.evaluate('element => element.innerText', pages[-2])

        for _ in range(0 , int(last_page)):
            await asyncio.sleep(4)
            await page.querySelectorEval(".btn_link.S_txt1", "(element) => element.click()")
            await asyncio.sleep(1)
            elements = await page.JJ(".member_li")
            for li in elements:
                await li.click()
            await asyncio.sleep(1)
            cancel_btn = await page.J('.W_btn_a[node-type="cancelFollowBtn"')
            await cancel_btn.click()
            await asyncio.sleep(2)
            sure = await page.J('[node-type="ok"]')
            await asyncio.sleep(3)
            await sure.click()

            await asyncio.sleep(10)
            curpages = await page.JJ("[bpfilter='page'].S_txt1.page")
            cust = await page.evaluate('element => element.innerText', curpages[-2])
            print("当前还剩%s页" % cust)


if __name__ == '__main__':
    password = '214500o'
    account = '18602522813'
    login = Follow(account, password)
    # login.run_weibo()
    # asyncio.get_event_loop().run_until_complete(login.start_a_page())
    asyncio.get_event_loop().run_until_complete(login.pyppeteer_get())

