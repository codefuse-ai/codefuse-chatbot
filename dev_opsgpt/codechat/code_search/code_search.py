# encoding: utf-8
'''
@author: 温进
@file: code_search.py
@time: 2023/11/21 下午2:35
@desc:
'''
import time
from loguru import logger
from collections import defaultdict

from dev_opsgpt.db_handler.graph_db_handler.nebula_handler import NebulaHandler
from dev_opsgpt.db_handler.vector_db_handler.chroma_handler import ChromaHandler

from dev_opsgpt.codechat.code_search.cypher_generator import CypherGenerator
from dev_opsgpt.codechat.code_search.tagger import Tagger
from dev_opsgpt.embeddings.get_embedding import get_embedding

# search_by_tag
VERTEX_SCORE = 10
HISTORY_VERTEX_SCORE = 5
VERTEX_MERGE_RATIO = 0.5

# search_by_description
MAX_DISTANCE = 0.5


class CodeSearch:
    def __init__(self, nh: NebulaHandler, ch: ChromaHandler, limit: int = 3):
        '''
        init
        @param nh: NebulaHandler
        @param ch: ChromaHandler
        @param limit: limit of result
        '''
        self.nh = nh
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

        # get all verticex
        vertex_list = self.nh.get_vertices().get('v', [])
        vertex_vid_list = [i.as_node().get_id().as_string() for i in vertex_list]
        logger.debug(vertex_vid_list)

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
        for vertex, score in vertex_score_dict.items():
            package = '#'.join(vertex.split('#')[0:2])
            package_score_dict[package] += score

        # get respective code
        res = []
        package_score_tuple = list(package_score_dict.items())
        package_score_tuple.sort(key=lambda x: x[1], reverse=True)

        ids = [i[0] for i in package_score_tuple]
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
        return res

    def search_by_desciption(self, query: str, engine: str):
        '''
        search by perform sim search
        @param query:
        @return:
        '''
        query = query.replace(',', '，')
        query_emb = get_embedding(engine=engine, text_list=[query])
        query_emb = query_emb[query]

        query_embeddings = [query_emb]
        query_result = self.ch.query(query_embeddings=query_embeddings, n_results=self.limit,
                                     include=['metadatas', 'distances'])
        logger.debug(query_result)

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
        cg = CypherGenerator()
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
    from configs.server_config import NEBULA_HOST, NEBULA_PORT, NEBULA_USER, NEBULA_PASSWORD, NEBULA_STORAGED_PORT
    from configs.server_config import CHROMA_PERSISTENT_PATH

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
