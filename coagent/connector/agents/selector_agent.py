from typing import List, Union
import copy
import random
from loguru import logger

from langchain.schema import BaseRetriever

from coagent.connector.schema import (
    Memory, Task, Role, Message, PromptField, LogVerboseEnum
)
from coagent.connector.memory_manager import BaseMemoryManager
from coagent.connector.memory_manager import LocalMemoryManager
from coagent.llm_models import LLMConfig, EmbedConfig
from coagent.base_configs.env_config import JUPYTER_WORK_PATH, KB_ROOT_PATH
from .base_agent import BaseAgent


class SelectorAgent(BaseAgent):

    def __init__(
            self, 
            role: Role,
            prompt_config: List[PromptField] = None,
            prompt_manager_type: str = "PromptManager",
            task: Task = None,
            memory: Memory = None,
            chat_turn: int = 1,
            focus_agents: List[str] = [],
            focus_message_keys: List[str] = [],
            group_agents: List[BaseAgent] = [],
            #
            llm_config: LLMConfig = None,
            embed_config: EmbedConfig = None,
            sandbox_server: dict = {},
            jupyter_work_path: str = JUPYTER_WORK_PATH,
            kb_root_path: str = KB_ROOT_PATH,
            doc_retrieval: Union[BaseRetriever] = None,
            code_retrieval = None,
            search_retrieval = None,
            log_verbose: str = "0"
            ):
        
        super().__init__(role, prompt_config, prompt_manager_type, task, memory, chat_turn, 
                         focus_agents, focus_message_keys, llm_config, embed_config, sandbox_server,
                         jupyter_work_path, kb_root_path, doc_retrieval, code_retrieval, search_retrieval, log_verbose
                         )
        self.group_agents = group_agents

    def astep(self, query: Message, history: Memory = None, background: Memory = None, memory_manager: BaseMemoryManager=None) -> Message:
        '''agent reponse from multi-message'''
        # insert query into memory
        query_c = copy.deepcopy(query)
        query_c = self.start_action_step(query_c)
        # create your llm prompt
        if memory_manager is None:
            memory_manager = LocalMemoryManager(
                unique_name=self.role.role_name, 
                do_init=True, 
                kb_root_path = self.kb_root_path, 
                embed_config=self.embed_config, 
                llm_config=self.embed_config
            )
            memory_manager.append(query)
        memory_pool = memory_manager.get_memory_pool(query_c.user_name)

        prompt = self.prompt_manager.generate_full_prompt(
                previous_agent_message=query_c, agent_long_term_memory=self.memory, ui_history=history, chain_summary_messages=background, react_memory=None, 
                memory_pool=memory_pool, agents=self.group_agents)
        content = self.llm.predict(prompt)

        if LogVerboseEnum.ge(LogVerboseEnum.Log2Level, self.log_verbose):
            logger.debug(f"{self.role.role_name} prompt: {prompt}")

        if LogVerboseEnum.ge(LogVerboseEnum.Log1Level, self.log_verbose):
            logger.info(f"{self.role.role_name} content: {content}")

        # select agent
        select_message = Message(
            role_name=self.role.role_name,
            role_type="assistant", #self.role.role_type,
            role_content=content,
            step_content=content,
            input_query=query_c.input_query,
            tools=query_c.tools,
            # parsed_output_list=[query_c.parsed_output]
            customed_kargs=query.customed_kargs
            )
        # common parse llm' content to message
        select_message = self.message_utils.parser(select_message)
        select_message.parsed_output_list.append(select_message.parsed_output)

        output_message = None
        if select_message.parsed_output.get("Role", "") in [agent.role.role_name for agent in self.group_agents]:
            for agent in self.group_agents:
                if agent.role.role_name == select_message.parsed_output.get("Role", ""):
                    break
            
            # 把除了role以外的信息传给下一个agent
            query_c.parsed_output.update({k:v for k,v in select_message.parsed_output.items() if k!="Role"})
            for output_message in agent.astep(query_c, history, background=background, memory_manager=memory_manager):
                yield output_message or select_message
            # update self_memory
            self.append_history(query_c)
            self.append_history(output_message)
            output_message.input_query = output_message.role_content
            # output_message.parsed_output_list.append(output_message.parsed_output)
            # 
            output_message = self.end_action_step(output_message)
            # update memory pool
            memory_manager.append(output_message)

            select_message.parsed_output = output_message.parsed_output
            select_message.spec_parsed_output.update(output_message.spec_parsed_output)
            select_message.parsed_output_list.extend(output_message.parsed_output_list)
        yield select_message

    def pre_print(self, query: Message, history: Memory = None, background: Memory = None, memory_manager: BaseMemoryManager=None):
        prompt = self.prompt_manager.pre_print(
                previous_agent_message=query, agent_long_term_memory=self.memory, ui_history=history, chain_summary_messages=background, react_memory=None, 
                memory_pool=memory_manager.current_memory, agents=self.group_agents)
        title = f"<<<<{self.role.role_name}'s prompt>>>>"
        print("#"*len(title) + f"\n{title}\n"+ "#"*len(title)+ f"\n\n{prompt}\n\n")

        for agent in self.group_agents:
            agent.pre_print(query=query, history=history, background=background, memory_manager=memory_manager)