# encoding: utf-8
'''
@author: 温进
@file: java_crawler.py
@time: 2023/10/23 下午5:02
@desc:
'''

import os
import glob
from loguru import logger


class JavaCrawler:
    @staticmethod
    def local_java_file_crawler(path: str):
        '''
        read local java file in path
        > path: path to crawl, must be absolute path like A/B/C
        < dict of java code string
        '''
        java_file_list = glob.glob('{path}{sep}**{sep}*.java'.format(path=path, sep=os.path.sep), recursive=True)
        java_code_dict = {}

        logger.debug('number of file={}'.format(len(java_file_list)))
        # logger.debug(java_file_list)

        for java_file in java_file_list:
            with open(java_file) as f:
                java_code = ''.join(f.readlines())
                java_code_dict[java_file] = java_code
        return java_code_dict