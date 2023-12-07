import os, sys

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(src_dir)

from configs.model_config import *
from dev_opsgpt.connector.phase import BasePhase
from dev_opsgpt.connector.agents import BaseAgent
from dev_opsgpt.connector.chains import BaseChain
from dev_opsgpt.connector.schema import (
    Message, load_role_configs, load_phase_configs, load_chain_configs
    )
from dev_opsgpt.connector.configs import AGETN_CONFIGS, CHAIN_CONFIGS, PHASE_CONFIGS
import importlib


role_configs = load_role_configs(AGETN_CONFIGS)
chain_configs = load_chain_configs(CHAIN_CONFIGS)
phase_configs = load_phase_configs(PHASE_CONFIGS)

agent_module = importlib.import_module("dev_opsgpt.connector.agents")


phase_name = "metagpt_code_devlop"
phase = BasePhase(phase_name,
            task = None,
            phase_config = PHASE_CONFIGS,
            chain_config = CHAIN_CONFIGS,
            role_config = AGETN_CONFIGS,
            do_summary=False,
            do_code_retrieval=False,
            do_doc_retrieval=True,
            do_search=False,
            )

query_content = "create a snake game"
query = Message(role_name="human", role_type="user", input_query=query_content, role_content=query_content, origin_query=query_content)

output_message = phase.step(query)
