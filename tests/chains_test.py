import os, sys, requests

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(src_dir)

from coagent.tools import (
    toLangchainTools, get_tool_schema, DDGSTool, DocRetrieval,
    TOOL_DICT, TOOL_SETS
    )

from configs.model_config import *
from coagent.connector.phase import BasePhase
from coagent.connector.agents import BaseAgent
from coagent.connector.chains import BaseChain
from coagent.connector.configs import AGETN_CONFIGS, CHAIN_CONFIGS, PHASE_CONFIGS
import importlib
from configs.model_config import JUPYTER_WORK_PATH, KB_ROOT_PATH
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig
from coagent.connector.configs import AGETN_CONFIGS
from coagent.connector.schema import Message, load_role_configs
print(src_dir)

# tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])

# TOOL_SETS = [
#      "StockInfo", "StockName"
#     ]

# tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])


# role_configs = load_role_configs(AGETN_CONFIGS)
# chain_configs = load_chain_configs(CHAIN_CONFIGS)
# phase_configs = load_phase_configs(PHASE_CONFIGS)

# agent_module = importlib.import_module("coagent.connector.agents")


# # agent的测试


# llm_config = LLMConfig(
#     model_name="gpt-3.5-turbo", model_device="cpu",api_key=os.environ["OPENAI_API_KEY"], 
#     api_base_url=os.environ["API_BASE_URL"], temperature=0.3
#     )
# embed_config = EmbedConfig(
#     embed_engine="model", embed_model="text2vec-base-chinese", 
#     embed_model_path="D://project/gitlab/llm/external/ant_code/Codefuse-chatbot/embedding_models/text2vec-base-chinese"
#     )

# # 从已有的配置中选择一个config，具体参数细节见下面
# role_configs = load_role_configs(AGETN_CONFIGS)
# agent_config = role_configs["general_planner"]
# # 生成agent实例
# base_agent = BaseAgent(
#     role=agent_config.role, 
#     prompt_config = agent_config.prompt_config,
#     prompt_manager_type=agent_config.prompt_manager_type,
#     chat_turn=agent_config.chat_turn,
#     focus_agents=[],
#     focus_message_keys=[],
#     llm_config=llm_config,
#     embed_config=embed_config,
#     jupyter_work_path=JUPYTER_WORK_PATH,
#     kb_root_path=KB_ROOT_PATH,
#     ) 
# # round-1
# query_content = "确认本地是否存在employee_data.csv，并查看它有哪些列和数据类型;然后画柱状图"
# query = Message(
#     role_name="human", role_type="user",
#     role_content=query_content, input_query=query_content, origin_query=query_content,
#     )
# output_message = base_agent.step(query)
# print(output_message.to_str_content(content_key="parsed_output_list"))



# chain的测试
llm_config = LLMConfig(
    model_name="gpt-3.5-turbo", api_key=os.environ["OPENAI_API_KEY"], 
    api_base_url=os.environ["API_BASE_URL"], temperature=0.3
    )
embed_config = EmbedConfig(
    embed_engine="model", embed_model="text2vec-base-chinese", 
    embed_model_path="D://project/gitlab/llm/external/ant_code/Codefuse-chatbot/embedding_models/text2vec-base-chinese"
    )


role_configs = load_role_configs(AGETN_CONFIGS)
agent_config = role_configs["general_planner"]


role1 = role_configs["general_planner"]
role2 = role_configs["executor"]
agent_module = importlib.import_module("coagent.connector.agents")
agents = [
    getattr(agent_module, role1.role.agent_type)(
            role=role1.role, 
            prompt_config = role1.prompt_config,
            prompt_manager_type=role1.prompt_manager_type,
            chat_turn=role1.chat_turn,
            focus_agents=role1.focus_agents,
            focus_message_keys=role1.focus_message_keys,
            llm_config=llm_config,
            embed_config=embed_config,
            jupyter_work_path=JUPYTER_WORK_PATH,
            kb_root_path=KB_ROOT_PATH,
        ),
    getattr(agent_module, role2.role.agent_type)(
            role=role2.role, 
            prompt_config = role2.prompt_config,
            prompt_manager_type=role2.prompt_manager_type,
            chat_turn=role2.chat_turn,
            focus_agents=role2.focus_agents,
            focus_message_keys=role2.focus_message_keys,
            llm_config=llm_config,
            embed_config=embed_config,
            jupyter_work_path=JUPYTER_WORK_PATH,
            kb_root_path=KB_ROOT_PATH,
        ),
    ]

chain = BaseChain(
    agents, 
    chat_turn=1, 
    jupyter_work_path=JUPYTER_WORK_PATH,
    kb_root_path=KB_ROOT_PATH,
    llm_config=llm_config,
    embed_config=embed_config,
    )


# round-1
query_content = "确认本地是否存在employee_data.csv，并查看它有哪些列和数据类型;然后画柱状图"
query = Message(
    role_name="human", role_type="user",
    role_content=query_content, input_query=query_content, origin_query=query_content,
    )

output_message, output_memory = chain.step(query)
print(output_memory.to_str_messages(content_key="parsed_output_list"))



# 测试 phase
# phase_name = "toolReactPhase"
# phase_name = "codeReactPhase"
# phase_name = "chatPhase"

# phase = BasePhase(phase_name,
#             task = None,
#             phase_config = PHASE_CONFIGS,
#             chain_config = CHAIN_CONFIGS,
#             role_config = AGETN_CONFIGS,
#             do_summary=False,
#             do_code_retrieval=False,
#             do_doc_retrieval=True,
#             do_search=False,
#             )

# query = Message(role_name="user", role_type="human", 
#                 input_query="确认本地是否存在employee_data.csv，并查看它有哪些列和数据类型，并选择合适的数值列画出折线图")


# phase_name = "baseTaskPhase"
# phase = BasePhase(phase_name,
#             task = None,
#             phase_config = PHASE_CONFIGS,
#             chain_config = CHAIN_CONFIGS,
#             role_config = AGETN_CONFIGS,
#             do_summary=False,
#             do_code_retrieval=False,
#             do_doc_retrieval=True,
#             do_search=False,
#             )

# query_content = "查询贵州茅台的股票代码，并查询截止到当前日期(2023年11月8日)的最近10天的每日时序数据，然后对时序数据画出折线图并分析"
# query_content = "判断下127.0.0.1这个服务器的在10点的监控数据，是否存在异常"
# query_content = "确认本地是否存在employee_data.csv，并查看它有哪些列和数据类型;然后画柱状图"

# query = Message(role_name="user", role_type="human", role_content=query_content, input_query=query_content,  origin_query=query_content, tools=tools)

# query = Message(role_name="human", role_type="human", input_query=query_content, role_content=query_content, origin_query=query_content)

# output_message = phase.step(query)

# print(phase.get_chains_memory(content_key="step_content"))
# print(phase.get_chains_memory_str(content_key="step_content"))
# print(output_message.to_tuple_message(return_all=True))


# from coagent.tools import DDGSTool, CodeRetrieval
# print(DDGSTool.run("langchain是什么", 3))
# print(CodeRetrieval.run("dsadsadsa", query.role_content, code_limit=3, history_node_list=[]))


# from dev_opsgpt.chat.agent_chat import AgentChat

# agentChat = AgentChat()
# value = {
#     "query": "帮我确认下127.0.0.1这个服务器的在10点是否存在异常，请帮我判断一下",
#     "phase_name": "toolReactPhase",
#     "chain_name": "",
#     "history": [],
#     "doc_engine_name": "DSADSAD",
#     "search_engine_name": "duckduckgo",
#     "code_engine_name": "",
#     "top_k": 3,
#     "score_threshold": 1.0,
#     "stream": False,
#     "local_doc_url": False,
#     "do_search": False,
#     "do_doc_retrieval": False,
#     "do_code_retrieval": False,
#     "do_tool_retrieval": False,
#     "custom_phase_configs": {},
#     "custom_chain_configs": {},
#     "custom_role_configs": {},
#     "choose_tools": list(TOOL_SETS),
#     "history_node_list": [],
#     "isDetailed": False,
#     "upload_file": ""
# }


# for answer in agentChat.achat(**value):
#     print("answer:", answer)