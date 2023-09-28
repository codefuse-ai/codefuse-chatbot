import requests
from fake_useragent import UserAgent
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import json
import os
from requests.exceptions import Timeout
from urllib.parse import urlsplit
import re
import math
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By


class WebHtmlExtractor():
    '''爬取web网站html格式数据，分为requests和selenium两种方式；selenium需提前下载chrome浏览器与chromedriver，并配置路径。
    '''

    def __init__(self, header=None, data={}, time_sleep=1, time_out=20, max_retry_times=3):
        # 最大重试次数
        self.max_retry_times = max_retry_times
        # requests请求的header
        if header:
            self.header = header
        else:
            self.header = {
                'User-Agent': UserAgent().random, 'Cookie': None
            }
        # 发送post请求时的data参数
        self.data = data
        # 请求时间间隔s
        self.time_sleep = time_sleep
        # 请求时间时间s
        self.time_out = time_out

    def save_url_html(self, base_url=None, reptile_lib="requests", method="get", time_sleep=None, time_out=None, html_dir=None,mode="w"):
        '''
        对base_url网址发送请求，爬取base_url网址中1度跳转的网址，限制目标网址以target_url_prefix为前缀
        :param base_url: 目标站点
        :param target_url_prefix: 基于base_url网址，1度跳转链接 且 以target_url_prefix开头。默认为target_url_prefix=base_url（请求返回的当前网址url，中文会自动转为编码）。
        :param reptile_lib: requests和selenium两种方式；requests为简单请求静态网址html内容，js动态数据无法获取；selenium为模拟人行为请求，可获取全部html数据，但请求时间较长，尽量设置5s以上的time_sleep。
        :param method: requests请求有get/post两种，selenium只支持get
        :param time_sleep: 等待时间s
        :param time_out: 超时时长s
        :param html_dir: 保存html地址，jsonl文件
        :return: None
        '''
        if time_out is None:
            time_out = self.time_out
        if time_sleep is None:
            time_sleep = self.time_sleep
        # 创建保存目录
        os.makedirs(os.path.dirname(html_dir), exist_ok=True)
        # 发送请求获取base_url结果：包含当前页面全部网址，默认限制在base_url路径下
        html_dict = self.get_html_dict(
            url=base_url, reptile_lib=reptile_lib, method=method, time_sleep=time_sleep, time_out=time_out)
        # 保存文件
        self.save_jsonl(file_path=html_dir, json_list=[
            html_dict], mode=mode)

    def save_1_jump_url_in_base(self, base_url=None, target_url_prefix=None, reptile_lib="requests", method="get", time_sleep=None, time_out=None, html_dir=None,mode = "w"):
        '''
        对base_url网址发送请求，爬取base_url网址中1度跳转的网址，限制目标网址以target_url_prefix为前缀
        :param base_url: 目标站点
        :param target_url_prefix: 基于base_url网址，1度跳转链接 且 以target_url_prefix开头。默认为target_url_prefix=base_url（请求返回的当前网址url，中文会自动转为编码）。
        :param reptile_lib: requests和selenium两种方式；requests为简单请求静态网址html内容，js动态数据无法获取；selenium为模拟人行为请求，可获取全部html数据，但请求时间较长，尽量设置5s以上的time_sleep。
        :param method: requests请求有get/post两种，selenium只支持get
        :param time_sleep: 等待时间s
        :param time_out: 超时时长s
        :param html_dir: 保存html地址，jsonl文件
        :return: None
        '''
        if time_out is None:
            time_out = self.time_out
        if time_sleep is None:
            time_sleep = self.time_sleep
        # 创建保存目录
        os.makedirs(os.path.dirname(html_dir), exist_ok=True)
        # 发送请求获取base_url结果：包含当前页面全部网址，默认限制在base_url路径下
        html_dict = self.get_html_dict(
            url=base_url, reptile_lib=reptile_lib, method=method, time_sleep=time_sleep, time_out=time_out)
        # 如果target_url_prefix为空，用base_url作为前缀
        if target_url_prefix is None:
            target_url_prefix = html_dict['url']
        sub_url_list = self.get_link_sub_url_list(
            html_dict=html_dict, target_url_prefix=target_url_prefix)
        sub_url_nums = len(sub_url_list)
        logging.info("站点根目录{base_url}包含{url_nums}个网址".format(
            base_url=base_url, url_nums=sub_url_nums))
        # 循环请求1度跳转网址列表，并保存数据
        k = 0
        while k < sub_url_nums:
            # 提取第k个网址
            sub_url = sub_url_list[k]
            # 发送请求并返回response
            logging.info(
                "第{k}个网址，进度{rate}%……".format(k=k + 1, rate=round((k + 1) / sub_url_nums * 100, 1), url=sub_url))
            if k == 0:
                mode = mode
            else:
                mode = "a"
            # 爬取url网页html全部内容，保存为字典
            html_dict = self.get_html_dict(
                url=sub_url, reptile_lib=reptile_lib, method=method, time_sleep=time_sleep, time_out=time_out)
            # 保存文件
            self.save_jsonl(file_path=html_dir, json_list=[
                            html_dict], mode=mode)
            k += 1

    def save_2_jump_url_in_base(self, base_url=None, target_url_prefix=None, reptile_lib="requests", method="get", time_sleep=None, time_out=None, html_dir=None):
        '''
        对base_url网址发送请求，爬取base_url网址中2度跳转的网址，限制目标网址以target_url_prefix为前缀
        :param base_url: 当前根网页站点
        :param target_url_prefix: 基于base_url网址，2度跳转目标页面网址前缀，目标网址需要以target_url_prefix开头
        :param reptile_lib: requests和selenium两种方式；requests为简单请求静态网址html内容，js动态数据无法获取；selenium为模拟人行为请求，可获取全部html数据，但请求时间较长，尽量设置5s以上的time_sleep。
        :param method: requests请求有get/post两种，selenium只支持get
        :param time_sleep: 等待时间s
        :param time_out: 超时时长s
        :param html_dir: 保存html地址，jsonl文件
        :return: None
        '''
        if time_out is None:
            time_out = self.time_out
        if time_sleep is None:
            time_sleep = self.time_sleep
        # 创建保存目录
        os.makedirs(os.path.dirname(html_dir), exist_ok=True)
        # 爬取html网页数据
        html_dict = self.get_html_dict(
            url=base_url, reptile_lib=reptile_lib, method=method, time_sleep=time_sleep, time_out=time_out)
        # 提取html中的链接网址
        sub_url_list = self.get_link_sub_url_list(html_dict=html_dict)
        logging.info("站点根目录{base_url}包含{url_nums}个网址".format(
            base_url=base_url, url_nums=len(sub_url_list)))
        n_url = 0
        # 2度跳转网址，爬取html网页并保存
        for k, sub_url in enumerate(sub_url_list):
            sub_url_html_dict = self.get_html_dict(
                url=sub_url, reptile_lib=reptile_lib, method=method, time_sleep=time_sleep, time_out=time_out)
            sub_url_list_2 = self.get_link_sub_url_list(
                html_dict=sub_url_html_dict, target_url_prefix=target_url_prefix)
            logging.info("第{k}个网址，进度{rate}%,目录{sub_url}包含{url_nums}个网址".format(k=k + 1, rate=round(
                (k + 1) / len(sub_url_list) * 100, 1), sub_url=sub_url, url_nums=len(sub_url_list_2)))
            for i, sub2_url in enumerate(sub_url_list_2):
                if k == 0 and i == 0:
                    mode = "w"
                else:
                    mode = "a"
                # 爬取url网页html全部内容，保存为字典
                html_dict = self.get_html_dict(
                    url=sub2_url, reptile_lib=reptile_lib, method=method, time_sleep=time_sleep, time_out=time_out)
                # 保存文件
                self.save_jsonl(file_path=html_dir, json_list=[
                                html_dict], mode=mode)
                n_url += 1
        logging.info("站点根目录{base_url}两度跳跃包含{url_nums}个网址".format(
            base_url=base_url, url_nums=n_url))

    def get_html_dict(self, url=None, reptile_lib="requests", method="get", selenium_headless=True, time_sleep=None, time_out=None):
        '''
        对url网址发送请求，返回html_dict，requests和selenium两种方式
        :param url: 目标网址
        :param reptile_lib: requests和selenium两种方式；requests为简单请求静态网址html内容，js动态数据无法获取；selenium为模拟人行为请求，可获取全部html数据，但请求时间较长，尽量设置5s以上的time_sleep。
        :param method: requests请求有get/post两种，selenium只支持get
        :param selenium_headless: False则会在电脑自动弹出窗口打开页面；True则不弹出窗口
        :param time_sleep: 等待时间s
        :param time_out: 超时时长s
        :return: html_dict:{}
        '''
        # 爬取url网页html全部内容，保存为字典
        assert reptile_lib in (
            "requests", "selenium"), "reptile_lib请选择requests/selenium方法"
        if time_out is None:
            time_out = self.time_out
        if time_sleep is None:
            time_sleep = self.time_sleep
        if reptile_lib == "requests":
            html_dict = self.get_request_html(
                url=url, method=method, time_sleep=time_sleep, time_out=time_out)
        elif reptile_lib == "selenium":
            html_dict = self.get_selenium_html(
                url=url, method=method, time_sleep=time_sleep, time_out=time_out, headless=selenium_headless)
        return html_dict

    def get_request_html(self, url=None, method="get", time_sleep=1, retry_times=1, header=None, data=None, time_out=None):
        '''
        对url网址发送requests请求，保存html字典
        :param url: 目标网址
        :param method: get/post
        :return: html_dict:{}
        '''
        assert method in ("get", "post"), "method请选择get/post方法"
        # 传入header
        if header:
            self.header = header
        if data:
            self.data = data
        if time_out is None:
            time_out = self.time_out
        if time_sleep is None:
            time_sleep = self.time_sleep
        # 每次发送请求前等待1s
        time.sleep(time_sleep)
        # 发送请求，超时10s重试
        try:
            if method == "get":
                response = requests.get(
                    url, headers=self.header, timeout=time_out)
            elif method == "post":
                response = requests.post(
                    url, headers=self.header, data=self.data, timeout=time_out)
        except Timeout:
            response = None
        # 查看返回结果是否为空，最大重试3次，response保存为html字典
        html_dict = {}
        if response is None:
            html_dict['url'] = url
            html_dict['host_url'] = self.split_host_url(url)
            html_dict['text'] = None
            html_dict['status'] = False
            if retry_times <= self.max_retry_times:
                logging.warning("第{retry_times}次重试……".format(
                    retry_times=retry_times))
                html_dict = self.get_request_html(
                    url=url, method=method, time_sleep=time_sleep, retry_times=retry_times+1)
            else:
                logging.warning("重试{max_retry_times}次，达到最大重试次数！".format(
                    max_retry_times=self.max_retry_times))
        else:
            html_dict['url'] = response.url
            html_dict['host_url'] = self.split_host_url(response.url)
            html_dict['text'] = response.text
            html_dict['status'] = True
            logging.info("请求{url}网址返回成功！".format(url=url))
        return html_dict

    def get_selenium_html(self, url=None, method="get", time_sleep=None, retry_times=1, headless=True, time_out=None):
        '''
        selenium模拟访问网站，保存html字典，需安装并调试chromedriver，版本与电脑chrome需一致，且正确配置路径。mac电脑路径：打开finder,再按command+shift+G进入/usr/local/bin；windows可配置路径。
        :param url: 目标网址
        :param method: 只能取值get
        :param headless: False则会在电脑自动弹出窗口打开页面；True则不弹出窗口
        :return: html_dict : {}
        '''
        assert method == "get", "selenium爬取method只支持get方法"
        if time_out is None:
            time_out = self.time_out
        if time_sleep is None:
            time_sleep = self.time_sleep
        # 创建Chrome浏览器实例，并不在电脑实际展示页面
        options = Options()
        options.headless = headless
        driver = webdriver.Chrome(options=options)
        # 再等待5秒
        time.sleep(time_sleep)
        try:
            # 打开目标网址，等待页面全部元素加载完成
            # url = 'https://market.cloud.tencent.com/products/3027'
            driver.get(url)
            wait = WebDriverWait(driver, time_out)
            wait.until(EC.visibility_of_all_elements_located)
            time.sleep(time_sleep)
            # # 获取整个页面的HTML数据
            page_source = driver.page_source
            current_url = driver.current_url
        except (WebDriverException, TimeoutException) as e:
            page_source = None
            current_url = url
            logging.info("Selenium请求错误:%s" % str(e))
        finally:
            # 关闭浏览器驱动
            driver.quit()

        # 保存html字典
        html_dict = {}
        html_dict['url'] = current_url
        html_dict['host_url'] = self.split_host_url(current_url)
        html_dict['text'] = page_source

        # 请求出错，最大重试3次
        if page_source is None:
            html_dict['status'] = False
            if retry_times <= self.max_retry_times:
                logging.warning("第{retry_times}次重试……".format(
                    retry_times=retry_times))
                html_dict = self.get_selenium_html(
                    url=url, time_sleep=time_sleep, retry_times=retry_times+1, headless=headless)
            else:
                logging.warning("重试{max_retry_times}次，达到最大重试次数！".format(
                    max_retry_times=self.max_retry_times))
        else:
            html_dict['status'] = True
            logging.info("请求{url}网址返回成功！".format(url=url))

        return html_dict

    def get_link_sub_url_list(self, html_dict={}, target_url_prefix=None):
        '''
        提取网页html中出现的相关网址列表，返回结果要以url_prefix为前缀
        :param html_dict: 网页返回的全部文本内容response.text和url
        :param url_prefix: 只返回url_prefix开头的网址，默认为html当前页面的url
        :return: sub_url_list: 网址列表
        '''
        # 从response中提取html_content、base_url
        html_content = html_dict['text']
        url = html_dict['url']
        # 创建BeautifulSoup对象
        soup = BeautifulSoup(html_content, 'html.parser')
        # 提取所有<a>标签的href属性值
        links = soup.find_all('a')
        # 存储提取到的网址
        sub_url_list = [url]
        # 如果没传，以url作为前缀
        if target_url_prefix is None:
            target_url_prefix = url
        # 遍历所有链接
        for link in links:
            href = link.get('href')
            if href:
                # 使用urljoin函数将相对网址转换为绝对网址
                host_url = self.split_host_url(url)
                absolute_url = urljoin(host_url, href)
                # 返回absolute_url以本页url_prefix开头
                if absolute_url.startswith(target_url_prefix):
                    sub_url_list.append(absolute_url)
        # 去重且不改变顺序
        return list(dict.fromkeys(sub_url_list))

    def save_jsonl(self, json_list=[], file_path=None, mode="w"):
        '''
        将json_list保存成jsonl格式文件
        '''
        with open(file_path, mode, encoding="utf-8") as f:
            for line in json_list:
                f.write(json.dumps(line, ensure_ascii=False) + "\n")

    def split_host_url(self, url):
        '''
        从url中提取host域名网址
        '''
        parsed_url = urlsplit(url)
        host_url = parsed_url.scheme + '://' + parsed_url.netloc
        return host_url
