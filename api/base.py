import asyncio
import json
import re
import cytoolz
import httpx
import random

from typing import Any, List, Optional
from abc import ABC, abstractmethod
import cytoolz
import httpx
import sentry_sdk
from aiogram.types import Message
from bs4 import BeautifulSoup
from httpcore import TimeoutException
from httpx import HTTPStatusError
from bot.data import VideoData
from urllib.parse import quote, urlencode


class TikTokAPI(API):

    @property
    def links(self) -> List[str]:
        return ['tiktok.com']

    @property
    def regexp_key(self) -> str:
        return r'"downloadAddr":"'

    def _parse_data(self, script: str) -> Optional[str]:
        return cytoolz.get_in(
            ['props', 'pageProps', 'itemInfo', 'itemStruct', 'video', 'downloadAddr'],
            json.loads(script)
        )

class API(ABC):

    @property
    def headers(self) -> dict[str, Any]:
        return {
            "Referer": "https://www.tiktok.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/86.0.4240.111 Safari/537.36",
        }

    def __add_url_params__(self) -> str:
        query = {
            "aid": 1988,
            "app_name": "tiktok_web",
            "device_platform": "web_mobile",
            "region": "US",
            "priority_region": "",
            "os": "ios",
            "referer": "",
            "root_referer": "",
            "cookie_enabled": "true",
            "screen_width": "1920",
            "screen_height": "1080",
            "browser_language": "en-us",
            "browser_platform": "iPhone",
            "browser_name": "Mozilla",
            "browser_version": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/86.0.4240.111 Safari/537.36",
            "browser_online": "true",
            "timezone_name": "America/Chicago",
            "is_page_visible": "true",
            "focus_state": "true",
            "is_fullscreen": "false",
            "history_len": random.randint(0, 30),
            "language": "en"
        }
        return urlencode(query)

    @property
    def cookies(self) -> dict[str, Any]:
        return {
            'tt_webid_v2': '1234567890123456789'
        }

    @property
    @abstractmethod
    def links(self) -> List[str]:
        return ['platform.com']

    @property
    @abstractmethod
    def regexp_key(self) -> str:
        return 'key'

    async def get_video_by_url(self, url: str): -> VideoData:



    async def handle_message(self, message: Message) -> List[VideoData]:

        urls = []
        for e in message.entities:
            for link in self.links:
                if link in (url := message.text[e.offset:e.offset + e.length]):
                    urls.append(url if url.startswith('http') else f'https://{url}')
        try:
            return [await self.download_video(url) for url in urls]
        except (KeyError, HTTPStatusError) as ex:
            sentry_sdk.capture_exception(ex)


        return []

    async def download_video(self, url: str, retries: int = 2) -> VideoData:

        if "@" in url and "/video/" in url:
            post_id = url.split("/video/")[1].split("?")[0]
        else:
            raise Exception(
                "URL format not supported. Below is an example of a supported url.\n"
                "https://www.tiktok.com/@therock/video/6829267836783971589"
            )
        language = "en"
        query = {
            "itemId": post_id,
            "language": language,
        }

        api_url = "https://t.tiktok.com/api/item/detail/?{}&{}".format(
            API.__add_url_params__(), urlencode(query)
        )











        download_url = post_id["itemInfo"]["itemStruct"]["video"]["downloadAddr"]










        for _ in range(retries):
            async with httpx.AsyncClient(headers=self.headers, timeout=30, cookies=self.cookies) as client:
                try:
                    page = await client.get(url)
                    soup = BeautifulSoup(page.content, 'html.parser')
                    if data := soup(text=re.compile(self.regexp_key)):
                        for script in data:
                            if link := self._parse_data(script):
                                if video := await client.get(link):
                                    video.raise_for_status()
                                    return VideoData(link, video.content)
                except TimeoutException:
                    pass
                await asyncio.sleep(0.5)
        return VideoData()

    @abstractmethod
    def _parse_data(self, script: str) -> Optional[str]:
        pass
