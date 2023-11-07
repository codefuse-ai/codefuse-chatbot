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
    chat_turn: int = 1
    do_search: bool =  False
    do_doc_retrieval: bool = False
    do_tool_retrieval: bool = False


class PhaseConfig(BaseModel):
    phase_name: str
    phase_type: str
    chains: List[str]
    do_summary: bool = False
    do_search: bool =  False
    do_doc_retrieval: bool = False
    do_code_retrieval: bool = False
    do_tool_retrieval: bool = False

class Message(BaseModel):
    role_name: str
    role_type: str
    role_prompt: str = None
    input_query: str = None

    # 模型最终返回
    role_content: str = None
    role_contents: List[str] = []
    step_content: str = None
    step_contents: List[str] = []
    chain_content: str = None
    chain_contents: List[str] = []

    # 模型结果解析
    plans: List[str] = None
    code_content: str = None
    code_filename: str = None
    tool_params: str = None
    tool_name: str = None

    # 执行结果
    action_status: str = ActionStatus.DEFAUILT
    code_answer: str = None
    tool_answer: str = None
    observation: str = None
    figures: Dict[str, str] = {}

    # 辅助信息
    tools: List[BaseTool] = []
    task: Task = None
    db_docs: List['Doc'] = []
    code_docs: List['CodeDoc'] = []
    search_docs: List['Doc'] = []

    # 执行输入
    phase_name: str = None
    chain_name: str = None
    do_search: bool = False
    doc_engine_name: str = None
    code_engine_name: str = None
    search_engine_name: str = None 
    top_k: int = 3
    score_threshold: float = 1.0
    do_doc_retrieval: bool = False
    do_code_retrieval: bool = False
    do_tool_retrieval: bool = False
    history_node_list: List[str] = []


    def to_tuple_message(self, return_all: bool = False, content_key="role_content"):
        if content_key == "role_content":
            role_content = self.role_content
        elif content_key == "step_content":
            role_content  = self.step_content or self.role_content
        else:
            role_content =self.role_content

        if return_all:
            return (self.role_name, self.role_type, role_content)
        else:
            return (self.role_name, role_content)
            return (self.role_type, re.sub("}", "}}", re.sub("{", "{{", str(self.role_content))))
    
    def to_dict_message(self, return_all: bool = False, content_key="role_content"):
        if content_key == "role_content":
            role_content =self.role_content
        elif content_key == "step_content":
            role_content  = self.step_content or self.role_content
        else:
            role_content =self.role_content

        if return_all:
            return vars(self)
        else:
            return {"role": self.role_name, "content": role_content}
    
    def is_system_role(self,):
        return self.role_type == "system"
    
    def __str__(self) -> str:
        # key_str = '\n'.join([k for k, v in vars(self).items()])
        # logger.debug(f"{key_str}")
        return "\n".join([": ".join([k, str(v)]) for k, v in vars(self).items()])
    


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