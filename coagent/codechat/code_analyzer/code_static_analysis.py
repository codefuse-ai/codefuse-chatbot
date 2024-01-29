# encoding: utf-8
'''
@author: 温进
@file: code_static_analysis.py
@time: 2023/11/21 下午2:28
@desc:
'''
from coagent.codechat.code_analyzer.language_static_analysis import *

class CodeStaticAnalysis:
    def __init__(self, language):
        self.language = language

    def analyze(self, code_dict):
        '''
        analyze code
        @param code_list:
        @return:
        '''
        if self.language == 'java':
            analyzer = JavaStaticAnalysis()
        else:
            raise ValueError('language should be one of [java]')

        analyze_res = analyzer.analyze(code_dict)
        return analyze_res
