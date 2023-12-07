# encoding: utf-8
'''
@author: 温进
@file: postprocess.py
@time: 2023/11/9 下午4:01
@desc:
'''
import html

def replace_lt_gt(text: str):
    text = html.unescape(text)
    return text