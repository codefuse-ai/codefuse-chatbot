from typing import List, Union, Dict, Tuple
import os
import json
import importlib
import copy
from loguru import logger

from coagent.connector.agents import BaseAgent
from coagent.connector.chains import BaseChain
from coagent.connector.schema import (
    Memory, Task, Message, AgentConfig, ChainConfig, PhaseConfig, LogVerboseEnum,
    CompletePhaseConfig,
    load_chain_configs, load_phase_configs, load_role_configs
)
from coagent.connector.memory_manager import BaseMemoryManager, LocalMemoryManager
from coagent.connector.configs import AGETN_CONFIGS, CHAIN_CONFIGS, PHASE_CONFIGS
from coagent.connector.message_process import MessageUtils
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig
from coagent.base_configs.env_config import JUPYTER_WORK_PATH, KB_ROOT_PATH

# from configs.model_config import JUPYTER_WORK_PATH, KB_ROOT_PATH
# from configs.server_config import SANDBOX_SERVER


role_configs = load_role_configs(AGETN_CONFIGS)
chain_configs = load_chain_configs(CHAIN_CONFIGS)
phase_configs = load_phase_configs(PHASE_CONFIGS)


CUR_DIR = os.path.dirname(os.path.abspath(__file__))


class BasePhase:

    def __init__(
            self,
            phase_name: str,
            phase_config: CompletePhaseConfig = None,
            kb_root_path: str = KB_ROOT_PATH,
            jupyter_work_path: str = JUPYTER_WORK_PATH,
            sandbox_server: dict = {},
            embed_config: EmbedConfig = EmbedConfig(),
            llm_config: LLMConfig = LLMConfig(),
            task: Task = None,
            base_phase_config: Union[dict, str] = PHASE_CONFIGS,
            base_chain_config: Union[dict, str] = CHAIN_CONFIGS,
            base_role_config: Union[dict, str] = AGETN_CONFIGS,
            log_verbose: str = "0"
            ) -> None:
        # 
        self.phase_name = phase_name
        self.do_summary = False
        self.do_search = False
        self.do_code_retrieval = False
        self.do_doc_retrieval = False
        self.do_tool_retrieval = False
        # memory_pool dont have specific order
        # self.memory_pool = Memory(messages=[])
        self.embed_config = embed_config
        self.llm_config = llm_config
        self.sandbox_server = sandbox_server
        self.jupyter_work_path = jupyter_work_path
        self.kb_root_path = kb_root_path
        self.log_verbose = max(os.environ.get("log_verbose", "0"), log_verbose)
        
        self.message_utils = MessageUtils(None, sandbox_server, jupyter_work_path, embed_config, llm_config, kb_root_path, log_verbose)
        self.global_memory = Memory(messages=[])
        self.phase_memory: List[Memory] = []
        # according phase name to init the phase contains
        self.chains: List[BaseChain] = self.init_chains(
            phase_name,
            phase_config,
            task=task, 
            memory=None,
            base_phase_config = base_phase_config,
            base_chain_config = base_chain_config,
            base_role_config = base_role_config,
            )
        self.memory_manager: BaseMemoryManager = LocalMemoryManager(
            unique_name=phase_name, do_init=True, kb_root_path = kb_root_path, embed_config=embed_config, llm_config=llm_config
            )
        self.conv_summary_agent = BaseAgent(
            role=role_configs["conv_summary"].role,
            prompt_config=role_configs["conv_summary"].prompt_config,
            task = None, memory = None,
            llm_config=self.llm_config,
            embed_config=self.embed_config,
            sandbox_server=sandbox_server,
            jupyter_work_path=jupyter_work_path,
            kb_root_path=kb_root_path
            )

    def astep(self, query: Message, history: Memory = None) -> Tuple[Message, Memory]:
        self.memory_manager.append(query)
        summary_message = None
        chain_message = Memory(messages=[])
        local_phase_memory = Memory(messages=[])
        # do_search、do_doc_search、do_code_search
        query = self.message_utils.get_extrainfo_step(query, self.do_search, self.do_doc_retrieval, self.do_code_retrieval, self.do_tool_retrieval)
        query.parsed_output = query.parsed_output if query.parsed_output else {"origin_query": query.input_query}
        query.parsed_output_list = query.parsed_output_list if query.parsed_output_list else [{"origin_query": query.input_query}]
        input_message = copy.deepcopy(query)
        
        self.global_memory.append(input_message)
        local_phase_memory.append(input_message)
        for chain in self.chains:
            # chain can supply background and query to next chain
            for output_message, local_chain_memory in chain.astep(input_message, history, background=chain_message, memory_manager=self.memory_manager):
                # logger.debug(f"local_memory: {local_phase_memory + local_chain_memory}")
                yield output_message, local_phase_memory + local_chain_memory

            output_message = self.message_utils.inherit_extrainfo(input_message, output_message)
            input_message = output_message
            # logger.info(f"{chain.chainConfig.chain_name} phase_step: {output_message.role_content}")
            # 这一段也有问题
            self.global_memory.extend(local_chain_memory)
            local_phase_memory.extend(local_chain_memory)

            # whether to use summary_llm
            if self.do_summary:
                if LogVerboseEnum.ge(LogVerboseEnum.Log1Level, self.log_verbose):
                    logger.info(f"{self.conv_summary_agent.role.role_name} input global memory: {local_phase_memory.to_str_messages(content_key='step_content')}")
                for summary_message in self.conv_summary_agent.astep(query, background=local_phase_memory, memory_manager=self.memory_manager):
                    pass
                # summary_message = Message(**summary_message)
                summary_message.role_name = chain.chainConfig.chain_name
                summary_message = self.conv_summary_agent.message_utils.parser(summary_message)
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

    def pre_print(self, query, history: Memory = None) -> List[str]:
        chain_message = Memory(messages=[])
        for chain in self.chains:
            chain.pre_print(query, history, background=chain_message, memory_manager=self.memory_manager)

    def init_chains(self, phase_name: str, phase_config: CompletePhaseConfig, base_phase_config, base_chain_config,
            base_role_config, task=None, memory=None) -> List[BaseChain]:
        # load config
        role_configs = load_role_configs(base_role_config)
        chain_configs = load_chain_configs(base_chain_config)
        phase_configs = load_phase_configs(base_phase_config)

        chains = []
        self.chain_module = importlib.import_module("coagent.connector.chains")
        self.agent_module = importlib.import_module("coagent.connector.agents")

        phase: PhaseConfig = phase_configs.get(phase_name)
        # set phase 
        self.do_summary = phase.do_summary
        self.do_search = phase.do_search
        self.do_code_retrieval = phase.do_code_retrieval
        self.do_doc_retrieval = phase.do_doc_retrieval
        self.do_tool_retrieval = phase.do_tool_retrieval
        logger.info(f"start to init the phase, the phase_name is {phase_name}, it contains these chains such as {phase.chains}")
        
        for chain_name in phase.chains:
            # logger.debug(f"{chain_configs.keys()}")
            chain_config: ChainConfig = chain_configs[chain_name]
            logger.info(f"start to init the chain, the chain_name is {chain_name}, it contains these agents such as {chain_config.agents}")

            agents = []
            for agent_name in chain_config.agents:
                agent_config: AgentConfig = role_configs[agent_name]
                llm_config = copy.deepcopy(self.llm_config)
                llm_config.stop = agent_config.stop
                baseAgent: BaseAgent = getattr(self.agent_module, agent_config.role.agent_type)
                base_agent = baseAgent(
                    role=agent_config.role, 
                    prompt_config = agent_config.prompt_config,
                    prompt_manager_type=agent_config.prompt_manager_type,
                    task = task,
                    memory = memory,
                    chat_turn=agent_config.chat_turn,
                    focus_agents=agent_config.focus_agents,
                    focus_message_keys=agent_config.focus_message_keys,
                    llm_config=llm_config,
                    embed_config=self.embed_config,
                    sandbox_server=self.sandbox_server,
                    jupyter_work_path=self.jupyter_work_path,
                    kb_root_path=self.kb_root_path,
                    log_verbose=self.log_verbose
                ) 
                if agent_config.role.agent_type == "SelectorAgent":
                    for group_agent_name in agent_config.group_agents:
                        group_agent_config = role_configs[group_agent_name]
                        llm_config = copy.deepcopy(self.llm_config)
                        llm_config.stop = group_agent_config.stop
                        baseAgent: BaseAgent = getattr(self.agent_module, group_agent_config.role.agent_type)
                        group_base_agent = baseAgent(
                            role=group_agent_config.role, 
                            prompt_config = group_agent_config.prompt_config,
                            prompt_manager_type=agent_config.prompt_manager_type,
                            task = task,
                            memory = memory,
                            chat_turn=group_agent_config.chat_turn,
                            focus_agents=group_agent_config.focus_agents,
                            focus_message_keys=group_agent_config.focus_message_keys,
                            llm_config=llm_config,
                            embed_config=self.embed_config,
                            sandbox_server=self.sandbox_server,
                            jupyter_work_path=self.jupyter_work_path,
                            kb_root_path=self.kb_root_path,
                            log_verbose=self.log_verbose
                        ) 
                        base_agent.group_agents.append(group_base_agent)

                agents.append(base_agent)
            
            chain_instance = BaseChain(
                agents, chain_config.chat_turn, 
                do_checker=chain_configs[chain_name].do_checker, 
                jupyter_work_path=self.jupyter_work_path,
                sandbox_server=self.sandbox_server,
                embed_config=self.embed_config,
                llm_config=self.llm_config,
                kb_root_path=self.kb_root_path,
                log_verbose=self.log_verbose
                )
            chains.append(chain_instance)

        return chains

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