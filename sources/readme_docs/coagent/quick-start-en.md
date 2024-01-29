---
title: Quick Start
slug: Quick Start
url: "coagent/quick-start"
aliases:
- "/coagent/quick-start"
---





## Quick Start
### First, set up the LLM configuration
```
import os, sys
import openai

# llm config
os.environ["API_BASE_URL"] = OPENAI_API_BASE
os.environ["OPENAI_API_KEY"] = "sk-xxx"
openai.api_key = "sk-xxx"
# os.environ["OPENAI_PROXY"] = "socks5h://127.0.0.1:13659"
```

### Next, configure the LLM settings and vector model
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

### Finally, choose a pre-existing scenario to execute
```
from coagent.tools import toLangchainTools, TOOL_DICT, TOOL_SETS
from coagent.connector.phase import BasePhase
from coagent.connector.schema import Message

# Copy the data to a working directory; specify the directory if needed (default can also be used)
import shutil
source_file = 'D://project/gitlab/llm/external/ant_code/Codefuse-chatbot/jupyter_work/book_data.csv'
shutil.copy(source_file, JUPYTER_WORK_PATH)

# Choose a scenario to execute
phase_name = "baseGroupPhase"
phase = BasePhase(
    phase_name, embed_config=embed_config, llm_config=llm_config, 
)

# round-1: Use a code interpreter to complete tasks
query_content = "Check if 'employee_data.csv' exists locally, view its columns and data types; then draw a bar chart"
query = Message(
    role_name="human", role_type="user", tools=[],
    role_content=query_content, input_query=query_content, origin_query=query_content,
    )

# phase.pre_print(query)  # This function is used to preview the Prompt of the Agents' execution chain
output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))

# round-2: Execute tools
tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])

query_content = "Please check if there were any issues with the server at 127.0.0.1 at 10 o'clock; help me make a judgment"
query = Message(
    role_name="human", role_type="user", tools=tools,
    role_content=query_content, input_query=query_content, origin_query=query_content,
    )

# phase.pre_print(query)  # This function is used to preview the Prompt of the Agents' execution chain
output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))

```

## Phase Introduction and Usage

Below are some specific Phase introduced and how to use them.

Feel free to brainstorm and create some interesting cases.

### baseGroupPhase
The group usage Phase in autogen

```
# Copy the data to a working directory; specify the directory if needed (default can also be used)
import shutil
source_file = 'D://project/gitlab/llm/external/ant_code/Codefuse-chatbot/jupyter_work/book_data.csv'
shutil.copy(source_file, JUPYTER_WORK_PATH)

# Set the log level to control the printing of the prompt, LLM output, or other information
os.environ["log_verbose"] = "0"

phase_name = "baseGroupPhase"
phase = BasePhase(
    phase_name, embed_config=embed_config, llm_config=llm_config, 
)

# round-1
query_content = "Check if 'employee_data.csv' exists locally, view its columns and data types; then draw a bar chart"

query = Message(
    role_name="human", role_type="user", tools=[],
    role_content=query_content, input_query=query_content, origin_query=query_content,
    )

# phase.pre_print(query) # This function is used to preview the Prompt of the Agents' execution chain
output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
```

### baseTaskPhase
The task splitting and multi-step execution scenario in xAgents

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
query_content = "Check if 'employee_data.csv' exists locally, view its columns and data types; then draw a bar chart"
query = Message(
    role_name="human", role_type="user",
    role_content=query_content, input_query=query_content, origin_query=query_content,
    )

output_message, output_memory = phase.step(query)

print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
```


### codeReactPhase
The code interpreter scenario based on React

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
query_content = "Check if 'employee_data.csv' exists locally, view its columns and data types; then draw a bar chart"
query = Message(
    role_name="human", role_type="user",
    role_content=query_content, input_query=query_content, origin_query=query_content,
    )

output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
```

### codeToolReactPhase
The tool invocation and code interpreter scenario based on the React template


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
The knowledge base retrieval Q&A Phase

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
query_content = "what modules does langchain have?"
query = Message(
    role_name="human", role_type="user", 
    origin_query=query_content,
    doc_engine_name=kb_name, score_threshold=1.0, top_k=3
    )

output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))

# round-2
query_content = "What is the purpose of prompts?"
query = Message(
    role_name="human", role_type="user",
    origin_query=query_content,
    doc_engine_name=kb_name, score_threshold=1.0, top_k=3
    )
output_message, output_memory = phase.step(query)

print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
```


### metagpt_code_devlop
The code construction Phase in metagpt

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
The fixed Phase: search first, then answer directly with LLM

```
# log-level，print prompt和llm predict
os.environ["log_verbose"] = "2"

phase_name = "searchChatPhase"
phase = BasePhase(
    phase_name, embed_config=embed_config, llm_config=llm_config, 
)

# round-1
query_content1 = "who is the president of the United States?"
query = Message(
    role_name="human", role_type="user", 
    role_content=query_content1, input_query=query_content1, origin_query=query_content1,
    search_engine_name="duckduckgo", score_threshold=1.0, top_k=3
    )

output_message, output_memory = phase.step(query)

print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))

# round-2
query_content2 = "Who was the previous president of the United States, and is there any relationship between the two individuals?"
query = Message(
    role_name="human", role_type="user", 
    role_content=query_content2, input_query=query_content2, origin_query=query_content2,
    search_engine_name="duckduckgo", score_threshold=1.0, top_k=3
    )
output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
```


### toolReactPhase
The tool invocation scene based on the React template

```
# log-level，print prompt和llm predict
os.environ["log_verbose"] = "2"

phase_name = "toolReactPhase"
phase = BasePhase(
    phase_name, embed_config=embed_config, llm_config=llm_config,
)

# round-1
tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])
query_content = "Please check if there were any issues with the server at 127.0.0.1 at 10 o'clock; help me make a judgment"
query = Message(
    role_name="human", role_type="user", tools=tools,
    role_content=query_content, input_query=query_content, origin_query=query_content
    )

# phase.pre_print(query)  # This function is used to preview the Prompt of the Agents' execution chain
output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))
```