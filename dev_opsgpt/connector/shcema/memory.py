from pydantic import BaseModel
from typing import List
from loguru import logger

from dev_opsgpt.connector.connector_schema import Message
from dev_opsgpt.utils.common_utils import (
    save_to_jsonl_file, save_to_json_file, read_json_file, read_jsonl_file
)


class Memory:
    
    def __init__(self, messages: List[Message] = []):
        self.messages = messages

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

    def get_messages(self, ) -> List[Message]:
        return self.messages

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
    
    def to_tuple_messages(self, return_system: bool = False, return_all: bool = False, content_key="role_content"):
        # logger.debug(f"{[message.to_tuple_message(return_all, content_key) for message in self.messages  ]}")
        return [
            message.to_tuple_message(return_all, content_key) for message in self.messages 
            if not message.is_system_role() |  return_system
            ]
    
    def to_dict_messages(self, return_system: bool = False, return_all: bool = False, content_key="role_content"):
        return [
            message.to_dict_message(return_all, content_key) for message in self.messages 
            if not message.is_system_role() |  return_system
            ]
    
    def to_str_messages(self, return_system: bool = False, return_all: bool = False, content_key="role_content"):
        # logger.debug(f"{[message.to_tuple_message(return_all, content_key) for message in self.messages  ]}")
        return "\n".join([
            ": ".join(message.to_tuple_message(return_all, content_key)) for message in self.messages 
            if not message.is_system_role() |  return_system
            ])
    
    @classmethod
    def from_memory_list(cls, memorys: List['Memory']) -> 'Memory':
        return cls([message for memory in memorys for message in memory.get_messages()])
    
    def __len__(self, ):
        return len(self.messages)

    def __str__(self) -> str:
        return "\n".join([":".join(i) for i in self.to_tuple_messages()])