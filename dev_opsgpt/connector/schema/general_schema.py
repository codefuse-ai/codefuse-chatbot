from pydantic import BaseModel
from typing import List, Dict
from enum import Enum
import re
import json
from loguru import logger
from langchain.tools import BaseTool


class ActionStatus(Enum):
    FINISHED = "finished"
    CODING = "coding"
    TOOL_USING = "tool_using"
    REASONING = "reasoning"
    PLANNING = "planning"
    EXECUTING_CODE = "executing_code"
    EXECUTING_TOOL = "executing_tool"
    DEFAUILT = "default"
    CODING2FILE = "coding2file"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)
    

class RoleTypeEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    OBSERVATION = "observation"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)


class InputKeyEnums(Enum):
    # Origin Query is ui's user question
    ORIGIN_QUERY = "origin_query"
    # agent's input from last agent
    CURRENT_QUESTION = "current_question"
    # ui memory contaisn (user and assistants)
    UI_MEMORY = "ui_memory"
    # agent's memory
    SELF_MEMORY = "self_memory"
    # chain memory
    CHAIN_MEMORY = "chain_memory"
    # agent's memory
    SELF_ONE_MEMORY = "self_one_memory"
    # chain memory
    CHAIN_ONE_MEMORY = "chain_one_memory"
    # Doc Infomations contains (Doc\Code\Search)
    DOC_INFOS = "doc_infos"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)


class Doc(BaseModel):
    title: str
    snippet: str
    link: str
    index: int

    def get_title(self):
        return self.title

    def get_snippet(self, ):
        return self.snippet

    def get_link(self, ):
        return self.link

    def get_index(self, ):
        return self.index
    
    def to_json(self):
        return vars(self)
    
    def __str__(self,):
        return f"""出处 [{self.index + 1}] 标题 [{self.title}]\n\n来源 ({self.link}) \n\n内容 {self.snippet}\n\n"""


class CodeDoc(BaseModel):
    code: str
    related_nodes: list
    index: int

    def get_code(self, ):
        return self.code

    def get_related_node(self, ):
        return self.related_nodes

    def get_index(self, ):
        return self.index
    
    def to_json(self):
        return vars(self)
    
    def __str__(self,):
        return f"""出处 [{self.index + 1}] \n\n来源 ({self.related_nodes}) \n\n内容 {self.code}\n\n"""


class Docs:

    def __init__(self, docs: List[Doc]):
        self.titles: List[str] = [doc.get_title() for doc in docs]
        self.snippets: List[str] = [doc.get_snippet() for doc in docs]
        self.links: List[str] = [doc.get_link() for doc in docs]
        self.indexs: List[int] = [doc.get_index() for doc in docs]

class Task(BaseModel):
    task_type: str
    task_name: str
    task_desc: str
    task_prompt: str
    # def __init__(self, task_type, task_name, task_desc) -> None:
    #     self.task_type = task_type
    #     self.task_name = task_name
    #     self.task_desc = task_desc

class Env(BaseModel):
    env_type: str
    env_name: str
    env_desc:str


class Role(BaseModel):
    role_type: str
    role_name: str
    role_desc: str
    agent_type: str = ""
    role_prompt: str = ""
    template_prompt: str = ""



class ChainConfig(BaseModel):
    chain_name: str
    chain_type: str
    agents: List[str]
    do_checker: bool = False
    chat_turn: int = 1
    clear_structure: bool = False
    brainstorming: bool = False
    gui_design: bool = True
    git_management: bool = False
    self_improve: bool = False


class AgentConfig(BaseModel):
    role: Role
    stop: str = None
    chat_turn: int = 1
    do_search: bool =  False
    do_doc_retrieval: bool = False
    do_tool_retrieval: bool = False
    focus_agents: List = []
    focus_message_keys: List = []


class PhaseConfig(BaseModel):
    phase_name: str
    phase_type: str
    chains: List[str]
    do_summary: bool = False
    do_search: bool =  False
    do_doc_retrieval: bool = False
    do_code_retrieval: bool = False
    do_tool_retrieval: bool = False


def load_role_configs(config) -> Dict[str, AgentConfig]:
    if isinstance(config, str):
        with open(config, 'r', encoding="utf8") as file:
            configs = json.load(file)
    else:
        configs = config

    return {name: AgentConfig(**v) for name, v in configs.items()}


def load_chain_configs(config) -> Dict[str, ChainConfig]:
    if isinstance(config, str):
        with open(config, 'r', encoding="utf8") as file:
            configs = json.load(file)
    else:
        configs = config
    return {name: ChainConfig(**v) for name, v in configs.items()}


def load_phase_configs(config) -> Dict[str, PhaseConfig]:
    if isinstance(config, str):
        with open(config, 'r', encoding="utf8") as file:
            configs = json.load(file)
    else:
        configs = config
    return {name: PhaseConfig(**v) for name, v in configs.items()}