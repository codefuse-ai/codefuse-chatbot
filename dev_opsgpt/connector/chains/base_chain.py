from pydantic import BaseModel
from typing import List
import json
import re
from loguru import logger
import traceback
import uuid
import copy

from dev_opsgpt.connector.agents import BaseAgent, CheckAgent
from dev_opsgpt.tools.base_tool import BaseTools, Tool

from dev_opsgpt.connector.schema import (
    Memory, Role, Message, ActionStatus, ChainConfig,
    load_role_configs
)
from dev_opsgpt.connector.message_process import MessageUtils

from dev_opsgpt.connector.configs.agent_config import AGETN_CONFIGS
role_configs = load_role_configs(AGETN_CONFIGS)


class BaseChain:
    def __init__(
            self, 
            chainConfig: ChainConfig,
            agents: List[BaseAgent],
            chat_turn: int = 1,
            do_checker: bool = False,
            # prompt_mamnger: PromptManager
            ) -> None:
        self.chainConfig = chainConfig
        self.agents = agents
        self.chat_turn = chat_turn
        self.do_checker = do_checker
        self.checker = CheckAgent(role=role_configs["checker"].role,
            task = None,
            memory = None,
            do_search = role_configs["checker"].do_search,
            do_doc_retrieval = role_configs["checker"].do_doc_retrieval,
            do_tool_retrieval = role_configs["checker"].do_tool_retrieval,
            do_filter=False, do_use_self_memory=False)
        self.messageUtils = MessageUtils()
        # all memory created by agent until instance deleted
        self.global_memory = Memory(messages=[])

    def step(self, query: Message, history: Memory = None, background: Memory = None, memory_pool: Memory = None) -> Message:
        '''execute chain'''
        for output_message, local_memory in self.astep(query, history, background, memory_pool):
            pass
        return output_message, local_memory
    
    def astep(self, query: Message, history: Memory = None, background: Memory = None, memory_pool: Memory = None) -> Message:
        '''execute chain'''
        local_memory = Memory(messages=[])
        input_message = copy.deepcopy(query)
        step_nums = copy.deepcopy(self.chat_turn)
        check_message = None

        self.global_memory.append(input_message)
        # local_memory.append(input_message)
        while step_nums > 0:
            for agent in self.agents:
                for output_message in agent.arun(input_message, history, background=background, memory_pool=memory_pool):
                    # logger.debug(f"local_memory {local_memory + output_message}")
                    yield output_message, local_memory + output_message
                    
                output_message = self.messageUtils.inherit_extrainfo(input_message, output_message)
                # according the output to choose one action for code_content or tool_content
                # logger.info(f"{agent.role.role_name}  currenct message: {output_message.step_content}\n next llm question: {output_message.input_query}")
                output_message = self.messageUtils.parser(output_message)
                yield output_message, local_memory + output_message
                # output_message = self.step_router(output_message)

                input_message = output_message
                self.global_memory.append(output_message)

                local_memory.append(output_message)
                # when get finished signal can stop early
                if output_message.action_status == ActionStatus.FINISHED or output_message.action_status == ActionStatus.STOPED:
                    action_status = False
                    break
                
            if output_message.action_status == ActionStatus.FINISHED:
                break

            if self.do_checker and self.chat_turn > 1:
                # logger.debug(f"{self.checker.role.role_name} input global memory: {self.global_memory.to_str_messages(content_key='step_content', return_all=False)}")
                for check_message in self.checker.arun(query, background=local_memory, memory_pool=memory_pool):
                    pass
                check_message = self.messageUtils.parser(check_message)
                check_message = self.messageUtils.filter(check_message)
                check_message = self.messageUtils.inherit_extrainfo(output_message, check_message)
                logger.debug(f"{self.checker.role.role_name}: {check_message.role_content}")

                if check_message.action_status == ActionStatus.FINISHED: 
                    self.global_memory.append(check_message)
                    break

            step_nums -= 1
        # 
        output_message = check_message or output_message # 返回chain和checker的结果
        output_message.input_query = query.input_query # chain和chain之间消息通信不改变问题
        yield output_message, local_memory
    
    def get_memory(self, content_key="role_content") -> Memory:
        memory = self.global_memory
        return memory.to_tuple_messages(content_key=content_key)
    
    def get_memory_str(self, content_key="role_content") -> Memory:
        memory = self.global_memory
        # for i in memory.to_tuple_messages(content_key=content_key):
        #     logger.debug(f"{i}")
        return "\n".join([": ".join(i) for i in memory.to_tuple_messages(content_key=content_key)])
    
    def get_agents_memory(self, content_key="role_content"):
        return [agent.get_memory(content_key=content_key) for agent in self.agents]
    
    def get_agents_memory_str(self, content_key="role_content"):
        return "************".join([f"{agent.role.role_name}\n" + agent.get_memory_str(content_key=content_key) for agent in self.agents])