# encoding: utf-8
'''
@author: 温进
@file: tagger.py
@time: 2023/11/24 下午1:32
@desc:
'''
import re
from loguru import logger


class Tagger:
    def __init__(self):
        pass

    def generate_tag_query(self, query):
        '''
        generate tag from query
        '''
        # simple extract english
        tag_list = re.findall(r'[a-zA-Z\_\.]+', query)
        tag_list = list(set(tag_list))
        return tag_list
