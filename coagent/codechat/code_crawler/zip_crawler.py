# encoding: utf-8
'''
@author: 温进
@file: zip_crawler.py
@time: 2023/11/21 下午2:02
@desc:
'''
from loguru import logger

import zipfile
from coagent.codechat.code_crawler.dir_crawler import DirCrawler


class ZipCrawler:
    @staticmethod
    def crawl(zip_file, output_path, suffix):
        '''
        unzip to output_path
        @param zip_file:
        @param output_path:
        @return:
        '''
        logger.info(f'output_path={output_path}')
        print(f'output_path={output_path}')
        with zipfile.ZipFile(zip_file, 'r') as z:
            z.extractall(output_path)

        code_dict = DirCrawler.crawl(output_path, suffix)
        return code_dict


