from pydantic import BaseModel
from typing import List, Union, Dict
from loguru import logger

from .message import Message
from coagent.utils.common_utils import (
    save_to_jsonl_file, save_to_json_file, read_json_file, read_jsonl_file
)


class Memory(BaseModel):
    messages: List[Message] = []

    # def __init__(self, messages: List[Message] = []):
    #     self.messages = messages

    def append(self, message: Message):
        self.messages.append(message)

    def extend(self, memory: 'Memory'):
        self.messages.extend(memory.messages)

    def update(self, role_name: str, role_type: str, role_content: str):
        self.messages.append(Message(role_name, role_type, role_content, role_content))

    def clear(self, ):
        self.messages = []

    def delete(self, ):
        pass

    def get_messages(self, k=0) -> List[Message]:
        """Return the most recent k memories, return all when k=0"""
        return self.messages[-k:]
    
    def split_by_role_type(self) -> List[Dict[str, 'Memory']]:
        """
        Split messages into rounds of conversation based on role_type.
        Each round consists of consecutive messages of the same role_type.
        User messages form a single round, while assistant and function messages are combined into a single round.
        Each round is represented by a dict with 'role' and 'memory' keys, with assistant and function messages
        labeled as 'assistant'.
        """
        rounds = []
        current_memory = Memory()
        current_role = None
        
        logger.debug(len(self.messages))

        for msg in self.messages:
            # Determine the message's role, considering 'function' as 'assistant'
            message_role = 'assistant' if msg.role_type in ['assistant', 'function'] else 'user'
            
            # If the current memory is empty or the current message is of the same role_type as current_role, add to current memory
            if not current_memory.messages or current_role == message_role:
                current_memory.append(msg)
            else:
                # Finish the current memory and start a new one
                rounds.append({'role': current_role, 'memory': current_memory})
                current_memory = Memory()
                current_memory.append(msg)
            
            # Update the current_role, considering 'function' as 'assistant'
            current_role = message_role

        # Don't forget to add the last memory if it exists
        if current_memory.messages:
            rounds.append({'role': current_role, 'memory': current_memory})
            
        logger.debug(rounds)
        
        return rounds

    def format_rounds_to_html(self) -> str:
        formatted_html_str = ""
        rounds = self.split_by_role_type()

        for round in rounds:
            role = round['role']
            memory = round['memory']
            
            # 转换当前round的Memory为字符串
            messages_str = memory.to_str_messages()

            # 根据角色类型添加相应的HTML标签
            if role == 'user':
                formatted_html_str += f"<user-message>\n{messages_str}\n</user-message>\n"
            else:  # 对于'assistant'和'function'角色，我们将其视为'assistant'
                formatted_html_str += f"<assistant-message>\n{messages_str}\n</assistant-message>\n"

        return formatted_html_str
    

    def filter_by_role_type(self, role_types: List[str]) -> List[Message]:
        # Filter messages based on role types
        return [message for message in self.messages if message.role_type not in role_types]

    def select_by_role_type(self, role_types: List[str]) -> List[Message]:
        # Select messages based on role types
        return [message for message in self.messages if message.role_type in role_types]
    
    def to_tuple_messages(self, return_all: bool = True, content_key="role_content", filter_roles=[]):
        # Convert messages to tuples based on parameters
        # logger.debug(f"{[message.to_tuple_message(return_all, content_key) for message in self.messages  ]}")
        return [
            message.to_tuple_message(return_all, content_key) for message in self.messages 
            if message.role_name not in filter_roles
            ]
    
    def to_dict_messages(self, filter_roles=[]):
        # Convert messages to dictionaries based on filter roles
        return [
            message.to_dict_message() for message in self.messages 
            if message.role_name not in filter_roles
            ]
    
    def to_str_messages(self, return_all: bool = True, content_key="role_content", filter_roles=[], with_tag=False):
        # Convert messages to strings based on parameters
        # for message in self.messages:
        #     logger.debug(f"{message.role_name}: {message.to_str_content(return_all, content_key, with_tag=with_tag)}")
        # logger.debug(f"{[message.to_tuple_message(return_all, content_key) for message in self.messages  ]}")
        return "\n\n".join([message.to_str_content(return_all, content_key, with_tag=with_tag) for message in self.messages 
            if message.role_name not in filter_roles
            ])
    
    def get_parserd_output(self, ):
        return [message.parsed_output for message in self.messages]
    
    def get_parserd_output_list(self, ):
        # for message in self.messages:
        #     logger.debug(f"{message.role_name}: {message.parsed_output_list}")
        # return [parsed_output for message in self.messages for parsed_output in message.parsed_output_list[1:]]
        return [parsed_output for message in self.messages for parsed_output in message.parsed_output_list]
    
    def get_rolenames(self, ):
        ''''''
        return [message.role_name for message in self.messages]
    
    @classmethod
    def from_memory_list(cls, memorys: List['Memory']) -> 'Memory':
        return cls(messages=[message for memory in memorys for message in memory.get_messages()])
    
    def __len__(self, ):
        return len(self.messages)

    def __str__(self) -> str:
        return "\n".join([":".join(i) for i in self.to_tuple_messages()])
    
    def __add__(self, other: Union[Message, 'Memory']) -> 'Memory':
        if isinstance(other, Message):
            return Memory(messages=self.messages + [other])
        elif isinstance(other, Memory):
            return Memory(messages=self.messages + other.messages)
        else:
            raise ValueError(f"cant add unspecified type like as {type(other)}")
        
    
    