from typing import List, Union
import importlib
import re, os
import copy
from loguru import logger

from coagent.connector.schema import (
    Memory, Task, Role, Message, PromptField, LogVerboseEnum
)
from coagent.connector.memory_manager import BaseMemoryManager
from coagent.connector.configs.prompts import BEGIN_PROMPT_INPUT
from coagent.connector.message_process import MessageUtils
from coagent.llm_models import getChatModel, getExtraModel, LLMConfig, getChatModelFromConfig, EmbedConfig
from coagent.connector.prompt_manager import PromptManager
from coagent.connector.memory_manager import LocalMemoryManager
from coagent.connector.utils import parse_section
# from configs.model_config import JUPYTER_WORK_PATH
# from configs.server_config import SANDBOX_SERVER

class BaseAgent:

    def __init__(
            self, 
            role: Role,
            prompt_config: [PromptField],
            prompt_manager_type: str = "PromptManager",
            task: Task = None,
            memory: Memory = None,
            chat_turn: int = 1,
            focus_agents: List[str] = [],
            focus_message_keys: List[str] = [],
            #
            llm_config: LLMConfig = None,
            embed_config: EmbedConfig = None,
            sandbox_server: dict = {},
            jupyter_work_path: str = "",
            kb_root_path: str = "",
            log_verbose: str = "0"
            ):
        
        self.task = task
        self.role = role
        self.sandbox_server = sandbox_server
        self.jupyter_work_path = jupyter_work_path
        self.kb_root_path = kb_root_path
        self.message_utils = MessageUtils(role, sandbox_server, jupyter_work_path, embed_config, llm_config, kb_root_path, log_verbose)
        self.memory = self.init_history(memory)
        self.llm_config: LLMConfig = llm_config
        self.embed_config: EmbedConfig = embed_config
        self.llm = self.create_llm_engine(llm_config=self.llm_config)
        self.chat_turn = chat_turn
        # 
        self.focus_agents = focus_agents
        self.focus_message_keys = focus_message_keys
        # 
        prompt_manager_module = importlib.import_module("coagent.connector.prompt_manager")
        prompt_manager = getattr(prompt_manager_module, prompt_manager_type)
        self.prompt_manager: PromptManager = prompt_manager(role_prompt=role.role_prompt, prompt_config=prompt_config)
        self.log_verbose = max(os.environ.get("log_verbose", "0"), log_verbose)

    def step(self, query: Message, history: Memory = None, background: Memory = None, memory_manager: BaseMemoryManager=None) -> Message:
        '''agent reponse from multi-message'''
        message = None
        for message in self.astep(query, history, background, memory_manager):
            pass
        return message
    
    def astep(self, query: Message, history: Memory = None, background: Memory = None, memory_manager: BaseMemoryManager=None) -> Message:
        '''agent reponse from multi-message'''
        # insert query into memory
        query_c = copy.deepcopy(query)
        query_c = self.start_action_step(query_c)

        # llm predict
        # prompt = self.create_prompt(query_c, self.memory, history, background, memory_pool=memory_manager.current_memory)
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


        logger.debug(f"memory_pool: {memory_pool}")
        prompt = self.prompt_manager.generate_full_prompt(
            previous_agent_message=query_c, agent_long_term_memory=self.memory, ui_history=history, chain_summary_messages=background, memory_pool=memory_pool)
        content = self.llm.predict(prompt)

        if LogVerboseEnum.ge(LogVerboseEnum.Log2Level, self.log_verbose):
            logger.debug(f"{self.role.role_name} prompt: {prompt}")

        if LogVerboseEnum.ge(LogVerboseEnum.Log1Level, self.log_verbose):
            logger.info(f"{self.role.role_name} content: {content}")

        output_message = Message(
            role_name=self.role.role_name,
            role_type="assistant", #self.role.role_type,
            role_content=content,
            step_content=content,
            input_query=query_c.input_query,
            tools=query_c.tools,
            # parsed_output_list=[query.parsed_output],
            customed_kargs=query_c.customed_kargs
            )
        
        # common parse llm' content to message
        output_message = self.message_utils.parser(output_message)

        # action step
        output_message, observation_message = self.message_utils.step_router(output_message, history, background, memory_manager=memory_manager)
        output_message.parsed_output_list.append(output_message.parsed_output)
        if observation_message:
            output_message.parsed_output_list.append(observation_message.parsed_output)

        # update self_memory
        self.append_history(query_c)
        self.append_history(output_message)

        output_message.input_query = output_message.role_content
        # end
        output_message = self.message_utils.inherit_extrainfo(query, output_message)
        output_message = self.end_action_step(output_message)

        # update memory pool
        memory_manager.append(output_message)
        yield output_message
    
    def pre_print(self, query: Message, history: Memory = None, background: Memory = None, memory_manager: BaseMemoryManager=None):
        prompt = self.prompt_manager.pre_print(
            previous_agent_message=query, agent_long_term_memory=self.memory, ui_history=history, chain_summary_messages=background, memory_pool=memory_manager.current_memory)
        title = f"<<<<{self.role.role_name}'s prompt>>>>"
        print("#"*len(title) + f"\n{title}\n"+ "#"*len(title)+ f"\n\n{prompt}\n\n")

    def init_history(self, memory: Memory = None) -> Memory:
        return Memory(messages=[])
    
    def update_history(self, message: Message):
        self.memory.append(message)

    def append_history(self, message: Message):
        self.memory.append(message)
        
    def clear_history(self, ):
        self.memory.clear()
        self.memory = self.init_history()
    
    def create_llm_engine(self, llm_config: LLMConfig = None, temperature=0.2, stop=None):
        if llm_config is None:
            return getChatModel(temperature=temperature, stop=stop)
        else:
            return getChatModelFromConfig(llm_config=llm_config)
    
    def registry_actions(self, actions):
        '''registry llm's actions'''
        self.action_list = actions

    def start_action_step(self, message: Message) -> Message:
        '''do action before agent predict '''
        # action_json = self.start_action()
        # message["customed_kargs"]["xx"] = action_json
        return message

    def end_action_step(self, message: Message) -> Message:
        '''do action after agent predict '''
        # action_json = self.end_action()
        # message["customed_kargs"]["xx"] = action_json
        return message
    
    def token_usage(self, ):
        '''calculate the usage of token'''
        pass

    def select_memory_by_key(self, memory: Memory) -> Memory:
        return Memory(
            messages=[self.select_message_by_key(message) for message in memory.messages 
                      if self.select_message_by_key(message) is not None]
                      )

    def select_memory_by_agent_key(self, memory: Memory) -> Memory:
        return Memory(
            messages=[self.select_message_by_agent_key(message) for message in memory.messages 
                      if self.select_message_by_agent_key(message) is not None]
                      )

    def select_message_by_agent_key(self, message: Message) -> Message:
        # assume we focus all agents
        if self.focus_agents == []:
            return message
        return None if message is None or message.role_name not in self.focus_agents else self.select_message_by_key(message)
    
    def select_message_by_key(self, message: Message) -> Message:
        # assume we focus all key contents
        if message is None:
            return message
        
        if self.focus_message_keys == []:
            return message
        
        message_c = copy.deepcopy(message)
        message_c.parsed_output = {k: v for k,v in message_c.parsed_output.items() if k in self.focus_message_keys}
        message_c.parsed_output_list = [{k: v for k,v in parsed_output.items() if k in self.focus_message_keys} for parsed_output in message_c.parsed_output_list]
        return message_c
    
    def get_memory(self, content_key="role_content"):
        return self.memory.to_tuple_messages(content_key="step_content")
    
    def get_memory_str(self, content_key="role_content"):
        return "\n".join([": ".join(i) for i in self.memory.to_tuple_messages(content_key="step_content")])


    def create_prompt(
            self, query: Message, memory: Memory =None, history: Memory = None, background: Memory = None, memory_pool: Memory=None, prompt_mamnger=None) -> str:
        '''
        prompt engineer, contains role\task\tools\docs\memory
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
        
        # extra_system_prompt = self.role.role_prompt

        
        prompt = self.role.role_prompt.format(**{"formatted_tools": formatted_tools, "tool_names": tool_names})
        #
        memory_pool_select_by_agent_key = self.select_memory_by_agent_key(memory_pool)
        memory_pool_select_by_agent_key_context = '\n\n'.join([f"*{k}*\n{v}" for parsed_output in memory_pool_select_by_agent_key.get_parserd_output_list() for k, v in parsed_output.items() if k not in ['Action Status']])
        
        # input_query = query.input_query

        # # logger.debug(f"{self.role.role_name}  extra_system_prompt: {self.role.role_prompt}")
        # # logger.debug(f"{self.role.role_name}  input_query: {input_query}")
        # # logger.debug(f"{self.role.role_name}  doc_infos: {doc_infos}")
        # # logger.debug(f"{self.role.role_name}  tool_names: {tool_names}")
        # if "**Context:**" in self.role.role_prompt:
        #     # logger.debug(f"parsed_output_list: {query.parsed_output_list}")
        #     # input_query =  "'''" + "\n".join([f"###{k}###\n{v}" for i in query.parsed_output_list for k,v in i.items() if "Action Status" !=k]) + "'''"
        #     context =  "\n".join([f"*{k}*\n{v}" for i in query.parsed_output_list for k,v in i.items() if "Action Status" !=k])
        #     # context = history_prompt or '""'
        #     # logger.debug(f"parsed_output_list: {t}")
        #     prompt += "\n" + QUERY_CONTEXT_PROMPT_INPUT.format(**{"context": context, "query": query.origin_query})
        # else:
        #     prompt += "\n" + PLAN_PROMPT_INPUT.format(**{"query": input_query})

        task = query.task or self.task
        if task_prompt is not None:
            prompt += "\n" + task.task_prompt

        DocInfos = ""
        if doc_infos is not None and doc_infos!="" and doc_infos!="不存在知识库辅助信息":
            DocInfos += f"\nDocument Information: {doc_infos}"

        if code_infos is not None and code_infos!="" and code_infos!="不存在代码库辅助信息":
            DocInfos += f"\nCodeBase Infomation: {code_infos}"
            
        # if selfmemory_prompt:
        #     prompt += "\n" + selfmemory_prompt

        # if background_prompt:
        #     prompt += "\n" + background_prompt

        # if history_prompt:
        #     prompt += "\n" + history_prompt

        input_query = query.input_query

        # logger.debug(f"{self.role.role_name}  extra_system_prompt: {self.role.role_prompt}")
        # logger.debug(f"{self.role.role_name}  input_query: {input_query}")
        # logger.debug(f"{self.role.role_name}  doc_infos: {doc_infos}")
        # logger.debug(f"{self.role.role_name}  tool_names: {tool_names}")

        # extra_system_prompt = self.role.role_prompt
        input_keys = parse_section(self.role.role_prompt, 'Input Format')
        prompt = self.role.role_prompt.format(**{"formatted_tools": formatted_tools, "tool_names": tool_names})
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
                if DocInfos:
                    prompt += "\n**DocInfos:**\n" + DocInfos
                else:
                    prompt += "\n**DocInfos:**\n" + "Empty"
            elif input_key == "Question":
                prompt += "\n**Question:**\n" + input_query

        # if "**Context:**" in self.role.role_prompt:
        #     # logger.debug(f"parsed_output_list: {query.parsed_output_list}")
        #     # input_query =  "'''" + "\n".join([f"###{k}###\n{v}" for i in query.parsed_output_list for k,v in i.items() if "Action Status" !=k]) + "'''"
        #     context =  "\n".join([f"*{k}*\n{v}" for i in query.parsed_output_list for k,v in i.items() if "Action Status" !=k])
        #     if history:
        #         context = history_prompt + "\n" + context

        #     if not context:
        #         context = "there is no context"

        #     # logger.debug(f"parsed_output_list: {t}")
        #     if "DocInfos" in prompt:
        #         prompt += "\n" + QUERY_CONTEXT_DOC_PROMPT_INPUT.format(**{"context": context, "query": query.origin_query, "DocInfos": DocInfos})
        #     else:
        #         prompt += "\n" + QUERY_CONTEXT_PROMPT_INPUT.format(**{"context": context, "query": query.origin_query, "DocInfos": DocInfos})
        # else:
        #     prompt += "\n" + BASE_PROMPT_INPUT.format(**{"query": input_query})

        # prompt = extra_system_prompt.format(**{"query": input_query, "doc_infos": doc_infos, "formatted_tools": formatted_tools, "tool_names": tool_names})
        while "{{" in prompt or "}}" in prompt:
            prompt = prompt.replace("{{", "{")
            prompt = prompt.replace("}}", "}")

        # logger.debug(f"{self.role.role_name}  prompt: {prompt}")
        return prompt
    
    def create_doc_prompt(self, message: Message) -> str: 
        ''''''
        db_docs = message.db_docs
        search_docs = message.search_docs
        doc_infos = "\n".join([doc.get_snippet() for doc in db_docs] + [doc.get_snippet() for doc in search_docs])
        return doc_infos or "不存在知识库辅助信息"
    
    def create_codedoc_prompt(self, message: Message) -> str: 
        ''''''
        code_docs = message.code_docs
        doc_infos = "\n".join([doc.get_code() for doc in code_docs])
        return doc_infos or "不存在代码库辅助信息"
    
    def create_tools_prompt(self, message: Message) -> str:
        tools = message.tools
        tool_strings = []
        tools_descs = []
        for tool in tools:
            args_schema = re.sub("}", "}}}}", re.sub("{", "{{{{", str(tool.args)))
            tool_strings.append(f"{tool.name}: {tool.description}, args: {args_schema}")
            tools_descs.append(f"{tool.name}: {tool.description}")
        formatted_tools = "\n".join(tool_strings)
        tools_desc_str = "\n".join(tools_descs)
        tool_names = ", ".join([tool.name for tool in tools])
        return formatted_tools, tool_names, tools_desc_str
    
    def create_task_prompt(self, message: Message) -> str:
        task = message.task or self.task
        return "\n任务目标: " + task.task_prompt if task is not None else None
    
    def create_background_prompt(self, background: Memory, control_key="role_content") -> str:
        background_message = None if background is None else background.to_str_messages(content_key=control_key)
        # logger.debug(f"background_message: {background_message}")
        if background_message:
            background_message = re.sub("}", "}}", re.sub("{", "{{", background_message))
        return "\n背景信息: " + background_message if background_message else None
    
    def create_history_prompt(self, history: Memory, control_key="role_content") -> str:
        history_message = None if history is None else history.to_str_messages(content_key=control_key)
        if history_message:
            history_message = re.sub("}", "}}", re.sub("{", "{{", history_message))
        return "\n补充对话信息: " + history_message if history_message else None
    
    def create_selfmemory_prompt(self, selfmemory: Memory, control_key="role_content") -> str:
        selfmemory_message = None if selfmemory is None else selfmemory.to_str_messages(content_key=control_key)
        if selfmemory_message:
            selfmemory_message = re.sub("}", "}}", re.sub("{", "{{", selfmemory_message))
        return "\n补充自身对话信息: " + selfmemory_message if selfmemory_message else None
    