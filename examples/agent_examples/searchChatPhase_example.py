import os, sys, requests

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(src_dir)

from dev_opsgpt.tools import (
    toLangchainTools, get_tool_schema, DDGSTool, DocRetrieval,
    TOOL_DICT, TOOL_SETS
    )

from configs.model_config import *
from dev_opsgpt.connector.phase import BasePhase
from dev_opsgpt.connector.agents import BaseAgent
from dev_opsgpt.connector.chains import BaseChain
from dev_opsgpt.connector.schema import (
    Message, Memory, load_role_configs, load_phase_configs, load_chain_configs
    )
from dev_opsgpt.connector.configs import AGETN_CONFIGS, CHAIN_CONFIGS, PHASE_CONFIGS
import importlib

tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])


role_configs = load_role_configs(AGETN_CONFIGS)
chain_configs = load_chain_configs(CHAIN_CONFIGS)
phase_configs = load_phase_configs(PHASE_CONFIGS)

agent_module = importlib.import_module("dev_opsgpt.connector.agents")


phase_name = "searchChatPhase"
phase = BasePhase(phase_name,
            task = None,
            phase_config = PHASE_CONFIGS,
            chain_config = CHAIN_CONFIGS,
            role_config = AGETN_CONFIGS,
            do_summary=False,
            do_code_retrieval=False,
            do_doc_retrieval=False,
            do_search=True,
            )

# round-1
query_content = "美国当前总统是谁？"
query = Message(
    role_name="user", role_type="human", 
    role_content=query_content, input_query=query_content, origin_query=query_content,
    search_engine_name="duckduckgo", score_threshold=1.0, top_k=3
    )

output_message, _ = phase.step(query)

# round-2
history = Memory(messages=[
            Message(role_name="user", role_type="human", role_content="美国当前总统是谁？"),
            Message(role_name="ai", role_type="assistant", role_content=output_message.step_content),
            ])

query_content = "美国上一任总统是谁，两个人有什么关系没？"
query = Message(
    role_name="human", role_type="user", 
    role_content=query_content, input_query=query_content, origin_query=query_content,
    search_engine_name="duckduckgo", score_threshold=1.0, top_k=3
    )
output_message, _ = phase.step(query)