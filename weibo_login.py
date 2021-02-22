# -*- coding: utf-8 -*-
"""
Description:
Author:henly
Date:2021/1/26
Change Activity:2021/1/26:
"""
__author__ = 'henly'

import random
import asyncio
import pymongo

from time import sleep
import time
from pyppeteer import launch
from pyppeteer.page import Page
from pyppeteer.errors import TimeoutError
from bson.objectid import ObjectId

from weibo_follow import MONGO_CONNECTION_STRING
from weibo_follow import collection

WINDOW_WIDTH, WINDOW_HEIGHT = 1366, 768
client = pymongo.MongoClient(MONGO_CONNECTION_STRING)

class Follow(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    async def web_brownser(self):
        browser = await launch({'headless': False,
                                'userDataDir': './userData',
                                # 'devtools': True,
                                'userGesture': False,
                                'autoClose': False,
                                'args': [
                                    '--disable-infobars', f'--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}'
                                ]})
        page = await browser.newPage()
        await page.setViewport({'width': WINDOW_WIDTH, 'height': WINDOW_HEIGHT})
        await page.evaluateOnNewDocument('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')
        return page

    async def web_page(self, url, selecter, page: Page):
        try:
            await page.goto(url, options={"timeout": 1000 * 60})
            await asyncio.wait(
                [
                    asyncio.sleep(3),
                    page.waitForNavigation({'waitUntil': 'networkidle0'}),
                    page.waitForSelector(selecter, options={"timeout": 1000 * 60})
                ]
            )
            await self.run_browser(page)
        except TimeoutError:
            print('timeout error')

    async def run_browser(self, page: Page):
        # 未登录
        await page.type("input[node-type='username']", self.username)
        await page.type("input[node-type='password']", self.password)
        await page.click("a[tabindex='6']")
        await asyncio.wait(
            [
                page.waitForNavigation({'waitUntil': 'networkidle0'}),
                page.click('div[node-type="focusLink"] > a:nth-child(1)'),
            ]
        )
        await asyncio.sleep(5)
        print('finish scrool')

    async def pyppeteer_get(self):
        page = await self.web_brownser()
        try:
            await self.web_page('https://weibo.com', '.WB_miniblog_fb', page)
        finally:
            pass


if __name__ == '__main__':
    password = '214500o'
    account = '18602522813'
    login = Follow(account, password)
    asyncio.get_event_loop().run_until_complete(login.pyppeteer_get())
