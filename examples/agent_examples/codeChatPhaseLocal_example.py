# encoding: utf-8
'''
@author: 温进
@file: codeChatPhaseLocal_example.py
@time: 2024/1/31 下午4:32
@desc:
'''
import os, sys, requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

import requests
from typing import List

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(src_dir)

from configs.model_config import KB_ROOT_PATH, JUPYTER_WORK_PATH, CB_ROOT_PATH
from configs.server_config import SANDBOX_SERVER
from coagent.tools import toLangchainTools, TOOL_DICT, TOOL_SETS
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig
from coagent.connector.phase import BasePhase
from coagent.connector.schema import Message, Memory
from coagent.codechat.codebase_handler.codebase_handler import CodeBaseHandler



# log-level，print prompt和llm predict
os.environ["log_verbose"] = "1"

llm_config = LLMConfig(
    model_name="gpt-3.5-turbo", model_device="cpu",api_key=os.environ["OPENAI_API_KEY"],
    api_base_url=os.environ["API_BASE_URL"], temperature=0.3
    )
embed_config = EmbedConfig(
    embed_engine="model", embed_model="text2vec-base-chinese",
    embed_model_path=os.path.join(src_dir, "embedding_models/text2vec-base-chinese")
    )


# delete codebase
codebase_name = 'client_nebula'
code_path = '/Users/bingxu/Desktop/工作/大模型/chatbot/test_code_repo/client'
code_path = "D://chromeDownloads/devopschat-bot/client_v2/client"
use_nh = True
do_interpret = False
cbh = CodeBaseHandler(codebase_name, code_path, crawl_type='dir', use_nh=use_nh, local_graph_path=CB_ROOT_PATH,
                      llm_config=llm_config, embed_config=embed_config)
cbh.delete_codebase(codebase_name=codebase_name)

# initialize codebase
cbh = CodeBaseHandler(codebase_name, code_path, crawl_type='dir', use_nh=use_nh, local_graph_path=CB_ROOT_PATH,
                      llm_config=llm_config, embed_config=embed_config)
cbh.import_code(do_interpret=do_interpret)



# chat with codebase
phase_name = "codeChatPhase"
phase = BasePhase(
    phase_name, sandbox_server=SANDBOX_SERVER, jupyter_work_path=JUPYTER_WORK_PATH,
    embed_config=embed_config, llm_config=llm_config, kb_root_path=KB_ROOT_PATH,
)

# remove 这个函数是做什么的  => 基于标签
# 有没有函数已经实现了从字符串删除指定字符串的功能，使用的话可以怎么使用，写个java代码  => 基于描述
# 有根据我以下的需求用 java 开发一个方法：输入为字符串，将输入中的 .java 字符串给删除掉，然后返回新的字符串 => 基于描述

## 需要启动容器中的nebula，采用use_nh=True来构建代码库，是可以通过cypher来查询
# round-1
query_content = "代码一共有多少类"
query = Message(
    role_name="human", role_type="user",
    role_content=query_content, input_query=query_content, origin_query=query_content,
    code_engine_name="client_1", score_threshold=1.0, top_k=3, cb_search_type="cypher"
    )

output_message1, _ = phase.step(query)
print(output_message1)

# round-2
query_content = "代码库里有哪些函数，返回5个就行"
query = Message(
    role_name="human", role_type="user",
    role_content=query_content, input_query=query_content, origin_query=query_content,
    code_engine_name="client_1", score_threshold=1.0, top_k=3, cb_search_type="cypher"
    )
output_message2, _ = phase.step(query)
print(output_message2)


# round-3
query_content = "remove 这个函数是做什么的"
query = Message(
    role_name="user", role_type="human",
    role_content=query_content, input_query=query_content, origin_query=query_content,
    code_engine_name=codebase_name, score_threshold=1.0, top_k=3, cb_search_type="tag",
    use_nh=False, local_graph_path=CB_ROOT_PATH
    )
output_message3, output_memory3 = phase.step(query)
print(output_memory3.to_str_messages(return_all=True, content_key="parsed_output_list"))

#
# # round-4
query_content = "有没有函数已经实现了从字符串删除指定字符串的功能，使用的话可以怎么使用，写个java代码"
query = Message(
    role_name="human", role_type="user",
    role_content=query_content, input_query=query_content, origin_query=query_content,
    code_engine_name=codebase_name, score_threshold=1.0, top_k=3, cb_search_type="description",
    use_nh=False, local_graph_path=CB_ROOT_PATH
    )
output_message4, output_memory4 = phase.step(query)
print(output_memory4.to_str_messages(return_all=True, content_key="parsed_output_list"))


# # round-5
query_content = "有根据我以下的需求用 java 开发一个方法：输入为字符串，将输入中的 .java 字符串给删除掉，然后返回新的字符串"
query = Message(
    role_name="human", role_type="user",
    role_content=query_content, input_query=query_content, origin_query=query_content,
    code_engine_name=codebase_name, score_threshold=1.0, top_k=3, cb_search_type="description",
    use_nh=False, local_graph_path=CB_ROOT_PATH
    )
output_message5, output_memory5 = phase.step(query)
print(output_memory5.to_str_messages(return_all=True, content_key="parsed_output_list"))
