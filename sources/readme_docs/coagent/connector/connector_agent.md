---
title: Connector Agent
slug: Connector Agent ZH
url: "coagent/connector-agent-zh"
aliases:
- "/coagent/connector-agent-zh"
---


## 快速构建一个Agent
- 首先增加openai配置，也可以是其它类似于openai接口的模型（通过fastchat启动）
```
from coagent.base_configs.env_config import JUPYTER_WORK_PATH, KB_ROOT_PATH
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig
from coagent.connector.configs import AGETN_CONFIGS
from coagent.connector.agents import BaseAgent
from coagent.connector.schema import Message, load_role_configs


os.environ["API_BASE_URL"] = OPENAI_API_BASE
os.environ["OPENAI_API_KEY"] = "sk-xx"
openai.api_key = "sk-xxx"
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

- 这里从已有的agent配置选一个role来做示例
```
# 从已有的配置中选择一个config，具体参数细节见下面
role_configs = load_role_configs(AGETN_CONFIGS)
agent_config = role_configs["general_planner"]
# 生成agent实例
base_agent = BaseAgent(
    role=agent_config.role, 
    prompt_config = agent_config.prompt_config,
    prompt_manager_type=agent_config.prompt_manager_type,
    chat_turn=agent_config.chat_turn,
    focus_agents=[],
    focus_message_keys=[],
    llm_config=llm_config,
    embed_config=embed_config,
    jupyter_work_path=JUPYTER_WORK_PATH,
    kb_root_path=KB_ROOT_PATH,
    ) 
# round-1
query_content = "确认本地是否存在employee_data.csv，并查看它有哪些列和数据类型;然后画柱状图"
query = Message(
    role_name="human", role_type="user",
    role_content=query_content, input_query=query_content, origin_query=query_content,
    )

output_message = base_agent.step(query)
print(output_message.to_str_content(content_key="parsed_output_list"))
```

## Agent 参数配置
```
# 配置结构在这个目录
from coagent.connector.schema import Role, PromptField
```


### Agent Config
|Config Key Name|	Type|	Description|
| ------------------ | ---------- | ---------- |
|role|	Role	|角色描述|
|prompt_config	|List[PromptField]	|Enum：PromptManager 也可以继承以上几种Agent然后去构造相关的Agent|
|prompt_manager_type	|String	|Enum：PromptManager 也可以继承以上几种Agent然后去构造自定义的Enum：PromptManager|
|focus_agents	|List[String]	|metagpt的逻辑，关注哪些agent生成的message，可选值范围为：role_name
|focus_message_keys	|List[String]|	额外增加的逻辑，关注message里面具体的 key 信息可选值范围为：agent 的 output_keys|
|chat_turn	|int	|只针对ReactAgent有效|
|llm_config	|LLMConfig	|大语言模型配置|
|embed_config	|EmbedConfig	|向量模型配置|
|sandbox_server	|Dict	|沙盒环境即notebook启动配置|
|jupyter_work_path	|str	|沙盒环境的工作目录|
|kb_root_path	|str	|memory的存储路径|
|log_verbose	|str	|agent prompt&predict的日志打印级别|

### Role

| Config Key Name  | Type | Description        |
|------------------|------|--------------------|
| role_type        | str  | 角色类型, Enum: system、user、assistant、function、observation、summary           |
| role_name        | str  | 角色名称           |
| role_desc        | str  | 角色描述           |
| agent_type       | str  | 代理类型           |
| role_prompt      | str  | 角色提示           |
| template_prompt  | str  | 模板提示           |


### PromptField

| Config Key Name | Type | Description |
|-----------------|------|-------------|
| field_name      | str  |             |
| function_name   | str  |             |
| title           | str  |             |
| description     | str  |             |
| is_context      | bool |             |
| omit_if_empty   | bool |             |