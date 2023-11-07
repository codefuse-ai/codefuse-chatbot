import os, sys, requests

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
from dev_opsgpt.connector.connector_schema import (
    Message, load_role_configs, load_phase_configs, load_chain_configs
    )
from dev_opsgpt.connector.configs import AGETN_CONFIGS, CHAIN_CONFIGS, PHASE_CONFIGS
import importlib

print(src_dir)

tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])

role_configs = load_role_configs(AGETN_CONFIGS)
chain_configs = load_chain_configs(CHAIN_CONFIGS)
phase_configs = load_phase_configs(PHASE_CONFIGS)

agent_module = importlib.import_module("dev_opsgpt.connector.agents")


# agent的测试
query = Message(role_name="tool_react", role_type="human", 
                role_content="我有一份时序数据，[0.857, 2.345, 1.234, 4.567, 3.456, 9.876, 5.678, 7.890, 6.789, 8.901, 10.987, 12.345, 11.234, 14.567, 13.456, 19.876, 15.678, 17.890, 16.789, \
                    18.901, 20.987, 22.345, 21.234, 24.567, 23.456, 29.876, 25.678, 27.890, 26.789, 28.901, 30.987, 32.345, 31.234, 34.567, 33.456, 39.876, 35.678, 37.890, 36.789, 38.901, 40.987]，\
                        我不知道这份数据是否存在问题，请帮我判断一下", tools=tools)

query = Message(role_name="tool_react", role_type="human", 
                role_content="帮我确认下127.0.0.1这个服务器的在10点是否存在异常，请帮我判断一下", tools=tools)

query = Message(role_name="code_react", role_type="human", 
                role_content="帮我确认当前目录下有哪些文件", tools=tools)

# "给我一份冒泡排序的代码"
query = Message(role_name="intention_recognizer", role_type="human", 
                role_content="对employee_data.csv进行数据分析", tools=tools)

# role = role_configs["general_planner"]
# agent_class = getattr(agent_module, role.role.agent_type)
# agent = agent_class(role.role,
#             task = None,
#             memory = None,
#             chat_turn=role.chat_turn,
#             do_search = role.do_search,
#             do_doc_retrieval = role.do_doc_retrieval,
#             do_tool_retrieval = role.do_tool_retrieval,)

# message = agent.run(query)
# print(message.role_content)


# chain的测试

# query = Message(role_name="deveploer", role_type="human", role_content="编写冒泡排序，并生成测例")
# query = Message(role_name="general_planner", role_type="human", role_content="对employee_data.csv进行数据分析")
# query = Message(role_name="tool_react", role_type="human", role_content="我有一份时序数据，[0.857, 2.345, 1.234, 4.567, 3.456, 9.876, 5.678, 7.890, 6.789, 8.901, 10.987, 12.345, 11.234, 14.567, 13.456, 19.876, 15.678, 17.890, 16.789, 18.901, 20.987, 22.345, 21.234, 24.567, 23.456, 29.876, 25.678, 27.890, 26.789, 28.901, 30.987, 32.345, 31.234, 34.567, 33.456, 39.876, 35.678, 37.890, 36.789, 38.901, 40.987]，\我不知道这份数据是否存在问题，请帮我判断一下", tools=tools)

# role = role_configs[query.role_name]
role1 = role_configs["planner"]
role2 = role_configs["code_react"]

agents = [
    getattr(agent_module, role1.role.agent_type)(role1.role,
                task = None,
                memory = None,
                do_search = role1.do_search,
                do_doc_retrieval = role1.do_doc_retrieval,
                do_tool_retrieval = role1.do_tool_retrieval,),
    getattr(agent_module, role2.role.agent_type)(role2.role,
                task = None,
                memory = None,
                do_search = role2.do_search,
                do_doc_retrieval = role2.do_doc_retrieval,
                do_tool_retrieval = role2.do_tool_retrieval,),
                ]

query = Message(role_name="user", role_type="human", 
                role_content="确认本地是否存在employee_data.csv，并查看它有哪些列和数据类型，分析这份数据的内容，根据这个数据预测未来走势", tools=tools)
query = Message(role_name="user", role_type="human", 
                role_content="确认本地是否存在employee_data.csv，并查看它有哪些列和数据类型", tools=tools)
chain = BaseChain(chain_configs["dataAnalystChain"], agents, do_code_exec=False)

# message = chain.step(query)
# print(message.role_content)

# print("\n".join("\n".join([": ".join(j) for j in i]) for i in chain.get_agents_memory()))
# print("\n".join(": ".join(i) for i in chain.get_memory()))
# print( chain.get_agents_memory_str())
# print( chain.get_memory_str())




# 测试 phase
phase_name = "toolReactPhase"
# phase_name = "codeReactPhase"
# phase_name = "chatPhase"

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

query = Message(role_name="user", role_type="human", 
                role_content="确认本地是否存在employee_data.csv，并查看它有哪些列和数据类型，并选择合适的数值列画出折线图")

query = Message(role_name="user", role_type="human", 
                role_content="判断下127.0.0.1这个服务器的在10点的监控数据，是否存在异常", tools=tools)

# 根据其他类似的类，新开发个 ExceptionComponent2，继承 AbstractTrafficComponent
# query = Message(role_name="human", role_type="human", role_content="langchain有什么用")

# output_message = phase.step(query)

# print(phase.get_chains_memory(content_key="step_content"))
# print(phase.get_chains_memory_str(content_key="step_content"))
# print(output_message.to_tuple_message(return_all=True))


from dev_opsgpt.tools import DDGSTool, CodeRetrieval
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
#     "choose_tools": list(TOOL_SETS)
# }

# answer = agentChat.chat(**value)
# print(answer)