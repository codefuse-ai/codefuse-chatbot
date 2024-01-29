---
title: Connector Chain
slug: Connector Chain ZH
url: "coagent/connector-chain-zh"
aliases:
- "/coagent/connector-chain-zh"
---

## 快速构建一个 agent chain
- 首先增加openai配置，也可以是其它类似于openai接口的模型（通过fastchat启动）
```
# 设置openai的api-key
import os, sys
import openai
import importlib

os.environ["API_BASE_URL"] = OPENAI_API_BASE
os.environ["OPENAI_API_KEY"] = "sk-xxxx"
openai.api_key = "sk-xxxx"
# os.environ["OPENAI_PROXY"] = "socks5h://127.0.0.1:13659"
os.environ["DUCKDUCKGO_PROXY"] = os.environ.get("DUCKDUCKGO_PROXY") or "socks5://127.0.0.1:13659"
```

- 配置相关 LLM 和 Embedding Model
```
# LLM 和 Embedding Model 配置
llm_config = LLMConfig(
    model_name="gpt-3.5-turbo", model_device="cpu",api_key=os.environ["OPENAI_API_KEY"], 
    api_base_url=os.environ["API_BASE_URL"], temperature=0.3
    )
embed_config = EmbedConfig(
    embed_engine="model", embed_model="text2vec-base-chinese", 
    embed_model_path="D://project/gitlab/llm/external/ant_code/Codefuse-chatbot/embedding_models/text2vec-base-chinese"
    )
```


- 这里从已有的agent配置选多个role组合成 agent chain
```
from coagent.base_configs.env_config import JUPYTER_WORK_PATH, KB_ROOT_PATH
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig
from coagent.connector.configs import AGETN_CONFIGS
from coagent.connector.chains import BaseChain
from coagent.connector.schema import Message, load_role_configs

# 构建 agent chain 链路
role_configs = load_role_configs(AGETN_CONFIGS)
agent_config = role_configs["general_planner"]
role1 = role_configs["general_planner"]
role2 = role_configs["executor"]
agent_module = importlib.import_module("examples.connector.agents")
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
```


- 开始执行
```
# round-1
query_content = "确认本地是否存在employee_data.csv，并查看它有哪些列和数据类型;然后画柱状图"
query = Message(
    role_name="human", role_type="user",
    role_content=query_content, input_query=query_content, origin_query=query_content,
    )

output_message, output_memory = chain.step(query)
print(output_memory.to_str_messages(content_key="parsed_output_list"))

```


## Chain 参数配置
|Config Key Name|	Type	|Description|
| ------------------ | ---------- | ---------- |
|agents| List[BaseAgent] | 
|llm_config	|LLMConfig	|大语言模型配置|
|embed_config	|EmbedConfig	|向量模型配置|
|sandbox_server	|Dict	|沙盒环境即notebook启动配置|
|jupyter_work_path	|str	|沙盒环境的工作目录|
|kb_root_path	|str	|memory的存储路径|
|log_verbose	|str	|agent prompt&predict的日志打印级别|
