from typing import List
from dev_opsgpt.connector.agents import BaseAgent
from .base_chain import BaseChain



class simpleChatChain(BaseChain):

    def __init__(self, agents: List[BaseAgent], do_code_exec: bool = False) -> None:
        super().__init__(agents, do_code_exec)


class toolChatChain(BaseChain):

    def __init__(self, agents: List[BaseAgent], do_code_exec: bool = False) -> None:
        super().__init__(agents, do_code_exec)


class dataAnalystChain(BaseChain):

    def __init__(self, agents: List[BaseAgent], do_code_exec: bool = False) -> None:
        super().__init__(agents, do_code_exec)


class plannerChain(BaseChain):

    def __init__(self, agents: List[BaseAgent], do_code_exec: bool = False) -> None:
        super().__init__(agents, do_code_exec)
