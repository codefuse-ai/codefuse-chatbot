from pydantic import BaseModel
from typing import List, Dict
from enum import Enum
import re
import json
from loguru import logger
from langchain.tools import BaseTool


class ActionStatus(Enum):
    DEFAUILT = "default"

    FINISHED = "finished"
    STOPED = "stoped"
    CONTINUED = "continued"

    TOOL_USING = "tool_using"
    CODING = "coding"
    CODE_EXECUTING = "code_executing"
    CODING2FILE = "coding2file"

    PLANNING = "planning"
    UNCHANGED = "unchanged"
    ADJUSTED = "adjusted"
    CODE_RETRIEVAL = "code_retrieval"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value.lower() == other.lower()
        return super().__eq__(other)
    

class Action(BaseModel):
    action_name: str
    description: str

class FinishedAction(Action):
    action_name: str = ActionStatus.FINISHED
    description: str = "provide the final answer to the original query to break the chain answer"

class StopedAction(Action):
    action_name: str = ActionStatus.STOPED
    description: str = "provide the final answer to the original query to break the agent answer"

class ContinuedAction(Action):
    action_name: str = ActionStatus.CONTINUED
    description: str = "cant't provide the final answer to the original query"

class ToolUsingAction(Action):
    action_name: str = ActionStatus.TOOL_USING
    description: str = "proceed with using the specified tool."

class CodingdAction(Action):
    action_name: str = ActionStatus.CODING
    description: str = "provide the answer by writing code"

class Coding2FileAction(Action):
    action_name: str = ActionStatus.CODING2FILE
    description: str = "provide the answer by writing code and filename"

class CodeExecutingAction(Action):
    action_name: str = ActionStatus.CODE_EXECUTING
    description: str = "provide the answer by writing executable code"

class PlanningAction(Action):
    action_name: str = ActionStatus.PLANNING
    description: str = "provide a sequence of tasks"

class UnchangedAction(Action):
    action_name: str = ActionStatus.UNCHANGED
    description: str = "this PLAN has no problem, just set PLAN_STEP to CURRENT_STEP+1."

class AdjustedAction(Action):
    action_name: str = ActionStatus.ADJUSTED
    description: str = "the PLAN is to provide an optimized version of the original plan."

# extended action exmaple
class CodeRetrievalAction(Action):
    action_name: str = ActionStatus.CODE_RETRIEVAL
    description: str = "execute the code retrieval to acquire more code information"


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


class PromptKey(BaseModel):
    key_name: str
    description: str

class PromptKeyEnums(Enum):
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
    SELF_LOCAL_MEMORY = "self_local_memory"
    # chain memory
    CHAIN_LOCAL_MEMORY = "chain_local_memory"
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
    group_agents: List = []


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