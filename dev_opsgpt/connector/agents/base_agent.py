from pydantic import BaseModel
from typing import List, Union
import re
import copy
import json
import traceback
import uuid
from loguru import logger

from dev_opsgpt.connector.shcema.memory import Memory
from dev_opsgpt.connector.connector_schema import (
    Task, Role, Message, ActionStatus, Doc, CodeDoc
    )
from configs.server_config import SANDBOX_SERVER
from dev_opsgpt.sandbox import PyCodeBox, CodeBoxResponse
from dev_opsgpt.tools import DDGSTool, DocRetrieval, CodeRetrieval
from dev_opsgpt.connector.configs.agent_config import REACT_PROMPT_INPUT

from dev_opsgpt.llm_models import getChatModel


class BaseAgent:

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
            # docs_prompt: str,
            # prompt_mamnger: PromptManager
            ):
        
        self.task = task
        self.role = role
        self.llm = self.create_llm_engine(temperature, stop)
        self.memory = self.init_history(memory)
        self.chat_turn = chat_turn
        self.do_search = do_search
        self.do_doc_retrieval = do_doc_retrieval
        self.do_tool_retrieval = do_tool_retrieval
        self.codebox = PyCodeBox(
                    remote_url=SANDBOX_SERVER["url"],
                    remote_ip=SANDBOX_SERVER["host"],
                    remote_port=SANDBOX_SERVER["port"],
                    token="mytoken",
                    do_code_exe=True,
                    do_remote=SANDBOX_SERVER["do_remote"],
                    do_check_net=False
                    )
        self.do_filter = do_filter
        self.do_use_self_memory = do_use_self_memory
        # self.docs_prompt = docs_prompt
        # self.prompt_manager = None

    def run(self, query: Message, history: Memory = None, background: Memory = None) -> Message:
        '''llm inference'''
        # insert query into memory
        query_c = copy.deepcopy(query)
        
        self_memory = self.memory if self.do_use_self_memory else None
        prompt = self.create_prompt(query_c, self_memory, history, background)
        content = self.llm.predict(prompt)
        logger.debug(f"{self.role.role_name} prompt: {prompt}")
        # logger.debug(f"{self.role.role_name} content: {content}")

        output_message = Message(
            role_name=self.role.role_name,
            role_type="ai", #self.role.role_type,
            role_content=content,
            role_contents=[content],
            input_query=query_c.input_query,
            tools=query_c.tools
            )
        
        output_message = self.parser(output_message)
        if self.do_filter:
            output_message = self.filter(output_message)


        # 更新自身的回答
        self.append_history(query_c)
        self.append_history(output_message)
        logger.info(f"{self.role.role_name} step_run: {output_message.role_content}")
        return output_message

    def create_prompt(
            self, query: Message, memory: Memory =None, history: Memory = None, background: Memory = None, prompt_mamnger=None) -> str:
        '''
        role\task\tools\docs\memory
        '''
        # 
        doc_infos = self.create_doc_prompt(query)
        code_infos = self.create_codedoc_prompt(query)
        # 
        formatted_tools, tool_names = self.create_tools_prompt(query)
        task_prompt = self.create_task_prompt(query)
        background_prompt = self.create_background_prompt(background, control_key="step_content")
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

        # input_query = memory.to_tuple_messages(content_key="step_content")
        # input_query = "\n".join([f"{k}: {v}" for k, v in input_query if v])

        input_query = query.role_content

        # logger.debug(f"{self.role.role_name}  extra_system_prompt: {self.role.role_prompt}")
        logger.debug(f"{self.role.role_name}  input_query: {input_query}")
        # logger.debug(f"{self.role.role_name}  doc_infos: {doc_infos}")
        logger.debug(f"{self.role.role_name}  tool_names: {tool_names}")
        prompt += "\n" + REACT_PROMPT_INPUT.format(**{"query": input_query})
        # prompt = extra_system_prompt.format(**{"query": input_query, "doc_infos": doc_infos, "formatted_tools": formatted_tools, "tool_names": tool_names})
        while "{{" in prompt or "}}" in prompt:
            prompt = prompt.replace("{{", "{")
            prompt = prompt.replace("}}", "}")
        return prompt
    
        # prompt_comp = [("system", extra_system_prompt)] + memory.to_tuple_messages()
        # prompt = ChatPromptTemplate.from_messages(prompt_comp)
        # prompt = prompt.format(**{"query": query.role_content, "doc_infos": doc_infos, "formatted_tools": formatted_tools, "tool_names": tool_names})
        # return prompt

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
        for tool in tools:
            args_schema = re.sub("}", "}}}}", re.sub("{", "{{{{", str(tool.args)))
            tool_strings.append(f"{tool.name}: {tool.description}, args: {args_schema}")
        formatted_tools = "\n".join(tool_strings)
        tool_names = ", ".join([tool.name for tool in tools])
        return formatted_tools, tool_names
    
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
    
    def init_history(self, memory: Memory = None) -> Memory:
        return Memory([])
    
    def update_history(self, message: Message):
        self.memory.append(message)

    def append_history(self, message: Message):
        self.memory.append(message)
        
    def clear_history(self, ):
        self.memory.clear()
        self.memory = self.init_history()
    
    def create_llm_engine(self, temperature=0.2, stop=None):
        return getChatModel(temperature=temperature, stop=stop)

    def filter(self, message: Message, stop=None) -> Message:

        tool_params = self.parser_spec_key(message.role_content, "tool_params")
        code_content = self.parser_spec_key(message.role_content, "code_content")
        plan = self.parser_spec_key(message.role_content, "plan")
        plans = self.parser_spec_key(message.role_content, "plans", do_search=False)
        content = self.parser_spec_key(message.role_content, "content", do_search=False)

        # logger.debug(f"tool_params: {tool_params}, code_content: {code_content}, plan: {plan}, plans: {plans}, content: {content}")
        role_content = tool_params or code_content or plan or plans or content
        message.role_content = role_content or message.role_content
        return message
    
    def token_usage(self, ):
        pass

    def get_extra_infos(self, message: Message) -> Message:
        ''''''
        if self.do_search:
            message = self.get_search_retrieval(message)
        
        if self.do_doc_retrieval:
            message = self.get_doc_retrieval(message)

        if self.do_tool_retrieval:
            message = self.get_tool_retrieval(message)
        
        return message 
    
    def get_search_retrieval(self, message: Message,) -> Message:
        SEARCH_ENGINES = {"duckduckgo": DDGSTool}
        search_docs = []
        for idx, doc in enumerate(SEARCH_ENGINES["duckduckgo"].run(message.role_content, 3)):
            doc.update({"index": idx})
            search_docs.append(Doc(**doc))
        message.search_docs = search_docs
        return message
    
    def get_doc_retrieval(self, message: Message) -> Message:
        query = message.role_content
        knowledge_basename = message.doc_engine_name
        top_k = message.top_k
        score_threshold = message.score_threshold
        if knowledge_basename:
            docs = DocRetrieval.run(query, knowledge_basename, top_k, score_threshold)
            message.db_docs = [Doc(**doc) for doc in docs]
        return message
    
    def get_code_retrieval(self, message: Message) -> Message:
        # DocRetrieval.run("langchain是什么", "DSADSAD")
        query = message.input_query
        code_engine_name = message.code_engine_name
        history_node_list = message.history_node_list
        code_docs = CodeRetrieval.run(code_engine_name, query, code_limit=message.top_k, history_node_list=history_node_list)
        message.code_docs = [CodeDoc(**doc) for doc in code_docs]
        return message
    
    def get_tool_retrieval(self, message: Message) -> Message:
        return message
    
    def step_router(self, message: Message) -> Message:
        ''''''
        # message = self.parser(message)
        # logger.debug(f"message.action_status: {message.action_status}")
        if message.action_status == ActionStatus.CODING:
            message = self.code_step(message)
        elif message.action_status == ActionStatus.TOOL_USING:
            message = self.tool_step(message)

        return message

    def code_step(self, message: Message) -> Message:
        '''execute code'''
        # logger.debug(f"message.role_content: {message.role_content}, message.code_content: {message.code_content}")
        code_answer = self.codebox.chat('```python\n{}```'.format(message.code_content))
        code_prompt = f"执行上述代码后存在报错信息为 {code_answer.code_exe_response}，需要进行修复" \
                    if code_answer.code_exe_type == "error" else f"执行上述代码后返回信息为 {code_answer.code_exe_response}"
        uid = str(uuid.uuid1())
        if code_answer.code_exe_type == "image/png":
            message.figures[uid] = code_answer.code_exe_response
            message.code_answer = f"\n观察: 执行上述代码后生成一张图片, 图片名为{uid}\n"
            message.observation = f"\n观察: 执行上述代码后生成一张图片, 图片名为{uid}\n"
            message.step_content += f"\n观察: 执行上述代码后生成一张图片, 图片名为{uid}\n"
            message.step_contents += [f"\n观察: 执行上述代码后生成一张图片, 图片名为{uid}\n"]
            message.role_content += f"\n观察:执行上述代码后生成一张图片, 图片名为{uid}\n"
        else:
            message.code_answer = code_answer.code_exe_response
            message.observation = code_answer.code_exe_response
            message.step_content += f"\n观察: {code_prompt}\n"
            message.step_contents += [f"\n观察: {code_prompt}\n"]
            message.role_content += f"\n观察: {code_prompt}\n"
        # logger.info(f"观察: {message.action_status}, {message.observation}")
        return message

    def tool_step(self, message: Message) -> Message:
        '''execute tool'''
        # logger.debug(f"message: {message.action_status}, {message.tool_name}, {message.tool_params}")
        tool_names = [tool.name for tool in message.tools]
        if message.tool_name not in tool_names:
            message.tool_answer = "不存在可以执行的tool"    
            message.observation = "不存在可以执行的tool"    
            message.role_content += f"\n观察: 不存在可以执行的tool\n"
            message.step_content += f"\n观察: 不存在可以执行的tool\n"
            message.step_contents += [f"\n观察: 不存在可以执行的tool\n"]
        for tool in message.tools:
            if tool.name == message.tool_name:
                tool_res = tool.func(**message.tool_params)
                message.tool_answer = tool_res    
                message.observation = tool_res
                message.role_content += f"\n观察: {tool_res}\n"
                message.step_content += f"\n观察: {tool_res}\n"
                message.step_contents += [f"\n观察: {tool_res}\n"]

        # logger.info(f"观察: {message.action_status}, {message.observation}")
        return message
    
    def parser(self, message: Message) -> Message:
        ''''''
        content = message.role_content
        parser_keys = ["action", "code_content", "code_filename", "tool_params", "plans"]
        try:
            s_json = self._parse_json(content)
            message.action_status = s_json.get("action")
            message.code_content = s_json.get("code_content")
            message.tool_params = s_json.get("tool_params")
            message.tool_name = s_json.get("tool_name")
            message.code_filename = s_json.get("code_filename")
            message.plans = s_json.get("plans")
            # for parser_key in parser_keys:
            #     message.action_status = content.get(parser_key)
        except Exception as e:
            # logger.warning(f"{traceback.format_exc()}")
            action_value = self._match(r"'action':\s*'([^']*)'", content) if "'action'" in content else self._match(r'"action":\s*"([^"]*)"', content)
            code_content_value = self._match(r"'code_content':\s*'([^']*)'", content) if "'code_content'" in content else self._match(r'"code_content":\s*"([^"]*)"', content)
            filename_value = self._match(r"'code_filename':\s*'([^']*)'", content) if "'code_filename'" in content else self._match(r'"code_filename":\s*"([^"]*)"', content)
            tool_params_value = self._match(r"'tool_params':\s*(\{[^{}]*\})", content, do_json=True) if "'tool_params'" in content \
                                    else self._match(r'"tool_params":\s*(\{[^{}]*\})', content, do_json=True)
            tool_name_value = self._match(r"'tool_name':\s*'([^']*)'", content) if "'tool_name'" in content else self._match(r'"tool_name":\s*"([^"]*)"', content)
            plans_value = self._match(r"'plans':\s*(\[.*?\])", content, do_search=False) if "'plans'" in content else self._match(r'"plans":\s*(\[.*?\])', content, do_search=False, )
            # re解析
            message.action_status = action_value or "default"
            message.code_content = code_content_value
            message.code_filename = filename_value
            message.tool_params = tool_params_value
            message.tool_name = tool_name_value
            message.plans = plans_value

        # logger.debug(f"确认当前的action: {message.action_status}")

        return message
    
    def parser_spec_key(self, content, key, do_search=True, do_json=False) -> str:
        ''''''
        key2pattern = {
            "'action'": r"'action':\s*'([^']*)'", '"action"': r'"action":\s*"([^"]*)"',
            "'code_content'": r"'code_content':\s*'([^']*)'", '"code_content"': r'"code_content":\s*"([^"]*)"',
            "'code_filename'": r"'code_filename':\s*'([^']*)'", '"code_filename"': r'"code_filename":\s*"([^"]*)"',
            "'tool_params'": r"'tool_params':\s*(\{[^{}]*\})", '"tool_params"': r'"tool_params":\s*(\{[^{}]*\})',
            "'tool_name'": r"'tool_name':\s*'([^']*)'", '"tool_name"': r'"tool_name":\s*"([^"]*)"',
            "'plans'": r"'plans':\s*(\[.*?\])", '"plans"': r'"plans":\s*(\[.*?\])',
            "'content'": r"'content':\s*'([^']*)'", '"content"': r'"content":\s*"([^"]*)"',
            }
        
        s_json = self._parse_json(content)
        try:
            if s_json and key in s_json:
                return str(s_json[key])
        except:
            pass

        keystr = f"'{key}'" if f"'{key}'" in content else f'"{key}"'
        return self._match(key2pattern.get(keystr, fr"'{key}':\s*'([^']*)'"), content, do_search=do_search, do_json=do_json)
    
    def _match(self, pattern, s, do_search=True, do_json=False):
        try:
            if do_search:
                match = re.search(pattern, s)
                if match:
                    value = match.group(1).replace("\\n", "\n")
                    if do_json:
                        value = json.loads(value)
                else:
                    value = None
            else:
                match = re.findall(pattern, s, re.DOTALL)
                if match:
                    value = match[0]
                    if do_json:
                        value = json.loads(value)
                else:
                    value = None
        except Exception as e:
            logger.warning(f"{traceback.format_exc()}")

        # logger.debug(f"pattern: {pattern}, s: {s}, match: {match}")
        return value
    
    def _parse_json(self, s):
        try:
            pattern = r"```([^`]+)```"
            match = re.findall(pattern, s)
            if match:
                return eval(match[0])
        except:
            pass
        return None

    
    def get_memory(self, ):
        return self.memory.to_tuple_messages(content_key="step_content")
    
    def get_memory_str(self, ):
        return "\n".join([": ".join(i) for i in self.memory.to_tuple_messages(content_key="step_content")])