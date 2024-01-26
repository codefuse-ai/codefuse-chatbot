---
title: Customed Examples
slug: Customed Examples ZH
url: "coagent/customed-examples-zh"
aliases:
- "/coagent/customed-examples-zh"
---


## 如何创建你个性化的 agent phase 场景

下面通过 autogen 的 auto_feedback_from_code_execution 构建过来，来详细演示如何自定义一个 agent phase 的构建

### 设计你的prompt结构
```
import os, sys, requests

# from configs.model_config import *
from coagent.connector.phase import BasePhase
from coagent.connector.chains import BaseChain
from coagent.connector.schema import Message
from coagent.connector.configs import AGETN_CONFIGS, CHAIN_CONFIGS, PHASE_CONFIGS
import importlib


# update new agent configs
auto_feedback_from_code_execution_PROMPT = """#### Agent Profile

You are a helpful AI assistant. Solve tasks using your coding and language skills.
In the following cases, suggest python code (in a python coding block) or shell script (in a sh coding block) for the user to execute.
    1. When you need to collect info, use the code to output the info you need, for example, browse or search the web, download/read a file, print the content of a webpage or a file, get the current date/time, check the operating system. After sufficient info is printed and the task is ready to be solved based on your language skill, you can solve the task by yourself.
    2. When you need to perform some task with code, use the code to perform the task and output the result. Finish the task smartly.
Solve the task step by step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.
When using code, you must indicate the script type in the code block. The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. The user can't modify your code. So do not suggest incomplete code which requires users to modify. Don't use a code block if it's not intended to be executed by the user.
If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.
Reply "stopped" in the end when everything is done.

ATTENTION: The Action Status field ensures that the tools or code mentioned in the Action can be parsed smoothly. Please make sure not to omit the Action Status field when replying.

#### Response Output Format

**Thoughts:** Based on the question and observations above, provide the plan for executing this step.

**Action Status:** Set to 'stopped' or 'code_executing'. If it's 'stopped', the action is to provide the final answer to the original question. If it's 'code_executing', the action is to write the code.

**Action:** 
# Write your code here
import os
...


**Observation:** Check the results and effects of the executed code.

... (Repeat this Thoughts/Action/Observation cycle as needed)

**Thoughts:** I now know the final answer

**Action Status:** stopped

**Action:** The final answer to the original input question
"""
```

### 开始配置 Prompt Configs
```
AUTO_FEEDBACK_FROM_CODE_EXECUTION_PROMPT_CONFIGS = [
    {"field_name": 'agent_profile', "function_name": 'handle_agent_profile', "is_context": False},
    {"field_name": 'context_placeholder', "function_name": '', "is_context": True},
    {"field_name": 'session_records', "function_name": 'handle_session_records'},
    {"field_name": 'output_format', "function_name": 'handle_output_format', 'title': 'Response Output Format', "is_context": False},
    {"field_name": 'begin!!!', "function_name": 'handle_response', "is_context": False, "omit_if_empty": False}
]
```

### 更新完整的agent、chain、phase配置，以便后续更读取执行
```
from coagent.connector.configs import AGETN_CONFIGS, CHAIN_CONFIGS, PHASE_CONFIGS
import os

## set a 
AGETN_CONFIGS.update({
    "auto_feedback_from_code_execution": {
        "role": {
            "role_prompt": auto_feedback_from_code_execution_PROMPT,
            "role_type": "assistant",
            "role_name": "auto_feedback_from_code_execution",
            "role_desc": "",
            "agent_type": "ReactAgent"
        },
        "prompt_config": AUTO_FEEDBACK_FROM_CODE_EXECUTION_PROMPT_CONFIGS,
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

```



### 接下来就构建 phase 实例，开始执行
```
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig
from coagent.connector.phase import BasePhase
from coagent.connector.schema import Message
import base64, openai

#
os.environ["API_BASE_URL"] = "http://openai.com/v1/chat/completions"
os.environ["OPENAI_API_KEY"] = "sk-xxxx"
openai.api_key = "sk-xxxx"

llm_config = LLMConfig(
    model_name="gpt-3.5-turbo", model_device="cpu",api_key=os.environ["OPENAI_API_KEY"], 
    api_base_url=os.environ["API_BASE_URL"], temperature=0.3
    )

embed_config = EmbedConfig(
    embed_engine="model", embed_model="text2vec-base-chinese", 
    embed_model_path="D://project/gitlab/llm/external/ant_code/Codefuse-chatbot/embedding_models/text2vec-base-chinese"
    )


# log-level，print prompt和llm predict
os.environ["log_verbose"] = "2"

# 
phase_name = "auto_feedback_from_code_executionPhase"
phase = BasePhase(
    phase_name,
    embed_config=embed_config, llm_config=llm_config, 
    base_phase_config = PHASE_CONFIGS,
    base_chain_config = CHAIN_CONFIGS,
    base_role_config = AGETN_CONFIGS,
)


# round-1
query_content = """Plot a chart of META and TESLA's stock prices for the past year and save it as stock_price_ytd.png."""
query = Message(
    role_name="human", role_type="user", 
    role_content=query_content, input_query=query_content, origin_query=query_content,
    )

output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
```