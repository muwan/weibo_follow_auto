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
                                'args': [
                                    '--disable-infobars',
                                    f'--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}',
                                    '--no-sandbox'
                                ]})
        apage = await browser.newPage()
        return apage

    async def web_page(self, url, selecter, page:Page) -> Page:
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

    async def run_browser(self, uri, page:Page) -> Page:
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
                await asyncio.sleep(1)

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
            #                               {"_id": {"$gt": ObjectId("5ff480232d896ec165b8464c")}}
            userList = list(collection.find({"_id": {"$gt": ObjectId("5ff48b902d896ec165b881c3"), "$lt": ObjectId("5ff48b902d896ec165b881c5")}}))
            lastObject = userList[-1]
            print(lastObject["_id"])
            # 本次启动已经关注人数
            real_count = 0
            status = False

            for index, user in enumerate(userList):
                status, need_sleep = await self.run_browser(user["uri"], page)
                if need_sleep:
                    await self.run_browser(user["uri"], page)

                real_count = real_count + 1 if status else real_count

                print("user : %s,\nindex : %s" % (user, index))
                print("已经取消关注 %s 人"%(real_count))
       finally:
            pass

    # async def gather_weibo(self, urls):
    #     try:
    #         abrownser = await self.web_brownser_new()
    #         await self.run_browser_new(urls[0], abrownser)
    #         await asyncio.sleep(5)
    #         futures = asyncio.gather(*[self.run_browser_new(url,abrownser) for url in urls[1:]])
    #         futures.add_done_callback(self.calcuate)
    #         await futures
    #     finally:
    #         pass
    #
    # async def web_page_new(self, browser:Browser, url, selecter) -> Page:
    #     try:
    #         page = await browser.newPage()
    #         await page.setViewport({'width': WINDOW_WIDTH, 'height': WINDOW_HEIGHT})
    #         await page.evaluateOnNewDocument('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')
    #         await page.goto(url, options={"timeout": 1000 * 60})
    #         await asyncio.wait(
    #             [
    #                 asyncio.sleep(3),
    #                 page.waitForSelector(selecter, options={"timeout": 1000 * 60})
    #             ]
    #         )
    #         return page
    #     except TimeoutError:
    #         print('timeout error')
    #
    # async def run_browser_new(self, uri, browser:Browser) -> Page:
    #     status = False
    #     need_sleep = False
    #     url = f"https://weibo.com/{uri}"
    #     await asyncio.sleep(random.randint(1, 3))
    #     page = await self.web_page_new(browser, url, '.WB_frame_c')
    #     await asyncio.sleep(1)
    #     sexElement = await page.querySelector("i.icon_pf_male")
    #     if sexElement:
    #         element = await page.querySelector('div[node-type="focusLink"]')
    #         js = await element.getProperties()
    #         if not await element.getProperty("action-type") == "unFollow": await element.click()
    #         await asyncio.sleep(2)
    #         # yzm_frame = await apage.querySelector('div[node-type="outer"]')
    #         yzm_frame = await page.querySelector('input.yzm_input')
    #
    #         if yzm_frame:
    #             print("阿哦，遇到验证码了，休息一会儿吧")
    #             sleep_time = random.randint(70 * 60, 95 * 60)
    #             print("现在时间: %s , 休息时间 : %s 秒" % (time.strftime("%H:%M:%S", time.localtime()), sleep_time))
    #             await asyncio.sleep(sleep_time)
    #             need_sleep = True
    #         print('finish scrool')
    #         status = True
    #         return status,need_sleep
    #     else:
    #         print("skip female")
    #         status = False
    #         return status,need_sleep
    #
    # async def web_brownser_new(self)->Browser:
    #     abrowser = await launch({'headless': False,
    #                             'userDataDir': './userData',
    #                             'userGesture': True,
    #                             'args': [
    #                                 '--disable-infobars', f'--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}'
    #                             ]})
    #     return abrowser

    def calcuate(self, futter):
        print(futter.result())

    # def run_weibo(self):
    #     userList = list(collection.find({}))[:10]
    #     urls = [user["uri"] for user in userList]
    #     asyncio.get_event_loop().run_until_complete(self.gather_weibo(urls))


if __name__ == '__main__':
    password = '214500o'
    account = '18602522813'
    login = Follow(account, password)
    # login.run_weibo()
    asyncio.get_event_loop().run_until_complete(login.pyppeteer_get())
