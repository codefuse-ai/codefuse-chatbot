# encoding: utf-8
'''
@author: 温进
@file: dir_crawler.py
@time: 2023/11/22 下午2:54
@desc:
'''
from loguru import logger
import os
import glob


class DirCrawler:
    @staticmethod
    def crawl(path: str, suffix: str):
        '''
        read local java file in path
        > path: path to crawl, must be absolute path like A/B/C
        < dict of java code string
        '''
        java_file_list = glob.glob('{path}{sep}**{sep}*.{suffix}'.format(path=path, sep=os.path.sep, suffix=suffix),
                                   recursive=True)
        java_code_dict = {}

        logger.info(path)
        logger.info('number of file={}'.format(len(java_file_list)))
        logger.info(java_file_list)

        for java_file in java_file_list:
            with open(java_file) as f:
                java_code = ''.join(f.readlines())
                java_code_dict[java_file] = java_code
        return java_code_dict


if __name__ == '__main__':
    path = '/Users/bingxu/Desktop/工作/大模型/chatbot/test_code_repo/middleware-alipay-starters-parent'
    suffix = 'java'
    DirCrawler.crawl(path, suffix)