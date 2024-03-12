import os, sys, requests
from loguru import logger
src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(src_dir)

from configs.model_config import KB_ROOT_PATH, JUPYTER_WORK_PATH
from configs.server_config import SANDBOX_SERVER
from coagent.tools import toLangchainTools, TOOL_DICT, TOOL_SETS
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig

from coagent.connector.phase import BasePhase
from coagent.connector.agents import BaseAgent
from coagent.connector.chains import BaseChain
from coagent.connector.schema import (
    Message, Memory, load_role_configs, load_phase_configs, load_chain_configs, ActionStatus
    )
from coagent.connector.memory_manager import BaseMemoryManager
from coagent.connector.configs import AGETN_CONFIGS, CHAIN_CONFIGS, PHASE_CONFIGS, BASE_PROMPT_CONFIGS
from coagent.connector.prompt_manager.prompt_manager import PromptManager
import importlib

from loguru import logger



# update new agent configs
codeRetrievalJudger_PROMPT = """#### Agent Profile

Given the user's question and respective code, you need to decide whether the provided codes are enough to answer the question.

#### Input Format

**Origin Query:** the initial question or objective that the user wanted to achieve

**Retrieval Codes:** the Retrieval Codes from the code base

#### Response Output Format
**Action Status:** Set to 'finished' or 'continued'. 
If it's 'finished', the provided codes can answer the origin query.
If it's 'continued', the origin query cannot be answered well from the provided code.

**REASON:** Justify the decision of choosing 'finished' and 'continued' by evaluating the progress step by step.
"""

# 将下面的话放到上面的prompt里面去执行，让它判断是否停止
# **Action Status:** Set to 'finished' or 'continued'.
# If it's 'finished', the provided codes can answer the origin query.
# If it's 'continued', the origin query cannot be answered well from the provided code.

codeRetrievalDivergent_PROMPT = """#### Agent Profile

You are a assistant that helps to determine which code package is needed to answer the question.

Given the user's question, Retrieval code, and the code Packages related to Retrieval code. you need to decide which code package we need to read to better answer the question.

#### Input Format

**Origin Query:** the initial question or objective that the user wanted to achieve

**Retrieval Codes:** the Retrieval Codes from the code base

**Code Packages:** the code packages related to Retrieval code

#### Response Output Format

**Code Package:** Identify another Code Package from the Code Packages that can most help to provide a better answer to the Origin Query, only put one name of the code package here.

**REASON:** Justify the decision of choosing 'finished' and 'continued' by evaluating the progress step by step.
"""


class CodeRetrievalPM(PromptManager):
    def handle_code_packages(self, **kwargs) -> str:
        if 'previous_agent_message' not in kwargs:
            return ""
        previous_agent_message: Message = kwargs['previous_agent_message']
        # 由于两个agent共用了同一个manager，所以临时性处理
        vertices = previous_agent_message.customed_kargs.get("RelatedVerticesRetrivalRes", {}).get("vertices", [])
        return ", ".join([str(v) for v in vertices])

    def handle_retrieval_codes(self, **kwargs) -> str:
        if 'previous_agent_message' not in kwargs:
            return ""
        previous_agent_message: Message = kwargs['previous_agent_message']
        return '\n'.join(previous_agent_message.customed_kargs["Retrieval_Codes"])


# Design your personal PROMPT INPPUT FORMAT 
CODE_RETRIEVAL_PROMPT_CONFIGS = [
    {"field_name": 'agent_profile', "function_name": 'handle_agent_profile', "is_context": False},
    {"field_name": 'tool_information',"function_name": 'handle_tool_data', "is_context": False},
    {"field_name": 'context_placeholder', "function_name": '', "is_context": True},
    # {"field_name": 'reference_documents', "function_name": 'handle_doc_info'},
    {"field_name": 'session_records', "function_name": 'handle_session_records'},
    {"field_name": 'retrieval_codes', "function_name": 'handle_retrieval_codes'},
    {"field_name": 'code_packages', "function_name": 'handle_code_packages'},
    {"field_name": 'output_format', "function_name": 'handle_output_format', 'title': 'Response Output Format', "is_context": False},
    {"field_name": 'begin!!!', "function_name": 'handle_response', "is_context": False, "omit_if_empty": False}
    ]


AGETN_CONFIGS.update({
    "codeRetrievalJudger": {
        "role": {
            "role_prompt": codeRetrievalJudger_PROMPT,
            "role_type": "assistant",
            "role_name": "codeRetrievalJudger",
            "role_desc": "",
            "agent_type": "CodeRetrievalJudger"
            # "agent_type": "BaseAgent"
        },
        "prompt_config": CODE_RETRIEVAL_PROMPT_CONFIGS,
        "prompt_manager_type": "CodeRetrievalPM",
        "chat_turn": 1,
        "focus_agents": [],
        "focus_message_keys": [],
    },
    "codeRetrievalDivergent": {
        "role": {
            "role_prompt": codeRetrievalDivergent_PROMPT,
            "role_type": "assistant",
            "role_name": "codeRetrievalDivergent",
            "role_desc": "",
            "agent_type": "CodeRetrievalDivergent"
            # "agent_type": "BaseAgent"
        },
        "prompt_config": CODE_RETRIEVAL_PROMPT_CONFIGS,
        "prompt_manager_type": "CodeRetrievalPM",
        "chat_turn": 1,
        "focus_agents": [],
        "focus_message_keys": [],
    },
})
# update new chain configs
CHAIN_CONFIGS.update({
    "codeRetrievalChain": {
        "chain_name": "codeRetrievalChain",
        "chain_type": "BaseChain",
        "agents": ["codeRetrievalJudger", "codeRetrievalDivergent"],
        "chat_turn": 3,
        "do_checker": False,
        "chain_prompt": ""
    }
})

# update phase configs
PHASE_CONFIGS.update({
    "codeRetrievalPhase": {
        "phase_name": "codeRetrievalPhase",
        "phase_type": "BasePhase",
        "chains": ["codeRetrievalChain"],
        "do_summary": False,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_code_retrieval": True,
        "do_tool_retrieval": False,
    },
})


role_configs = load_role_configs(AGETN_CONFIGS)
chain_configs = load_chain_configs(CHAIN_CONFIGS)
phase_configs = load_phase_configs(PHASE_CONFIGS)


from coagent.tools import CodeRetrievalSingle, RelatedVerticesRetrival, Vertex2Code

# 定义一个新的类
class CodeRetrievalJudger(BaseAgent):

    def start_action_step(self, message: Message) -> Message:
        '''do action before agent predict '''
        if 'Retrieval_Codes' in message.customed_kargs:
            # already retrive the code
            pass
        else:
            action_json = CodeRetrievalSingle.run(message.code_engine_name, message.origin_query, llm_config=self.llm_config, embed_config=self.embed_config)
            message.customed_kargs["CodeRetrievalSingleRes"] = action_json
            message.customed_kargs['Current_Vertex'] = action_json['vertex']
            message.customed_kargs.setdefault("Retrieval_Codes", [])
            message.customed_kargs["Retrieval_Codes"].append(action_json["code"])
        return message


# 定义一个新的类
class CodeRetrievalDivergent(BaseAgent):
    def start_action_step(self, message: Message) -> Message:
        '''do action before agent predict '''
        action_json = RelatedVerticesRetrival.run(message.code_engine_name, message.customed_kargs['Current_Vertex'])
        if not action_json['vertices']:
            message.action_status = ActionStatus.FINISHED
        message.customed_kargs["RelatedVerticesRetrivalRes"] = action_json
        return message

    def end_action_step(self, message: Message) -> Message:
        '''do action before agent predict '''
        # logger.error(f"message: {message}")
        action_json = Vertex2Code.run(message.code_engine_name, message.parsed_output["Code Package"])
        logger.debug(f'action_json={action_json}')
        if not action_json['code']:
            message.action_status = ActionStatus.FINISHED
            return message

        message.customed_kargs["Vertex2Code"] = action_json
        message.customed_kargs['Current_Vertex'] = message.parsed_output["Code Package"]
        message.customed_kargs.setdefault("Retrieval_Codes", [])

        if action_json['code'] in message.customed_kargs["Retrieval_Codes"]:
            message.action_status = ActionStatus.FINISHED
            return message

        message.customed_kargs["Retrieval_Codes"].append(action_json['code'])

        return message

# add agent or prompt_manager class
agent_module = importlib.import_module("coagent.connector.agents")
prompt_manager_module = importlib.import_module("coagent.connector.prompt_manager")

setattr(agent_module, 'CodeRetrievalJudger', CodeRetrievalJudger)
setattr(agent_module, 'CodeRetrievalDivergent', CodeRetrievalDivergent)
setattr(prompt_manager_module, 'CodeRetrievalPM', CodeRetrievalPM)


# log-level，print prompt和llm predict
os.environ["log_verbose"] = "2"

phase_name = "codeRetrievalPhase"
llm_config = LLMConfig(
    model_name="gpt-3.5-turbo", api_key=os.environ["OPENAI_API_KEY"], 
    api_base_url=os.environ["API_BASE_URL"], temperature=0.3
    )
embed_config = EmbedConfig(
    embed_engine="model", embed_model="text2vec-base-chinese", 
    embed_model_path=os.path.join(src_dir, "embedding_models/text2vec-base-chinese")
    )
phase = BasePhase(
    phase_name, sandbox_server=SANDBOX_SERVER, jupyter_work_path=JUPYTER_WORK_PATH,
    embed_config=embed_config, llm_config=llm_config, kb_root_path=KB_ROOT_PATH,
)
# round-1
query_content = "UtilsTest 这个类中测试了哪些函数,测试的函数代码是什么"
query = Message(
    role_name="human", role_type="user", 
    role_content=query_content, input_query=query_content, origin_query=query_content,
    code_engine_name="client_1", score_threshold=1.0, top_k=3, cb_search_type="tag"
    )


output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))