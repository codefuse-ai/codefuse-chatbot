import os, sys, requests

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(src_dir)

# from configs.model_config import *
from coagent.connector.phase import BasePhase
from coagent.connector.agents import BaseAgent
from coagent.connector.chains import BaseChain
from coagent.connector.schema import (
    Message, Memory, load_role_configs, load_phase_configs, load_chain_configs
    )
from coagent.connector.configs import AGETN_CONFIGS, CHAIN_CONFIGS, PHASE_CONFIGS
from coagent.connector.utils import parse_section
import importlib


# update new agent configs
auto_feedback_from_code_execution_PROMPT = """#### Code React Assistance Guidance

You are a helpful AI assistant. Solve tasks using your coding and language skills.
In the following cases, suggest python code (in a python coding block) or shell script (in a sh coding block) for the user to execute.
    1. When you need to collect info, use the code to output the info you need, for example, browse or search the web, download/read a file, print the content of a webpage or a file, get the current date/time, check the operating system. After sufficient info is printed and the task is ready to be solved based on your language skill, you can solve the task by yourself.
    2. When you need to perform some task with code, use the code to perform the task and output the result. Finish the task smartly.
Solve the task step by step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.
When using code, you must indicate the script type in the code block. The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. The user can't modify your code. So do not suggest incomplete code which requires users to modify. Don't use a code block if it's not intended to be executed by the user.
If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.
Reply "stopped" in the end when everything is done.

#### Response Process

**Question:** First, clarify the problem to be solved.

**Thoughts:** Based on the question and observations above, provide the plan for executing this step.

**Action Status:** Set to 'stopped' or 'code_executing'. If it's 'stopped', the action is to provide the final answer to the original question. If it's 'code_executing', the action is to write the code.

**Action:** 
```python
# Write your code here
import os
...
```

**Observation:** Check the results and effects of the executed code.

... (Repeat this Thoughts/Action/Observation cycle as needed)

**Thoughts:** I now know the final answer

**Action Status:** stopped

**Action:** The final answer to the original input question


"""


AGETN_CONFIGS.update({
    "auto_feedback_from_code_execution": {
        "role": {
            "role_prompt": auto_feedback_from_code_execution_PROMPT,
            "role_type": "assistant",
            "role_name": "auto_feedback_from_code_execution",
            "role_desc": "",
            "agent_type": "ReactAgent"
            # "agent_type": "BaseAgent"
        },
        "chat_turn": 5,
        "stop": "\n**Observation:**",
        "focus_agents": [],
        "focus_message_keys": [],
    },
})
# update new chain configs
CHAIN_CONFIGS.update({
    "auto_feedback_from_code_executionChain": {
        "chain_name": "auto_feedback_from_code_executionChain",
        "chain_type": "BaseChain",
        "agents": ["auto_feedback_from_code_execution"],
        "chat_turn": 1,
        "do_checker": False,
        "chain_prompt": ""
    }
})

# update phase configs
PHASE_CONFIGS.update({
    "auto_feedback_from_code_executionPhase": {
        "phase_name": "auto_feedback_from_code_executionPhase",
        "phase_type": "BasePhase",
        "chains": ["auto_feedback_from_code_executionChain"],
        "do_summary": False,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_code_retrieval": False,
        "do_tool_retrieval": False,
        "do_using_tool": False
    },
})




role_configs = load_role_configs(AGETN_CONFIGS)
chain_configs = load_chain_configs(CHAIN_CONFIGS)
phase_configs = load_phase_configs(PHASE_CONFIGS)

agent_module = importlib.import_module("coagent.connector.agents")

# 
phase_name = "auto_feedback_from_code_executionPhase"
phase = BasePhase(phase_name, task = None,
            base_phase_config= PHASE_CONFIGS,
            base_chain_config= CHAIN_CONFIGS,
            base_role_config= AGETN_CONFIGS,
            )

# round-1
query_content = """
Find arxiv papers that show how are people studying trust calibration in AI based systems 
"""
query = Message(
    role_name="human", role_type="user", 
    role_content=query_content, input_query=query_content, origin_query=query_content,
    code_engine_name="client", score_threshold=1.0, top_k=3, cb_search_type="cypher"
    )

output_message1, _ = phase.step(query)


# 重复auto_gen 其余task即可
task2 = "analyze the above the results to list the application domains studied by these papers "

task3 = """Use this data to generate a bar chart of domains and number of papers in that domain and save to a file 
"""

task4 = """Reflect on the sequence and create a recipe containing all the steps 
necessary and name for it. Suggest well-documented, generalized python function(s)
 to perform similar tasks for coding steps in future. Make sure coding steps and 
 non-coding steps are never mixed in one function. In the docstr of the function(s),
 clarify what non-coding steps are needed to use the language skill of the assistant.
"""