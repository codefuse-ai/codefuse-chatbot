# encoding: utf-8
'''
@author: 温进
@file: tagger.py
@time: 2023/10/23 下午5:01
@desc:
'''
import re
from loguru import logger


class Tagger:
    def __init__(self):
        pass

    def generate_tag(self, parse_res_dict: dict):
        '''
        generate tag from parse_res
        '''
        res = {}
        for java_code, parse_res in parse_res_dict.items():
            tag = {}
            tag['pac_name'] = parse_res.get('pac_name')
            tag['class_name'] = set(parse_res.get('class_name_list'))
            tag['func_name'] = set()

            for _, func_name_list in parse_res.get('func_name_dict', {}).items():
                tag['func_name'].update(func_name_list)

            res[java_code] = tag
        return res

    def generate_tag_query(self, query):
        '''
        generate tag from query
        '''
        # simple extract english
        tag_list = re.findall(r'[a-zA-Z\_\.]+', query)
        tag_list = list(set(tag_list))
        return tag_list


if __name__ == '__main__':
    tagger = Tagger()
    logger.debug(tagger.generate_tag_query('com.CheckHolder 有哪些函数'))



