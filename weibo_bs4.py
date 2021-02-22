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

import time
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
        self.username = username
        self.password = password
        self.real_count = 0
        self.cjy = Chaojiying_Client("sunbofu", "awgmRFEHbKSe.u7", "909639")

    async def web_brownser(self) -> Page:
        browser = await launch({'headless': False,
                                'userDataDir': './userData',
                                'args': [
                                    '--disable-infobars', f'--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}'
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

    async def run_browser(self, uri, page: Page) -> Page:
        status = False
        need_sleep = False
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
                    if self.real_count % 100 > 0 or self.real_count == 0:
                        await asyncio.sleep(1)
                        yzm_img = await web_page.waitForSelector("img.yzm_img")
                        img = await yzm_img.screenshot()
                        yzm_res = self.cjy.PostPic(img, "6004")
                        error_no = yzm_res.get("err_no")
                        pic_id = yzm_res.get("pic_id")
                        input_text = yzm_res.get("pic_str")
                        if input_text and error_no == 0 :
                            await web_page.type("input[action-type='yzm_input']", input_text)
                            submit_btn = await web_page.querySelector("[action-type='yzm_submit']")
                            await asyncio.sleep(1)
                            await submit_btn.click()
                            await asyncio.sleep(1)
                            yzm_frame_new = await web_page.querySelector('div.layer_verification')
                            status = True
                            if yzm_frame_new:
                                need_sleep = True
                                self.cjy.ReportError(pic_id)
                                print("现在时间: %s , 验证码未通过" % (time.strftime("%H:%M:%S", time.localtime())))
                                png_name = f"{time.strftime('%Y%m%d%H:%M:%S', time.localtime())}.png"
                                await web_page.screenshot({'path':f'./errImg/{png_name}'})
                                status = False
                            else:
                                print("验证成功")
                    else:
                        status = False
                        sleep_time = random.randint(100 * 60, 120 * 60)
                        print("现在时间: %s , 休息时间 : %s 小时 %s 分 %s 秒" % (
                            time.strftime("%H:%M:%S", time.localtime()), int(sleep_time / 3600),
                            int((sleep_time % 3600) / 60), (sleep_time % 3600) % 60))
                        await asyncio.sleep(sleep_time)
                        need_sleep = True
                else:
                    print('finish follow')
                    status = True
            else:
                print("pass followed")
            return status, need_sleep
        else:
            print("skip female")
            status = False
            return status, need_sleep

    async def pyppeteer_get(self):
        page = await self.web_brownser()
        try:
            #                               {"_id": {"$gt": ObjectId("5ff480232d896ec165b8464c")}}
            userList = list(collection.find({"_id": {"$gt": ObjectId("5ff487d62d896ec165b86d37")}}))
            lastObject = userList[-1]
            print(lastObject["_id"])
            # 本次启动已经关注人数

            for index, user in enumerate(userList):
                status, need_sleep = await self.run_browser(user["uri"], page)
                self.real_count = self.real_count + 1 if status else self.real_count
                print("user : %s,\nindex : %s" % (user, index))
                print("已经关注 %s 人" % self.real_count)
                print("当前时间：%s \n" %time.strftime("%H:%M:%S", time.localtime()))
                if self.real_count > 500:
                    continue
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

    # async def web_brownser_new(self)->Browser:
    #     abrowser = await launch({'headless': False,
    #                             'userDataDir': './userData',
    #                             'userGesture': True,
    #                             'args': [
    #                                 '--disable-infobars', f'--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}'
    #                             ]})
    #     return abrowser

    # def calcuate(self, futter):
    #     print(futter.result())

    # def run_weibo(self):
    #     userList = list(collection.find({"_id": {"$gt": ObjectId("5ff47d012d896ec165b83626")}}))[:10]
    #     urls = [user["uri"] for user in userList]
    #     asyncio.get_event_loop().run_until_complete(self.gather_weibo(urls))


if __name__ == '__main__':
    password = '214500o'
    account = '18602522813'
    login = Follow(account, password)
    # login.run_weibo()
    # login.pyppeteer_get()
    asyncio.get_event_loop().run_until_complete(login.pyppeteer_get())
    # loop
