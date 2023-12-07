# encoding: utf-8
'''
@author: 温进
@file: cypher_generator.py
@time: 2023/11/24 上午10:17
@desc:
'''
from loguru import logger

from dev_opsgpt.llm_models.openai_model import getChatModel
from dev_opsgpt.utils.postprocess import replace_lt_gt
from langchain.schema import (
    HumanMessage,
)
from langchain.chains.graph_qa.prompts import NGQL_GENERATION_PROMPT


schema = '''
Node properties: [{'tag': 'package', 'properties': []}, {'tag': 'class', 'properties': []}, {'tag': 'method', 'properties': []}]
Edge properties: [{'edge': 'contain', 'properties': []}, {'edge': 'depend', 'properties': []}]
Relationships: ['(:package)-[:contain]->(:class)', '(:class)-[:contain]->(:method)', '(:package)-[:contain]->(:package)']
'''


class CypherGenerator:
    def __init__(self):
        self.model = getChatModel()

    def get_cypher(self, query: str):
        '''
        get cypher from query
        @param query:
        @return:
        '''
        content = NGQL_GENERATION_PROMPT.format(schema=schema, question=query)

        ans = ''
        message = [HumanMessage(content=content)]
        chat_res = self.model.predict_messages(message)
        ans = chat_res.content

        ans = replace_lt_gt(ans)

        ans = self.post_process(ans)
        return ans

    def post_process(self, cypher_res: str):
        '''
        判断是否为正确的 cypher
        @param cypher_res:
        @return:
        '''
        if '(' not in cypher_res or ')' not in cypher_res:
            return ''

        return cypher_res


if __name__ == '__main__':
    query = '代码中一共有多少个类'
    cg = CypherGenerator(engine='openai')

    cg.get_cypher(query)
