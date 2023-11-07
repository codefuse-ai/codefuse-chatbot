from fastapi import Body, Request
from fastapi.responses import StreamingResponse
import asyncio, json
from typing import List, AsyncIterable

from langchain import LLMChain
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.prompts.chat import ChatPromptTemplate

from dev_opsgpt.llm_models import getChatModel
from dev_opsgpt.chat.utils import History, wrap_done
from configs.model_config import (llm_model_dict, LLM_MODEL, VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD)
from dev_opsgpt.utils import BaseResponse
from loguru import logger



class Chat:
    def __init__(
            self,
            engine_name: str = "",
            top_k: int = 1,
            stream: bool = False,
            ) -> None:
        self.engine_name = engine_name
        self.top_k = top_k
        self.stream = stream

    def check_service_status(self, ) -> BaseResponse:
        return BaseResponse(code=200, msg=f"okok")

    def chat(
            self, 
            query: str = Body(..., description="用户输入", examples=["hello"]),
            history: List[History] = Body(
                [], description="历史对话",
                examples=[[{"role": "user", "content": "我们来玩成语接龙，我先来，生龙活虎"}]]
                ),
            engine_name: str = Body(..., description="知识库名称", examples=["samples"]),
            top_k: int = Body(VECTOR_SEARCH_TOP_K, description="匹配向量数"),
            score_threshold: float = Body(SCORE_THRESHOLD, description="知识库匹配相关度阈值，取值范围在0-1之间，SCORE越小，相关度越高，取到1相当于不筛选，建议设置在0.5左右", ge=0, le=1),
            stream: bool = Body(False, description="流式输出"),
            local_doc_url: bool = Body(False, description="知识文件返回本地路径(true)或URL(false)"),
            request: Request = None,
            **kargs
            ):
        self.engine_name = engine_name if isinstance(engine_name, str) else engine_name.default
        self.top_k = top_k if isinstance(top_k, int) else top_k.default
        self.score_threshold = score_threshold if isinstance(score_threshold, float) else score_threshold.default
        self.stream = stream if isinstance(stream, bool) else stream.default
        self.local_doc_url = local_doc_url if isinstance(local_doc_url, bool) else local_doc_url.default
        self.request = request
        return self._chat(query, history, **kargs)
    
    def _chat(self, query: str, history: List[History], **kargs):
        history = [History(**h) if isinstance(h, dict) else h for h in history]

        ## check service dependcy is ok
        service_status = self.check_service_status()

        if service_status.code!=200: return service_status

        def chat_iterator(query: str, history: List[History]):
            model = getChatModel()

            result, content = self.create_task(query, history, model, **kargs)
            logger.info('result={}'.format(result))
            logger.info('content={}'.format(content))

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
        
    def achat(
            self, 
            query: str = Body(..., description="用户输入", examples=["hello"]),
            history: List[History] = Body(
                [], description="历史对话",
                examples=[[{"role": "user", "content": "我们来玩成语接龙，我先来，生龙活虎"}]]
                ),
            engine_name: str = Body(..., description="知识库名称", examples=["samples"]),
            top_k: int = Body(VECTOR_SEARCH_TOP_K, description="匹配向量数"),
            score_threshold: float = Body(SCORE_THRESHOLD, description="知识库匹配相关度阈值，取值范围在0-1之间，SCORE越小，相关度越高，取到1相当于不筛选，建议设置在0.5左右", ge=0, le=1),
            stream: bool = Body(False, description="流式输出"),
            local_doc_url: bool = Body(False, description="知识文件返回本地路径(true)或URL(false)"),
            request: Request = None,
            ):
        self.engine_name = engine_name if isinstance(engine_name, str) else engine_name.default
        self.top_k = top_k if isinstance(top_k, int) else top_k.default
        self.score_threshold = score_threshold if isinstance(score_threshold, float) else score_threshold.default
        self.stream = stream if isinstance(stream, bool) else stream.default
        self.local_doc_url = local_doc_url if isinstance(local_doc_url, bool) else local_doc_url.default
        self.request = request
        return self._achat(query, history)
    
    def _achat(self, query: str, history: List[History]):
        history = [History(**h) if isinstance(h, dict) else h for h in history]
        ## check service dependcy is ok
        service_status = self.check_service_status()
        if service_status.code!=200: return service_status

        async def chat_iterator(query, history):
            callback = AsyncIteratorCallbackHandler()
            model = getChatModel()

            task, result = self.create_atask(query, history, model, callback)
            if self.stream:
                for token in callback["text"]:
                    result["answer"] = token
                    yield json.dumps(result, ensure_ascii=False)
            else:
                for token in callback["text"]:
                    result["answer"] += token
                yield json.dumps(result, ensure_ascii=False)
            await task
        
        return StreamingResponse(chat_iterator(query, history),
                                     media_type="text/event-stream")
        
    def create_task(self, query: str, history: List[History], model, **kargs):
        '''构建 llm 生成任务'''
        chat_prompt = ChatPromptTemplate.from_messages(
            [i.to_msg_tuple() for i in history] + [("human", "{input}")]
        )
        chain = LLMChain(prompt=chat_prompt, llm=model)
        content = chain({"input": query})
        return {"answer": "", "docs": ""}, content

    def create_atask(self, query, history, model, callback: AsyncIteratorCallbackHandler):
        chat_prompt = ChatPromptTemplate.from_messages(
            [i.to_msg_tuple() for i in history] + [("human", "{input}")]
        )
        chain = LLMChain(prompt=chat_prompt, llm=model)
        task = asyncio.create_task(wrap_done(
            chain.acall({"input": query}), callback.done
        ))
        return task, {"answer": "", "docs": ""}