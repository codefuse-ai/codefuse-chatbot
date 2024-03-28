# encoding: utf-8
'''
@author: 温进
@file: codebase_handler.py
@time: 2023/11/21 下午2:25
@desc:
'''
import os
import time
import json
from typing import List
from loguru import logger

from coagent.base_configs.env_config import (
    NEBULA_HOST, NEBULA_PORT, NEBULA_USER, NEBULA_PASSWORD, NEBULA_STORAGED_PORT,
    CHROMA_PERSISTENT_PATH, CB_ROOT_PATH
)


from coagent.db_handler.graph_db_handler.nebula_handler import NebulaHandler
from coagent.db_handler.vector_db_handler.chroma_handler import ChromaHandler
from coagent.codechat.code_crawler.zip_crawler import *
from coagent.codechat.code_analyzer.code_analyzer import CodeAnalyzer
from coagent.codechat.codebase_handler.code_importer import CodeImporter
from coagent.codechat.code_search.code_search import CodeSearch
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig


class CodeBaseHandler:
    def __init__(
            self, 
            codebase_name: str, 
            code_path: str = '',
            language: str = 'java', 
            crawl_type: str = 'ZIP',
            embed_config: EmbedConfig = EmbedConfig(),
            llm_config: LLMConfig = LLMConfig(),
            use_nh: bool = True,
            local_graph_path: str = CB_ROOT_PATH
        ):
        self.codebase_name = codebase_name
        self.code_path = code_path
        self.language = language
        self.crawl_type = crawl_type
        self.embed_config = embed_config
        self.llm_config = llm_config
        self.local_graph_file_path = local_graph_path + os.sep + f'{self.codebase_name}_graph.json'

        if use_nh:
            try:
                self.nh = NebulaHandler(host=NEBULA_HOST, port=NEBULA_PORT, username=NEBULA_USER,
                                        password=NEBULA_PASSWORD, space_name=codebase_name)
                self.nh.add_host(NEBULA_HOST, NEBULA_STORAGED_PORT)
                time.sleep(1)
            except:
                self.nh = None
                try:
                    with open(self.local_graph_file_path, 'r') as f:
                        self.graph = json.load(f)
                except:
                    pass
        elif local_graph_path:
            self.nh = None
            try:
                with open(self.local_graph_file_path, 'r') as f:
                    self.graph = json.load(f)
            except:
                pass

        self.ch = ChromaHandler(path=CHROMA_PERSISTENT_PATH, collection_name=codebase_name)

    def import_code(self, zip_file='', do_interpret=True):
        '''
        analyze code and save it to codekg and codedb
        @return:
        '''
        # init graph to init tag and edge
        code_importer = CodeImporter(embed_config=self.embed_config, codebase_name=self.codebase_name,
                                     nh=self.nh, ch=self.ch, local_graph_file_path=self.local_graph_file_path)
        if self.nh:
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
        code_analyzer = CodeAnalyzer(language=self.language, llm_config=self.llm_config)
        static_analysis_res, interpretation = code_analyzer.analyze(code_dict, do_interpret=do_interpret)
        logger.debug('analyze done, rt={}'.format(time.time() - st1))

        # add info to nebula and chroma
        st2 = time.time()
        code_importer.import_code(static_analysis_res, interpretation, do_interpret=do_interpret)
        logger.debug('update codebase done, rt={}'.format(time.time() - st2))

        # get KG info
        if self.nh:
            time.sleep(10) # aviod nebula staus didn't complete
            stat = self.nh.get_stat()
            vertices_num, edges_num = stat['vertices'], stat['edges']
        else:
            vertices_num = 0
            edges_num = 0

        # get chroma info
        file_num = self.ch.count()['result']

        return vertices_num, edges_num, file_num

    def delete_codebase(self, codebase_name: str):
        '''
        delete codebase
        @param codebase_name: name of codebase
        @return:
        '''
        if self.nh:
            self.nh.drop_space(space_name=codebase_name)
        elif self.local_graph_file_path and os.path.isfile(self.local_graph_file_path):
            os.remove(self.local_graph_file_path)

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
        if self.nh:
            assert search_type in ['cypher', 'tag', 'description']
        else:
            if search_type == 'tag':
                search_type = 'tag_by_local_graph'
            assert search_type in ['tag_by_local_graph', 'description']

        code_search = CodeSearch(llm_config=self.llm_config, nh=self.nh, ch=self.ch, limit=limit,
                                 local_graph_file_path=self.local_graph_file_path)

        if search_type == 'cypher':
            search_res = code_search.search_by_cypher(query=query)
        elif search_type == 'tag':
            search_res = code_search.search_by_tag(query=query)
        elif search_type == 'description':
            search_res = code_search.search_by_desciption(
                query=query, engine=self.embed_config.embed_engine, model_path=self.embed_config.embed_model_path, 
                embedding_device=self.embed_config.model_device, embed_config=self.embed_config)
        elif search_type == 'tag_by_local_graph':
            search_res = code_search.search_by_tag_by_graph(query=query)


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
        elif search_type == 'tag_by_local_graph':
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

    def search_vertices(self, vertex_type="class") -> List[str]:
        '''
        通过 method/class 来搜索所有的节点
        '''
        vertices = []
        if self.nh:
            vertices = self.nh.get_all_vertices()
            vertices = [str(v.as_node().get_id()) for v in vertices["v"] if vertex_type in v.as_node().tags()]
            # for v in vertices["v"]:
            #     logger.debug(f"{v.as_node().get_id()}, {v.as_node().tags()}")
        else:
            if vertex_type == "class":
                vertices = [str(class_name) for code, structure in self.graph.items() for class_name in structure['class_name_list']]
            elif vertex_type == "method":
                vertices = [
                    str(methods_name)
                    for code, structure in self.graph.items() 
                    for methods_names in structure['func_name_dict'].values() 
                    for methods_name in methods_names
                ]
        # logger.debug(vertices)
        return vertices


if __name__ == '__main__':
    from configs.model_config import KB_ROOT_PATH, JUPYTER_WORK_PATH
    from configs.server_config import SANDBOX_SERVER

    LLM_MODEL = "gpt-3.5-turbo"
    llm_config = LLMConfig(
        model_name=LLM_MODEL, model_device="cpu", api_key=os.environ["OPENAI_API_KEY"],
        api_base_url=os.environ["API_BASE_URL"], temperature=0.3
    )
    src_dir = '/Users/bingxu/Desktop/工作/大模型/chatbot/Codefuse-chatbot-antcode'
    embed_config = EmbedConfig(
        embed_engine="model", embed_model="text2vec-base-chinese",
        embed_model_path=os.path.join(src_dir, "embedding_models/text2vec-base-chinese")
    )

    codebase_name = 'client_local'
    code_path = '/Users/bingxu/Desktop/工作/大模型/chatbot/test_code_repo/client'
    use_nh = False
    local_graph_path = '/Users/bingxu/Desktop/工作/大模型/chatbot/Codefuse-chatbot-antcode/code_base'
    CHROMA_PERSISTENT_PATH = '/Users/bingxu/Desktop/工作/大模型/chatbot/Codefuse-chatbot-antcode/data/chroma_data'

    cbh = CodeBaseHandler(codebase_name, code_path, crawl_type='dir', use_nh=use_nh, local_graph_path=local_graph_path,
                          llm_config=llm_config, embed_config=embed_config)

    # test import code
    # cbh.import_code(do_interpret=True)

    # query = '使用不同的HTTP请求类型（GET、POST、DELETE等）来执行不同的操作'
    # query = '代码中一共有多少个类'
    # query = 'remove 这个函数是用来做什么的'
    query = '有没有函数是从字符串中删除指定字符串的功能'

    search_type = 'description'
    limit = 2
    res = cbh.search_code(query, search_type, limit)
    logger.debug(res)
