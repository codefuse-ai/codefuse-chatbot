# encoding: utf-8
'''
@author: 温进
@file: code_chat.py
@time: 2023/10/24 下午4:04
@desc:
'''

from fastapi import Request, Body
import os, asyncio
from urllib.parse import urlencode
from typing import List
from fastapi.responses import StreamingResponse

from langchain import LLMChain
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.prompts.chat import ChatPromptTemplate

from configs.model_config import (
    llm_model_dict, LLM_MODEL, PROMPT_TEMPLATE,
    VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD, CODE_PROMPT_TEMPLATE)
from dev_opsgpt.chat.utils import History, wrap_done
from dev_opsgpt.utils import BaseResponse
from .base_chat import Chat
from dev_opsgpt.llm_models import getChatModel

from dev_opsgpt.service.kb_api import search_docs, KBServiceFactory
from dev_opsgpt.service.cb_api import search_code, cb_exists_api
from loguru import logger
import json


class CodeChat(Chat):

    def __init__(
            self,
            code_base_name: str = '',
            code_limit: int = 1,
            stream: bool = False,
            request: Request = None,
    ) -> None:
        super().__init__(engine_name=code_base_name, stream=stream)
        self.engine_name = code_base_name
        self.code_limit = code_limit
        self.request = request
        self.history_node_list = []

    def check_service_status(self) -> BaseResponse:
        cb = cb_exists_api(self.engine_name)
        if not cb:
            return BaseResponse(code=404, msg=f"未找到代码库 {self.engine_name}")
        return BaseResponse(code=200, msg=f"找到代码库 {self.engine_name}")

    def _process(self, query: str, history: List[History], model):
        '''process'''
        codes_res = search_code(query=query, cb_name=self.engine_name, code_limit=self.code_limit,
                                history_node_list=self.history_node_list)

        codes = codes_res['related_code']
        nodes = codes_res['related_node']

        # update node names
        node_names = [node[0] for node in nodes]
        self.history_node_list.extend(node_names)
        self.history_node_list = list(set(self.history_node_list))

        context = "\n".join(codes)
        source_nodes = []

        for inum, node_info in enumerate(nodes[0:5]):
            node_name, node_type, node_score = node_info[0], node_info[1], node_info[2]
            source_nodes.append(f'{inum + 1}. 节点名为 {node_name}, 节点类型为 `{node_type}`, 节点得分为 `{node_score}`')

        logger.info('history={}'.format(history))
        logger.info('message={}'.format([i.to_msg_tuple() for i in history] + [("human", CODE_PROMPT_TEMPLATE)]))
        chat_prompt = ChatPromptTemplate.from_messages(
            [i.to_msg_tuple() for i in history] + [("human", CODE_PROMPT_TEMPLATE)]
        )
        logger.info('chat_prompt={}'.format(chat_prompt))
        chain = LLMChain(prompt=chat_prompt, llm=model)
        result = {"answer": "", "codes": source_nodes}
        return chain, context, result

    def chat(
            self,
            query: str = Body(..., description="用户输入", examples=["hello"]),
            history: List[History] = Body(
                [], description="历史对话",
                examples=[[{"role": "user", "content": "我们来玩成语接龙，我先来，生龙活虎"}]]
                ),
            engine_name: str = Body(..., description="知识库名称", examples=["samples"]),
            code_limit: int = Body(1, examples=['1']),
            stream: bool = Body(False, description="流式输出"),
            local_doc_url: bool = Body(False, description="知识文件返回本地路径(true)或URL(false)"),
            request: Request = None,
            **kargs
            ):
        self.engine_name = engine_name if isinstance(engine_name, str) else engine_name.default
        self.code_limit = code_limit
        self.stream = stream if isinstance(stream, bool) else stream.default
        self.local_doc_url = local_doc_url if isinstance(local_doc_url, bool) else local_doc_url.default
        self.request = request
        return self._chat(query, history, **kargs)

    def _chat(self, query: str, history: List[History], **kargs):
        history = [History(**h) if isinstance(h, dict) else h for h in history]

        service_status = self.check_service_status()

        if service_status.code != 200: return service_status

        def chat_iterator(query: str, history: List[History]):
            model = getChatModel()

            result, content = self.create_task(query, history, model, **kargs)
            # logger.info('result={}'.format(result))
            # logger.info('content={}'.format(content))

            if self.stream:
                for token in content["text"]:
                    result["answer"] = token
                    yield json.dumps(result, ensure_ascii=False)
            else:
                for token in content["text"]:
                    result["answer"] += token
                yield json.dumps(result, ensure_ascii=False)

        return StreamingResponse(chat_iterator(query, history),
                                 media_type="text/event-stream")

    def create_task(self, query: str, history: List[History], model):
        '''构建 llm 生成任务'''
        chain, context, result = self._process(query, history, model)
        logger.info('chain={}'.format(chain))
        try:
            content = chain({"context": context, "question": query})
        except Exception as e:
            content = {"text": str(e)}
        return result, content

    def create_atask(self, query, history, model, callback: AsyncIteratorCallbackHandler):
        chain, context, result = self._process(query, history, model)
        task = asyncio.create_task(wrap_done(
            chain.acall({"context": context, "question": query}), callback.done
        ))
        return task, result
