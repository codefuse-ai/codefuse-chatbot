# encoding: utf-8
'''
@author: 温进
@file: codebase_handler.py
@time: 2023/10/23 下午5:05
@desc:
'''

from loguru import logger
import time
import os

from dev_opsgpt.codebase_handler.parser.java_paraser.java_crawler import JavaCrawler
from dev_opsgpt.codebase_handler.parser.java_paraser.java_preprocess import JavaPreprocessor
from dev_opsgpt.codebase_handler.parser.java_paraser.java_dedup import JavaDedup
from dev_opsgpt.codebase_handler.parser.java_paraser.java_parser import JavaParser
from dev_opsgpt.codebase_handler.tagger.tagger import Tagger
from dev_opsgpt.codebase_handler.tagger.tuple_generation import node_edge_update

from dev_opsgpt.codebase_handler.networkx_handler.networkx_handler import NetworkxHandler
from dev_opsgpt.codebase_handler.codedb_handler.local_codedb_handler import LocalCodeDBHandler


class CodeBaseHandler():
    def __init__(self, code_name: str, code_path: str = '', cb_root_path: str = '', history_node_list: list = []):
        self.nh = None
        self.lcdh = None
        self.code_name = code_name
        self.code_path = code_path

        self.codebase_path = cb_root_path + os.sep + code_name
        self.graph_path = self.codebase_path + os.sep + 'graph.pk'
        self.codedb_path = self.codebase_path + os.sep + 'codedb.pk'

        self.tagger = Tagger()
        self.history_node_list = history_node_list

    def import_code(self, do_save: bool=False, do_load: bool=False) -> bool:
        '''
        import code to codeBase
        @param code_path:
        @param do_save:
        @param do_load:
        @return: True as success; False as failure
        '''
        if do_load:
            logger.info('start load from codebase_path')
            load_graph_path = self.graph_path
            load_codedb_path = self.codedb_path

            st = time.time()
            self.nh = NetworkxHandler(graph_path=load_graph_path)
            logger.info('generate graph success, rt={}'.format(time.time() - st))

            st = time.time()
            self.lcdh = LocalCodeDBHandler(db_path=load_codedb_path)
            logger.info('generate codedb success, rt={}'.format(time.time() - st))
        else:
            logger.info('start load from code_path')
            st = time.time()
            java_code_dict = JavaCrawler.local_java_file_crawler(self.code_path)
            logger.info('crawl success, rt={}'.format(time.time() - st))

            jp = JavaPreprocessor()
            java_code_dict = jp.preprocess(java_code_dict)

            jd = JavaDedup()
            java_code_dict = jd.dedup(java_code_dict)

            st = time.time()
            j_parser = JavaParser()
            parse_res = j_parser.parse(java_code_dict)
            logger.info('parse success, rt={}'.format(time.time() - st))

            st = time.time()
            tagged_code = self.tagger.generate_tag(parse_res)
            node_list, edge_list = node_edge_update(parse_res.values())
            logger.info('get node and edge success, rt={}'.format(time.time() - st))

            st = time.time()
            self.nh = NetworkxHandler(node_list=node_list, edge_list=edge_list)
            logger.info('generate graph success, rt={}'.format(time.time() - st))

            st = time.time()
            self.lcdh = LocalCodeDBHandler(tagged_code)
            logger.info('CodeDB load success, rt={}'.format(time.time() - st))

            if do_save:
                save_graph_path = self.graph_path
                save_codedb_path = self.codedb_path
                self.nh.save_graph(save_graph_path)
                self.lcdh.save_db(save_codedb_path)

    def search_code(self, query: str, code_limit: int, history_node_list: list = []):
        '''
        search code related to query
        @param self:
        @param query:
        @return:
        '''
        # get query tag
        query_tag_list = self.tagger.generate_tag_query(query)

        related_node_score_list = self.nh.search_node_with_score(query_tag_list=query_tag_list,
                                                                 history_node_list=history_node_list)

        score_dict = {
            i[0]: i[1]
            for i in related_node_score_list
        }
        related_node = [i[0] for i in related_node_score_list]
        related_score = [i[1] for i in related_node_score_list]

        related_code, code_related_node = self.lcdh.search_by_multi_tag(related_node, lim=code_limit)

        related_node = [
            (node, self.nh.get_node_type(node), score_dict[node])
            for node in code_related_node
        ]

        related_node.sort(key=lambda x: x[2], reverse=True)

        logger.info('related_node={}'.format(related_node))
        logger.info('related_code={}'.format(related_code))
        logger.info('num of code={}'.format(len(related_code)))
        return related_code, related_node

    def refresh_history(self):
        self.history_node_list = []










