import os, sys, requests

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(src_dir)

from configs.model_config import *
from dev_opsgpt.connector.phase import BasePhase
from dev_opsgpt.connector.agents import BaseAgent
from dev_opsgpt.connector.chains import BaseChain
from dev_opsgpt.connector.schema import (
    Message, Memory, load_role_configs, load_phase_configs, load_chain_configs
    )
from dev_opsgpt.connector.configs import AGETN_CONFIGS, CHAIN_CONFIGS, PHASE_CONFIGS
from dev_opsgpt.connector.utils import parse_section
import importlib



# update new agent configs
codeRetrievalJudger_PROMPT = """#### CodeRetrievalJudger Assistance Guidance

Given the user's question and respective code, you need to decide whether the provided codes are enough to answer the question.

#### Input Format

**Origin Query:** the initial question or objective that the user wanted to achieve

**Retrieval Codes:** the Retrieval Codes from the code base

#### Response Output Format

**REASON:** Justify the decision of choosing 'finished' and 'continued' by evaluating the progress step by step.
"""

# 将下面的话放到上面的prompt里面去执行，让它判断是否停止
# **Action Status:** Set to 'finished' or 'continued'. 
# If it's 'finished', the provided codes can answer the origin query.
# If it's 'continued', the origin query cannot be answered well from the provided code.

codeRetrievalDivergent_PROMPT = """#### CodeRetrievalDivergen Assistance Guidance

You are a assistant that helps to determine which code package is needed to answer the question.

Given the user's question, Retrieval code, and the code Packages related to Retrieval code. you need to decide which code package we need to read to better answer the question.

#### Input Format

**Origin Query:** the initial question or objective that the user wanted to achieve

**Retrieval Codes:** the Retrieval Codes from the code base

**Code Packages:** the code packages related to Retrieval code

#### Response Output Format

**Code Package:** Identify another Code Package from the Code Packages that should be read to provide a better answer to the Origin Query.

**REASON:** Justify the decision of choosing 'finished' and 'continued' by evaluating the progress step by step.
"""

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
        "chat_turn": 5,
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
        "do_using_tool": False
    },
})




role_configs = load_role_configs(AGETN_CONFIGS)
chain_configs = load_chain_configs(CHAIN_CONFIGS)
phase_configs = load_phase_configs(PHASE_CONFIGS)

agent_module = importlib.import_module("dev_opsgpt.connector.agents")

from dev_opsgpt.tools import CodeRetrievalSingle, RelatedVerticesRetrival, Vertex2Code

# 定义一个新的类
class CodeRetrievalJudger(BaseAgent):

    def start_action_step(self, message: Message) -> Message:
        '''do action before agent predict '''
        action_json = CodeRetrievalSingle.run(message.code_engine_name, message.origin_query)
        message.customed_kargs["CodeRetrievalSingleRes"] = action_json
        message.customed_kargs.setdefault("Retrieval_Codes", "")
        message.customed_kargs["Retrieval_Codes"] += "\n" + action_json["code"]
        return message

    def create_prompt(
            self, query: Message, memory: Memory =None, history: Memory = None, background: Memory = None, memory_pool: Memory=None, prompt_mamnger=None) -> str:
        '''
        prompt engineer, contains role\task\tools\docs\memory
        '''
        # 
        logger.debug(f"query: {query.customed_kargs}")
        formatted_tools, tool_names, _ = self.create_tools_prompt(query)
        prompt = self.role.role_prompt.format(**{"formatted_tools": formatted_tools, "tool_names": tool_names})
        #
        input_keys = parse_section(self.role.role_prompt, 'Input Format')
        prompt += "\n#### Begin!!!\n"
        # 
        for input_key in input_keys:
            if input_key == "Origin Query": 
                prompt += f"\n**{input_key}:**\n" + query.origin_query
            elif input_key == "Retrieval Codes":
                prompt += f"\n**{input_key}:**\n" + query.customed_kargs["Retrieval_Codes"]

        while "{{" in prompt or "}}" in prompt:
            prompt = prompt.replace("{{", "{")
            prompt = prompt.replace("}}", "}")
        return prompt

# 定义一个新的类
class CodeRetrievalDivergent(BaseAgent):

    def start_action_step(self, message: Message) -> Message:
        '''do action before agent predict '''
        action_json = RelatedVerticesRetrival.run(message.code_engine_name, message.customed_kargs["CodeRetrievalSingleRes"]["vertex"])
        message.customed_kargs["RelatedVerticesRetrivalRes"] = action_json
        return message

    def end_action_step(self, message: Message) -> Message:
        '''do action before agent predict '''
        # logger.error(f"message: {message}")
        # action_json = Vertex2Code.run(message.code_engine_name, "com.theokanning.openai.client#Utils.java") # message.parsed_output["Code_Filename"])
        action_json = Vertex2Code.run(message.code_engine_name, message.parsed_output["Code Package"])
        message.customed_kargs["Vertex2Code"] = action_json
        message.customed_kargs.setdefault("Retrieval_Codes", "")
        message.customed_kargs["Retrieval_Codes"] += "\n" + action_json["code"]
        return message
    
    def create_prompt(
            self, query: Message, memory: Memory =None, history: Memory = None, background: Memory = None, memory_pool: Memory=None, prompt_mamnger=None) -> str:
        '''
        prompt engineer, contains role\task\tools\docs\memory
        '''
        formatted_tools, tool_names, _ = self.create_tools_prompt(query)
        prompt = self.role.role_prompt.format(**{"formatted_tools": formatted_tools, "tool_names": tool_names})
        # 
        input_query = query.input_query
        input_keys = parse_section(self.role.role_prompt, 'Input Format')
        prompt += "\n#### Begin!!!\n"
        # 
        for input_key in input_keys:
            if input_key == "Origin Query": 
                prompt += f"\n**{input_key}:**\n" + query.origin_query
            elif input_key == "Retrieval Codes":
                prompt += f"\n**{input_key}:**\n" + query.customed_kargs["Retrieval_Codes"]
            elif input_key == "Code Packages":
                vertices = query.customed_kargs["RelatedVerticesRetrivalRes"]["vertices"]
                prompt += f"\n**{input_key}:**\n" + ", ".join([str(v) for v in vertices])

        while "{{" in prompt or "}}" in prompt:
            prompt = prompt.replace("{{", "{")
            prompt = prompt.replace("}}", "}")
        return prompt
    

setattr(agent_module, 'CodeRetrievalJudger', CodeRetrievalJudger)
setattr(agent_module, 'CodeRetrievalDivergent', CodeRetrievalDivergent)


# 
phase_name = "codeRetrievalPhase"
phase = BasePhase(phase_name,
            task = None,
            phase_config = PHASE_CONFIGS,
            chain_config = CHAIN_CONFIGS,
            role_config = AGETN_CONFIGS,
            do_summary=False,
            do_code_retrieval=False,
            do_doc_retrieval=False,
            do_search=False,
            )

# round-1
query_content = "remove 这个函数是用来做什么的"
query = Message(
    role_name="user", role_type="human", 
    role_content=query_content, input_query=query_content, origin_query=query_content,
    code_engine_name="client", score_threshold=1.0, top_k=3, cb_search_type="cypher"
    )

output_message1, _ = phase.step(query)

