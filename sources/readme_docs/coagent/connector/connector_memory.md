---
title: Connector Memory
slug: Connector Memory ZH
url: "coagent/connector-memory-zh"
aliases:
- "/coagent/connector-memory-zh"
---


## Memory Manager
主要用于 chat history 的管理，暂未完成
- 将chat history在数据库进行读写管理，包括user input、 llm output、doc retrieval、code retrieval、search retrieval
- 对 chat history 进行关键信息总结 summary context，作为 prompt context
- 提供检索功能，检索 chat history 或者 summary context 中与问题相关信息，辅助问答



## 使用示例

### 创建 memory manager 实例
```
import os
import openai

from coagent.base_configs.env_config import KB_ROOT_PATH
from coagent.connector.memory_manager import BaseMemoryManager, LocalMemoryManager
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig
from coagent.connector.schema import Message

os.environ["API_BASE_URL"] = OPENAI_API_BASE
os.environ["OPENAI_API_KEY"] = "sk-xx"
openai.api_key = "sk-xxx"
# os.environ["OPENAI_PROXY"] = "socks5h://127.0.0.1:13659"
os.environ["DUCKDUCKGO_PROXY"] = os.environ.get("DUCKDUCKGO_PROXY") or "socks5://127.0.0.1:13659"

# LLM 和 Embedding Model 配置
llm_config = LLMConfig(
    model_name="gpt-3.5-turbo", model_device="cpu",api_key=os.environ["OPENAI_API_KEY"], 
    api_base_url=os.environ["API_BASE_URL"], temperature=0.3
    )
embed_config = EmbedConfig(
    embed_engine="model", embed_model="text2vec-base-chinese", 
    embed_model_path="D://project/gitlab/llm/external/ant_code/Codefuse-chatbot/embedding_models/text2vec-base-chinese"
    )

# 
phase_name = "test"
memory_manager = LocalMemoryManager(
            unique_name=phase_name, 
            do_init=True, 
            kb_root_path = KB_ROOT_PATH, 
            embed_config=embed_config, 
            llm_config=llm_config
        )
```

### 支持Message管理

```
message1 = Message(
    role_name="test1", role_type="user", input_query="hello", origin_query="hello",
    parsed_output_list=[{"input": "hello"}]
)

text = "hi! how can I help you?"
message2 = Message(
    role_name="test2", role_type="assistant", input_query=text, origin_query=text,
    role_content=text, step_content=text, parsed_output_list=[{"answer": text}]
)

text = "they say hello and hi to each other"
message3 = Message(
    role_name="test3", role_type="summary",
    role_content=text, step_content=text,
    parsed_output_list=[{"summary": text}]
    )

```

### 支持 memory 检索
```
# embedding retrieval test
text = "say hi, i want some help"
print(memory_manager.router_retrieval(text=text, datetime="2024-01-08 20:22:00", n=4, top_k=5, retrieval_type= "datetime"))
print(memory_manager.router_retrieval(text=text, datetime="2024-01-08 20:22:00", n=4, top_k=5, retrieval_type= "embedding"))
print(memory_manager.router_retrieval(text=text, datetime="2024-01-08 20:22:00", n=4, top_k=5, retrieval_type= "text"))

```
### 支持 memory 总结
```
# recursive_summary test
print(memory_manager.recursive_summary(local_memory_manager.recall_memory.messages, split_n=1))
```