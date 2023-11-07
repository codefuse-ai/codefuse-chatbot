import asyncio
from typing import List

from langchain import LLMChain
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.prompts.chat import ChatPromptTemplate
from langchain.agents import AgentType, initialize_agent
import langchain
from langchain.schema import (
            AgentAction
        )


# langchain.debug = True

from dev_opsgpt.tools import (
    TOOL_SETS, TOOL_DICT,
    toLangchainTools, get_tool_schema
    )
from .utils import History, wrap_done
from .base_chat import Chat
from loguru import logger


def get_tool_agent(tools, llm):
    return initialize_agent(
        tools,
        llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        return_intermediate_steps=True
    )


class ToolChat(Chat):

    def __init__(
            self,
            engine_name: str = "",
            top_k: int = 1,
            stream: bool = False,
            ) -> None:
        super().__init__(engine_name, top_k, stream)
        self.tool_prompt = """结合上下文信息，{tools} {input}"""
        self.tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])

    def create_task(self, query: str, history: List[History], model, **kargs):
        '''构建 llm 生成任务'''
        logger.debug("content:{}".format([i.to_msg_tuple() for i in history] + [("human", "{query}")]))
        # chat_prompt = ChatPromptTemplate.from_messages(
        #     [i.to_msg_tuple() for i in history] + [("human", "{query}")]
        # )
        tools = kargs.get("tool_sets", [])
        tools = toLangchainTools([TOOL_DICT[i] for i in tools if i in TOOL_DICT])
        agent = get_tool_agent(tools if tools else self.tools, model)
        content = agent(query)

        logger.debug(f"content: {content}")

        s = ""
        if isinstance(content, str):
            s = content
        else:
            for i in content["intermediate_steps"]:
                for j in i:
                    if isinstance(j, AgentAction):
                        s += j.log + "\n"
                    else:
                        s += "Observation: " + str(j) + "\n"

            s += "final answer:" + content["output"]
        # chain = LLMChain(prompt=chat_prompt, llm=model)
        # content = chain({"tools": tools, "input": query})
        return {"answer": "", "docs": ""}, {"text": s}

    def create_atask(self, query, history, model, callback: AsyncIteratorCallbackHandler):
        chat_prompt = ChatPromptTemplate.from_messages(
            [i.to_msg_tuple() for i in history] + [("human", self.tool_prompt)]
        )
        chain = LLMChain(prompt=chat_prompt, llm=model)
        task = asyncio.create_task(wrap_done(
            chain.acall({"input": query}), callback.done
        ))
        return task, {"answer": "", "docs": ""}