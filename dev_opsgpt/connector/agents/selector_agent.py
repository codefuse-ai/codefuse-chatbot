from pydantic import BaseModel
from typing import List, Union
import re
import json
import traceback
import copy
import random
from loguru import logger

from langchain.prompts.chat import ChatPromptTemplate

from dev_opsgpt.connector.schema import (
    Memory, Task, Env, Role, Message, ActionStatus
)
from dev_opsgpt.llm_models import getChatModel
from dev_opsgpt.connector.configs.prompts import BASE_PROMPT_INPUT, QUERY_CONTEXT_DOC_PROMPT_INPUT, BEGIN_PROMPT_INPUT
from dev_opsgpt.connector.utils import parse_section

from .base_agent import BaseAgent


class SelectorAgent(BaseAgent):
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
            group_agents: List[BaseAgent] = [],
            # prompt_mamnger: PromptManager
            ):
        
        super().__init__(role, task, memory, chat_turn, do_search, do_doc_retrieval, 
                         do_tool_retrieval, temperature, stop, do_filter,do_use_self_memory,
                         focus_agents, focus_message_keys
                         )
        self.group_agents = group_agents

    def arun(self, query: Message, history: Memory = None, background: Memory = None, memory_pool: Memory=None) -> Message:
        '''agent reponse from multi-message'''
        # insert query into memory
        query_c = copy.deepcopy(query)
        query = self.start_action_step(query)
        self_memory = self.memory if self.do_use_self_memory else None
        # create your llm prompt
        prompt = self.create_prompt(query_c, self_memory, history, background, memory_pool=memory_pool)
        content = self.llm.predict(prompt)
        logger.debug(f"{self.role.role_name} prompt: {prompt}")
        logger.debug(f"{self.role.role_name} content: {content}")

        # select agent
        select_message = Message(
            role_name=self.role.role_name,
            role_type="ai", #self.role.role_type,
            role_content=content,
            step_content=content,
            input_query=query_c.input_query,
            tools=query_c.tools,
            parsed_output_list=[query.parsed_output]
            )
        # common parse llm' content to message
        select_message = self.message_utils.parser(select_message)
        if self.do_filter:
            select_message = self.message_utils.filter(select_message)

        output_message = None
        if select_message.parsed_output.get("Role", "") in [agent.role.role_name for agent in self.group_agents]:
            for agent in self.group_agents:
                if agent.role.role_name == select_message.parsed_output.get("Role", ""):
                    break
            for output_message in agent.arun(query, history, background=background, memory_pool=memory_pool):
                pass
            # update self_memory
            self.append_history(query_c)
            self.append_history(output_message)
            logger.info(f"{agent.role.role_name} currenct question: {output_message.input_query}\nllm_step_run: {output_message.role_content}")
            output_message.input_query = output_message.role_content
            output_message.parsed_output_list.append(output_message.parsed_output)
            # 
            output_message = self.end_action_step(output_message)
            # update memory pool
            memory_pool.append(output_message)
        yield output_message or select_message

    def create_prompt(
            self, query: Message, memory: Memory =None, history: Memory = None, background: Memory = None, memory_pool: Memory=None, prompt_mamnger=None) -> str:
        '''
        role\task\tools\docs\memory
        '''
        # 
        doc_infos = self.create_doc_prompt(query)
        code_infos = self.create_codedoc_prompt(query)
        # 
        formatted_tools, tool_names, tools_descs = self.create_tools_prompt(query)
        agent_names, agents = self.create_agent_names()
        task_prompt = self.create_task_prompt(query)
        background_prompt = self.create_background_prompt(background)
        history_prompt = self.create_history_prompt(history)
        selfmemory_prompt = self.create_selfmemory_prompt(memory, control_key="step_content")
        

        DocInfos = ""
        if doc_infos is not None and doc_infos!="" and doc_infos!="不存在知识库辅助信息":
            DocInfos += f"\nDocument Information: {doc_infos}"

        if code_infos is not None and code_infos!="" and code_infos!="不存在代码库辅助信息":
            DocInfos += f"\nCodeBase Infomation: {code_infos}"

        input_query = query.input_query
        logger.debug(f"{self.role.role_name}  input_query: {input_query}")
        prompt = self.role.role_prompt.format(**{"agent_names": agent_names, "agents": agents, "formatted_tools": tools_descs, "tool_names": tool_names})
        #
        memory_pool_select_by_agent_key = self.select_memory_by_agent_key(memory_pool)
        memory_pool_select_by_agent_key_context = '\n\n'.join([f"*{k}*\n{v}" for parsed_output in memory_pool_select_by_agent_key.get_parserd_output_list() for k, v in parsed_output.items() if k not in ['Action Status']])

        input_keys = parse_section(self.role.role_prompt, 'Input Format')
        # 
        prompt += "\n" + BEGIN_PROMPT_INPUT
        for input_key in input_keys:
            if input_key == "Origin Query": 
                prompt += "\n**Origin Query:**\n" + query.origin_query
            elif input_key == "Context":
                context =  "\n".join([f"*{k}*\n{v}" for i in query.parsed_output_list for k,v in i.items() if "Action Status" !=k])
                if history:
                    context = history_prompt + "\n" + context
                if not context:
                    context = "there is no context"

                if self.focus_agents and memory_pool_select_by_agent_key_context:
                    context = memory_pool_select_by_agent_key_context
                prompt += "\n**Context:**\n" + context + "\n" + input_query
            elif input_key == "DocInfos":
                prompt += "\n**DocInfos:**\n" + DocInfos
            elif input_key == "Question":
                prompt += "\n**Question:**\n" + input_query

        while "{{" in prompt or "}}" in prompt:
            prompt = prompt.replace("{{", "{")
            prompt = prompt.replace("}}", "}")

        # logger.debug(f"{self.role.role_name}  prompt: {prompt}")
        return prompt
    
    def create_agent_names(self):
        random.shuffle(self.group_agents)
        agent_names = ", ".join([f'{agent.role.role_name}' for agent in self.group_agents])
        agent_descs = []
        for agent in self.group_agents:
            role_desc = agent.role.role_prompt.split("####")[1]
            while "\n\n" in role_desc:
                role_desc = role_desc.replace("\n\n", "\n")
            role_desc = role_desc.replace("\n", ",")

            agent_descs.append(f'"role name: {agent.role.role_name}\nrole description: {role_desc}"')

        return agent_names, "\n".join(agent_descs)