from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import json
import os
import re
import random
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)
chromedriver_path = "E:\\Code\\weibo-spider\\public-opinion-monitoring-and-visualization\\WeiboScrapy\\WeiboScrapy\\chromedriver.exe"
cookies_path = "WeiboScrapy/cookies.txt"


class WeiboscrapySpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class RotateAgentMiddleware(UserAgentMiddleware):
    '''
    Random User Agent
    '''

    def __init__(self, user_agent):
        self.user_agent = user_agent

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            user_agent=crawler.settings.get('MY_USER_AGENT')
        )

    def process_request(self, request, spider):

        # real time random select user agent from website
        agent = random.choice(self.user_agent)
        logger.info("Hold Agent {agent}".format(agent=agent))

        # hold user agent
        request.headers["User-Agent"] = agent


class RotateProxyMiddleware(object):

    def process_request(self, request, spider):
        '''
        get random proxy from "Free Proxy List" website
        not enabled unless necessary
        '''

        # webdriver setting
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')

        # webdriver request
        driver = webdriver.Chrome(
            executable_path=chromedriver_path, chrome_options=options)
        driver.get("http://free-proxy-list.net")
        time.sleep(1)

        # real time random select free proxy from website
        row = int(random.randint(1, 20))
        ip = driver.find_element_by_xpath(
            "//tbody/tr[{row}]/td[1]".format(row=row)).text
        port = driver.find_element_by_xpath(
            "//tbody/tr[{row}]/td[2]".format(row=row)).text
        proxy = "{ip}:{port}".format(ip=ip, port=port)
        logger.info("Hold Proxy {proxy}".format(proxy=proxy))
        driver.quit()

        # hold proxy
        request.meta["proxy"] = proxy


class WeiboDownloaderMiddleware(object):
    def connection(self, request):
        '''
        登录微博，返回driver对象
        '''
        # webdriver setting
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--user-agent=%s' % request.headers["User-Agent"])

        # webdriver request
        driver = webdriver.Chrome(
            executable_path=chromedriver_path, chrome_options=options)
        driver.set_window_size(1440, 800)
        driver.delete_all_cookies()
        driver.get(request.url)

        # 检查登录
        if os.path.exists(cookies_path):
            # use saved cookies to login
            with open(cookies_path, 'r') as f:
                cookies = json.loads(f.read())
                for cookie in cookies:
                    driver.add_cookie(cookie)
                driver.refresh()
                time.sleep(10)
                print("login successfully")
        else:
            driver.get("https://passport.weibo.cn/signin/login")
            time.sleep(3)
            # wait for the user to log in manually
            input(
                'Please login in Chrome. \nPress Enter to continue if successful.')
            # get and save cookies in a local file
            with open(cookies_path, 'w') as f:
                cookies = driver.get_cookies()
                f.write(json.dumps(cookies))

        return driver

    def process_request(self, request, spider):
        if request.url == "https://m.weibo.cn":
            if spider.name == "weibospider":

                data = []

                # 登录
                driver = self.connection(request)

                # 开始搜索
                # keywords = input("请输入感兴趣的舆论话题/关键词，以空格进行分隔\n")
                keywords = "找工作"
                driver.find_element_by_class_name("nav-search").click()
                time.sleep(5)
                driver.refresh()
                time.sleep(5)
                # search_box=driver.find_element_by_xpath('//*[@id="app"]//form/input')
                search_box = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="app"]//form/input')))
                time.sleep(5)
                # input keywords and hit enter
                search_box.send_keys(keywords, Keys.ENTER)
                time.sleep(5)
                # switch from 综合 to 实时
                driver.find_element_by_xpath(
                    "//*[@id=\"app\"]/div[1]/div[1]/div[2]/div[2]/div[1]/div/div/div/ul/li[3]/span").click()
                time.sleep(15)

                # search params
                containerid = '100103'
                search_type = '61'
                query = quote(keywords, 'utf-8')
                # get each page
                for index in range(5):
                    index += 1
                    request_url = "https://m.weibo.cn/api/container/getIndex?containerid=" + containerid + \
                        r"type%3D" + search_type + "%26q%3D" + query + \
                        "%26t%3D0&page_type=searchall&page=" + str(index)
                    driver.get(request_url)
                    html_innertext = re.sub(
                        r'<html>.*?white-space: pre-wrap;">|</pre></body></html>', "", driver.page_source)
                    json_text = json.loads(html_innertext)
                    for card in json_text["data"]["cards"]:
                        uid = card["mblog"]["user"]["id"]  # 用户id
                        info_url = "https://m.weibo.cn/p/index?containerid=230283" + \
                            str(uid) + "_-_INFO"
                        driver.get(info_url)
                        time.sleep(2)
                        info_html = driver.page_source
                        time.sleep(2)
                        try:
                            card["mblog"]["user"]["city"] = driver.find_element_by_xpath(
                                "//div[contains(text(),'所在地')]/following-sibling::div").text
                        except:
                            card["mblog"]["user"]["city"] = ""
                            pass
                    html_innertext = json.dumps(json_text)
                    data.append(html_innertext)
                    time.sleep(10)

                driver.quit()

                # 构建response，并发送给spider
                return HtmlResponse(url=request.url, body=json.dumps(data).encode('utf-8'), request=request, encoding='utf-8')

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
