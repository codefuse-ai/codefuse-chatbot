import asyncio
from typing import List

from langchain import LLMChain
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.prompts.chat import ChatPromptTemplate


from dev_opsgpt.chat.utils import History, wrap_done
from .base_chat import Chat
from loguru import logger


class LLMChat(Chat):

    def __init__(
            self,
            engine_name: str = "",
            top_k: int = 1,
            stream: bool = False,
            ) -> None:
        super().__init__(engine_name, top_k, stream)

    def create_task(self, query: str, history: List[History], model):
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