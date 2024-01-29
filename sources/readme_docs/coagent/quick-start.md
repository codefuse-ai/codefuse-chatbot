---
title: 快速开始
slug: 快速开始
url: "coagent/快速开始"
aliases:
- "/coagent/快速开始"
- "/coagent/quick-start-zh"
---



## 快速使用
注意：
只在GPT-3.5-turbo及以上模型进行过测试。需要模型具备较强的指令遵循能力。
推荐拿qwen-72b、openai等较强的模型进行测试

### 首先，填写LLM配置
```
import os, sys
import openai

# llm config
os.environ["API_BASE_URL"] = OPENAI_API_BASE
os.environ["OPENAI_API_KEY"] = "sk-xxx"
openai.api_key = "sk-xxx"
# os.environ["OPENAI_PROXY"] = "socks5h://127.0.0.1:13659"
```

### 然后设置LLM配置和向量模型配置
```
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig

llm_config = LLMConfig(
    model_name="gpt-3.5-turbo", model_device="cpu",api_key=os.environ["OPENAI_API_KEY"], 
    api_base_url=os.environ["API_BASE_URL"], temperature=0.3
    )

embed_config = EmbedConfig(
    embed_engine="model", embed_model="text2vec-base-chinese", 
    embed_model_path="D://project/gitlab/llm/external/ant_code/Codefuse-chatbot/embedding_models/text2vec-base-chinese"
    )
```

### 最后选择一个已有场景进行执行
```
from coagent.tools import toLangchainTools, TOOL_DICT, TOOL_SETS
from coagent.connector.phase import BasePhase
from coagent.connector.schema import Message

# 选择一个已实现得场景进行执行

# 如果需要做一个数据分析，需要将数据放到某个工作目录，同时指定工作目录（也可使用默认目录）
import shutil
source_file = 'D://project/gitlab/llm/external/ant_code/Codefuse-chatbot/jupyter_work/book_data.csv'
shutil.copy(source_file, JUPYTER_WORK_PATH)

# 选择一个场景
phase_name = "baseGroupPhase"
phase = BasePhase(
    phase_name, embed_config=embed_config, llm_config=llm_config, 
)

# round-1 需要通过代码解释器来完成
query_content = "确认本地是否存在employee_data.csv，并查看它有哪些列和数据类型;然后画柱状图"
query = Message(
    role_name="human", role_type="user", tools=[],
    role_content=query_content, input_query=query_content, origin_query=query_content,
    )

# phase.pre_print(query)  # 该功能用于预打印 Agents 执行链路的Prompt
output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))

# round-2 需要执行工具
tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])

query_content = "帮我确认下127.0.0.1这个服务器的在10点是否存在异常，请帮我判断一下"
query = Message(
    role_name="human", role_type="user", tools=tools,
    role_content=query_content, input_query=query_content, origin_query=query_content,
    )

# phase.pre_print(query)  # 该功能用于预打印 Agents 执行链路的Prompt
output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))

```

## 场景介绍和使用

下面是一些具体的场景介绍和使用。

欢迎大家开脑洞构造一些有趣的case。

### baseGroupPhase
autogen的group使用场景

```
# 如果需要做一个数据分析，需要将数据放到某个工作目录，同时指定工作目录（也可使用默认目录）
import shutil
source_file = 'D://project/gitlab/llm/external/ant_code/Codefuse-chatbot/jupyter_work/book_data.csv'
shutil.copy(source_file, JUPYTER_WORK_PATH)

# 设置日志级别，控制打印prompt或者llm 输出或其它信息
os.environ["log_verbose"] = "0"

phase_name = "baseGroupPhase"
phase = BasePhase(
    phase_name, embed_config=embed_config, llm_config=llm_config, 
)

# round-1
query_content = "确认本地是否存在book_data.csv，并查看它有哪些列和数据类型;然后画柱状图"

query = Message(
    role_name="human", role_type="user", tools=[],
    role_content=query_content, input_query=query_content, origin_query=query_content,
    )

# phase.pre_print(query) # 该功能用于预打印 Agents 执行链路的Prompt
output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
```

### baseTaskPhase
xAgents的任务拆分及多步骤执行场景

```
# if you want to analyze a data.csv, please put the csv file into a jupyter_work_path (or your defined path)
import shutil
source_file = 'D://project/gitlab/llm/external/ant_code/Codefuse-chatbot/jupyter_work/book_data.csv'
shutil.copy(source_file, JUPYTER_WORK_PATH)

# log-level，print prompt和llm predict
os.environ["log_verbose"] = "2"

phase_name = "baseTaskPhase"
phase = BasePhase(
    phase_name, embed_config=embed_config, llm_config=llm_config,
)
# round-1
query_content = "确认本地是否存在book_data.csv，并查看它有哪些列和数据类型;然后画柱状图"
query = Message(
    role_name="human", role_type="user",
    role_content=query_content, input_query=query_content, origin_query=query_content,
    )

output_message, output_memory = phase.step(query)

print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
```


### codeReactPhase
基于 React 的代码解释器场景

```
# if you want to analyze a data.csv, please put the csv file into a jupyter_work_path (or your defined path)
import shutil
source_file = 'D://project/gitlab/llm/external/ant_code/Codefuse-chatbot/jupyter_work/book_data.csv'
shutil.copy(source_file, JUPYTER_WORK_PATH)

# then, create a data analyze phase
phase_name = "codeReactPhase"
phase = BasePhase(
    phase_name, embed_config=embed_config, llm_config=llm_config, 
    jupyter_work_path=JUPYTER_WORK_PATH,
)

# round-1
query_content = "确认本地是否存在book_data.csv，并查看它有哪些列和数据类型;然后画柱状图"
query = Message(
    role_name="human", role_type="user",
    role_content=query_content, input_query=query_content, origin_query=query_content,
    )

output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
```

### codeToolReactPhase
基于 React 模板的工具调用和代码解释器场景


```
TOOL_SETS = [
     "StockName", "StockInfo", 
    ]
tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])

# log-level，print prompt和llm predict
os.environ["log_verbose"] = "2"

phase_name = "codeToolReactPhase"

phase = BasePhase(
    phase_name, embed_config=embed_config, llm_config=llm_config, 
)

query_content = "查询贵州茅台的股票代码，并查询截止到当前日期(2023年12月24日)的最近10天的每日时序数据，然后用代码画出折线图并分析"

query = Message(
  role_name="human", role_type="user", 
  input_query=query_content, role_content=query_content, 
  origin_query=query_content, tools=tools
  )

output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
```


### docChatPhase
知识库检索问答链路
```
# create your knowledge base
from io import BytesIO
from pathlib import Path

from coagent.service.kb_api import create_kb, upload_doc
from coagent.service.service_factory import get_kb_details
from coagent.utils.server_utils import run_async
kb_list = {x["kb_name"]: x for x in get_kb_details(KB_ROOT_PATH)}


# create a knowledge base
kb_name = "example_test"
data = {
    "knowledge_base_name": kb_name,
    "vector_store_type": "faiss", # default
    "kb_root_path": KB_ROOT_PATH, 
    "embed_model": embed_config.embed_model,
    "embed_engine": embed_config.embed_engine, 
    "embed_model_path": embed_config.embed_model_path,
    "model_device": embed_config.model_device,
}
run_async(create_kb(**data))

# add doc to knowledge base
file = os.path.join("D://project/gitlab/llm/external/ant_code/Codefuse-chatbot/sources/docs/langchain_text_10.jsonl")
files = [file]
# if embedding init failed, you can use override = True
data = [{"override": True, "file": f, 
         "knowledge_base_name": kb_name, "not_refresh_vs_cache": False,
         "kb_root_path": KB_ROOT_PATH, "embed_model": embed_config.embed_model,
         "embed_engine": embed_config.embed_engine, "embed_model_path": embed_config.embed_model_path,
         "model_device": embed_config.model_device,
         } 
         for f in files]

for k in data:
    file = Path(file).absolute().open("rb")
    filename = file.name

    from fastapi import UploadFile
    from tempfile import SpooledTemporaryFile

    temp_file = SpooledTemporaryFile(max_size=10 * 1024 * 1024)
    temp_file.write(file.read())
    temp_file.seek(0)
    
    k.update({"file": UploadFile(file=temp_file, filename=filename),})
    run_async(upload_doc(**k))


# start to chat with knowledge base
# log-level，print prompt和llm predict
os.environ["log_verbose"] = "2"

# set chat phase
phase_name = "docChatPhase"
phase = BasePhase(
    phase_name, embed_config=embed_config, llm_config=llm_config,
)
# round-1
query_content = "langchain有哪些模块"
query = Message(
    role_name="human", role_type="user", 
    origin_query=query_content,
    doc_engine_name=kb_name, score_threshold=1.0, top_k=3
    )

output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))

# round-2
query_content = "提示（prompts）有什么用？"
query = Message(
    role_name="human", role_type="user",
    origin_query=query_content,
    doc_engine_name=kb_name, score_threshold=1.0, top_k=3
    )
output_message, output_memory = phase.step(query)

print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
```


### metagpt_code_devlop
metagpt的代码构造链路

```
# log-level，print prompt和llm predict
os.environ["log_verbose"] = "2"

phase_name = "metagpt_code_devlop"
llm_config = LLMConfig(
    model_name="gpt-4", model_device="cpu",api_key=os.environ["OPENAI_API_KEY"], 
    api_base_url=os.environ["API_BASE_URL"], temperature=0.3
    )
embed_config = EmbedConfig(
    embed_engine="model", embed_model="text2vec-base-chinese", 
    embed_model_path="D://project/gitlab/llm/external/ant_code/Codefuse-chatbot/embedding_models/text2vec-base-chinese"
    )

phase = BasePhase(
    phase_name, embed_config=embed_config, llm_config=llm_config,
)

query_content = "create a snake game by pygame"
query = Message(role_name="human", role_type="user", input_query=query_content, role_content=query_content, origin_query=query_content)

output_message, output_memory = phase.step(query)

print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
```


### searchChatPhase
固定场景链路，先搜索后基于LLM直接回答

```
# log-level，print prompt和llm predict
os.environ["log_verbose"] = "2"

phase_name = "searchChatPhase"
phase = BasePhase(
    phase_name, embed_config=embed_config, llm_config=llm_config, 
)

# round-1
query_content1 = "美国当前总统是谁？"
query = Message(
    role_name="human", role_type="user", 
    role_content=query_content1, input_query=query_content1, origin_query=query_content1,
    search_engine_name="duckduckgo", score_threshold=1.0, top_k=3
    )

output_message, output_memory = phase.step(query)

print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))

# round-2
query_content2 = "美国上一任总统是谁，两个人有什么关系没？"
query = Message(
    role_name="human", role_type="user", 
    role_content=query_content2, input_query=query_content2, origin_query=query_content2,
    search_engine_name="duckduckgo", score_threshold=1.0, top_k=3
    )
output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
```


### toolReactPhase
基于 React 模板的工具调用场景

```
# log-level，print prompt和llm predict
os.environ["log_verbose"] = "2"

phase_name = "toolReactPhase"
phase = BasePhase(
    phase_name, embed_config=embed_config, llm_config=llm_config,
)

# round-1
tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])
query_content = "帮我确认下127.0.0.1这个服务器的在10点是否存在异常，请帮我判断一下"
query = Message(
    role_name="human", role_type="user", tools=tools,
    role_content=query_content, input_query=query_content, origin_query=query_content
    )

# phase.pre_print(query)  # 该功能用于预打印 Agents 执行链路的Prompt
output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
```