# encoding: utf-8
'''
@author: 温进
@file: postprocess.py
@time: 2023/11/9 下午4:01
@desc:
'''

def replace_lt_gt(text: str):
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    return text