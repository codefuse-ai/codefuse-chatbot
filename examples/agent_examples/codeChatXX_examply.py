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


phase_name = "codeChatPhase"
phase = BasePhase(phase_name,
            task = None,
            phase_config = PHASE_CONFIGS,
            chain_config = CHAIN_CONFIGS,
            role_config = AGETN_CONFIGS,
            do_summary=False,
            do_code_retrieval=True,
            do_doc_retrieval=False,
            do_search=False,
            )

# 代码一共有多少类 => 基于cypher
# 代码库里有哪些函数，返回5个就行 => 基于cypher
# remove 这个函数是做什么的  => 基于标签
# 有没有函数已经实现了从字符串删除指定字符串的功能，使用的话可以怎么使用，写个java代码  => 基于描述
# 有根据我以下的需求用 java 开发一个方法：输入为字符串，将输入中的 .java 字符串给删除掉，然后返回新的字符串 => 基于描述

# round-1
query_content = "代码一共有多少类"
query = Message(
    role_name="user", role_type="human", 
    role_content=query_content, input_query=query_content, origin_query=query_content,
    code_engine_name="client", score_threshold=1.0, top_k=3, cb_search_type="cypher"
    )

output_message1, _ = phase.step(query)
