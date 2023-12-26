from pydantic import BaseModel
from loguru import logger

from .general_schema import *


class Message(BaseModel):
    chat_index: str = None
    role_name: str
    role_type: str
    role_prompt: str = None
    input_query: str = None
    origin_query: str = None

    # llm output
    role_content: str = None
    step_content: str = None

    # llm parsed information
    plans: List[str] = None
    code_content: str = None
    code_filename: str = None
    tool_params: str = None
    tool_name: str = None
    parsed_output: dict = {}
    spec_parsed_output: dict = {}
    parsed_output_list: List[Dict] = []

    # llm\tool\code executre information
    action_status: str = ActionStatus.DEFAUILT
    agent_index: int = None
    code_answer: str = None
    tool_answer: str = None
    observation: str = None
    figures: Dict[str, str] = {}

    # prompt support information
    tools: List[BaseTool] = []
    task: Task = None
    db_docs: List['Doc'] = []
    code_docs: List['CodeDoc'] = []
    search_docs: List['Doc'] = []
    agents: List = []

    # phase input
    phase_name: str = None
    chain_name: str = None
    do_search: bool = False
    doc_engine_name: str = None
    code_engine_name: str = None
    cb_search_type: str = None
    search_engine_name: str = None 
    top_k: int = 3
    score_threshold: float = 1.0
    do_doc_retrieval: bool = False
    do_code_retrieval: bool = False
    do_tool_retrieval: bool = False
    history_node_list: List[str] = []
    # user's customed kargs for init or end action
    customed_kargs: dict = {}

    def to_tuple_message(self, return_all: bool = True, content_key="role_content"):
        role_content = self.to_str_content(False, content_key)
        if return_all:
            return (self.role_name, role_content)
        else:
            return (role_content)
    
    def to_dict_message(self, return_all: bool = True, content_key="role_content"):
        role_content = self.to_str_content(False, content_key)
        if return_all:
            return {"role": self.role_name, "content": role_content}
        else:
            return vars(self)
        
    def to_str_content(self, return_all: bool = True, content_key="role_content"):
        if content_key == "role_content":
            role_content = self.role_content or self.input_query
        elif content_key == "step_content":
            role_content  = self.step_content or self.role_content or self.input_query
        else:
            role_content = self.role_content or self.input_query

        if return_all:
            return f"{self.role_name}: {role_content}"
        else:
            return role_content
    
    def is_system_role(self,):
        return self.role_type == "system"
    
    def __str__(self) -> str:
        # key_str = '\n'.join([k for k, v in vars(self).items()])
        # logger.debug(f"{key_str}")
        return "\n".join([": ".join([k, str(v)]) for k, v in vars(self).items()])
    