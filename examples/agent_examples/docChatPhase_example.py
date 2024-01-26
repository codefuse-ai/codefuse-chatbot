import os, sys

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(src_dir)
sys.path.append(os.path.join(src_dir, "examples"))

from configs.model_config import EMBEDDING_MODEL, CB_ROOT_PATH
from configs.model_config import KB_ROOT_PATH, JUPYTER_WORK_PATH
from configs.server_config import SANDBOX_SERVER
from coagent.tools import toLangchainTools, TOOL_DICT, TOOL_SETS
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig
from coagent.connector.phase import BasePhase
from coagent.connector.schema import Message, Memory


tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])
llm_config = LLMConfig(
    model_name="gpt-3.5-turbo", model_device="cpu",api_key=os.environ["OPENAI_API_KEY"], 
    api_base_url=os.environ["API_BASE_URL"], temperature=0.3
    )
embed_config = EmbedConfig(
    embed_engine="model", embed_model="text2vec-base-chinese", 
    embed_model_path=os.path.join(src_dir, "embedding_models/text2vec-base-chinese")
    )




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



## start to chat with knowledge base
    
# log-level，print prompt和llm predict
os.environ["log_verbose"] = "2"

# set chat phase
phase_name = "docChatPhase"
phase = BasePhase(
    phase_name, sandbox_server=SANDBOX_SERVER, jupyter_work_path=JUPYTER_WORK_PATH,
    embed_config=embed_config, llm_config=llm_config, kb_root_path=KB_ROOT_PATH,
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