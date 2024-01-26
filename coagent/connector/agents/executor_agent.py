from typing import List, Union
import copy
from loguru import logger

from coagent.connector.schema import (
    Memory, Task, Env, Role, Message, ActionStatus, PromptField, LogVerboseEnum
)
from coagent.connector.memory_manager import BaseMemoryManager
from coagent.connector.configs.prompts import BEGIN_PROMPT_INPUT
from coagent.llm_models import LLMConfig, EmbedConfig
from coagent.connector.memory_manager import LocalMemoryManager

from .base_agent import BaseAgent


class ExecutorAgent(BaseAgent):
    def __init__(
            self, 
            role: Role,
            prompt_config: [PromptField],
            prompt_manager_type: str= "PromptManager",
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
        
        super().__init__(role, prompt_config, prompt_manager_type, task, memory, chat_turn,
                         focus_agents, focus_message_keys, llm_config, embed_config, sandbox_server,
                         jupyter_work_path, kb_root_path, log_verbose
                         )
        self.do_all_task = True # run all tasks

    def astep(self, query: Message, history: Memory = None, background: Memory = None, memory_manager: BaseMemoryManager=None) -> Message:
        '''agent reponse from multi-message'''
        # insert query into memory
        task_executor_memory = Memory(messages=[])
        # insert query
        output_message = Message(
                role_name=self.role.role_name,
                role_type="assistant", #self.role.role_type,
                role_content=query.input_query,
                step_content="",
                input_query=query.input_query,
                tools=query.tools,
                # parsed_output_list=[query.parsed_output],
                customed_kargs=query.customed_kargs
            )
        
        if memory_manager is None:
            memory_manager = LocalMemoryManager(
                unique_name=self.role.role_name, 
                do_init=True, 
                kb_root_path = self.kb_root_path, 
                embed_config=self.embed_config, 
                llm_config=self.embed_config
            )
            memory_manager.append(query)

        # self_memory = self.memory if self.do_use_self_memory else None

        plan_step = int(query.parsed_output.get("PLAN_STEP", 0))
        # 如果存在plan字段且plan字段为str的时候
        if "PLAN" not in query.parsed_output or isinstance(query.parsed_output.get("PLAN", []), str) or plan_step >= len(query.parsed_output.get("PLAN", [])):
            query_c = copy.deepcopy(query)
            query_c = self.start_action_step(query_c)
            query_c.parsed_output = {"CURRENT_STEP": query_c.input_query}
            task_executor_memory.append(query_c)
            for output_message, task_executor_memory in self._arun_step(output_message, query_c, self.memory, history, background, memory_manager, task_executor_memory):
                pass
            # task_executor_memory.append(query_c)
            # content = "the execution step of the plan is exceed the planned scope."
            # output_message.parsed_dict = {"Thought": content, "Action Status": "finished", "Action": content}
            # task_executor_memory.append(output_message)

        elif "PLAN" in query.parsed_output:
            if self.do_all_task:
                # run all tasks step by step
                for task_content in query.parsed_output["PLAN"][plan_step:]:
                    # create your llm prompt
                    query_c = copy.deepcopy(query)
                    query_c.parsed_output = {"CURRENT_STEP": task_content}
                    task_executor_memory.append(query_c)
                    for output_message, task_executor_memory in self._arun_step(output_message, query_c, self.memory, history, background, memory_manager, task_executor_memory):
                        pass
                    yield output_message
            else:
                query_c = copy.deepcopy(query)
                query_c = self.start_action_step(query_c)
                task_content = query_c.parsed_output["PLAN"][plan_step]
                query_c.parsed_output = {"CURRENT_STEP": task_content}
                task_executor_memory.append(query_c)
                for output_message, task_executor_memory in self._arun_step(output_message, query_c, self.memory, history, background, memory_manager, task_executor_memory):
                    pass
                output_message.parsed_output.update({"CURRENT_STEP": plan_step})
        # update self_memory
        self.append_history(query)
        self.append_history(output_message)
        output_message.input_query = output_message.role_content
        # end_action_step
        output_message = self.end_action_step(output_message)
        # update memory pool
        memory_manager.append(output_message)
        yield output_message

    def _arun_step(self, output_message: Message, query: Message, self_memory: Memory, 
            history: Memory, background: Memory, memory_manager: BaseMemoryManager, 
            task_memory: Memory) -> Union[Message, Memory]:
        '''execute the llm predict by created prompt'''
        memory_pool = memory_manager.current_memory
        prompt = self.prompt_manager.generate_full_prompt(
            previous_agent_message=query, agent_long_term_memory=self_memory, ui_history=history, chain_summary_messages=background, memory_pool=memory_pool,
            task_memory=task_memory)
        content = self.llm.predict(prompt)

        if LogVerboseEnum.ge(LogVerboseEnum.Log2Level, self.log_verbose):
            logger.debug(f"{self.role.role_name} prompt: {prompt}")

        if LogVerboseEnum.ge(LogVerboseEnum.Log1Level, self.log_verbose):
            logger.info(f"{self.role.role_name} content: {content}")

        output_message.role_content = content
        output_message.step_content += "\n"+output_message.role_content
        output_message = self.message_utils.parser(output_message)
        # according the output to choose one action for code_content or tool_content
        output_message, observation_message = self.message_utils.step_router(output_message)
        # update parserd_output_list
        output_message.parsed_output_list.append(output_message.parsed_output)

        react_message = copy.deepcopy(output_message)
        task_memory.append(react_message)
        if observation_message:
            task_memory.append(observation_message)
            output_message.parsed_output_list.append(observation_message.parsed_output)
            # logger.debug(f"{observation_message.role_name} content: {observation_message.role_content}")
        yield output_message, task_memory

    def pre_print(self, query: Message, history: Memory = None, background: Memory = None, memory_manager: BaseMemoryManager = None):
        task_memory = Memory(messages=[])
        prompt = self.prompt_manager.pre_print(
                previous_agent_message=query, agent_long_term_memory=self.memory, ui_history=history, chain_summary_messages=background, react_memory=None, 
                memory_pool=memory_manager.current_memory, task_memory=task_memory)
        title = f"<<<<{self.role.role_name}'s prompt>>>>"
        print("#"*len(title) + f"\n{title}\n"+ "#"*len(title)+ f"\n\n{prompt}\n\n")
