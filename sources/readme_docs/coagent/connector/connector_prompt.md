---
title: Connector Prompt
slug: Connector Prompt ZH
url: "coagent/connector-prompt-zh"
aliases:
- "/coagent/connector-prompt-zh"
---

## Prompt 的标准结构
在整个Prompt的整个结构中，我们需要去定义三个部分
- Agent Profil
- Input Format
- Response Output Format

```
#### Agent Profile

Agent Description ...

#### Input Format

**Origin Query:** the initial question or objective that the user wanted to achieve

**Context:** the current status and history of the tasks to determine if Origin Query has been achieved.

#### Response Output Format
**Action Status:** finished or continued
If it's 'finished', the context can answer the origin query.
If it's 'continued', the context cant answer the origin query.

**REASON:** Justify the decision of choosing 'finished' and 'continued' by evaluating the progress step by step.
Consider all relevant information. If the tasks were aimed at an ongoing process, assess whether it has reached a satisfactory conclusion.
```


其中，我们整合了部分 `Input Format` 的通用操作，内置了一部分字段和操作流程,形成通用的配置化操作。如下所示
只需要定义如下字段和执行函数，

```
AUTO_FEEDBACK_FROM_CODE_EXECUTION_PROMPT_CONFIGS = [
    {"field_name": 'agent_profile', "function_name": 'handle_agent_profile', "is_context": False},
    {"field_name": 'context_placeholder', "function_name": '', "is_context": True},
    {"field_name": 'session_records', "function_name": 'handle_session_records'},
    {"field_name": 'output_format', "function_name": 'handle_output_format', 'title': 'Response Output Format', "is_context": False},
    {"field_name": 'begin!!!', "function_name": 'handle_response', "is_context": False, "omit_if_empty": False}
]
```

未来我们会也会进一步将 Agent Profile和Response Output Format的部分，实现可配置化操作，降低Prompt编写难度

### 自定义 Input Format
同时，我们也支持 用户自定义 Input Format 的操作

```
from coagent.connector.prompt_manager import PromptManager

# 增加了两个新处理函数，用于prompt组装
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
    {"field_name": 'reference_documents', "function_name": 'handle_doc_info'},
    {"field_name": 'session_records', "function_name": 'handle_session_records'},
    {"field_name": 'retrieval_codes', "function_name": 'handle_retrieval_codes'},
    {"field_name": 'code_packages', "function_name": 'handle_code_packages'},
    {"field_name": 'output_format', "function_name": 'handle_output_format', 'title': 'Response Output Format', "is_context": False},
    {"field_name": 'begin!!!', "function_name": 'handle_response', "is_context": False, "omit_if_empty": False}
    ]

# 进行注册
import importlib
prompt_manager_module = importlib.import_module("coagent.connector.prompt_manager")
setattr(prompt_manager_module, 'CodeRetrievalPM', CodeRetrievalPM)

# 更新配置
from coagent.connector.configs import AGETN_CONFIGS
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
    }）
```



在我们构建phase、chain或者agent之后，可以通过函数的预打印功能，实现agents链路确认，避免在执行后才发现问题，可提前进行debug
```
llm_config = LLMConfig(
    model_name="gpt-3.5-turbo", model_device="cpu",api_key=os.environ["OPENAI_API_KEY"], 
    api_base_url=os.environ["API_BASE_URL"], temperature=0.3
    )
embed_config = EmbedConfig(
    embed_engine="model", embed_model="text2vec-base-chinese", 
    embed_model_path="D://project/gitlab/llm/external/ant_code/Codefuse-chatbot/embedding_models/text2vec-base-chinese"
    )

phase_name = "baseGroupPhase"
phase = BasePhase(
    phase_name, embed_config=embed_config, llm_config=llm_config, 
)

phase.pre_print(query)

## 完整信息确认 coagent.connector.configs中进行确认
##########################
<<<<baseGroup's prompt>>>>
##########################

### Agent Profile
Your goal is to response according the Context Data's information with the role that will best facilitate a solution, taking into account all relevant context (Context) provided.
When you need to select the appropriate role for handling a user's query, carefully read the provided role names, role descriptions and tool list.
ATTENTION: response carefully referenced "Response Output Format" in format.

### Tool Information

### Agent Infomation
        Please ensure your selection is one of the listed roles. Available roles for selection:
        "role name: tool_react
role description:  Agent Profile,When interacting with users, your role is to respond in a helpful and accurate manner using the tools available. Follow the steps below to ensure efficient and effective use of the tools.,Please note that all the tools you can use are listed below. You can only choose from these tools for use. ,If there are no suitable tools, please do not invent any tools. Just let the user know that you do not have suitable tools to use.,ATTENTION: The Action Status field ensures that the tools or code mentioned in the Action can be parsed smoothly. Please make sure not to omit the Action Status field when replying.,"
"role name: code_react
role description:  Agent Profile,When users need help with coding, your role is to provide precise and effective guidance.,Write the code step by step, showing only the part necessary to solve the current problem. Each reply should contain only the code required for the current step.,"
        Please ensure select the Role from agent names, such as tool_react, code_react

### Context Data

#### Reference Documents

#### Session Records

#### Current Plan

### Response Output Format
**Thoughts:** think the reason step by step about why you selecte one role
**Role:** Select the role from agent names.

### Begin!!!

###################
<<<<LLM PREDICT>>>>
###################

**Thoughts:**
**Role:**


###########################
<<<<tool_react's prompt>>>>
###########################
### Agent Profile
When interacting with users, your role is to respond in a helpful and accurate manner using the tools available. Follow the steps below to ensure efficient and effective use of the tools.
Please note that all the tools you can use are listed below. You can only choose from these tools for use.
If there are no suitable tools, please do not invent any tools. Just let the user know that you do not have suitable tools to use.
ATTENTION: The Action Status field ensures that the tools or code mentioned in the Action can be parsed smoothly. Please make sure not to omit the Action Status field when replying.

### Tool Information

### Context Data

#### Reference Documents

#### Session Records

#### Task Records

### Response Output Format
**Thoughts:** According the previous observations, plan the approach for using the tool effectively.
...

### Begin!!!

###################
<<<<LLM PREDICT>>>>
###################
**Thoughts:**
**Action Status:**
**Action:**
**Observation:**
**Thoughts:**
**Action Status:**
**Action:**

###########################
<<<<code_react's prompt>>>>
###########################
### Agent Profile
When users need help with coding, your role is to provide precise and effective guidance.
Write the code step by step, showing only the part necessary to solve the current problem. Each reply should contain only the code required for the current step.

### Context Data

#### Reference Documents

#### Session Records

### Response Output Format

**Thoughts:** According the previous context, solve the problem step by step, only displaying the thought process necessary for the current step of solving the problem,
outline the plan for executing this step.

**Action Status:** Set to 'stopped' or 'code_executing'.
If it's 'stopped', the action is to provide the final answer to the session records and executed steps.
If it's 'code_executing', the action is to write the code.
...

### Begin!!!

###################
<<<<LLM PREDICT>>>>
###################

**Thoughts:**
**Action Status:**
**Action:**
**Observation:**
**Thoughts:**
**Action Status:**
**Action:**

```
