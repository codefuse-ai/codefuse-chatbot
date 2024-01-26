# encoding: utf-8
'''
@author: 温进
@file: code_dedup.py
@time: 2023/11/21 下午2:27
@desc:
'''
# encoding: utf-8
'''
@author: 温进
@file: java_dedup.py
@time: 2023/10/23 下午5:02
@desc:
'''


class CodeDedup:
    def __init__(self):
        pass

    def dedup(self, code_dict):
        code_dict = self.exact_dedup(code_dict)
        return code_dict

    def exact_dedup(self, code_dict):
        res = {}
        for fp, code_text in code_dict.items():
            if code_text not in res.values():
                res[fp] = code_text

        return res