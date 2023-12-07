# encoding: utf-8
'''
@author: 温进
@file: codebase_handler.py
@time: 2023/11/21 下午2:25
@desc:
'''
import time
from loguru import logger

from configs.server_config import NEBULA_HOST, NEBULA_PORT, NEBULA_USER, NEBULA_PASSWORD, NEBULA_STORAGED_PORT
from configs.server_config import CHROMA_PERSISTENT_PATH

from configs.model_config import EMBEDDING_ENGINE

from dev_opsgpt.db_handler.graph_db_handler.nebula_handler import NebulaHandler
from dev_opsgpt.db_handler.vector_db_handler.chroma_handler import ChromaHandler
from dev_opsgpt.codechat.code_crawler.zip_crawler import *
from dev_opsgpt.codechat.code_analyzer.code_analyzer import CodeAnalyzer
from dev_opsgpt.codechat.codebase_handler.code_importer import CodeImporter
from dev_opsgpt.codechat.code_search.code_search import CodeSearch


class CodeBaseHandler:
    def __init__(self, codebase_name: str, code_path: str = '',
                 language: str = 'java', crawl_type: str = 'ZIP'):
        self.codebase_name = codebase_name
        self.code_path = code_path
        self.language = language
        self.crawl_type = crawl_type

        self.nh = NebulaHandler(host=NEBULA_HOST, port=NEBULA_PORT, username=NEBULA_USER,
                                password=NEBULA_PASSWORD, space_name=codebase_name)
        self.nh.add_host(NEBULA_HOST, NEBULA_STORAGED_PORT)
        time.sleep(1)

        self.ch = ChromaHandler(path=CHROMA_PERSISTENT_PATH, collection_name=codebase_name)

    def import_code(self, zip_file='', do_interpret=True):
        '''
        analyze code and save it to codekg and codedb
        @return:
        '''
        # init graph to init tag and edge
        code_importer = CodeImporter(engine=EMBEDDING_ENGINE, codebase_name=self.codebase_name,
                                     nh=self.nh, ch=self.ch)
        code_importer.init_graph()
        time.sleep(5)

        # crawl code
        st0 = time.time()
        logger.info('start crawl')
        code_dict = self.crawl_code(zip_file)
        logger.debug('crawl done, rt={}'.format(time.time() - st0))

        # analyze code
        logger.info('start analyze')
        st1 = time.time()
        code_analyzer = CodeAnalyzer(language=self.language)
        static_analysis_res, interpretation = code_analyzer.analyze(code_dict, do_interpret=do_interpret)
        logger.debug('analyze done, rt={}'.format(time.time() - st1))

        # add info to nebula and chroma
        st2 = time.time()
        code_importer.import_code(static_analysis_res, interpretation, do_interpret=do_interpret)
        logger.debug('update codebase done, rt={}'.format(time.time() - st2))

        # get KG info
        stat = self.nh.get_stat()
        vertices_num, edges_num = stat['vertices'], stat['edges']

        # get chroma info
        file_num = self.ch.count()['result']

        return vertices_num, edges_num, file_num

    def delete_codebase(self, codebase_name: str):
        '''
        delete codebase
        @param codebase_name: name of codebase
        @return:
        '''
        self.nh.drop_space(space_name=codebase_name)
        self.ch.delete_collection(collection_name=codebase_name)

    def crawl_code(self, zip_file=''):
        '''
        @return:
        '''
        if self.language == 'java':
            suffix = 'java'

        logger.info(f'crawl_type={self.crawl_type}')

        code_dict = {}
        if self.crawl_type.lower() == 'zip':
            code_dict = ZipCrawler.crawl(zip_file, output_path=self.code_path, suffix=suffix)
        elif self.crawl_type.lower() == 'dir':
            code_dict = DirCrawler.crawl(self.code_path, suffix)

        return code_dict

    def search_code(self, query: str, search_type: str, limit: int = 3):
        '''
        search code from codebase
        @param limit:
        @param engine:
        @param query: query from user
        @param search_type: ['cypher', 'graph', 'vector']
        @return: 
        '''
        assert search_type in ['cypher', 'tag', 'description']

        code_search = CodeSearch(nh=self.nh, ch=self.ch, limit=limit)

        if search_type == 'cypher':
            search_res = code_search.search_by_cypher(query=query)
        elif search_type == 'tag':
            search_res = code_search.search_by_tag(query=query)
        elif search_type == 'description':
            search_res = code_search.search_by_desciption(query=query, engine=EMBEDDING_ENGINE)

        context, related_vertice = self.format_search_res(search_res, search_type)
        return context, related_vertice

    def format_search_res(self, search_res: str, search_type: str):
        '''
        format search_res
        @param search_res:
        @param search_type:
        @return:
        '''
        CYPHER_QA_PROMPT = '''
        执行的 Cypher 是: {cypher}
        Cypher 的结果是: {result}
        '''

        if search_type == 'cypher':
            context = CYPHER_QA_PROMPT.format(cypher=search_res['cypher'], result=search_res['cypher_res'])
            related_vertice = []
        elif search_type == 'tag':
            context = ''
            related_vertice = []
            for code in search_res:
                context = context + code['code_text'] + '\n'
                related_vertice.append(code['vertex'])
        elif search_type == 'description':
            context = ''
            related_vertice = []
            for code in search_res:
                context = context + code['code_text'] + '\n'
                related_vertice.append(code['vertex'])

        return context, related_vertice


if __name__ == '__main__':
    codebase_name = 'testing'
    code_path = '/Users/bingxu/Desktop/工作/大模型/chatbot/test_code_repo/client'
    cbh = CodeBaseHandler(codebase_name, code_path, crawl_type='dir')

    # query = '使用不同的HTTP请求类型（GET、POST、DELETE等）来执行不同的操作'
    # query = '代码中一共有多少个类'

    query = 'intercept 函数作用是什么'
    search_type = 'graph'
    limit = 2
    res = cbh.search_code(query, search_type, limit)
    logger.debug(res)
