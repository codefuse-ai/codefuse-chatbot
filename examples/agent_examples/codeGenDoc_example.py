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
from coagent.tools import CodeRetrievalSingle
from coagent.codechat.codebase_handler.codebase_handler import CodeBaseHandler
import importlib


# 定义一个新的agent类
class CodeGenDocer(BaseAgent):

    def start_action_step(self, message: Message) -> Message:
        '''do action before agent predict '''
        # 根据问题获取代码片段和节点信息
        action_json = CodeRetrievalSingle.run(message.code_engine_name, message.origin_query, 
                                              llm_config=self.llm_config, embed_config=self.embed_config, local_graph_path=message.local_graph_path, use_nh=message.use_nh,search_type="tag")
        current_vertex = action_json['vertex']
        message.customed_kargs["Code Snippet"] = action_json["code"]
        message.customed_kargs['Current_Vertex'] = current_vertex
        return message


# add agent or prompt_manager class
agent_module = importlib.import_module("coagent.connector.agents")
setattr(agent_module, 'CodeGenDocer', CodeGenDocer)


# log-level，print prompt和llm predict
os.environ["log_verbose"] = "1"

phase_name = "code2DocsGroup"
llm_config = LLMConfig(
    model_name="gpt-4", api_key=os.environ["OPENAI_API_KEY"], 
    api_base_url=os.environ["API_BASE_URL"], temperature=0.3
)
embed_config = EmbedConfig(
    embed_engine="model", embed_model="text2vec-base-chinese", 
    embed_model_path=os.path.join(src_dir, "embedding_models/text2vec-base-chinese")
    )

# initialize codebase
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

# 根据前面的load过程进行初始化
cbh = CodeBaseHandler(codebase_name, code_path, crawl_type='dir', use_nh=use_nh, local_graph_path=CB_ROOT_PATH,
                      llm_config=llm_config, embed_config=embed_config)
phase = BasePhase(
    phase_name, sandbox_server=SANDBOX_SERVER, jupyter_work_path=JUPYTER_WORK_PATH,
    embed_config=embed_config, llm_config=llm_config, kb_root_path=KB_ROOT_PATH,
)

for vertex_type in ["class", "method"]:
    vertexes = cbh.search_vertices(vertex_type=vertex_type)
    logger.info(f"vertexes={vertexes}")

    # round-1
    docs = []
    for vertex in vertexes:
        vertex = vertex.split("-")[0] # -为method的参数
        query_content = f"为{vertex_type}节点 {vertex}生成文档"
        query = Message(
            role_name="human", role_type="user", 
            role_content=query_content, input_query=query_content, origin_query=query_content,
            code_engine_name="client_local", score_threshold=1.0, top_k=3, cb_search_type="tag", use_nh=use_nh,
            local_graph_path=CB_ROOT_PATH,
            )
        output_message, output_memory = phase.step(query, reinit_memory=True)
        # print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
        docs.append(output_memory.get_spec_parserd_output())

        os.makedirs(f"{CB_ROOT_PATH}/docs", exist_ok=True)
        with open(f"{CB_ROOT_PATH}/docs/raw_{vertex_type}.json", "w") as f:
            json.dump(docs, f)
    

# 下面把生成的文档信息转换成markdown文本
from coagent.utils.code2doc_util import *
import json
with open(f"{CB_ROOT_PATH}/docs/raw_method.json", "r") as f:
    method_raw_data = json.load(f)

with open(f"{CB_ROOT_PATH}/docs/raw_class.json", "r") as f:
    class_raw_data = json.load(f)
    

method_data = method_info_decode(method_raw_data)
class_data = class_info_decode(class_raw_data)
method_mds = encode2md(method_data, method_text_md)
class_mds = encode2md(class_data, class_text_md)


docs_dict = {}
for k,v in class_mds.items():
    method_textmds = method_mds.get(k, [])
    for vv in v:
        # 理论上只有一个
        text_md = vv

    for method_textmd in method_textmds:
        text_md += "\n<br>" + method_textmd

    docs_dict.setdefault(k, []).append(text_md)
    
    with open(f"{CB_ROOT_PATH}//docs/{k}.md", "w") as f:
        f.write(text_md)
    




####################################
######## 下面是完整的复现过程 ########
####################################

# import os, sys, requests
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
# from coagent.connector.agents import BaseAgent, SelectorAgent
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


# from coagent.tools import CodeRetrievalSingle, RelatedVerticesRetrival, Vertex2Code


# # update new agent configs
# codeGenDocGroup_PROMPT = """#### Agent Profile

# Your goal is to response according the Context Data's information with the role that will best facilitate a solution, taking into account all relevant context (Context) provided.

# When you need to select the appropriate role for handling a user's query, carefully read the provided role names, role descriptions and tool list.

# ATTENTION: response carefully referenced "Response Output Format" in format.

# #### Input Format

# #### Response Output Format

# **Code Path:** Extract the paths for the class/method/function that need to be addressed from the context

# **Role:** Select the role from agent names
# """

# classGenDoc_PROMPT = """#### Agent Profile
# As an advanced code documentation generator, you are proficient in translating class definitions into comprehensive documentation with a focus on instantiation parameters. 
# Your specific task is to parse the given code snippet of a class, extract information regarding its instantiation parameters.

# ATTENTION: response carefully in "Response Output Format".

# #### Input Format

# **Code Snippet:** Provide the full class definition, including the constructor and any parameters it may require for instantiation.

# #### Response Output Format
# **Class Base:** Specify the base class or interface from which the current class extends, if any.

# **Class Description:** Offer a brief description of the class's purpose and functionality.

# **Init Parameters:** List each parameter from construct. For each parameter, provide:
#     - `param`: The parameter name
#     - `param_description`: A concise explanation of the parameter's purpose.
#     - `param_type`: The data type of the parameter, if explicitly defined.

#     ```json
#     [
#         {
#             "param": "parameter_name",
#             "param_description": "A brief description of what this parameter is used for.",
#             "param_type": "The data type of the parameter"
#         },
#         ...
#     ]
#     ```

        
#     If no parameter for construct, return 
#     ```json
#     []
#     ```
# """

# funcGenDoc_PROMPT = """#### Agent Profile
# You are a high-level code documentation assistant, skilled at extracting information from function/method code into detailed and well-structured documentation.

# ATTENTION: response carefully in "Response Output Format".


# #### Input Format
# **Code Path:** Provide the code path of the function or method you wish to document. 
# This name will be used to identify and extract the relevant details from the code snippet provided.
    
# **Code Snippet:** A segment of code that contains the function or method to be documented.

# #### Response Output Format

# **Class Description:** Offer a brief description of the method(function)'s purpose and functionality.

# **Parameters:** Extract parameter for the specific function/method Code from Code Snippet. For parameter, provide:
#     - `param`: The parameter name
#     - `param_description`: A concise explanation of the parameter's purpose.
#     - `param_type`: The data type of the parameter, if explicitly defined.
#     ```json
#     [
#         {
#             "param": "parameter_name",
#             "param_description": "A brief description of what this parameter is used for.",
#             "param_type": "The data type of the parameter"
#         },
#         ...
#     ]
#     ```

#     If no parameter for function/method, return 
#     ```json
#     []
#     ```

# **Return Value Description:** Describe what the function/method returns upon completion.

# **Return Type:** Indicate the type of data the function/method returns (e.g., string, integer, object, void).
# """

# CODE_GENERATE_GROUP_PROMPT_CONFIGS = [
#     {"field_name": 'agent_profile', "function_name": 'handle_agent_profile', "is_context": False},
#     {"field_name": 'agent_infomation', "function_name": 'handle_agent_data', "is_context": False, "omit_if_empty": False},
#     # {"field_name": 'tool_information',"function_name": 'handle_tool_data', "is_context": False},
#     {"field_name": 'context_placeholder', "function_name": '', "is_context": True},
#     # {"field_name": 'reference_documents', "function_name": 'handle_doc_info'},
#     {"field_name": 'session_records', "function_name": 'handle_session_records'},
#     {"field_name": 'Specific Objective', "function_name": 'handle_specific_objective'},
#     {"field_name": 'Code Snippet', "function_name": 'handle_code_snippet'},
#     {"field_name": 'output_format', "function_name": 'handle_output_format', 'title': 'Response Output Format', "is_context": False},
#     {"field_name": 'begin!!!', "function_name": 'handle_response', "is_context": False, "omit_if_empty": False}
# ]

# CODE_GENERATE_DOC_PROMPT_CONFIGS = [
#     {"field_name": 'agent_profile', "function_name": 'handle_agent_profile', "is_context": False},
#     # {"field_name": 'tool_information',"function_name": 'handle_tool_data', "is_context": False},
#     {"field_name": 'context_placeholder', "function_name": '', "is_context": True},
#     # {"field_name": 'reference_documents', "function_name": 'handle_doc_info'},
#     {"field_name": 'session_records', "function_name": 'handle_session_records'},
#     {"field_name": 'Specific Objective', "function_name": 'handle_specific_objective'},
#     {"field_name": 'Code Snippet', "function_name": 'handle_code_snippet'},
#     {"field_name": 'output_format', "function_name": 'handle_output_format', 'title': 'Response Output Format', "is_context": False},
#     {"field_name": 'begin!!!', "function_name": 'handle_response', "is_context": False, "omit_if_empty": False}
# ]


# class CodeGenDocPM(PromptManager):
#     def handle_code_snippet(self, **kwargs) -> str:
#         if 'previous_agent_message' not in kwargs:
#             return ""
#         previous_agent_message: Message = kwargs['previous_agent_message']
#         code_snippet = previous_agent_message.customed_kargs.get("Code Snippet", "")
#         current_vertex = previous_agent_message.customed_kargs.get("Current_Vertex", "")
#         instruction = "A segment of code that contains the function or method to be documented.\n"
#         return instruction + "\n" + f"name: {current_vertex}\n{code_snippet}"

#     def handle_specific_objective(self, **kwargs) -> str:
#         if 'previous_agent_message' not in kwargs:
#             return ""
#         previous_agent_message: Message = kwargs['previous_agent_message']
#         specific_objective = previous_agent_message.parsed_output.get("Code Path")

#         instruction = "Provide the code path of the function or method you wish to document.\n"
#         s = instruction + f"\n{specific_objective}"
#         return s


# from coagent.tools import CodeRetrievalSingle

# # 定义一个新的agent类
# class CodeGenDocer(BaseAgent):

#     def start_action_step(self, message: Message) -> Message:
#         '''do action before agent predict '''
#         # 根据问题获取代码片段和节点信息
#         action_json = CodeRetrievalSingle.run(message.code_engine_name, message.origin_query, 
#                                               llm_config=self.llm_config, embed_config=self.embed_config, local_graph_path=message.local_graph_path, use_nh=message.use_nh,search_type="tag")
#         current_vertex = action_json['vertex']
#         message.customed_kargs["Code Snippet"] = action_json["code"]
#         message.customed_kargs['Current_Vertex'] = current_vertex
#         return message

# # add agent or prompt_manager class
# agent_module = importlib.import_module("coagent.connector.agents")
# prompt_manager_module = importlib.import_module("coagent.connector.prompt_manager")

# setattr(agent_module, 'CodeGenDocer', CodeGenDocer)
# setattr(prompt_manager_module, 'CodeGenDocPM', CodeGenDocPM)




# AGETN_CONFIGS.update({
#     "classGenDoc": {
#         "role": {
#             "role_prompt": classGenDoc_PROMPT,
#             "role_type": "assistant",
#             "role_name": "classGenDoc",
#             "role_desc": "",
#             "agent_type": "CodeGenDocer"
#         },
#         "prompt_config": CODE_GENERATE_DOC_PROMPT_CONFIGS,
#         "prompt_manager_type": "CodeGenDocPM",
#         "chat_turn": 1,
#         "focus_agents": [],
#         "focus_message_keys": [],
#     },
#     "funcGenDoc": {
#         "role": {
#             "role_prompt": funcGenDoc_PROMPT,
#             "role_type": "assistant",
#             "role_name": "funcGenDoc",
#             "role_desc": "",
#             "agent_type": "CodeGenDocer"
#         },
#         "prompt_config": CODE_GENERATE_DOC_PROMPT_CONFIGS,
#         "prompt_manager_type": "CodeGenDocPM",
#         "chat_turn": 1,
#         "focus_agents": [],
#         "focus_message_keys": [],
#     },
#     "codeGenDocsGrouper": {
#         "role": {
#             "role_prompt": codeGenDocGroup_PROMPT,
#             "role_type": "assistant",
#             "role_name": "codeGenDocsGrouper",
#             "role_desc": "",
#             "agent_type": "SelectorAgent"
#         },
#         "prompt_config": CODE_GENERATE_GROUP_PROMPT_CONFIGS,
#         "group_agents": ["classGenDoc", "funcGenDoc"],
#         "chat_turn": 1,
#     },
# })
# # update new chain configs
# CHAIN_CONFIGS.update({
#     "codeGenDocsGroupChain": {
#         "chain_name": "codeGenDocsGroupChain",
#         "chain_type": "BaseChain",
#         "agents": ["codeGenDocsGrouper"],
#         "chat_turn": 1,
#         "do_checker": False,
#         "chain_prompt": ""
#     }
# })

# # update phase configs
# PHASE_CONFIGS.update({
#     "codeGenDocsGroup": {
#         "phase_name": "codeGenDocsGroup",
#         "phase_type": "BasePhase",
#         "chains": ["codeGenDocsGroupChain"],
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

# # log-level，print prompt和llm predict
# os.environ["log_verbose"] = "1"

# phase_name = "codeGenDocsGroup"
# llm_config = LLMConfig(
#     model_name="gpt-4", api_key=os.environ["OPENAI_API_KEY"], 
#     api_base_url=os.environ["API_BASE_URL"], temperature=0.3
# )
# embed_config = EmbedConfig(
#     embed_engine="model", embed_model="text2vec-base-chinese", 
#     embed_model_path=os.path.join(src_dir, "embedding_models/text2vec-base-chinese")
#     )


# # initialize codebase
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
# use_nh = False
# do_interpret = True
# cbh = CodeBaseHandler(codebase_name, code_path, crawl_type='dir', use_nh=use_nh, local_graph_path=CB_ROOT_PATH,
#                       llm_config=llm_config, embed_config=embed_config)
# cbh.import_code(do_interpret=do_interpret)


# phase = BasePhase(
#     phase_name, sandbox_server=SANDBOX_SERVER, jupyter_work_path=JUPYTER_WORK_PATH,
#     embed_config=embed_config, llm_config=llm_config, kb_root_path=KB_ROOT_PATH,
# )

# for vertex_type in ["class", "method"]:
#     vertexes = cbh.search_vertices(vertex_type=vertex_type)
#     logger.info(f"vertexes={vertexes}")

#     # round-1
#     docs = []
#     for vertex in vertexes:
#         vertex = vertex.split("-")[0] # -为method的参数
#         query_content = f"为{vertex_type}节点 {vertex}生成文档"
#         query = Message(
#             role_name="human", role_type="user", 
#             role_content=query_content, input_query=query_content, origin_query=query_content,
#             code_engine_name="client_local", score_threshold=1.0, top_k=3, cb_search_type="tag", use_nh=use_nh,
#             local_graph_path=CB_ROOT_PATH,
#             )
#         output_message, output_memory = phase.step(query, reinit_memory=True)
#         # print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
#         docs.append(output_memory.get_spec_parserd_output())

#         import json
#         os.makedirs("/home/user/code_base/docs", exist_ok=True)
#         with open(f"/home/user/code_base/docs/raw_{vertex_type}.json", "w") as f:
#             json.dump(docs, f)


# # 下面把生成的文档信息转换成markdown文本
# from coagent.utils.code2doc_util import *

# import json
# with open(f"/home/user/code_base/docs/raw_method.json", "r") as f:
#     method_raw_data = json.load(f)

# with open(f"/home/user/code_base/docs/raw_class.json", "r") as f:
#     class_raw_data = json.load(f)
    

# method_data = method_info_decode(method_raw_data)
# class_data = class_info_decode(class_raw_data)
# method_mds = encode2md(method_data, method_text_md)
# class_mds = encode2md(class_data, class_text_md)

# docs_dict = {}
# for k,v in class_mds.items():
#     method_textmds = method_mds.get(k, [])
#     for vv in v:
#         # 理论上只有一个
#         text_md = vv

#     for method_textmd in method_textmds:
#         text_md += "\n<br>" + method_textmd

#     docs_dict.setdefault(k, []).append(text_md)
    
#     with open(f"/home/user/code_base/docs/{k}.md", "w") as f:
#         f.write(text_md)