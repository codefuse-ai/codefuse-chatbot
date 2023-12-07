# encoding: utf-8
'''
@author: 温进
@file: java_static_analysis.py
@time: 2023/11/21 下午4:25
@desc:
'''
import os
from loguru import logger
import javalang


class JavaStaticAnalysis:
    def __init__(self):
        pass

    def analyze(self, java_code_dict):
        '''
        parse java code and extract entity
        '''
        tree_dict = self.preparse(java_code_dict)
        res = self.multi_java_code_parse(tree_dict)

        return res

    def preparse(self, java_code_dict):
        '''
        preparse by javalang
        < dict of java_code and tree
        '''
        tree_dict = {}
        for fp, java_code in java_code_dict.items():
            try:
                tree = javalang.parse.parse(java_code)
            except Exception as e:
                continue

            if tree.package is not None:
                tree_dict[fp] = {'code': java_code, 'tree': tree}
        logger.info('success parse {} files'.format(len(tree_dict)))
        return tree_dict

    def single_java_code_parse(self, tree, fp):
        '''
        parse single code file
        > tree: javalang parse result
        < {pac_name: '', class_name_list: [], func_name_dict: {}, import_pac_name_list: []]}
        '''
        import_pac_name_list = []

        # get imports
        import_list = tree.imports

        for import_pac in import_list:
            import_pac_name = import_pac.path
            import_pac_name_list.append(import_pac_name)

        fp_last = fp.split(os.path.sep)[-1]
        pac_name = tree.package.name + '#' + fp_last
        class_name_list = []
        func_name_dict = {}

        for node in tree.types:
            if type(node) in (javalang.tree.ClassDeclaration, javalang.tree.InterfaceDeclaration):
                class_name = pac_name + '#' + node.name
                class_name_list.append(class_name)

                for node_inner in node.body:
                    if type(node_inner) is javalang.tree.MethodDeclaration:
                        func_name = class_name + '#' + node_inner.name

                        # add params name to func_name
                        params_list = node_inner.parameters

                        for params in params_list:
                            params_name = params.type.name
                            func_name = func_name + '-' + params_name

                        if class_name not in func_name_dict:
                            func_name_dict[class_name] = []

                        func_name_dict[class_name].append(func_name)

        res = {
            'pac_name': pac_name,
            'class_name_list': class_name_list,
            'func_name_dict': func_name_dict,
            'import_pac_name_list': import_pac_name_list
        }
        return res

    def multi_java_code_parse(self, tree_dict):
        '''
        parse multiple java code
        > tree_list
        < parse_result_dict
        '''
        res_dict = {}
        for fp, value in tree_dict.items():
            java_code = value['code']
            tree = value['tree']
            try:
                res_dict[java_code] = self.single_java_code_parse(tree, fp)
            except Exception as e:
                logger.debug(java_code)
                raise ImportError

        return res_dict








