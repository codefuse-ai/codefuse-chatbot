from pydantic import BaseModel
from typing import List, Union
import re
import json
import traceback
import copy
from loguru import logger

from langchain.prompts.chat import ChatPromptTemplate

from dev_opsgpt.connector.schema import (
    Memory, Task, Env, Role, Message, ActionStatus
)
from dev_opsgpt.llm_models import getChatModel
from dev_opsgpt.connector.configs.agent_config import REACT_PROMPT_INPUT, CONTEXT_PROMPT_INPUT, QUERY_CONTEXT_PROMPT_INPUT

from .base_agent import BaseAgent


class CheckAgent(BaseAgent):
    def __init__(
            self, 
            role: Role,
            task: Task = None,
            memory: Memory = None,
            chat_turn: int = 1,
            do_search: bool = False,
            do_doc_retrieval: bool = False,
            do_tool_retrieval: bool = False,
            temperature: float = 0.2,
            stop: Union[List[str], str] = None,
            do_filter: bool = True,
            do_use_self_memory: bool = True,
            focus_agents: List[str] = [],
            focus_message_keys: List[str] = [],
            # prompt_mamnger: PromptManager
            ):
        
        super().__init__(role, task, memory, chat_turn, do_search, do_doc_retrieval, 
                         do_tool_retrieval, temperature, stop, do_filter,do_use_self_memory,
                         focus_agents, focus_message_keys
                         )

    def create_prompt(
            self, query: Message, memory: Memory =None, history: Memory = None, background: Memory = None, memory_pool: Memory=None, prompt_mamnger=None) -> str:
        '''
        role\task\tools\docs\memory
        '''
        # 
        doc_infos = self.create_doc_prompt(query)
        code_infos = self.create_codedoc_prompt(query)
        # 
        formatted_tools, tool_names = self.create_tools_prompt(query)
        task_prompt = self.create_task_prompt(query)
        background_prompt = self.create_background_prompt(background)
        history_prompt = self.create_history_prompt(history)
        selfmemory_prompt = self.create_selfmemory_prompt(memory, control_key="step_content")
        
        # react 流程是自身迭代过程，另外二次触发的是需要作为历史对话信息
        # input_query = react_memory.to_tuple_messages(content_key="step_content")
        input_query = query.input_query

        # logger.debug(f"{self.role.role_name}  extra_system_prompt: {self.role.role_prompt}")
        # logger.debug(f"{self.role.role_name}  input_query: {input_query}")
        # logger.debug(f"{self.role.role_name}  doc_infos: {doc_infos}")
        # logger.debug(f"{self.role.role_name}  tool_names: {tool_names}")
        # prompt += "\n" + CHECK_PROMPT_INPUT.format(**{"query": input_query})
        # prompt.format(**{"query": input_query})
        
        # extra_system_prompt = self.role.role_prompt
        prompt = self.role.role_prompt.format(**{"query": input_query, "formatted_tools": formatted_tools, "tool_names": tool_names})

        if "**Context:**" in self.role.role_prompt:
            # logger.debug(f"parsed_output_list: {query.parsed_output_list}")
            # input_query =  "'''" + "\n".join([f"*{k}*\n{v}" for i in background.get_parserd_output_list() for k,v in i.items() if "Action Status" !=k]) + "'''"
            context =  "\n".join([f"*{k}*\n{v}" for i in background.get_parserd_output_list() for k,v in i.items() if "Action Status" !=k])
            # logger.debug(context)
            # logger.debug(f"parsed_output_list: {t}")
            prompt += "\n" + QUERY_CONTEXT_PROMPT_INPUT.format(**{"query": query.origin_query, "context": context})
        else:
            prompt += "\n" + REACT_PROMPT_INPUT.format(**{"query": input_query})


        task = query.task or self.task
        if task_prompt is not None:
            prompt += "\n" + task.task_prompt

        # if doc_infos is not None and doc_infos!="" and doc_infos!="不存在知识库辅助信息":
        #     prompt += f"\n知识库信息: {doc_infos}"

        # if code_infos is not None and code_infos!="" and code_infos!="不存在代码库辅助信息":
        #     prompt += f"\n代码库信息: {code_infos}"

        # if background_prompt:
        #     prompt += "\n" + background_prompt

        # if history_prompt:
        #     prompt += "\n" + history_prompt

        # if selfmemory_prompt:
        #     prompt += "\n" + selfmemory_prompt

        # prompt = extra_system_prompt.format(**{"query": input_query, "doc_infos": doc_infos, "formatted_tools": formatted_tools, "tool_names": tool_names})
        while "{{" in prompt or "}}" in prompt:
            prompt = prompt.replace("{{", "{")
            prompt = prompt.replace("}}", "}")

        # logger.debug(f"{self.role.role_name}  prompt: {prompt}")
        return prompt
    
