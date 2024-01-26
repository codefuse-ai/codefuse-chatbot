from coagent.connector.schema import Memory, Message
import random
from textwrap import dedent
import copy
from loguru import logger

from coagent.connector.utils import extract_section, parse_section


class PromptManager:
    def __init__(self, role_prompt="", prompt_config=None, monitored_agents=[], monitored_fields=[]):
        self.role_prompt = role_prompt
        self.monitored_agents = monitored_agents
        self.monitored_fields = monitored_fields
        self.field_handlers = {}
        self.context_handlers = {}
        self.field_order = []  # 用于普通字段的顺序
        self.context_order = []  # 单独维护上下文字段的顺序
        self.field_descriptions = {}
        self.omit_if_empty_flags = {}
        self.context_title = "### Context Data\n\n"  
        
        self.prompt_config = prompt_config
        if self.prompt_config:
            self.register_fields_from_config()
    
    def register_field(self, field_name, function=None, title=None, description=None, is_context=True, omit_if_empty=True):
        """
        注册一个新的字段及其处理函数。
        Args:
            field_name (str): 字段名称。
            function (callable): 处理字段数据的函数。
            title (str, optional): 字段的自定义标题（可选）。
            description (str, optional): 字段的描述（可选，可以是几句话）。
            is_context (bool, optional): 指示该字段是否为上下文字段。
            omit_if_empty (bool, optional): 如果数据为空，是否省略该字段。
        """
        if not function:
            function = self.handle_custom_data
        
        # Register the handler function based on context flag
        if is_context:
            self.context_handlers[field_name] = function
        else:
            self.field_handlers[field_name] = function
        
        # Store the custom title if provided and adjust the title prefix based on context
        title_prefix = "####" if is_context else "###"
        if title is not None:
            self.field_descriptions[field_name] = f"{title_prefix} {title}\n\n"
        elif description is not None:
            # If title is not provided but description is, use description as title
            self.field_descriptions[field_name] = f"{title_prefix} {field_name.replace('_', ' ').title()}\n\n{description}\n\n"
        else:
            # If neither title nor description is provided, use the field name as title
            self.field_descriptions[field_name] = f"{title_prefix} {field_name.replace('_', ' ').title()}\n\n"
            
        # Store the omit_if_empty flag for this field
        self.omit_if_empty_flags[field_name] = omit_if_empty
        
        if is_context and field_name != 'context_placeholder':
            self.context_handlers[field_name] = function
            self.context_order.append(field_name)
        else:
            self.field_handlers[field_name] = function
            self.field_order.append(field_name)
    
    def generate_full_prompt(self, **kwargs):
        full_prompt = []
        context_prompts = []  # 用于收集上下文内容
        is_pre_print = kwargs.get("is_pre_print", False) # 用于强制打印所有prompt 字段信息，不管有没有空

        # 先处理上下文字段
        for field_name in self.context_order:
            handler = self.context_handlers[field_name]
            processed_prompt = handler(**kwargs)
            # Check if the field should be omitted when empty
            if self.omit_if_empty_flags.get(field_name, False) and not processed_prompt and not is_pre_print:
                continue  # Skip this field
            title_or_description = self.field_descriptions.get(field_name, f"#### {field_name.replace('_', ' ').title()}\n\n")
            context_prompts.append(title_or_description + processed_prompt + '\n\n')

        # 处理普通字段，同时查找 context_placeholder 的位置
        for field_name in self.field_order:
            if field_name == 'context_placeholder':
                # 在 context_placeholder 的位置插入上下文数据
                full_prompt.append(self.context_title)  # 添加上下文部分的大标题
                full_prompt.extend(context_prompts)  # 添加收集的上下文内容
            else:
                handler = self.field_handlers[field_name]
                processed_prompt = handler(**kwargs)
                # Check if the field should be omitted when empty
                if self.omit_if_empty_flags.get(field_name, False) and not processed_prompt and not is_pre_print:
                    continue  # Skip this field
                title_or_description = self.field_descriptions.get(field_name, f"### {field_name.replace('_', ' ').title()}\n\n")
                full_prompt.append(title_or_description + processed_prompt + '\n\n')

        # 返回完整的提示，移除尾部的空行
        return ''.join(full_prompt).rstrip('\n')
        
    def pre_print(self, **kwargs):
        kwargs.update({"is_pre_print": True})
        prompt = self.generate_full_prompt(**kwargs)

        input_keys = parse_section(self.role_prompt, 'Response Output Format')
        llm_predict = "\n".join([f"**{k}:**" for k in input_keys])
        return prompt + "\n\n" + "#"*19 + "\n<<<<LLM PREDICT>>>>\n" + "#"*19  + f"\n\n{llm_predict}\n"

    def handle_custom_data(self, **kwargs):
        return ""
    
    def handle_tool_data(self, **kwargs):
        if 'previous_agent_message' not in kwargs:
            return ""
        
        previous_agent_message = kwargs.get('previous_agent_message')
        tools = previous_agent_message.tools
        
        if not tools:
            return ""
        
        tool_strings = []
        for tool in tools:
            args_schema = str(tool.args)
            tool_strings.append(f"{tool.name}: {tool.description}, args: {args_schema}")
        formatted_tools = "\n".join(tool_strings)
        
        tool_names = ", ".join([tool.name for tool in tools])
        
        tool_prompt = dedent(f"""
Below is a list of tools that are available for your use:
{formatted_tools}

valid "tool_name" value is:
{tool_names}
""")
        
        return tool_prompt

    def handle_agent_data(self, **kwargs):
        if 'agents' not in kwargs:
            return ""
        
        agents = kwargs.get('agents')
        random.shuffle(agents)
        agent_names = ", ".join([f'{agent.role.role_name}' for agent in agents])
        agent_descs = []
        for agent in agents:
            role_desc = agent.role.role_prompt.split("####")[1]
            while "\n\n" in role_desc:
                role_desc = role_desc.replace("\n\n", "\n")
            role_desc = role_desc.replace("\n", ",")

            agent_descs.append(f'"role name: {agent.role.role_name}\nrole description: {role_desc}"')

        agents =  "\n".join(agent_descs)
        agent_prompt = f'''
        Please ensure your selection is one of the listed roles. Available roles for selection:
        {agents}
        Please ensure select the Role from agent names, such as {agent_names}'''

        return dedent(agent_prompt)
    
    def handle_doc_info(self, **kwargs) -> str:
        if 'previous_agent_message' not in kwargs:
            return ""
        previous_agent_message: Message = kwargs.get('previous_agent_message')
        db_docs = previous_agent_message.db_docs
        search_docs = previous_agent_message.search_docs
        code_cocs = previous_agent_message.code_docs
        doc_infos = "\n".join([doc.get_snippet() for doc in db_docs] + [doc.get_snippet() for doc in search_docs] + 
                              [doc.get_code() for doc in code_cocs])
        return doc_infos
    
    def handle_session_records(self, **kwargs) -> str:

        memory_pool: Memory = kwargs.get('memory_pool', Memory(messages=[]))
        memory_pool = self.select_memory_by_agent_name(memory_pool)
        memory_pool = self.select_memory_by_parsed_key(memory_pool)

        return memory_pool.to_str_messages(content_key="parsed_output_list", with_tag=True)
    
    def handle_current_plan(self, **kwargs) -> str:
        if 'previous_agent_message' not in kwargs:
            return ""
        previous_agent_message = kwargs['previous_agent_message']
        return previous_agent_message.parsed_output.get("CURRENT_STEP", "")
    
    def handle_agent_profile(self, **kwargs) -> str:
        return extract_section(self.role_prompt, 'Agent Profile')
    
    def handle_output_format(self, **kwargs) -> str:
        return extract_section(self.role_prompt, 'Response Output Format')
    
    def handle_response(self, **kwargs) -> str:
        if 'react_memory' not in kwargs:
            return ""

        react_memory = kwargs.get('react_memory', Memory(messages=[]))
        if react_memory is None:
            return ""
        
        return "\n".join(["\n".join([f"**{k}:**\n{v}" for k,v in _dict.items()]) for _dict in react_memory.get_parserd_output()])

    def handle_task_records(self, **kwargs) -> str:
        if 'task_memory' not in kwargs:
            return ""

        task_memory: Memory = kwargs.get('task_memory', Memory(messages=[]))
        if task_memory is None:
            return ""
        
        return "\n".join(["\n".join([f"**{k}:**\n{v}" for k,v in _dict.items() if k not in ["CURRENT_STEP"]]) for _dict in task_memory.get_parserd_output()])
    
    def handle_previous_message(self, message: Message) -> str: 
        pass
    
    def handle_message_by_role_name(self, message: Message) -> str: 
        pass
    
    def handle_message_by_role_type(self, message: Message) -> str:
        pass
    
    def handle_current_agent_react_message(self, message: Message) -> str:
        pass
    
    def extract_codedoc_info_for_prompt(self, message: Message) -> str: 
        code_docs = message.code_docs
        doc_infos = "\n".join([doc.get_code() for doc in code_docs])
        return doc_infos
    
    def select_memory_by_parsed_key(self, memory: Memory) -> Memory:
        return Memory(
            messages=[self.select_message_by_parsed_key(message) for message in memory.messages 
                      if self.select_message_by_parsed_key(message) is not None]
                      )

    def select_memory_by_agent_name(self, memory: Memory) -> Memory:
        return Memory(
            messages=[self.select_message_by_agent_name(message) for message in memory.messages 
                      if self.select_message_by_agent_name(message) is not None]
                      )

    def select_message_by_agent_name(self, message: Message) -> Message:
        # assume we focus all agents
        if self.monitored_agents == []:
            return message
        return None if message is None or message.role_name not in self.monitored_agents else self.select_message_by_parsed_key(message)
    
    def select_message_by_parsed_key(self, message: Message) -> Message:
        # assume we focus all key contents
        if message is None:
            return message
        
        if self.monitored_fields == []:
            return message
        
        message_c = copy.deepcopy(message)
        message_c.parsed_output = {k: v for k,v in message_c.parsed_output.items() if k in self.monitored_fields}
        message_c.parsed_output_list = [{k: v for k,v in parsed_output.items() if k in self.monitored_fields} for parsed_output in message_c.parsed_output_list]
        return message_c
    
    def get_memory(self, content_key="role_content"):
        return self.memory.to_tuple_messages(content_key="step_content")
    
    def get_memory_str(self, content_key="role_content"):
        return "\n".join([": ".join(i) for i in self.memory.to_tuple_messages(content_key="step_content")])
    
    def register_fields_from_config(self):
        
        for prompt_field in self.prompt_config:
            
            function_name = prompt_field.function_name
            # 检查function_name是否是self的一个方法
            if function_name and hasattr(self, function_name):
                function = getattr(self, function_name)
            else:
                function = self.handle_custom_data
                
            self.register_field(prompt_field.field_name, 
                                function=function, 
                                title=prompt_field.title,
                                description=prompt_field.description,
                                is_context=prompt_field.is_context,
                                omit_if_empty=prompt_field.omit_if_empty)
    
    def register_standard_fields(self):
        self.register_field('agent_profile', function=self.handle_agent_profile, is_context=False)
        self.register_field('tool_information', function=self.handle_tool_data, is_context=False)
        self.register_field('context_placeholder', is_context=True)  # 用于标记上下文数据部分的位置
        self.register_field('reference_documents', function=self.handle_doc_info, is_context=True)
        self.register_field('session_records', function=self.handle_session_records, is_context=True)
        self.register_field('output_format', function=self.handle_output_format, title='Response Output Format', is_context=False)
        self.register_field('response', function=self.handle_response, is_context=False, omit_if_empty=False)
        
    def register_executor_fields(self):
        self.register_field('agent_profile', function=self.handle_agent_profile, is_context=False)
        self.register_field('tool_information', function=self.handle_tool_data, is_context=False)
        self.register_field('context_placeholder', is_context=True)  # 用于标记上下文数据部分的位置
        self.register_field('reference_documents', function=self.handle_doc_info, is_context=True)
        self.register_field('session_records', function=self.handle_session_records, is_context=True)
        self.register_field('current_plan', function=self.handle_current_plan, is_context=True)
        self.register_field('output_format', function=self.handle_output_format, title='Response Output Format', is_context=False)
        self.register_field('response', function=self.handle_response, is_context=False, omit_if_empty=False)
        
    def register_fields_from_dict(self, fields_dict):
        # 使用字典注册字段的函数
        for field_name, field_config in fields_dict.items():
            function_name = field_config.get('function', None)
            title = field_config.get('title', None)
            description = field_config.get('description', None)
            is_context = field_config.get('is_context', True)
            omit_if_empty = field_config.get('omit_if_empty', True)
            
            # 检查function_name是否是self的一个方法
            if function_name and hasattr(self, function_name):
                function = getattr(self, function_name)
            else:
                function = self.handle_custom_data
            
            # 调用已存在的register_field方法注册字段
            self.register_field(field_name, function=function, title=title, description=description, is_context=is_context, omit_if_empty=omit_if_empty)



def main():
    manager = PromptManager()
    manager.register_standard_fields()

    manager.register_field('agents_work_progress', title=f"Agents' Work Progress", is_context=True)

    # 创建数据字典
    data_dict = {
        "agent_profile": "这是代理配置文件...",
        # "tool_list": "这是工具列表...",
        "reference_documents": "这是参考文档...",
        "session_records": "这是会话记录...",
        "agents_work_progress": "这是代理工作进展...",
        "output_format": "这是预期的输出格式...",
        # "response": "这是生成或继续回应的指令...",
        "response": "",
        "test": 'xxxxx'
        }

    # 组合完整的提示
    full_prompt = manager.generate_full_prompt(data_dict)
    print(full_prompt)

if __name__ == "__main__":
    main()