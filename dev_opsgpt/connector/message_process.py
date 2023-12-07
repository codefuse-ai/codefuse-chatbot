import re, traceback, uuid, copy, json, os
from loguru import logger


from configs.server_config import SANDBOX_SERVER
from configs.model_config import JUPYTER_WORK_PATH
from dev_opsgpt.connector.schema import (
    Memory, Task, Env, Role, Message, ActionStatus, CodeDoc, Doc
)
from dev_opsgpt.tools import DDGSTool, DocRetrieval, CodeRetrieval
from dev_opsgpt.sandbox import PyCodeBox, CodeBoxResponse


class MessageUtils:
    def __init__(self, role: Role = None) -> None:
        self.role = role
        self.codebox = PyCodeBox(
                    remote_url=SANDBOX_SERVER["url"],
                    remote_ip=SANDBOX_SERVER["host"],
                    remote_port=SANDBOX_SERVER["port"],
                    token="mytoken",
                    do_code_exe=True,
                    do_remote=SANDBOX_SERVER["do_remote"],
                    do_check_net=False
                    )
        
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
    
    def inherit_extrainfo(self, input_message: Message, output_message: Message):
        output_message.db_docs = input_message.db_docs
        output_message.search_docs = input_message.search_docs
        output_message.code_docs = input_message.code_docs
        output_message.figures.update(input_message.figures)
        output_message.origin_query = input_message.origin_query
        return output_message

    def get_extrainfo_step(self, message: Message, do_search, do_doc_retrieval, do_code_retrieval, do_tool_retrieval) -> Message:
        ''''''
        if do_search:
            message = self.get_search_retrieval(message)
        
        if do_doc_retrieval:
            message = self.get_doc_retrieval(message)

        if do_code_retrieval:
            input_message = self.get_code_retrieval(message)

        if do_tool_retrieval:
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
        code_docs = CodeRetrieval.run(code_engine_name, query, code_limit=message.top_k, history_node_list=history_node_list, search_type=message.cb_search_type)
        message.code_docs = [CodeDoc(**doc) for doc in code_docs]
        return message
    
    def get_tool_retrieval(self, message: Message) -> Message:
        return message
    
    def step_router(self, message: Message) -> tuple[Message, ...]:
        ''''''
        # message = self.parser(message)
        # logger.debug(f"message.action_status: {message.action_status}")
        observation_message = None
        if message.action_status == ActionStatus.CODING:
            message, observation_message = self.code_step(message)
        elif message.action_status == ActionStatus.TOOL_USING:
            message, observation_message = self.tool_step(message)
        elif message.action_status == ActionStatus.CODING2FILE:
            self.save_code2file(message)

        return message, observation_message

    def code_step(self, message: Message) -> Message:
        '''execute code'''
        # logger.debug(f"message.role_content: {message.role_content}, message.code_content: {message.code_content}")
        code_answer = self.codebox.chat('```python\n{}```'.format(message.code_content))
        code_prompt = f"The return error after executing the above code is {code_answer.code_exe_response}，need to recover" \
                    if code_answer.code_exe_type == "error" else f"The return information after executing the above code is {code_answer.code_exe_response}"
        
        observation_message = Message(
                role_name="observation",
                role_type="func", #self.role.role_type,
                role_content="",
                step_content="",
                input_query=message.code_content,
                )
        uid = str(uuid.uuid1())
        if code_answer.code_exe_type == "image/png":
            message.figures[uid] = code_answer.code_exe_response
            message.code_answer = f"\n**Observation:**: The return figure name is {uid} after executing the above code.\n"
            message.observation = f"\n**Observation:**: The return figure name is {uid} after executing the above code.\n"
            message.step_content += f"\n**Observation:**: The return figure name is {uid} after executing the above code.\n"
            message.step_contents += [f"\n**Observation:**:The return figure name is {uid} after executing the above code.\n"]
            # message.role_content += f"\n**Observation:**:执行上述代码后生成一张图片, 图片名为{uid}\n"
            observation_message.role_content = f"\n**Observation:**: The return figure name is {uid} after executing the above code.\n"
            observation_message.parsed_output = {"Observation": f"The return figure name is {uid} after executing the above code."}
        else:
            message.code_answer = code_answer.code_exe_response
            message.observation = code_answer.code_exe_response
            message.step_content += f"\n**Observation:**: {code_prompt}\n"
            message.step_contents += [f"\n**Observation:**: {code_prompt}\n"]
            # message.role_content += f"\n**Observation:**: {code_prompt}\n"
            observation_message.role_content = f"\n**Observation:**: {code_prompt}\n"
            observation_message.parsed_output = {"Observation": code_prompt}
        # logger.info(f"**Observation:** {message.action_status}, {message.observation}")
        return message, observation_message

    def tool_step(self, message: Message) -> Message:
        '''execute tool'''
        # logger.debug(f"{message}")
        observation_message = Message(
                role_name="observation",
                role_type="function", #self.role.role_type,
                role_content="\n**Observation:** there is no tool can execute\n"    ,
                step_content="",
                input_query=str(message.tool_params),
                tools=message.tools,
                )
        # logger.debug(f"message: {message.action_status}, {message.tool_name}, {message.tool_params}")
        tool_names = [tool.name for tool in message.tools]
        if message.tool_name not in tool_names:
            message.tool_answer = "\n**Observation:** there is no tool can execute\n"    
            message.observation = "\n**Observation:** there is no tool can execute\n"    
            # message.role_content += f"\n**Observation:**: 不存在可以执行的tool\n"
            message.step_content += f"\n**Observation:** there is no tool can execute\n"
            message.step_contents += [f"\n**Observation:** there is no tool can execute\n"]
            observation_message.role_content = f"\n**Observation:** there is no tool can execute\n"
            observation_message.parsed_output = {"Observation": "there is no tool can execute\n"}
        for tool in message.tools:
            if tool.name == message.tool_name:
                tool_res = tool.func(**message.tool_params.get("tool_params", {}))
                logger.debug(f"tool_res {tool_res}")
                message.tool_answer = tool_res    
                message.observation = tool_res
                # message.role_content += f"\n**Observation:**: {tool_res}\n"
                message.step_content += f"\n**Observation:** {tool_res}\n"
                message.step_contents += [f"\n**Observation:** {tool_res}\n"]
                observation_message.role_content = f"\n**Observation:** {tool_res}\n"
                observation_message.parsed_output = {"Observation": tool_res}
                break

        # logger.info(f"**Observation:** {message.action_status}, {message.observation}")
        return message, observation_message
    
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
            def parse_text_to_dict(text):
                # Define a regular expression pattern to capture the key and value
                main_pattern = r"\*\*(.+?):\*\*\s*(.*?)\s*(?=\*\*|$)"
                list_pattern = r'```python\n(.*?)```'

                # Use re.findall to find all main matches in the text
                main_matches = re.findall(main_pattern, text, re.DOTALL)

                # Convert main matches to a dictionary
                parsed_dict = {key.strip(): value.strip() for key, value in main_matches}

                for k, v in parsed_dict.items():
                    for pattern in [list_pattern]:
                        if "PLAN" != k: continue
                        v = v.replace("```list", "```python")
                        match_value = re.search(pattern, v, re.DOTALL)
                        if match_value:
                            # Add the code block to the dictionary
                            parsed_dict[k] = eval(match_value.group(1).strip())
                            break

                return parsed_dict
            
            def extract_content_from_backticks(text):
                code_blocks = []
                lines = text.split('\n')
                is_code_block = False
                code_block = ''
                language = ''
                for line in lines:
                    if line.startswith('```') and not is_code_block:
                        is_code_block = True
                        language = line[3:]
                        code_block = ''
                    elif line.startswith('```') and is_code_block:
                        is_code_block = False
                        code_blocks.append({language.strip(): code_block.strip()})
                    elif is_code_block:
                        code_block += line + '\n'
                return code_blocks
            
            def parse_dict_to_dict(parsed_dict) -> dict:
                code_pattern = r'```python\n(.*?)```'
                tool_pattern = r'```json\n(.*?)```'
                
                pattern_dict = {"code": code_pattern, "json": tool_pattern}
                spec_parsed_dict = copy.deepcopy(parsed_dict)
                for key, pattern in pattern_dict.items():
                    for k, text in parsed_dict.items():
                        # Search for the code block
                        if not isinstance(text, str): continue
                        _match = re.search(pattern, text, re.DOTALL)
                        if _match:
                            # Add the code block to the dictionary
                            try:
                                spec_parsed_dict[key] = json.loads(_match.group(1).strip())
                            except:
                                spec_parsed_dict[key] = _match.group(1).strip()
                            break
                return spec_parsed_dict

            parsed_dict = parse_text_to_dict(content)
            spec_parsed_dict = parse_dict_to_dict(parsed_dict)
            action_value = parsed_dict.get('Action Status')
            if action_value:
                action_value = action_value.lower()
            logger.info(f'{message.role_name}: action_value: {action_value}')
            # action_value = self._match(r"'action':\s*'([^']*)'", content) if "'action'" in content else self._match(r'"action":\s*"([^"]*)"', content)
            
            code_content_value = spec_parsed_dict.get('code')
            # code_content_value = self._match(r"'code_content':\s*'([^']*)'", content) if "'code_content'" in content else self._match(r'"code_content":\s*"([^"]*)"', content)
            filename_value = self._match(r"'code_filename':\s*'([^']*)'", content) if "'code_filename'" in content else self._match(r'"code_filename":\s*"([^"]*)"', content)

            if action_value == 'tool_using':
                tool_params_value = spec_parsed_dict.get('json')
            else:
                tool_params_value = None
            # tool_params_value = spec_parsed_dict.get('tool_params')
            # tool_params_value = self._match(r"'tool_params':\s*(\{[^{}]*\})", content, do_json=True) if "'tool_params'" in content \
            #                         else self._match(r'"tool_params":\s*(\{[^{}]*\})', content, do_json=True)
            tool_name_value = self._match(r"'tool_name':\s*'([^']*)'", content) if "'tool_name'" in content else self._match(r'"tool_name":\s*"([^"]*)"', content)
            plans_value = self._match(r"'plans':\s*(\[.*?\])", content, do_search=False) if "'plans'" in content else self._match(r'"plans":\s*(\[.*?\])', content, do_search=False, )
            # re解析
            message.action_status = action_value or "default"
            message.code_content = code_content_value
            message.code_filename = filename_value
            message.tool_params = tool_params_value
            message.tool_name = tool_name_value
            message.plans = plans_value
            message.parsed_output = parsed_dict
            message.spec_parsed_output = spec_parsed_dict

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
    

    def save_code2file(self, message: Message, project_dir=JUPYTER_WORK_PATH):
        filename = message.parsed_output.get("SaveFileName")
        code = message.spec_parsed_output.get("code")

        for k, v in {"&gt;": ">", "&ge;": ">=", "&lt;": "<", "&le;": "<="}.items():
            code = code.replace(k, v)

        file_path = os.path.join(project_dir, filename)

        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w") as f:
            f.write(code)
        