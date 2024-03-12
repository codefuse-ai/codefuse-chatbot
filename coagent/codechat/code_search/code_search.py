# encoding: utf-8
'''
@author: 温进
@file: code_search.py
@time: 2023/11/21 下午2:35
@desc:
'''
import json
import time
from loguru import logger
from collections import defaultdict

from coagent.db_handler.graph_db_handler.nebula_handler import NebulaHandler
from coagent.db_handler.vector_db_handler.chroma_handler import ChromaHandler

from coagent.codechat.code_search.cypher_generator import CypherGenerator
from coagent.codechat.code_search.tagger import Tagger
from coagent.embeddings.get_embedding import get_embedding
from coagent.llm_models.llm_config import LLMConfig, EmbedConfig


# from configs.model_config import EMBEDDING_DEVICE, EMBEDDING_MODEL
# search_by_tag
VERTEX_SCORE = 10
HISTORY_VERTEX_SCORE = 5
VERTEX_MERGE_RATIO = 0.5

# search_by_description
MAX_DISTANCE = 1000


class CodeSearch:
    def __init__(self, llm_config: LLMConfig, nh: NebulaHandler, ch: ChromaHandler, limit: int = 3,
                 local_graph_file_path: str = ''):
        '''
        init
        @param nh: NebulaHandler
        @param ch: ChromaHandler
        @param limit: limit of result
        '''
        self.llm_config = llm_config

        self.nh = nh

        if not self.nh:
            with open(local_graph_file_path, 'r') as f:
                self.graph = json.load(f)

        self.ch = ch
        self.limit = limit

    def search_by_tag(self, query: str):
        '''
        search_code_res by tag
        @param query: str
        @return:
        '''
        tagger = Tagger()
        tag_list = tagger.generate_tag_query(query)
        logger.info(f'query tag={tag_list}')

        # get all vertices
        vertex_list = self.nh.get_vertices().get('v', [])
        vertex_vid_list = [i.as_node().get_id().as_string() for i in vertex_list]

        # update score
        vertex_score_dict = defaultdict(lambda: 0)
        for vid in vertex_vid_list:
            for tag in tag_list:
                if tag in vid:
                    vertex_score_dict[vid] += VERTEX_SCORE

        # merge depend adj score
        vertex_score_dict_final = {}
        for vertex in vertex_score_dict:
            cypher = f'''MATCH (v1)-[e]-(v2) where id(v1) == "{vertex}" RETURN v2'''
            cypher_res = self.nh.execute_cypher(cypher, self.nh.space_name)
            cypher_res_dict = self.nh.result_to_dict(cypher_res)

            adj_vertex_list = [i.as_node().get_id().as_string() for i in cypher_res_dict.get('v2', [])]

            score = vertex_score_dict.get(vertex, 0)
            for adj_vertex in adj_vertex_list:
                score += vertex_score_dict.get(adj_vertex, 0) * VERTEX_MERGE_RATIO

            if score > 0:
                vertex_score_dict_final[vertex] = score

        # get most prominent package tag
        package_score_dict = defaultdict(lambda: 0)

        for vertex, score in vertex_score_dict_final.items():
            if '#' in vertex:
                # get class name first
                cypher = f'''MATCH (v1:class)-[e:contain]->(v2) WHERE id(v2) == '{vertex}' RETURN id(v1) as id;'''
                cypher_res = self.nh.execute_cypher(cypher=cypher, format_res=True)
                class_vertices = cypher_res.get('id', [])
                if not class_vertices:
                    continue

                vertex = class_vertices[0].as_string()

            # get package name
            cypher = f'''MATCH (v1:package)-[e:contain]->(v2) WHERE id(v2) == '{vertex}' RETURN id(v1) as id;'''
            cypher_res = self.nh.execute_cypher(cypher=cypher, format_res=True)
            pac_vertices = cypher_res.get('id', [])
            if not pac_vertices:
                continue

            package = pac_vertices[0].as_string()
            package_score_dict[package] += score

        # get respective code
        res = []
        package_score_tuple = list(package_score_dict.items())
        package_score_tuple.sort(key=lambda x: x[1], reverse=True)

        ids = [i[0] for i in package_score_tuple]
        logger.info(f'ids={ids}')
        chroma_res = self.ch.get(ids=ids, include=['metadatas'])

        for vertex, score in package_score_tuple:
            index = chroma_res['result']['ids'].index(vertex)
            code_text = chroma_res['result']['metadatas'][index]['code_text']
            res.append({
                "vertex": vertex,
                "code_text": code_text}
            )
            if len(res) >= self.limit:
                break
        # logger.info(f'retrival code={res}')
        return res

    def search_by_tag_by_graph(self, query: str):
        '''
        search code by tag with graph
        @param query:
        @return:
        '''
        tagger = Tagger()
        tag_list = tagger.generate_tag_query(query)
        logger.info(f'query tag={tag_list}')

        # loop to get package node
        package_score_dict = {}
        for code, structure in self.graph.items():
            score = 0
            for class_name in structure['class_name_list']:
                for tag in tag_list:
                    if tag.lower() in class_name.lower():
                        score += 1

            for func_name_list in structure['func_name_dict'].values():
                for func_name in func_name_list:
                    for tag in tag_list:
                        if tag.lower() in func_name.lower():
                            score += 1
            package_score_dict[structure['pac_name']] = score

        # get respective code
        res = []
        package_score_tuple = list(package_score_dict.items())
        package_score_tuple.sort(key=lambda x: x[1], reverse=True)

        ids = [i[0] for i in package_score_tuple]
        logger.info(f'ids={ids}')
        chroma_res = self.ch.get(ids=ids, include=['metadatas'])

        # logger.info(chroma_res)
        for vertex, score in package_score_tuple:
            index = chroma_res['result']['ids'].index(vertex)
            code_text = chroma_res['result']['metadatas'][index]['code_text']
            res.append({
                "vertex": vertex,
                "code_text": code_text}
            )
            if len(res) >= self.limit:
                break
        # logger.info(f'retrival code={res}')
        return res

    def search_by_desciption(self, query: str, engine: str, model_path: str = "text2vec-base-chinese", embedding_device: str = "cpu", embed_config: EmbedConfig=None):
        '''
        search by perform sim search
        @param query:
        @return:
        '''
        query = query.replace(',', '，')
        query_emb = get_embedding(engine=engine, text_list=[query], model_path=model_path, embedding_device= embedding_device, embed_config=embed_config)
        query_emb = query_emb[query]

        query_embeddings = [query_emb]
        query_result = self.ch.query(query_embeddings=query_embeddings, n_results=self.limit,
                                     include=['metadatas', 'distances'])

        res = []
        for idx, distance in enumerate(query_result['result']['distances'][0]):
            if distance < MAX_DISTANCE:
                vertex = query_result['result']['ids'][0][idx]
                code_text = query_result['result']['metadatas'][0][idx]['code_text']
                res.append({
                    "vertex": vertex,
                    "code_text": code_text
                })

        return res

    def search_by_cypher(self, query: str):
        '''
        search by generating cypher
        @param query:
        @param engine:
        @return:
        '''
        cg = CypherGenerator(self.llm_config)
        cypher = cg.get_cypher(query)

        if not cypher:
            return None

        cypher_res = self.nh.execute_cypher(cypher, self.nh.space_name)
        logger.info(f'cypher execution result={cypher_res}')
        if not cypher_res.is_succeeded():
            return {
            'cypher': '',
            'cypher_res': ''
        }

        res = {
            'cypher': cypher,
            'cypher_res': cypher_res
        }

        return res


if __name__ == '__main__':
    # from configs.server_config import NEBULA_HOST, NEBULA_PORT, NEBULA_USER, NEBULA_PASSWORD, NEBULA_STORAGED_PORT
    # from configs.server_config import CHROMA_PERSISTENT_PATH
    from coagent.base_configs.env_config import (
        NEBULA_HOST, NEBULA_PORT, NEBULA_USER, NEBULA_PASSWORD, NEBULA_STORAGED_PORT,
        CHROMA_PERSISTENT_PATH
    )
    codebase_name = 'testing'

    nh = NebulaHandler(host=NEBULA_HOST, port=NEBULA_PORT, username=NEBULA_USER,
                       password=NEBULA_PASSWORD, space_name=codebase_name)
    nh.add_host(NEBULA_HOST, NEBULA_STORAGED_PORT)
    time.sleep(0.5)

    ch = ChromaHandler(path=CHROMA_PERSISTENT_PATH, collection_name=codebase_name)

    cs = CodeSearch(nh, ch)
    # res = cs.search_by_tag(tag_list=['createFineTuneCompletion', 'OpenAiApi'])
    # logger.debug(res)

    # res = cs.search_by_cypher('代码中一共有多少个类', 'openai')
    # logger.debug(res)

    res = cs.search_by_desciption('使用不同的HTTP请求类型（GET、POST、DELETE等）来执行不同的操作', 'openai')
    logger.debug(res)
