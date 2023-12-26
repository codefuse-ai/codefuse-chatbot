from pydantic import BaseModel
from typing import List, Union, Tuple, Any
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
from dev_opsgpt.connector.configs.prompts import EXECUTOR_PROMPT_INPUT, BEGIN_PROMPT_INPUT
from dev_opsgpt.connector.utils import parse_section

from .base_agent import BaseAgent


class ExecutorAgent(BaseAgent):
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
        self.do_all_task = True # run all tasks

    def arun(self, query: Message, history: Memory = None, background: Memory = None, memory_pool: Memory=None) -> Message:
        '''agent reponse from multi-message'''
        # insert query into memory
        task_executor_memory = Memory(messages=[])
        # insert query
        output_message = Message(
                role_name=self.role.role_name,
                role_type="ai", #self.role.role_type,
                role_content=query.input_query,
                step_content="",
                input_query=query.input_query,
                tools=query.tools,
                parsed_output_list=[query.parsed_output],
                customed_kargs=query.customed_kargs
            )
        
        self_memory = self.memory if self.do_use_self_memory else None

        plan_step = int(query.parsed_output.get("PLAN_STEP", 0))
        # 如果存在plan字段且plan字段为str的时候
        if "PLAN" not in query.parsed_output or isinstance(query.parsed_output.get("PLAN", []), str) or plan_step >= len(query.parsed_output.get("PLAN", [])):
            query_c = copy.deepcopy(query)
            query_c = self.start_action_step(query_c)
            query_c.parsed_output = {"Question": query_c.input_query}
            task_executor_memory.append(query_c)
            for output_message, task_executor_memory in self._arun_step(output_message, query_c, self_memory, history, background, memory_pool, task_executor_memory):
                pass
            # task_executor_memory.append(query_c)
            # content = "the execution step of the plan is exceed the planned scope."
            # output_message.parsed_dict = {"Thought": content, "Action Status": "finished", "Action": content}
            # task_executor_memory.append(output_message)

        elif "PLAN" in query.parsed_output:
            logger.debug(f"{query.parsed_output['PLAN']}")
            if self.do_all_task:
                # run all tasks step by step
                for task_content in query.parsed_output["PLAN"][plan_step:]:
                    # create your llm prompt
                    query_c = copy.deepcopy(query)
                    query_c.parsed_output = {"Question": task_content}
                    task_executor_memory.append(query_c)
                    for output_message, task_executor_memory in self._arun_step(output_message, query_c, self_memory, history, background, memory_pool, task_executor_memory):
                        pass
                    yield output_message
            else:
                query_c = copy.deepcopy(query)
                query_c = self.start_action_step(query_c)
                task_content = query_c.parsed_output["PLAN"][plan_step]
                query_c.parsed_output = {"Question": task_content}
                task_executor_memory.append(query_c)
                for output_message, task_executor_memory in self._arun_step(output_message, query_c, self_memory, history, background, memory_pool, task_executor_memory):
                    pass
                output_message.parsed_output.update({"CURRENT_STEP": plan_step})
        # update self_memory
        self.append_history(query)
        self.append_history(output_message)
        # logger.info(f"{self.role.role_name} currenct question: {output_message.input_query}\nllm_executor_run: {output_message.step_content}")
        # logger.info(f"{self.role.role_name} currenct parserd_output_list: {output_message.parserd_output_list}")
        output_message.input_query = output_message.role_content
        # end_action_step
        output_message = self.end_action_step(output_message)
        # update memory pool
        memory_pool.append(output_message)
        yield output_message

    def _arun_step(self, output_message: Message, query: Message, self_memory: Memory, 
            history: Memory, background: Memory, memory_pool: Memory, 
            react_memory: Memory) -> Union[Message, Memory]:
        '''execute the llm predict by created prompt'''
        prompt = self.create_prompt(query, self_memory, history, background, memory_pool=memory_pool, react_memory=react_memory)
        content = self.llm.predict(prompt)
        # logger.debug(f"{self.role.role_name} prompt: {prompt}")
        logger.debug(f"{self.role.role_name} content: {content}")

        output_message.role_content = content
        output_message.step_content += "\n"+output_message.role_content

        output_message = self.message_utils.parser(output_message)
        # according the output to choose one action for code_content or tool_content
        output_message, observation_message = self.message_utils.step_router(output_message)
        # logger.debug(f"{self.role.role_name} content: {content}")
        # update parserd_output_list
        output_message.parsed_output_list.append(output_message.parsed_output)

        react_message = copy.deepcopy(output_message)
        react_memory.append(react_message)
        if observation_message:
            react_memory.append(observation_message)
            output_message.parsed_output_list.append(observation_message.parsed_output)
            logger.debug(f"{observation_message.role_name} content: {observation_message.role_content}")
        yield output_message, react_memory
    
    def create_prompt(
            self, query: Message, memory: Memory =None, history: Memory = None, background: Memory = None, memory_pool: Memory=None, react_memory: Memory = None, prompt_mamnger=None) -> str:
        '''
        role\task\tools\docs\memory
        '''
        # 
        doc_infos = self.create_doc_prompt(query)
        code_infos = self.create_codedoc_prompt(query)
        # 
        formatted_tools, tool_names, _ = self.create_tools_prompt(query)
        task_prompt = self.create_task_prompt(query)
        background_prompt = self.create_background_prompt(background, control_key="step_content")
        history_prompt = self.create_history_prompt(history)
        selfmemory_prompt = self.create_selfmemory_prompt(memory, control_key="step_content")
        
        #
        memory_pool_select_by_agent_key = self.select_memory_by_agent_key(memory_pool)
        memory_pool_select_by_agent_key_context = '\n\n'.join([
            f"*{k}*\n{v}" for parsed_output in memory_pool_select_by_agent_key.get_parserd_output_list() for k, v in parsed_output.items() if k not in ['Action Status']
            ])
        
        DocInfos = ""
        if doc_infos is not None and doc_infos!="" and doc_infos!="不存在知识库辅助信息":
            DocInfos += f"\nDocument Information: {doc_infos}"

        if code_infos is not None and code_infos!="" and code_infos!="不存在代码库辅助信息":
            DocInfos += f"\nCodeBase Infomation: {code_infos}"

        # extra_system_prompt = self.role.role_prompt
        prompt = self.role.role_prompt.format(**{"formatted_tools": formatted_tools, "tool_names": tool_names})
        
        # input_query = react_memory.to_tuple_messages(content_key="role_content")
        # logger.debug(f"get_parserd_dict {react_memory.get_parserd_output()}")
        input_query = "\n".join(["\n".join([f"**{k}:**\n{v}" for k,v in _dict.items()]) for _dict in react_memory.get_parserd_output()])
        # input_query = query.input_query + "\n".join([f"{v}" for k, v in input_query if v])
        last_agent_parsed_output = "\n".join(["\n".join([f"*{k}*\n{v}" for k,v in _dict.items()]) for _dict in query.parsed_output_list])
        react_parsed_output = "\n".join(["\n".join([f"*{k}_context*\n{v}" for k,v in _dict.items()]) for _dict in react_memory.get_parserd_output()[:-1]])
        # 
        prompt += "\n" + BEGIN_PROMPT_INPUT

        input_keys = parse_section(self.role.role_prompt, 'Input Format')
        if input_keys:
            for input_key in input_keys:
                if input_key == "Origin Query": 
                    prompt += "\n**Origin Query:**\n" + query.origin_query
                elif input_key == "DocInfos":
                    prompt += "\n**DocInfos:**\n" + DocInfos
                elif input_key == "Context":
                    if self.focus_agents and memory_pool_select_by_agent_key_context:
                        context = memory_pool_select_by_agent_key_context
                    else:
                        context = last_agent_parsed_output
                    prompt += "\n**Context:**\n" + context + f"\n{react_parsed_output}"
                elif input_key == "Question":
                    prompt += "\n**Question:**\n" + query.parsed_output.get("Question")
        else:
            prompt += "\n" + input_query

        task = query.task or self.task
        # if task_prompt is not None:
        #     prompt += "\n" + task.task_prompt

        # if selfmemory_prompt:
        #     prompt += "\n" + selfmemory_prompt

        # if background_prompt:
        #     prompt += "\n" + background_prompt

        # if history_prompt:
        #     prompt += "\n" + history_prompt

        # prompt = extra_system_prompt.format(**{"query": input_query, "doc_infos": doc_infos, "formatted_tools": formatted_tools, "tool_names": tool_names})
        while "{{" in prompt or "}}" in prompt:
            prompt = prompt.replace("{{", "{")
            prompt = prompt.replace("}}", "}")
        return prompt
    
    def set_task(self, do_all_task):
        '''set task exec type'''
        self.do_all_task = do_all_task