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

    async def web_page(self, url, selecter, page: Page):
        try:
            await page.setViewport({'width': WINDOW_WIDTH, 'height': WINDOW_HEIGHT})
            # await page.evaluateOnNewDocument('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')
            await page.goto(url, options={"timeout": 1000 * 60})
            await asyncio.wait(
                [
                    asyncio.sleep(3),
                    page.waitForSelector(selecter, options={"timeout": 1000 * 30})
                ]
            )
            return page

        except:
            print('timeout error')
            return None

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
            userList = list(collection.find({"_id": {"$lte": ObjectId("5ff481ae2d896ec165b84ec7")}}).sort("_id", -1))
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
        group_list = ["4680381133492558", "4682554790382754", "4686168904697800",
                      "4686168942182617", "4686169016631390", "4686169054642690",
                      "4686169240240869", "4686169272483997", "4686169314690317",
                      "4686169353487163", "4686169390712648", "4694652555625594",
                      "4694652588393188"]
        page: Page = await self.web_brownser()

        for group_id in group_list:
            initall_page = 1
            # print("当前到页面id %s" % group_id)
            # url = f"https://weibo.com/p/1005051764018647/myfollow?t=1&cfs=&Pl_Official_RelationMyfollow__88_page=1#Pl_Official_RelationMyfollow__88"
            url = f"https://weibo.com/p/1005051764018647/myfollow?t=1&gid={group_id}&cfs=&Pl_Official_RelationMyfollow__89_page={initall_page}#Pl_Official_RelationMyfollow__89"
            print("url ", url)
            await self.web_page(url, ".WB_frame", page)
            await asyncio.sleep(10)
            pages = await page.JJ("[bpfilter='page'].S_txt1.page")
            last_page = 1
            if len(pages) > 1:
                last_page = await page.evaluate('element => element.innerText', pages[-2])
                await asyncio.sleep(1)
            for _ in range(0, int(last_page)):
                # next_url = f"https://weibo.com/p/1005051764018647/myfollow?t=1&ignoreg=1&cfs=&Pl_Official_RelationMyfollow__88_page={initall_page}#Pl_Official_RelationMyfollow__88"
                next_url = f"https://weibo.com/p/1005051764018647/myfollow?t=1&gid={group_id}&cfs=&Pl_Official_RelationMyfollow__88_page={initall_page}#Pl_Official_RelationMyfollow__88"
                print("next_url ", next_url)
                next_page = await self.web_page(next_url, ".WB_frame", page)
                if next_page:
                    await asyncio.sleep(2)
                    await next_page.querySelectorEval(".btn_link.S_txt1", "(element) => element.click()")
                    await asyncio.sleep(1)
                    elements = await next_page.JJ(".member_li")
                    selected_count = 0
                    for li in elements:
                        # 如果未关注，才会勾选
                        status = await li.Jeval("span.S_txt1", "li => li.innerText")
                        if status != "互相关注":
                            await li.click()
                            selected_count += 1
                    await asyncio.sleep(1)

                    if selected_count > 0:
                        cancel_btn = await next_page.J('.W_btn_a[node-type="cancelFollowBtn"')
                        await cancel_btn.click()
                        await asyncio.sleep(1)
                        sure = await next_page.J('[node-type="ok"]')
                        await asyncio.sleep(1)
                        await sure.click()
                        print("取消关注 %s 人" % selected_count)
                        await asyncio.sleep(5)
                    else:
                        print("当前页没有选中的")

                    curpages = await next_page.JJ("[bpfilter='page'].S_txt1.page")
                    for each in curpages:
                        cust = await next_page.evaluate('element => element.innerText', each)
                        print(cust)
                    initall_page += 1

# 移动到一个分组
    async def start_move_page(self):
        group_list = ["4680381133492558", "4682554790382754", "4686168904697800",
                      "4686168942182617", "4686169016631390", "4686169054642690",
                      "4686169240240869", "4686169272483997", "4686169314690317",
                      "4686169353487163", "4686169390712648", "4694652555625594",
                      "4694652588393188"]
        page: Page = await self.web_brownser()

        for group_id in group_list:
            initall_page = 1
            # print("当前到页面id %s" % group_id)
            # url = f"https://weibo.com/p/1005051764018647/myfollow?t=1&cfs=&Pl_Official_RelationMyfollow__88_page=1#Pl_Official_RelationMyfollow__88"
            url = f"https://weibo.com/p/1005051764018647/myfollow?t=1&gid={group_id}&cfs=&Pl_Official_RelationMyfollow__89_page={initall_page}#Pl_Official_RelationMyfollow__89"
            print("url ", url)
            await self.web_page(url, ".WB_frame", page)
            await asyncio.sleep(10)
            pages = await page.JJ("[bpfilter='page'].S_txt1.page")
            last_page = 1
            if len(pages) > 1:
                last_page = await page.evaluate('element => element.innerText', pages[-2])
                await asyncio.sleep(1)
            for _ in range(0, int(last_page)):
                # next_url = f"https://weibo.com/p/1005051764018647/myfollow?t=1&ignoreg=1&cfs=&Pl_Official_RelationMyfollow__88_page={initall_page}#Pl_Official_RelationMyfollow__88"
                next_url = f"https://weibo.com/p/1005051764018647/myfollow?t=1&gid={group_id}&cfs=&Pl_Official_RelationMyfollow__88_page={initall_page}#Pl_Official_RelationMyfollow__88"
                print("next_url ", next_url)
                next_page = await self.web_page(next_url, ".WB_frame", page)
                if next_page:
                    await asyncio.sleep(2)
                    await next_page.querySelectorEval(".btn_link.S_txt1", "(element) => element.click()")
                    await asyncio.sleep(1)
                    elements = await next_page.JJ(".member_li")
                    selected_count = 0
                    for li in elements:
                        # 如果未关注，才会勾选
                        status = await li.Jeval("span.S_txt1", "li => li.innerText")
                        if status == "互相关注":
                            await li.click()
                            selected_count += 1
                    await asyncio.sleep(1)

                    if selected_count > 0:
                        move_btn = await next_page.J('.W_btn_a[node-type="addToOtherGroupBtn"')
                        await move_btn.click()
                        await asyncio.sleep(1)
                        label_sure = await next_page.J("[for='4686168971283766']")
                        await asyncio.sleep(1)
                        await label_sure.click()
                        print("移走 %s 人" % selected_count)
                        await asyncio.sleep(5)
                    else:
                        print("当前页没有选中的")

                    curpages = await next_page.JJ("[bpfilter='page'].S_txt1.page")
                    for each in curpages:
                        cust = await next_page.evaluate('element => element.innerText', each)
                        print(cust)
                    initall_page += 1

if __name__ == '__main__':
    password = '214500o'
    account = '18602522813'
    login = Follow(account, password)
    # login.run_weibo()
    # asyncio.get_event_loop().run_until_complete(login.start_a_page())
    asyncio.get_event_loop().run_until_complete(login.start_move_page())

    # asyncio.get_event_loop().run_until_complete(login.pyppeteer_get())
