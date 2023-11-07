from pydantic import BaseModel
from typing import List, Union
import re
import traceback
import copy
from loguru import logger

from langchain.prompts.chat import ChatPromptTemplate

from dev_opsgpt.connector.connector_schema import Message
from dev_opsgpt.connector.shcema.memory import Memory
from dev_opsgpt.connector.connector_schema import Task, Env, Role, Message, ActionStatus
from dev_opsgpt.llm_models import getChatModel
from dev_opsgpt.connector.configs.agent_config import REACT_PROMPT_INPUT

from .base_agent import BaseAgent


class ReactAgent(BaseAgent):
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
            stop: Union[List[str], str] = "观察",
            do_filter: bool = True,
            do_use_self_memory: bool = True,
            # docs_prompt: str,
            # prompt_mamnger: PromptManager
            ):
        super().__init__(role, task, memory, chat_turn, do_search, do_doc_retrieval, 
                         do_tool_retrieval, temperature, stop, do_filter,do_use_self_memory
                         )

    def run(self, query: Message, history: Memory = None, background: Memory = None) -> Message:
        step_nums = copy.deepcopy(self.chat_turn)
        react_memory = Memory([])
        # 问题插入
        output_message = Message(
                role_name=self.role.role_name,
                role_type="ai", #self.role.role_type,
                role_content=query.input_query,
                step_content=query.input_query,
                input_query=query.input_query,
                tools=query.tools
                )
        react_memory.append(output_message)
        idx = 0
        while step_nums > 0:
            output_message.role_content = output_message.step_content
            self_memory = self.memory if self.do_use_self_memory else None
            prompt = self.create_prompt(query, self_memory, history, background, react_memory)
            try:
                content = self.llm.predict(prompt)
            except Exception as e:
                logger.warning(f"error prompt: {prompt}")
                raise Exception(traceback.format_exc())
            
            output_message.role_content = content
            output_message.role_contents += [content]
            output_message.step_content += output_message.role_content
            output_message.step_contents + [output_message.role_content]

            # logger.debug(f"{self.role.role_name}, {idx} iteration prompt: {prompt}")
            # logger.info(f"{self.role.role_name}, {idx} iteration step_run: {output_message.role_content}")

            output_message = self.parser(output_message)
            # when get finished signal can stop early
            if output_message.action_status == ActionStatus.FINISHED: break
            # according the output to choose one action for code_content or tool_content
            output_message = self.step_router(output_message)
            logger.info(f"{self.role.role_name} react_run: {output_message.role_content}")
            
            idx += 1
            step_nums -= 1
        # react' self_memory saved at last
        self.append_history(output_message)
        return output_message

    def create_prompt(
            self, query: Message, memory: Memory =None, history: Memory = None, background: Memory = None, react_memory: Memory = None, prompt_mamnger=None) -> str:
        '''
        role\task\tools\docs\memory
        '''
        # 
        doc_infos = self.create_doc_prompt(query)
        code_infos = self.create_codedoc_prompt(query)
        # 
        formatted_tools, tool_names = self.create_tools_prompt(query)
        task_prompt = self.create_task_prompt(query)
        background_prompt = self.create_background_prompt(background)
        history_prompt = self.create_history_prompt(history)
        selfmemory_prompt = self.create_selfmemory_prompt(memory, control_key="step_content")
        # 
        # extra_system_prompt = self.role.role_prompt
        prompt = self.role.role_prompt.format(**{"formatted_tools": formatted_tools, "tool_names": tool_names})


        task = query.task or self.task
        if task_prompt is not None:
            prompt += "\n" + task.task_prompt

        if doc_infos is not None and doc_infos!="" and doc_infos!="不存在知识库辅助信息":
            prompt += f"\n知识库信息: {doc_infos}"

        if code_infos is not None and code_infos!="" and code_infos!="不存在代码库辅助信息":
            prompt += f"\n代码库信息: {code_infos}"

        if background_prompt:
            prompt += "\n" + background_prompt

        if history_prompt:
            prompt += "\n" + history_prompt

        if selfmemory_prompt:
            prompt += "\n" + selfmemory_prompt
        
        # react 流程是自身迭代过程，另外二次触发的是需要作为历史对话信息
        input_query = react_memory.to_tuple_messages(content_key="step_content")
        input_query = "\n".join([f"{v}" for k, v in input_query if v])

        # logger.debug(f"{self.role.role_name}  extra_system_prompt: {self.role.role_prompt}")
        # logger.debug(f"{self.role.role_name}  input_query: {input_query}")
        # logger.debug(f"{self.role.role_name}  doc_infos: {doc_infos}")
        # logger.debug(f"{self.role.role_name}  tool_names: {tool_names}")
        prompt += "\n" + REACT_PROMPT_INPUT.format(**{"query": input_query})

        # prompt = extra_system_prompt.format(**{"query": input_query, "doc_infos": doc_infos, "formatted_tools": formatted_tools, "tool_names": tool_names})
        while "{{" in prompt or "}}" in prompt:
            prompt = prompt.replace("{{", "{")
            prompt = prompt.replace("}}", "}")
        return prompt
    
