import json
import logging
import os
import random
import string
import time
from urllib.parse import quote, urlencode

import requests
from asyncinit import asyncinit
from playwright.sync_api import sync_playwright

from .exceptions import *
from .utilities import update_messager

os.environ["no_proxy"] = "127.0.0.1,localhost"

BASE_URL = "https://m.tiktok.com/"

@asyncinit
class TikTokApi():
    __instance = None

    async def __init__(self, **kwargs):
        """The TikTokApi class. Used to interact with TikTok, use get_instance NOT this."""
        # Forces Singleton
        if TikTokApi.__instance is None:
            TikTokApi.__instance = self
        else:
            raise Exception("Only one TikTokApi object is allowed")
        logging.basicConfig(level=kwargs.get("logging_level", logging.WARNING))
        logging.info("Class initalized")

        # Some Instance Vars
        self.executablePath = kwargs.get("executablePath", None)

        if kwargs.get("custom_did") != None:
            raise Exception("Please use custom_device_id instead of custom_device_id")
        self.custom_device_id = kwargs.get("custom_device_id", None)
        self.userAgent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/86.0.4240.111 Safari/537.36"
        )
        self.proxy = kwargs.get("proxy", None)
        self.custom_verifyFp = kwargs.get("custom_verifyFp")
        self.signer_url = kwargs.get("external_signer", None)
        self.request_delay = kwargs.get("request_delay", None)
        self.requests_extra_kwargs = kwargs.get("requests_extra_kwargs", {})

        if kwargs.get("use_test_endpoints", False):
            global BASE_URL
            BASE_URL = "https://t.tiktok.com/"
        if kwargs.get("use_selenium", False):
            print('kek')
        else:
            from .browser import browser

        if kwargs.get("generate_static_device_id", False):
            self.custom_device_id = "".join(random.choice(string.digits) for num in range(19))

        if self.signer_url is None:
            self.browser = browser(**kwargs)
            self.userAgent = self.browser.userAgent

        try:
            self.timezone_name = self.__format_new_params__(self.browser.timezone_name)
            self.browser_language = self.__format_new_params__(
                self.browser.browser_language
            )
            self.width = self.browser.width
            self.height = self.browser.height
            self.region = self.browser.region
            self.language = self.browser.language
        except Exception as e:
            logging.exception(e)
            logging.warning("An error ocurred while opening your browser but it was ignored.")
            logging.warning("Are you sure you ran python -m playwright install")

            self.timezone_name = ""
            self.browser_language = ""
            self.width = "1920"
            self.height = "1080"
            self.region = "US"
            self.language = "en"

    @staticmethod
    async def get_instance(**kwargs):
        """The TikTokApi class. Used to interact with TikTok. This is a singleton
            class to prevent issues from arising with playwright

        ##### Parameters
        * logging_level: The logging level you want the program to run at, optional
            These are the standard python logging module's levels.

        * request_delay: The amount of time to wait before making a request, optional
            This is used to throttle your own requests as you may end up making too
            many requests to TikTok for your IP.

        * custom_device_id: A TikTok parameter needed to download videos, optional
            The code generates these and handles these pretty well itself, however
            for some things such as video download you will need to set a consistent
            one of these. All the methods take this as a optional parameter, however
            it's cleaner code to store this at the instance level. You can override
            this at the specific methods.

        * generate_static_device_id: A parameter that generates a custom_device_id at the instance level
            Use this if you want to download videos from a script but don't want to generate
            your own custom_device_id parameter.

        * custom_verifyFp: A TikTok parameter needed to work most of the time, optional
            To get this parameter look at [this video](https://youtu.be/zwLmLfVI-VQ?t=117)
            I recommend watching the entire thing, as it will help setup this package. All
            the methods take this as a optional parameter, however it's cleaner code
            to store this at the instance level. You can override this at the specific
            methods.

            You can use the following to generate `"".join(random.choice(string.digits)
            for num in range(19))`

        * use_test_endpoints: Send requests to TikTok's test endpoints, optional
            This parameter when set to true will make requests to TikTok's testing
            endpoints instead of the live site. I can't guarantee this will work
            in the future, however currently basically any custom_verifyFp will
            work here which is helpful.

        * proxy: A string containing your proxy address, optional
            If you want to do a lot of scraping of TikTok endpoints you'll likely
            need a proxy.

            Ex: "https://0.0.0.0:8080"

            All the methods take this as a optional parameter, however it's cleaner code
            to store this at the instance level. You can override this at the specific
            methods.

        * use_selenium: Option to use selenium over playwright, optional
            Playwright is selected by default and is the one that I'm designing the
            package to be compatable for, however if playwright doesn't work on
            your machine feel free to set this to True.

        * executablePath: The location of the driver, optional
            This shouldn't be needed if you're using playwright

        * **kwargs
            Parameters that are passed on to basically every module and methods
            that interact with this main class. These may or may not be documented
            in other places.
        """
        if not TikTokApi.__instance:
            TikTokApi(**kwargs)
        return TikTokApi.__instance

    async def clean_up(self):
        """A basic cleanup method, called automatically from the code"""
        self.__del__()

    async def __del__(self):
        """A basic cleanup method, called automatically from the code"""
        try:
            self.browser.clean_up()
        except Exception:
            pass
        try:
            get_playwright().stop()
        except Exception:
            pass
        TikTokApi.__instance = None

    async def external_signer(self, url, custom_device_id=None, verifyFp=None):
        """Makes requests to an external signer instead of using a browser.

        ##### Parameters
        * url: The server to make requests to
            This server is designed to sign requests. You can find an example
            of this signature server in the examples folder.

        * custom_device_id: A TikTok parameter needed to download videos
            The code generates these and handles these pretty well itself, however
            for some things such as video download you will need to set a consistent
            one of these.

        * custom_verifyFp: A TikTok parameter needed to work most of the time,
            To get this parameter look at [this video](https://youtu.be/zwLmLfVI-VQ?t=117)
            I recommend watching the entire thing, as it will help setup this package.
        """
        if custom_device_id is not None:
            query = {"url": url, "custom_device_id": custom_device_id, "verifyFp": verifyFp}
        else:
            query = {"url": url, "verifyFp": verifyFp}
        data = requests.get(
            self.signer_url + "?{}".format(urlencode(query)),
            **self.requests_extra_kwargs,
        )
        parsed_data = data.json()

        return (
            parsed_data["verifyFp"],
            parsed_data["device_id"],
            parsed_data["_signature"],
            parsed_data["userAgent"],
            parsed_data["referrer"],
        )

    # 205
    async def get_data(self, **kwargs) -> dict:
        """Makes requests to TikTok and returns their JSON.

        This is all handled by the package so it's unlikely
        you will need to use this.
        """
        (
            region,
            language,
            proxy,
            maxCount,
            device_id,
        ) = self.__process_kwargs__(kwargs)
        kwargs["custom_device_id"] = device_id
        if self.request_delay is not None:
            time.sleep(self.request_delay)

        if self.proxy is not None:
            proxy = self.proxy

        if kwargs.get("custom_verifyFp") == None:
            if self.custom_verifyFp != None:
                verifyFp = self.custom_verifyFp
            else:
                verifyFp = "verify_khr3jabg_V7ucdslq_Vrw9_4KPb_AJ1b_Ks706M8zIJTq"
        else:
            verifyFp = kwargs.get("custom_verifyFp")

        tt_params = None
        if self.signer_url is None:
            kwargs["custom_verifyFp"] = verifyFp
            verify_fp, device_id, signature, tt_params = self.browser.sign_url(**kwargs)
            userAgent = self.browser.userAgent
            referrer = self.browser.referrer
        else:
            verify_fp, device_id, signature, userAgent, referrer = self.external_signer(
                kwargs["url"],
                custom_device_id=kwargs.get("custom_device_id"),
                verifyFp=kwargs.get("custom_verifyFp", verifyFp),
            )

        if not kwargs.get("send_tt_params", False):
            tt_params = None

        query = {"verifyFp": verify_fp, "device_id": device_id, "_signature": signature}
        url = "{}&{}".format(kwargs["url"], urlencode(query))

        h = requests.head(
            url,
            headers={"x-secsdk-csrf-version": "1.2.5", "x-secsdk-csrf-request": "1"},
            proxies=self.__format_proxy(proxy),
            **self.requests_extra_kwargs,
        )
        csrf_session_id = h.cookies["csrf_session_id"]
        csrf_token = h.headers["X-Ware-Csrf-Token"].split(",")[1]
        kwargs["csrf_session_id"] = csrf_session_id

        r = requests.get(
            url,
            headers={
                "authority": "m.tiktok.com",
                "method": "GET",
                "path": url.split("tiktok.com")[1],
                "scheme": "https",
                "accept": "application/json, text/plain, */*",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-US,en;q=0.9",
                "origin": referrer,
                "referer": referrer,
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "sec-gpc": "1",
                "user-agent": userAgent,
                "x-secsdk-csrf-token": csrf_token,
                "x-tt-params": tt_params
            },
            cookies=self.get_cookies(**kwargs),
            proxies=self.__format_proxy(proxy),
            **self.requests_extra_kwargs,
        )
        try:
            json = r.json()
            if (
                    json.get("type") == "verify"
                    or json.get("verifyConfig", {}).get("type", "") == "verify"
            ):
                logging.error(
                    "Tiktok wants to display a catcha. Response is:\n" + r.text
                )
                logging.error(self.get_cookies(**kwargs))
                raise TikTokCaptchaError()
            if json.get("statusCode", 200) == 10201:
                # Invalid Entity
                raise TikTokNotFoundError(
                    "TikTok returned a response indicating the entity is invalid"
                )
            return r.json()
        except ValueError as e:
            text = r.text
            logging.error("TikTok response: " + text)
            if len(text) == 0:
                raise EmptyResponseError(
                    "Empty response from Tiktok to " + url
                ) from None
            else:
                logging.error("Converting response to JSON failed")
                logging.error(e)
                raise JSONDecodeFailure() from e

    # 316
    async def get_cookies(self, **kwargs):
        """Extracts cookies from the kwargs passed to the function for get_data"""
        device_id = kwargs.get(
            "custom_device_id", "".join(random.choice(string.digits) for num in range(19))
        )
        if kwargs.get("custom_verifyFp") == None:
            if self.custom_verifyFp != None:
                verifyFp = self.custom_verifyFp
            else:
                verifyFp = "verify_khr3jabg_V7ucdslq_Vrw9_4KPb_AJ1b_Ks706M8zIJTq"
        else:
            verifyFp = kwargs.get("custom_verifyFp")

        if kwargs.get("force_verify_fp_on_cookie_header", False):
            return {
                "tt_webid": device_id,
                "tt_webid_v2": device_id,
                "csrf_session_id": kwargs.get("csrf_session_id"),
                "tt_csrf_token": "".join(
                    random.choice(string.ascii_uppercase + string.ascii_lowercase)
                    for i in range(16)
                ),
                "s_v_web_id": verifyFp,
            }
        else:
            return {
                "tt_webid": device_id,
                "tt_webid_v2": device_id,
                "csrf_session_id": kwargs.get("csrf_session_id"),
                "tt_csrf_token": "".join(
                    random.choice(string.ascii_uppercase + string.ascii_lowercase)
                    for i in range(16)
                ),
            }

    # 351
    async def get_bytes(self, **kwargs) -> bytes:
        """Returns TikTok's response as bytes, similar to get_data"""
        (
            region,
            language,
            proxy,
            maxCount,
            device_id,
        ) = self.__process_kwargs__(kwargs)
        kwargs["custom_device_id"] = device_id
        if self.signer_url is None:
            verify_fp, device_id, signature = self.browser.sign_url(**kwargs)
            userAgent = self.browser.userAgent
            referrer = self.browser.referrer
        else:
            verify_fp, device_id, signature, userAgent, referrer = self.external_signer(
                kwargs["url"], custom_device_id=kwargs.get("custom_device_id", None)
            )
        query = {"verifyFp": verify_fp, "_signature": signature}
        url = "{}&{}".format(kwargs["url"], urlencode(query))
        r = requests.get(
            url,
            headers={
                "Accept": "*/*",
                "Accept-Encoding": "identity;q=1, *;q=0",
                "Accept-Language": "en-US;en;q=0.9",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Host": url.split("/")[2],
                "Pragma": "no-cache",
                "Range": "bytes=0-",
                "Referer": "https://www.tiktok.com/",
                "User-Agent": userAgent,
            },
            proxies=self.__format_proxy(proxy),
            cookies=self.get_cookies(**kwargs),
        )
        return r.content

    # 1073
    async def get_tiktok_by_id(self, id, **kwargs) -> dict:
        """Returns a dictionary of a specific TikTok.

        ##### Parameters
        * id: The id of the TikTok you want to get the object for
        """
        (
            region,
            language,
            proxy,
            maxCount,
            device_id,
        ) = self.__process_kwargs__(kwargs)
        kwargs["custom_device_id"] = device_id
        device_id = kwargs.get("custom_device_id", None)
        query = {
            "itemId": id,
            "language": language,
        }
        api_url = "{}api/item/detail/?{}&{}".format(
            BASE_URL, self.__add_url_params__(), urlencode(query)
        )

        return self.get_data(url=api_url, **kwargs)

    # 1098
    async def get_tiktok_by_url(self, url, **kwargs) -> dict:
        """Returns a dictionary of a TikTok object by url.


        ##### Parameters
        * url: The TikTok url you want to retrieve

            This currently doesn't support the shortened TikTok
            url links.
        """
        (
            region,
            language,
            proxy,
            maxCount,
            device_id,
        ) = self.__process_kwargs__(kwargs)
        kwargs["custom_device_id"] = device_id
        custom_device_id = kwargs.get("custom_device_id", None)
        if "@" in url and "/video/" in url:
            post_id = url.split("/video/")[1].split("?")[0]
        else:
            raise Exception(
                "URL format not supported. Below is an example of a supported url.\n"
                "https://www.tiktok.com/@therock/video/6829267836783971589"
            )

        return self.get_tiktok_by_id(
            post_id,
            **kwargs,
        )

    # 1523
    async def get_video_by_url(self, video_url, **kwargs) -> bytes:
        """Downloads a TikTok video by a URL

        ##### Parameters
        * video_url: The TikTok url to download the video from
        """
        (
            region,
            language,
            proxy,
            maxCount,
            device_id,
        ) = self.__process_kwargs__(kwargs)
        kwargs["custom_device_id"] = device_id

        tiktok_schema = self.get_tiktok_by_url(video_url, **kwargs)
        download_url = tiktok_schema["itemInfo"]["itemStruct"]["video"]["downloadAddr"]

        return self.get_bytes(url=download_url, **kwargs)

    #
    # PRIVATE METHODS
    #

    def __format_proxy(self, proxy) -> dict:
        """
        Formats the proxy object
        """
        if proxy is None and self.proxy is not None:
            proxy = self.proxy
        if proxy is not None:
            return {"http": proxy, "https": proxy}
        else:
            return None

    def __format_new_params__(self, parm) -> str:
        # TODO: Maybe try not doing this? It should be handled by the urlencode.
        return parm.replace("/", "%2F").replace(" ", "+").replace(";", "%3B")

    def __add_url_params__(self) -> str:
        query = {
            "aid": 1988,
            "app_name": "tiktok_web",
            "device_platform": "web_mobile",
            "region": self.region or "US",
            "priority_region": "",
            "os": "ios",
            "referer": "",
            "root_referer": "",
            "cookie_enabled": "true",
            "screen_width": self.width,
            "screen_height": self.height,
            "browser_language": self.browser_language.lower() or "en-us",
            "browser_platform": "iPhone",
            "browser_name": "Mozilla",
            "browser_version": self.__format_new_params__(self.userAgent),
            "browser_online": "true",
            "timezone_name": self.timezone_name or "America/Chicago",
            "is_page_visible": "true",
            "focus_state": "true",
            "is_fullscreen": "false",
            "history_len": random.randint(0, 30),
            "language": self.language or "en"
        }
        return urlencode(query)

    # Process the kwargs
    def __process_kwargs__(self, kwargs):
        region = kwargs.get("region", "US")
        language = kwargs.get("language", "en")
        proxy = kwargs.get("proxy", None)
        maxCount = kwargs.get("maxCount", 35)

        if kwargs.get("custom_device_id", None) != None:
            device_id = kwargs.get("custom_device_id")
        else:
            if self.custom_device_id != None:
                device_id = self.custom_device_id
            else:
                device_id = "".join(random.choice(string.digits) for num in range(19))
        return region, language, proxy, maxCount, device_id
