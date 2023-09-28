from fastapi import Request
import os, asyncio
from urllib.parse import urlencode
from typing import List

from langchain import LLMChain
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.prompts.chat import ChatPromptTemplate


from configs.model_config import (
    llm_model_dict, LLM_MODEL, PROMPT_TEMPLATE, 
    VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD)
from dev_opsgpt.chat.utils import History, wrap_done
from dev_opsgpt.utils import BaseResponse
from .base_chat import Chat
from dev_opsgpt.service.kb_api import search_docs, KBServiceFactory
from loguru import logger


class KnowledgeChat(Chat):

    def __init__(
            self,
            engine_name: str = "",
            top_k: int = VECTOR_SEARCH_TOP_K,
            stream: bool = False,
            score_thresold: float = SCORE_THRESHOLD,
            local_doc_url: bool = False,
            request: Request = None,
            ) -> None:
        super().__init__(engine_name, top_k, stream)
        self.score_thresold = score_thresold
        self.local_doc_url = local_doc_url
        self.request = request

    def check_service_status(self) -> BaseResponse:
        kb = KBServiceFactory.get_service_by_name(self.engine_name)
        if kb is None:
            return BaseResponse(code=404, msg=f"未找到知识库 {self.engine_name}")
        return BaseResponse(code=200, msg=f"找到知识库 {self.engine_name}")
    
    def _process(self, query: str, history: List[History], model):
        '''process'''
        docs = search_docs(query, self.engine_name, self.top_k, self.score_threshold)
        context = "\n".join([doc.page_content for doc in docs])
        source_documents = []
        for inum, doc in enumerate(docs):
            filename = os.path.split(doc.metadata["source"])[-1]
            if self.local_doc_url:
                url = "file://" + doc.metadata["source"]
            else:
                parameters = urlencode({"knowledge_base_name": self.engine_name, "file_name":filename})
                url = f"{self.request.base_url}knowledge_base/download_doc?" + parameters
            text = f"""出处 [{inum + 1}] [{filename}]({url}) \n\n{doc.page_content}\n\n"""
            source_documents.append(text)
        chat_prompt = ChatPromptTemplate.from_messages(
            [i.to_msg_tuple() for i in history] + [("human", PROMPT_TEMPLATE)]
        )
        chain = LLMChain(prompt=chat_prompt, llm=model)
        result = {"answer": "", "docs": source_documents}
        return chain, context, result

    def create_task(self, query: str, history: List[History], model):
        '''构建 llm 生成任务'''
        logger.debug(f"query: {query}, history: {history}")
        chain, context, result = self._process(query, history, model)
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
