import os, sys, requests

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
# src_dir = os.path.join(
#     os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# )
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
    Message, load_role_configs, load_phase_configs, load_chain_configs
    )
from dev_opsgpt.connector.configs import AGETN_CONFIGS, CHAIN_CONFIGS, PHASE_CONFIGS
import importlib

print(src_dir)

# tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])

TOOL_SETS = [
     "StockName", "StockInfo", 
    ]

tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])


role_configs = load_role_configs(AGETN_CONFIGS)
chain_configs = load_chain_configs(CHAIN_CONFIGS)
phase_configs = load_phase_configs(PHASE_CONFIGS)

agent_module = importlib.import_module("dev_opsgpt.connector.agents")

phase_name = "codeToolReactPhase"
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

query_content = "查询贵州茅台的股票代码，并查询截止到当前日期(2023年12月24日)的最近10天的每日时序数据，然后对时序数据画出折线图并分析"

query = Message(role_name="human", role_type="user", input_query=query_content, role_content=query_content, origin_query=query_content, tools=tools)

output_message = phase.step(query)