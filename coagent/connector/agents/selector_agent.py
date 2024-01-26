from typing import List, Union
import copy
import random
from loguru import logger

from coagent.connector.schema import (
    Memory, Task, Role, Message, PromptField, LogVerboseEnum
)
from coagent.connector.memory_manager import BaseMemoryManager
from coagent.connector.configs.prompts import BEGIN_PROMPT_INPUT
from coagent.connector.memory_manager import LocalMemoryManager
from coagent.llm_models import LLMConfig, EmbedConfig
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
            jupyter_work_path: str = "",
            kb_root_path: str = "",
            log_verbose: str = "0"
            ):
        
        super().__init__(role, prompt_config, prompt_manager_type, task, memory, chat_turn, 
                         focus_agents, focus_message_keys, llm_config, embed_config, sandbox_server,
                         jupyter_work_path, kb_root_path, log_verbose
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
            memory_pool = memory_manager.current_memory
        else:
            memory_pool = memory_manager.current_memory
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

    # def create_prompt(
    #         self, query: Message, memory: Memory =None, history: Memory = None, background: Memory = None, memory_manager: BaseMemoryManager=None, prompt_mamnger=None) -> str:
    #     '''
    #     role\task\tools\docs\memory
    #     '''
    #     # 
    #     doc_infos = self.create_doc_prompt(query)
    #     code_infos = self.create_codedoc_prompt(query)
    #     # 
    #     formatted_tools, tool_names, tools_descs = self.create_tools_prompt(query)
    #     agent_names, agents = self.create_agent_names()
    #     task_prompt = self.create_task_prompt(query)
    #     background_prompt = self.create_background_prompt(background)
    #     history_prompt = self.create_history_prompt(history)
    #     selfmemory_prompt = self.create_selfmemory_prompt(memory, control_key="step_content")
        

    #     DocInfos = ""
    #     if doc_infos is not None and doc_infos!="" and doc_infos!="不存在知识库辅助信息":
    #         DocInfos += f"\nDocument Information: {doc_infos}"

    #     if code_infos is not None and code_infos!="" and code_infos!="不存在代码库辅助信息":
    #         DocInfos += f"\nCodeBase Infomation: {code_infos}"

    #     input_query = query.input_query
    #     logger.debug(f"{self.role.role_name}  input_query: {input_query}")
    #     prompt = self.role.role_prompt.format(**{"agent_names": agent_names, "agents": agents, "formatted_tools": tools_descs, "tool_names": tool_names})
    #     #
    #     memory_pool_select_by_agent_key = self.select_memory_by_agent_key(memory_manager.current_memory)
    #     memory_pool_select_by_agent_key_context = '\n\n'.join([f"*{k}*\n{v}" for parsed_output in memory_pool_select_by_agent_key.get_parserd_output_list() for k, v in parsed_output.items() if k not in ['Action Status']])

    #     input_keys = parse_section(self.role.role_prompt, 'Input Format')
    #     # 
    #     prompt += "\n" + BEGIN_PROMPT_INPUT
    #     for input_key in input_keys:
    #         if input_key == "Origin Query": 
    #             prompt += "\n**Origin Query:**\n" + query.origin_query
    #         elif input_key == "Context":
    #             context =  "\n".join([f"*{k}*\n{v}" for i in query.parsed_output_list for k,v in i.items() if "Action Status" !=k])
    #             if history:
    #                 context = history_prompt + "\n" + context
    #             if not context:
    #                 context = "there is no context"

    #             if self.focus_agents and memory_pool_select_by_agent_key_context:
    #                 context = memory_pool_select_by_agent_key_context
    #             prompt += "\n**Context:**\n" + context + "\n" + input_query
    #         elif input_key == "DocInfos":
    #             prompt += "\n**DocInfos:**\n" + DocInfos
    #         elif input_key == "Question":
    #             prompt += "\n**Question:**\n" + input_query

    #     while "{{" in prompt or "}}" in prompt:
    #         prompt = prompt.replace("{{", "{")
    #         prompt = prompt.replace("}}", "}")

    #     # logger.debug(f"{self.role.role_name}  prompt: {prompt}")
    #     return prompt
    
    # def create_agent_names(self):
    #     random.shuffle(self.group_agents)
    #     agent_names = ", ".join([f'{agent.role.role_name}' for agent in self.group_agents])
    #     agent_descs = []
    #     for agent in self.group_agents:
    #         role_desc = agent.role.role_prompt.split("####")[1]
    #         while "\n\n" in role_desc:
    #             role_desc = role_desc.replace("\n\n", "\n")
    #         role_desc = role_desc.replace("\n", ",")

    #         agent_descs.append(f'"role name: {agent.role.role_name}\nrole description: {role_desc}"')

    #     return agent_names, "\n".join(agent_descs)