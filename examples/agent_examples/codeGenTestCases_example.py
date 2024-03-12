import os, sys, json
from loguru import logger
src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(src_dir)

from configs.model_config import KB_ROOT_PATH, JUPYTER_WORK_PATH, CB_ROOT_PATH
from configs.server_config import SANDBOX_SERVER
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig

from coagent.connector.phase import BasePhase
from coagent.connector.agents import BaseAgent
from coagent.connector.schema import Message
from coagent.codechat.codebase_handler.codebase_handler import CodeBaseHandler

import importlib
from loguru import logger


from coagent.tools import CodeRetrievalSingle, RelatedVerticesRetrival, Vertex2Code

# 定义一个新的agent类
class CodeRetrieval(BaseAgent):

    def start_action_step(self, message: Message) -> Message:
        '''do action before agent predict '''
        # 根据问题获取代码片段和节点信息
        action_json = CodeRetrievalSingle.run(message.code_engine_name, message.origin_query, llm_config=self.llm_config, embed_config=self.embed_config, search_type="tag", 
                                              local_graph_path=message.local_graph_path, use_nh=message.use_nh)
        current_vertex = action_json['vertex']
        message.customed_kargs["Code Snippet"] = action_json["code"]
        message.customed_kargs['Current_Vertex'] = current_vertex

        # 获取邻近节点
        action_json = RelatedVerticesRetrival.run(message.code_engine_name, message.customed_kargs['Current_Vertex'])
        # 获取邻近节点所有代码
        relative_vertex = []
        retrieval_Codes = []
        for vertex in action_json["vertices"]:
            # 由于代码是文件级别，所以相同文件代码不再获取
            # logger.debug(f"{current_vertex}, {vertex}")
            current_vertex_name = current_vertex.replace("#", "").replace(".java", "" ) if current_vertex.endswith(".java") else current_vertex
            if current_vertex_name.split("#")[0] == vertex.split("#")[0]: continue

            action_json = Vertex2Code.run(message.code_engine_name, vertex)
            if action_json["code"]:
                retrieval_Codes.append(action_json["code"])
                relative_vertex.append(vertex)
        # 
        message.customed_kargs["Retrieval_Codes"] = retrieval_Codes
        message.customed_kargs["Relative_vertex"] = relative_vertex
        return message


# add agent or prompt_manager class
agent_module = importlib.import_module("coagent.connector.agents")
setattr(agent_module, 'CodeRetrieval', CodeRetrieval)



llm_config = LLMConfig(
    model_name="gpt-4", api_key=os.environ["OPENAI_API_KEY"], 
    api_base_url=os.environ["API_BASE_URL"], temperature=0.3
)
embed_config = EmbedConfig(
    embed_engine="model", embed_model="text2vec-base-chinese", 
    embed_model_path=os.path.join(src_dir, "embedding_models/text2vec-base-chinese")
    )

## initialize codebase
# delete codebase
codebase_name = 'client_local'
code_path = "D://chromeDownloads/devopschat-bot/client_v2/client"
use_nh = False
cbh = CodeBaseHandler(codebase_name, code_path, crawl_type='dir', use_nh=use_nh, local_graph_path=CB_ROOT_PATH,
                      llm_config=llm_config, embed_config=embed_config)
cbh.delete_codebase(codebase_name=codebase_name)


# load codebase
codebase_name = 'client_local'
code_path = "D://chromeDownloads/devopschat-bot/client_v2/client"
use_nh = True
do_interpret = True
cbh = CodeBaseHandler(codebase_name, code_path, crawl_type='dir', use_nh=use_nh, local_graph_path=CB_ROOT_PATH,
                      llm_config=llm_config, embed_config=embed_config)
cbh.import_code(do_interpret=do_interpret)


cbh = CodeBaseHandler(codebase_name, code_path, crawl_type='dir', use_nh=use_nh, local_graph_path=CB_ROOT_PATH,
                      llm_config=llm_config, embed_config=embed_config)
vertexes = cbh.search_vertices(vertex_type="class")


# log-level，print prompt和llm predict
os.environ["log_verbose"] = "0"

phase_name = "code2Tests"
phase = BasePhase(
    phase_name, sandbox_server=SANDBOX_SERVER, jupyter_work_path=JUPYTER_WORK_PATH,
    embed_config=embed_config, llm_config=llm_config, kb_root_path=KB_ROOT_PATH,
)

# round-1
logger.debug(vertexes)
test_cases = []
for vertex in vertexes:
    query_content = f"为{vertex}生成可执行的测例 "
    query = Message(
        role_name="human", role_type="user", 
        role_content=query_content, input_query=query_content, origin_query=query_content,
        code_engine_name=codebase_name, score_threshold=1.0, top_k=3, cb_search_type="tag",
        use_nh=use_nh, local_graph_path=CB_ROOT_PATH,
        )
    output_message, output_memory = phase.step(query, reinit_memory=True)
    # print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
    print(output_memory.get_spec_parserd_output())
    values = output_memory.get_spec_parserd_output()
    test_code = {k:v for i in values for k,v in i.items() if k in ["SaveFileName", "Test Code"]}
    test_cases.append(test_code)

    os.makedirs(f"{CB_ROOT_PATH}/tests", exist_ok=True)

    with open(f"{CB_ROOT_PATH}/tests/{test_code['SaveFileName']}", "w") as f:
        f.write(test_code["Test Code"])
    break




# import os, sys, json
# from loguru import logger
# src_dir = os.path.join(
#     os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# )
# sys.path.append(src_dir)

# from configs.model_config import KB_ROOT_PATH, JUPYTER_WORK_PATH, CB_ROOT_PATH
# from configs.server_config import SANDBOX_SERVER
# from coagent.tools import toLangchainTools, TOOL_DICT, TOOL_SETS
# from coagent.llm_models.llm_config import EmbedConfig, LLMConfig

# from coagent.connector.phase import BasePhase
# from coagent.connector.agents import BaseAgent
# from coagent.connector.chains import BaseChain
# from coagent.connector.schema import (
#     Message, Memory, load_role_configs, load_phase_configs, load_chain_configs, ActionStatus
#     )
# from coagent.connector.memory_manager import BaseMemoryManager
# from coagent.connector.configs import AGETN_CONFIGS, CHAIN_CONFIGS, PHASE_CONFIGS, BASE_PROMPT_CONFIGS
# from coagent.connector.prompt_manager.prompt_manager import PromptManager
# from coagent.codechat.codebase_handler.codebase_handler import CodeBaseHandler

# import importlib
# from loguru import logger

# # 下面给定了一份代码片段，以及来自于它的依赖类、依赖方法相关的代码片段，你需要判断是否为这段指定代码片段生成测例。
# # 理论上所有代码都需要写测例，但是受限于人的精力不可能覆盖所有代码
# # 考虑以下因素进行裁剪：
# # 功能性: 如果它实现的是一个具体的功能或逻辑，则通常需要编写测试用例以验证其正确性。
# # 复杂性: 如果代码较为，尤其是包含多个条件判断、循环、异常处理等的代码，更可能隐藏bug，因此应该编写测试用例。如果代码涉及复杂的算法或者逻辑，那么编写测试用例可以帮助确保逻辑的正确性，并在未来的重构中防止引入错误。
# # 关键性: 如果它是关键路径的一部分或影响到核心功能，那么它就需要被测试。对于核心业务逻辑或者系统的关键组件，应当编写全面的测试用例来确保功能的正确性和稳定性。
# # 依赖性: 如果代码有外部依赖，可能需要编写集成测试或模拟这些依赖进行单元测试。
# # 用户输入: 如果代码处理用户输入，尤其是来自外部的、非受控的输入，那么创建测试用例来检查输入验证和处理是很重要的。
# # 频繁更改：对于经常需要更新或修改的代码，有相应的测试用例可以确保更改不会破坏现有功能。


# # 代码公开或重用：如果代码将被公开或用于其他项目，编写测试用例可以提高代码的可信度和易用性。


# # update new agent configs
# judgeGenerateTests_PROMPT = """#### Agent Profile
# When determining the necessity of writing test cases for a given code snippet, 
# it's essential to evaluate its interactions with dependent classes and methods (retrieved code snippets), 
# in addition to considering these critical factors:
# 1. Functionality: If it implements a concrete function or logic, test cases are typically necessary to verify its correctness.
# 2. Complexity: If the code is complex, especially if it contains multiple conditional statements, loops, exceptions handling, etc., 
# it's more likely to harbor bugs, and thus test cases should be written. 
# If the code involves complex algorithms or logic, then writing test cases can help ensure the accuracy of the logic and prevent errors during future refactoring.
# 3. Criticality: If it's part of the critical path or affects core functionalities, then it needs to be tested. 
# Comprehensive test cases should be written for core business logic or key components of the system to ensure the correctness and stability of the functionality.
# 4. Dependencies: If the code has external dependencies, integration testing may be necessary, or mocking these dependencies during unit testing might be required.
# 5. User Input: If the code handles user input, especially from unregulated external sources, creating test cases to check input validation and handling is important.
# 6. Frequent Changes: For code that requires regular updates or modifications, having the appropriate test cases ensures that changes do not break existing functionalities.

# #### Input Format

# **Code Snippet:** the initial Code or objective that the user wanted to achieve

# **Retrieval Code Snippets:** These are the associated code segments that the main Code Snippet depends on. 
# Examine these snippets to understand how they interact with the main snippet and to determine how they might affect the overall functionality.

# #### Response Output Format
# **Action Status:** Set to 'finished' or 'continued'. 
# If set to 'finished', the code snippet does not warrant the generation of a test case.
# If set to 'continued', the code snippet necessitates the creation of a test case.

# **REASON:** Justify the selection of 'finished' or 'continued', contemplating the decision through a step-by-step rationale.
# """

# generateTests_PROMPT = """#### Agent Profile
# As an agent specializing in software quality assurance, 
# your mission is to craft comprehensive test cases that bolster the functionality, reliability, and robustness of a specified Code Snippet. 
# This task is to be carried out with a keen understanding of the snippet's interactions with its dependent classes and methods—collectively referred to as Retrieval Code Snippets. 
# Analyze the details given below to grasp the code's intended purpose, its inherent complexity, and the context within which it operates. 
# Your constructed test cases must thoroughly examine the various factors influencing the code's quality and performance.

# ATTENTION: response carefully referenced "Response Output Format" in format.

# Each test case should include:
# 1. clear description of the test purpose.
# 2. The input values or conditions for the test.
# 3. The expected outcome or assertion for the test.
# 4. Appropriate tags (e.g., 'functional', 'integration', 'regression') that classify the type of test case.
# 5. these test code should have package and import

# #### Input Format

# **Code Snippet:** the initial Code or objective that the user wanted to achieve

# **Retrieval Code Snippets:** These are the interrelated pieces of code sourced from the codebase, which support or influence the primary Code Snippet.

# #### Response Output Format
# **SaveFileName:** construct a local file name based on Question and Context, such as

# ```java
# package/class.java
# ```


# **Test Code:** generate the test code for the current Code Snippet.
# ```java
# ...
# ```

# """

# CODE_GENERATE_TESTS_PROMPT_CONFIGS = [
#     {"field_name": 'agent_profile', "function_name": 'handle_agent_profile', "is_context": False},
#     # {"field_name": 'tool_information',"function_name": 'handle_tool_data', "is_context": False},
#     {"field_name": 'context_placeholder', "function_name": '', "is_context": True},
#     # {"field_name": 'reference_documents', "function_name": 'handle_doc_info'},
#     {"field_name": 'session_records', "function_name": 'handle_session_records'},
#     {"field_name": 'code_snippet', "function_name": 'handle_code_snippet'},
#     {"field_name": 'retrieval_codes', "function_name": 'handle_retrieval_codes', "description": ""},
#     {"field_name": 'output_format', "function_name": 'handle_output_format', 'title': 'Response Output Format', "is_context": False},
#     {"field_name": 'begin!!!', "function_name": 'handle_response', "is_context": False, "omit_if_empty": False}
# ]


# class CodeRetrievalPM(PromptManager):
#     def handle_code_snippet(self, **kwargs) -> str:
#         if 'previous_agent_message' not in kwargs:
#             return ""
#         previous_agent_message: Message = kwargs['previous_agent_message']
#         code_snippet = previous_agent_message.customed_kargs.get("Code Snippet", "")
#         current_vertex = previous_agent_message.customed_kargs.get("Current_Vertex", "")
#         instruction = "the initial Code or objective that the user wanted to achieve"
#         return instruction + "\n" + f"name: {current_vertex}\n{code_snippet}"

#     def handle_retrieval_codes(self, **kwargs) -> str:
#         if 'previous_agent_message' not in kwargs:
#             return ""
#         previous_agent_message: Message = kwargs['previous_agent_message']
#         Retrieval_Codes = previous_agent_message.customed_kargs["Retrieval_Codes"]
#         Relative_vertex = previous_agent_message.customed_kargs["Relative_vertex"]
#         instruction = "the initial Code or objective that the user wanted to achieve"
#         s = instruction + "\n" + "\n".join([f"name: {vertext}\n{code}" for vertext, code in zip(Relative_vertex, Retrieval_Codes)])
#         return s



# AGETN_CONFIGS.update({
#     "CodeJudger": {
#         "role": {
#             "role_prompt": judgeGenerateTests_PROMPT,
#             "role_type": "assistant",
#             "role_name": "CodeJudger",
#             "role_desc": "",
#             "agent_type": "CodeRetrieval"
#             # "agent_type": "BaseAgent"
#         },
#         "prompt_config": CODE_GENERATE_TESTS_PROMPT_CONFIGS,
#         "prompt_manager_type": "CodeRetrievalPM",
#         "chat_turn": 1,
#         "focus_agents": [],
#         "focus_message_keys": [],
#     },
#     "generateTests": {
#         "role": {
#             "role_prompt": generateTests_PROMPT,
#             "role_type": "assistant",
#             "role_name": "generateTests",
#             "role_desc": "",
#             "agent_type": "CodeRetrieval"
#             # "agent_type": "BaseAgent"
#         },
#         "prompt_config": CODE_GENERATE_TESTS_PROMPT_CONFIGS,
#         "prompt_manager_type": "CodeRetrievalPM",
#         "chat_turn": 1,
#         "focus_agents": [],
#         "focus_message_keys": [],
#     },
# })
# # update new chain configs
# CHAIN_CONFIGS.update({
#     "codeRetrievalChain": {
#         "chain_name": "codeRetrievalChain",
#         "chain_type": "BaseChain",
#         "agents": ["CodeJudger", "generateTests"],
#         "chat_turn": 1,
#         "do_checker": False,
#         "chain_prompt": ""
#     }
# })

# # update phase configs
# PHASE_CONFIGS.update({
#     "codeGenerateTests": {
#         "phase_name": "codeGenerateTests",
#         "phase_type": "BasePhase",
#         "chains": ["codeRetrievalChain"],
#         "do_summary": False,
#         "do_search": False,
#         "do_doc_retrieval": False,
#         "do_code_retrieval": False,
#         "do_tool_retrieval": False,
#     },
# })


# role_configs = load_role_configs(AGETN_CONFIGS)
# chain_configs = load_chain_configs(CHAIN_CONFIGS)
# phase_configs = load_phase_configs(PHASE_CONFIGS)


# from coagent.tools import CodeRetrievalSingle, RelatedVerticesRetrival, Vertex2Code

# # 定义一个新的agent类
# class CodeRetrieval(BaseAgent):

#     def start_action_step(self, message: Message) -> Message:
#         '''do action before agent predict '''
#         # 根据问题获取代码片段和节点信息
#         action_json = CodeRetrievalSingle.run(message.code_engine_name, message.origin_query, llm_config=self.llm_config, embed_config=self.embed_config, search_type="tag", 
#                                               local_graph_path=message.local_graph_path, use_nh=message.use_nh)
#         current_vertex = action_json['vertex']
#         message.customed_kargs["Code Snippet"] = action_json["code"]
#         message.customed_kargs['Current_Vertex'] = current_vertex

#         # 获取邻近节点
#         action_json = RelatedVerticesRetrival.run(message.code_engine_name, message.customed_kargs['Current_Vertex'])
#         # 获取邻近节点所有代码
#         relative_vertex = []
#         retrieval_Codes = []
#         for vertex in action_json["vertices"]:
#             # 由于代码是文件级别，所以相同文件代码不再获取
#             # logger.debug(f"{current_vertex}, {vertex}")
#             current_vertex_name = current_vertex.replace("#", "").replace(".java", "" ) if current_vertex.endswith(".java") else current_vertex
#             if current_vertex_name.split("#")[0] == vertex.split("#")[0]: continue

#             action_json = Vertex2Code.run(message.code_engine_name, vertex)
#             if action_json["code"]:
#                 retrieval_Codes.append(action_json["code"])
#                 relative_vertex.append(vertex)
#         # 
#         message.customed_kargs["Retrieval_Codes"] = retrieval_Codes
#         message.customed_kargs["Relative_vertex"] = relative_vertex
#         return message


# # add agent or prompt_manager class
# agent_module = importlib.import_module("coagent.connector.agents")
# prompt_manager_module = importlib.import_module("coagent.connector.prompt_manager")

# setattr(agent_module, 'CodeRetrieval', CodeRetrieval)
# setattr(prompt_manager_module, 'CodeRetrievalPM', CodeRetrievalPM)


# # log-level，print prompt和llm predict
# os.environ["log_verbose"] = "0"

# phase_name = "codeGenerateTests"
# llm_config = LLMConfig(
#     model_name="gpt-4", api_key=os.environ["OPENAI_API_KEY"], 
#     api_base_url=os.environ["API_BASE_URL"], temperature=0.3
# )
# embed_config = EmbedConfig(
#     embed_engine="model", embed_model="text2vec-base-chinese", 
#     embed_model_path=os.path.join(src_dir, "embedding_models/text2vec-base-chinese")
#     )

# ## initialize codebase
# # delete codebase
# codebase_name = 'client_local'
# code_path = "D://chromeDownloads/devopschat-bot/client_v2/client"
# use_nh = False
# cbh = CodeBaseHandler(codebase_name, code_path, crawl_type='dir', use_nh=use_nh, local_graph_path=CB_ROOT_PATH,
#                       llm_config=llm_config, embed_config=embed_config)
# cbh.delete_codebase(codebase_name=codebase_name)


# # load codebase
# codebase_name = 'client_local'
# code_path = "D://chromeDownloads/devopschat-bot/client_v2/client"
# use_nh = True
# do_interpret = True
# cbh = CodeBaseHandler(codebase_name, code_path, crawl_type='dir', use_nh=use_nh, local_graph_path=CB_ROOT_PATH,
#                       llm_config=llm_config, embed_config=embed_config)
# cbh.import_code(do_interpret=do_interpret)


# cbh = CodeBaseHandler(codebase_name, code_path, crawl_type='dir', use_nh=use_nh, local_graph_path=CB_ROOT_PATH,
#                       llm_config=llm_config, embed_config=embed_config)
# vertexes = cbh.search_vertices(vertex_type="class")

# phase = BasePhase(
#     phase_name, sandbox_server=SANDBOX_SERVER, jupyter_work_path=JUPYTER_WORK_PATH,
#     embed_config=embed_config, llm_config=llm_config, kb_root_path=KB_ROOT_PATH,
# )

# # round-1
# logger.debug(vertexes)
# test_cases = []
# for vertex in vertexes:
#     query_content = f"为{vertex}生成可执行的测例 "
#     query = Message(
#         role_name="human", role_type="user", 
#         role_content=query_content, input_query=query_content, origin_query=query_content,
#         code_engine_name=codebase_name, score_threshold=1.0, top_k=3, cb_search_type="tag",
#         use_nh=use_nh, local_graph_path=CB_ROOT_PATH,
#         )
#     output_message, output_memory = phase.step(query, reinit_memory=True)
#     # print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
#     print(output_memory.get_spec_parserd_output())
#     values = output_memory.get_spec_parserd_output()
#     test_code = {k:v for i in values for k,v in i.items() if k in ["SaveFileName", "Test Code"]}
#     test_cases.append(test_code)

#     os.makedirs(f"{CB_ROOT_PATH}/tests", exist_ok=True)

#     with open(f"{CB_ROOT_PATH}/tests/{test_code['SaveFileName']}", "w") as f:
#         f.write(test_code["Test Code"])