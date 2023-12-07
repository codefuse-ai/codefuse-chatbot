from typing import List
from loguru import logger
import copy
from dev_opsgpt.connector.agents import BaseAgent
from .base_chain import BaseChain

from dev_opsgpt.connector.agents import BaseAgent, CheckAgent
from dev_opsgpt.connector.schema import (
    Memory, Role, Message, ActionStatus, ChainConfig,
    load_role_configs
)



class ExecutorRefineChain(BaseChain):

    def __init__(self, agents: List[BaseAgent], do_code_exec: bool = False) -> None:
        super().__init__(agents, do_code_exec)
