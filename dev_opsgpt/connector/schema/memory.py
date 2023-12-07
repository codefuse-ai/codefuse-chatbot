from pydantic import BaseModel
from typing import List, Union
from loguru import logger

from .message import Message
from dev_opsgpt.utils.common_utils import (
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

    def save(self, file_type="jsonl", return_all=True):
        try:
            if file_type == "jsonl":
                save_to_jsonl_file(self.to_dict_messages(return_all=return_all), "role_name_history"+f".{file_type}")
                return True
            elif file_type in ["json", "txt"]:
                save_to_json_file(self.to_dict_messages(return_all=return_all), "role_name_history"+f".{file_type}")
                return True
        except:
            return False
        return False

    def load(self, filepath):
        file_type = filepath
        try:
            if file_type == "jsonl":
                self.messages = [Message(**message) for message in read_jsonl_file(filepath)]
                return True
            elif file_type in ["json", "txt"]:
                self.messages = [Message(**message) for message in read_jsonl_file(filepath)]
                return True
        except:
            return False
        
        return False
    
    def to_tuple_messages(self, return_all: bool = True, content_key="role_content", filter_roles=[]):
        # logger.debug(f"{[message.to_tuple_message(return_all, content_key) for message in self.messages  ]}")
        return [
            message.to_tuple_message(return_all, content_key) for message in self.messages 
            if message.role_name not in filter_roles
            ]
    
    def to_dict_messages(self, return_all: bool = True, content_key="role_content", filter_roles=[]):
        return [
            message.to_dict_message(return_all, content_key) for message in self.messages 
            if message.role_name not in filter_roles
            ]
    
    def to_str_messages(self, return_all: bool = True, content_key="role_content", filter_roles=[]):
        # for message in self.messages:
        #     logger.debug(f"{message.to_tuple_message(return_all, content_key)}")
        # logger.debug(f"{[message.to_tuple_message(return_all, content_key) for message in self.messages  ]}")
        return "\n\n".join([message.to_str_content(return_all, content_key) for message in self.messages 
            if message.role_name not in filter_roles
            ])
    
    def get_parserd_output(self, ):
        return [message.parsed_output for message in self.messages]
    
    def get_parserd_output_list(self, ):
        # for message in self.messages:
        #     logger.debug(f"{message.role_name}: {message.parsed_output_list}")
        return [parsed_output for message in self.messages for parsed_output in message.parsed_output_list[1:]]
    
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
        
    
    