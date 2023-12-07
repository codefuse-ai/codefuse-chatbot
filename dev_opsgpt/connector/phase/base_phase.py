from typing import List, Union, Dict, Tuple
import os
import json
import importlib
import copy
from loguru import logger

from dev_opsgpt.connector.agents import BaseAgent
from dev_opsgpt.connector.chains import BaseChain
from dev_opsgpt.tools.base_tool import BaseTools, Tool

from dev_opsgpt.connector.schema import (
    Memory, Task, Env, Role, Message, Doc, Docs, AgentConfig, ChainConfig, PhaseConfig, CodeDoc,
    load_chain_configs, load_phase_configs, load_role_configs
)
from dev_opsgpt.connector.configs import AGETN_CONFIGS, CHAIN_CONFIGS, PHASE_CONFIGS
from dev_opsgpt.connector.message_process import MessageUtils

role_configs = load_role_configs(AGETN_CONFIGS)
chain_configs = load_chain_configs(CHAIN_CONFIGS)
phase_configs = load_phase_configs(PHASE_CONFIGS)


CUR_DIR = os.path.dirname(os.path.abspath(__file__))


class BasePhase:

    def __init__(
            self,
            phase_name: str,
            task: Task = None,
            do_summary: bool = False,
            do_search: bool = False,
            do_doc_retrieval: bool = False,
            do_code_retrieval: bool = False,
            do_tool_retrieval: bool = False,
            phase_config: Union[dict, str] = PHASE_CONFIGS,
            chain_config: Union[dict, str] = CHAIN_CONFIGS,
            role_config: Union[dict, str] = AGETN_CONFIGS,
            ) -> None:
        self.conv_summary_agent = BaseAgent(role=role_configs["conv_summary"].role,
            task = None,
            memory = None,
            do_search = role_configs["conv_summary"].do_search,
            do_doc_retrieval = role_configs["conv_summary"].do_doc_retrieval,
            do_tool_retrieval = role_configs["conv_summary"].do_tool_retrieval,
            do_filter=False, do_use_self_memory=False)
        
        self.chains: List[BaseChain] = self.init_chains(
            phase_name,
            task=task, 
            memory=None,
            phase_config = phase_config,
            chain_config = chain_config,
            role_config = role_config,
            )
        
        self.message_utils = MessageUtils()
        self.phase_name = phase_name
        self.do_summary = do_summary
        self.do_search = do_search
        self.do_code_retrieval = do_code_retrieval
        self.do_doc_retrieval = do_doc_retrieval
        self.do_tool_retrieval = do_tool_retrieval
        # 
        self.global_memory = Memory(messages=[])
        # self.chain_message = Memory([])
        self.phase_memory: List[Memory] = []
        # memory_pool dont have specific order
        self.memory_pool = Memory(messages=[])

    def astep(self, query: Message, history: Memory = None) -> Tuple[Message, Memory]:
        summary_message = None
        chain_message = Memory(messages=[])
        local_phase_memory = Memory(messages=[])
        # do_search、do_doc_search、do_code_search
        query = self.message_utils.get_extrainfo_step(query, self.do_search, self.do_doc_retrieval, self.do_code_retrieval, self.do_tool_retrieval)
        input_message = copy.deepcopy(query)
        
        self.global_memory.append(input_message)
        local_phase_memory.append(input_message)
        for chain in self.chains:
            # chain can supply background and query to next chain
            for output_message, local_chain_memory in chain.astep(input_message, history, background=chain_message, memory_pool=self.memory_pool):
                # logger.debug(f"local_memory: {local_memory + chain_memory}")
                yield output_message, local_phase_memory + local_chain_memory

            output_message = self.message_utils.inherit_extrainfo(input_message, output_message)
            input_message = output_message
            logger.info(f"{chain.chainConfig.chain_name} phase_step: {output_message.role_content}")
            # 这一段也有问题
            self.global_memory.extend(local_chain_memory)
            local_phase_memory.extend(local_chain_memory)

            # whether to use summary_llm
            if self.do_summary:
                logger.info(f"{self.conv_summary_agent.role.role_name} input global memory: {local_phase_memory.to_str_messages(content_key='step_content')}")
                for summary_message in self.conv_summary_agent.arun(query, background=local_phase_memory, memory_pool=self.memory_pool):
                    pass
                # summary_message = Message(**summary_message)
                summary_message.role_name = chain.chainConfig.chain_name
                summary_message = self.conv_summary_agent.message_utils.parser(summary_message)
                summary_message = self.conv_summary_agent.message_utils.filter(summary_message)
                summary_message = self.message_utils.inherit_extrainfo(output_message, summary_message)
                chain_message.append(summary_message)

                message = summary_message or output_message
                yield message, local_phase_memory

        # 由于不会存在多轮chain执行，所以直接保留memory即可
        for chain in self.chains:
            self.phase_memory.append(chain.global_memory)
        # TODO：local_memory缺少添加summary的过程
        message = summary_message or output_message
        message.role_name = self.phase_name
        yield message, local_phase_memory

    def step(self, query: Message, history: Memory = None) -> Tuple[Message, Memory]:
        for message, local_phase_memory in self.astep(query, history=history):
            pass
        return message, local_phase_memory

    def init_chains(self, phase_name,  phase_config, chain_config,
            role_config, task=None, memory=None) -> List[BaseChain]:
        # load config
        role_configs = load_role_configs(role_config)
        chain_configs = load_chain_configs(chain_config)
        phase_configs = load_phase_configs(phase_config)

        chains = []
        self.chain_module = importlib.import_module("dev_opsgpt.connector.chains")
        self.agent_module = importlib.import_module("dev_opsgpt.connector.agents")

        phase = phase_configs.get(phase_name)
        logger.info(f"start to init the phase, the phase_name is {phase_name}, it contains these chains such as {phase.chains}")
        
        for chain_name in phase.chains:
            # logger.debug(f"{chain_configs.keys()}")
            chain_config = chain_configs[chain_name]
            logger.info(f"start to init the chain, the chain_name is {chain_name}, it contains these agents such as {chain_config.agents}")

            agents = []
            for agent_name in chain_config.agents:
                agent_config = role_configs[agent_name]
                baseAgent: BaseAgent = getattr(self.agent_module, agent_config.role.agent_type)
                base_agent = baseAgent(
                    agent_config.role, 
                    task = task,
                    memory = memory,
                    chat_turn=agent_config.chat_turn,
                    do_search = agent_config.do_search,
                    do_doc_retrieval = agent_config.do_doc_retrieval,
                    do_tool_retrieval = agent_config.do_tool_retrieval,
                    stop= agent_config.stop,
                    focus_agents=agent_config.focus_agents,
                    focus_message_keys=agent_config.focus_message_keys,
                ) 
                agents.append(base_agent)
            
            chain_instance = BaseChain(
                chain_config, agents, chain_config.chat_turn, 
                do_checker=chain_configs[chain_name].do_checker, 
                do_code_exec=False,)
            chains.append(chain_instance)

        return chains

    # def get_extrainfo_step(self, input_message):
    #     if self.do_doc_retrieval:
    #         input_message = self.get_doc_retrieval(input_message)

    #     # logger.debug(F"self.do_code_retrieval: {self.do_code_retrieval}")
    #     if self.do_code_retrieval:
    #         input_message = self.get_code_retrieval(input_message)

    #     if self.do_search:
    #         input_message = self.get_search_retrieval(input_message)

    #     return input_message

    # def inherit_extrainfo(self, input_message: Message, output_message: Message):
    #     output_message.db_docs = input_message.db_docs
    #     output_message.search_docs = input_message.search_docs
    #     output_message.code_docs = input_message.code_docs
    #     output_message.figures.update(input_message.figures)
    #     output_message.origin_query = input_message.origin_query
    #     return output_message
        
    # def get_search_retrieval(self, message: Message,) -> Message:
    #     SEARCH_ENGINES = {"duckduckgo": DDGSTool}
    #     search_docs = []
    #     for idx, doc in enumerate(SEARCH_ENGINES["duckduckgo"].run(message.role_content, 3)):
    #         doc.update({"index": idx})
    #         search_docs.append(Doc(**doc))
    #     message.search_docs = search_docs
    #     return message
    
    # def get_doc_retrieval(self, message: Message) -> Message:
    #     query = message.role_content
    #     knowledge_basename = message.doc_engine_name
    #     top_k = message.top_k
    #     score_threshold = message.score_threshold
    #     if knowledge_basename:
    #         docs = DocRetrieval.run(query, knowledge_basename, top_k, score_threshold)
    #         message.db_docs = [Doc(**doc) for doc in docs]
    #     return message
    
    # def get_code_retrieval(self, message: Message) -> Message:
    #     # DocRetrieval.run("langchain是什么", "DSADSAD")
    #     query = message.input_query
    #     code_engine_name = message.code_engine_name
    #     history_node_list = message.history_node_list
    #     code_docs = CodeRetrieval.run(code_engine_name, query, code_limit=message.top_k, history_node_list=history_node_list)
    #     message.code_docs = [CodeDoc(**doc) for doc in code_docs]
    #     return message

    # def get_tool_retrieval(self, message: Message) -> Message:
    #     return message
    
    def update(self) -> Memory:
        pass

    def get_memory(self, ) -> Memory:
        return Memory.from_memory_list(
            [chain.get_memory() for chain in self.chains]
            )
    
    def get_memory_str(self, do_all_memory=True, content_key="role_content") -> str:
        memory = self.global_memory if do_all_memory else self.phase_memory
        return "\n".join([": ".join(i) for i in memory.to_tuple_messages(content_key=content_key)])
    
    def get_chains_memory(self, content_key="role_content") -> List[Tuple]:
        return [memory.to_tuple_messages(content_key=content_key) for memory in self.phase_memory]
    
    def get_chains_memory_str(self, content_key="role_content") -> str:
        return "************".join([f"{chain.chainConfig.chain_name}\n" + chain.get_memory_str(content_key=content_key) for chain in self.chains])