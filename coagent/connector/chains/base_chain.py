from typing import List
from loguru import logger
import copy, os

from coagent.connector.agents import BaseAgent

from coagent.connector.schema import (
    Memory, Role, Message, ActionStatus, ChainConfig,
    load_role_configs
)
from coagent.connector.memory_manager import BaseMemoryManager
from coagent.connector.message_process import MessageUtils
from coagent.llm_models.llm_config import LLMConfig, EmbedConfig
from coagent.connector.configs.agent_config import AGETN_CONFIGS
role_configs = load_role_configs(AGETN_CONFIGS)

# from configs.model_config import JUPYTER_WORK_PATH
# from configs.server_config import SANDBOX_SERVER


class BaseChain:
    def __init__(
            self, 
            # chainConfig: ChainConfig,
            agents: List[BaseAgent],
            chat_turn: int = 1,
            do_checker: bool = False,
            sandbox_server: dict = {},
            jupyter_work_path: str = "",
            kb_root_path: str = "",
            llm_config: LLMConfig = LLMConfig(),
            embed_config: EmbedConfig = None,
            log_verbose: str = "0"
            ) -> None:
        # self.chainConfig = chainConfig
        self.agents: List[BaseAgent] = agents
        self.chat_turn = chat_turn
        self.do_checker = do_checker
        self.sandbox_server = sandbox_server
        self.jupyter_work_path = jupyter_work_path
        self.llm_config = llm_config
        self.log_verbose = max(os.environ.get("log_verbose", "0"), log_verbose)
        self.checker = BaseAgent(role=role_configs["checker"].role,
            prompt_config=role_configs["checker"].prompt_config,
            task = None, memory = None,
            llm_config=llm_config, embed_config=embed_config,
            sandbox_server=sandbox_server, jupyter_work_path=jupyter_work_path,
            kb_root_path=kb_root_path
            )
        self.messageUtils = MessageUtils(None, sandbox_server, self.jupyter_work_path, embed_config, llm_config, kb_root_path, log_verbose)
        # all memory created by agent until instance deleted
        self.global_memory = Memory(messages=[])

    def step(self, query: Message, history: Memory = None, background: Memory = None, memory_manager: BaseMemoryManager = None) -> Message:
        '''execute chain'''
        for output_message, local_memory in self.astep(query, history, background, memory_manager):
            pass
        return output_message, local_memory

    def pre_print(self, query: Message, history: Memory = None, background: Memory = None, memory_manager: BaseMemoryManager = None) -> Message:
        '''execute chain'''
        for agent in self.agents:
            agent.pre_print(query, history, background=background, memory_manager=memory_manager)
    
    def astep(self, query: Message, history: Memory = None, background: Memory = None, memory_manager: BaseMemoryManager = None) -> Message:
        '''execute chain'''
        local_memory = Memory(messages=[])
        input_message = copy.deepcopy(query)
        step_nums = copy.deepcopy(self.chat_turn)
        check_message = None

        self.global_memory.append(input_message)
        # local_memory.append(input_message)
        while step_nums > 0:
            for agent in self.agents:
                for output_message in agent.astep(input_message, history, background=background, memory_manager=memory_manager):
                    # logger.debug(f"local_memory {local_memory + output_message}")
                    yield output_message, local_memory + output_message
                output_message = self.messageUtils.inherit_extrainfo(input_message, output_message)
                # according the output to choose one action for code_content or tool_content
                output_message = self.messageUtils.parser(output_message)
                yield output_message, local_memory + output_message
                # output_message = self.step_router(output_message)
                input_message = output_message
                self.global_memory.append(output_message)

                local_memory.append(output_message)
                # when get finished signal can stop early
                if output_message.action_status == ActionStatus.FINISHED or output_message.action_status == ActionStatus.STOPPED:
                    action_status = False
                    break
            if output_message.action_status == ActionStatus.FINISHED:
                break

            if self.do_checker and self.chat_turn > 1:
                for check_message in self.checker.astep(query, background=local_memory, memory_manager=memory_manager):
                    pass
                check_message = self.messageUtils.parser(check_message)
                check_message = self.messageUtils.inherit_extrainfo(output_message, check_message)
                # logger.debug(f"{self.checker.role.role_name}: {check_message.role_content}")

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
        return "\n".join([": ".join(i) for i in memory.to_tuple_messages(content_key=content_key)])
    
    def get_agents_memory(self, content_key="role_content"):
        return [agent.get_memory(content_key=content_key) for agent in self.agents]
    
    def get_agents_memory_str(self, content_key="role_content"):
        return "************".join([f"{agent.role.role_name}\n" + agent.get_memory_str(content_key=content_key) for agent in self.agents])