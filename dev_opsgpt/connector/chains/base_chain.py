from pydantic import BaseModel
from typing import List
import json
import re
from loguru import logger
import traceback
import uuid
import copy

from dev_opsgpt.connector.agents import BaseAgent
from dev_opsgpt.tools.base_tool import BaseTools, Tool
from dev_opsgpt.connector.shcema.memory import Memory
from dev_opsgpt.connector.connector_schema import (
    Role, Message, ActionStatus, ChainConfig,
    load_role_configs
)
from dev_opsgpt.sandbox import PyCodeBox, CodeBoxResponse


from configs.server_config import SANDBOX_SERVER

from dev_opsgpt.connector.configs.agent_config import AGETN_CONFIGS
role_configs = load_role_configs(AGETN_CONFIGS)


class BaseChain:
    def __init__(
            self, 
            chainConfig: ChainConfig,
            agents: List[BaseAgent],
            chat_turn: int = 1,
            do_checker: bool = False,
            do_code_exec: bool = False,
            # prompt_mamnger: PromptManager
            ) -> None:
        self.chainConfig = chainConfig
        self.agents = agents
        self.chat_turn = chat_turn
        self.do_checker = do_checker
        self.checker = BaseAgent(role=role_configs["checker"].role,
            task = None,
            memory = None,
            do_search = role_configs["checker"].do_search,
            do_doc_retrieval = role_configs["checker"].do_doc_retrieval,
            do_tool_retrieval = role_configs["checker"].do_tool_retrieval,
            do_filter=False, do_use_self_memory=False)
        
        self.global_memory = Memory([])
        self.local_memory = Memory([])
        self.do_code_exec = do_code_exec
        self.codebox = PyCodeBox(
            remote_url=SANDBOX_SERVER["url"],
            remote_ip=SANDBOX_SERVER["host"],
            remote_port=SANDBOX_SERVER["port"],
            token="mytoken",
            do_code_exe=True,
            do_remote=SANDBOX_SERVER["do_remote"],
            do_check_net=False
            )

    def step(self, query: Message, history: Memory = None, background: Memory = None) -> Message:
        '''execute chain'''
        local_memory = Memory([])
        input_message = copy.deepcopy(query)
        step_nums = copy.deepcopy(self.chat_turn)
        check_message = None

        self.global_memory.append(input_message)
        local_memory.append(input_message)
        while step_nums > 0:

            for agent in self.agents:
                output_message = agent.run(input_message, history, background=background)
                output_message = self.inherit_extrainfo(input_message, output_message)
                # according the output to choose one action for code_content or tool_content
                logger.info(f"{agent.role.role_name} message: {output_message.role_content}")
                output_message = self.parser(output_message)
                # output_message = self.step_router(output_message)

                input_message = output_message
                self.global_memory.append(output_message)

                local_memory.append(output_message)
                # when get finished signal can stop early
                if output_message.action_status == ActionStatus.FINISHED: 
                    break

            if self.do_checker:
                logger.debug(f"{self.checker.role.role_name} input global memory: {self.global_memory.to_str_messages(content_key='step_content')}")
                check_message = self.checker.run(query, background=self.global_memory)
                check_message = self.parser(check_message)
                check_message = self.filter(check_message)
                check_message = self.inherit_extrainfo(output_message, check_message)
                logger.debug(f"{self.checker.role.role_name}: {check_message.role_content}")

                if check_message.action_status == ActionStatus.FINISHED: 
                    self.global_memory.append(check_message)
                    break

            step_nums -= 1

        return check_message or output_message, local_memory
    
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
        uid = str(uuid.uuid1())
        if code_answer.code_exe_type == "image/png":
            message.figures[uid] = code_answer.code_exe_response
            message.code_answer = f"\n观察: 执行代码后获得输出一张图片, 文件名为{uid}\n"
            message.observation = f"\n观察: 执行代码后获得输出一张图片, 文件名为{uid}\n"
            message.step_content += f"\n观察: 执行代码后获得输出一张图片, 文件名为{uid}\n"
            message.step_contents += [f"\n观察: 执行代码后获得输出一张图片, 文件名为{uid}\n"]
            message.role_content += f"\n执行代码后获得输出一张图片, 文件名为{uid}\n"
        else:
            message.code_answer = code_answer.code_exe_response
            message.observation = code_answer.code_exe_response
            message.step_content += f"\n观察: 执行代码后获得输出是 {code_answer.code_exe_response}\n"
            message.step_contents += [f"\n观察: 执行代码后获得输出是 {code_answer.code_exe_response}\n"]
            message.role_content += f"\n观察: 执行代码后获得输出是 {code_answer.code_exe_response}\n"
        logger.info(f"观察: {message.action_status}, {message.observation}")
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
        return message

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

        logger.debug(f"确认当前的action: {message.action_status}")

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

    def inherit_extrainfo(self, input_message: Message, output_message: Message):
        output_message.db_docs = input_message.db_docs
        output_message.search_docs = input_message.search_docs
        output_message.code_docs = input_message.code_docs
        output_message.figures.update(input_message.figures)
        return output_message
    
    def get_memory(self, do_all_memory=True, content_key="role_content") -> Memory:
        memory = self.global_memory if do_all_memory else self.local_memory
        return memory.to_tuple_messages(content_key=content_key)
    
    def get_memory_str(self, do_all_memory=True, content_key="role_content") -> Memory:
        memory = self.global_memory if do_all_memory else self.local_memory
        # for i in memory.to_tuple_messages(content_key=content_key):
        #     logger.debug(f"{i}")
        return "\n".join([": ".join(i) for i in memory.to_tuple_messages(content_key=content_key)])
    
    def get_agents_memory(self, content_key="role_content"):
        return [agent.get_memory(content_key=content_key) for agent in self.agents]
    
    def get_agents_memory_str(self, content_key="role_content"):
        return "************".join([f"{agent.role.role_name}\n" + agent.get_memory_str(content_key=content_key) for agent in self.agents])