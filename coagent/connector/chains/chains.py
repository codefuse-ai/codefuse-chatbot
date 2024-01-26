from typing import List
from loguru import logger
from coagent.connector.agents import BaseAgent
from .base_chain import BaseChain




class ExecutorRefineChain(BaseChain):

    def __init__(self, agents: List[BaseAgent], do_code_exec: bool = False) -> None:
        super().__init__(agents, do_code_exec)
