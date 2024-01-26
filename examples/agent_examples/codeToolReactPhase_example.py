import os, sys, requests

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(src_dir)

from configs.model_config import KB_ROOT_PATH, JUPYTER_WORK_PATH, LLM_MODEL
from configs.server_config import SANDBOX_SERVER
from coagent.tools import toLangchainTools, TOOL_DICT, TOOL_SETS
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig

from coagent.connector.phase import BasePhase
from coagent.connector.schema import Message


TOOL_SETS = [
     "StockName", "StockInfo", 
    ]
tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])

# log-level，print prompt和llm predict
os.environ["log_verbose"] = "2"

phase_name = "codeToolReactPhase"
llm_config = LLMConfig(
    model_name="gpt-3.5-turbo-0613", model_device="cpu",api_key=os.environ["OPENAI_API_KEY"], 
    api_base_url=os.environ["API_BASE_URL"], temperature=0.7
    )
embed_config = EmbedConfig(
    embed_engine="model", embed_model="text2vec-base-chinese", 
    embed_model_path=os.path.join(src_dir, "embedding_models/text2vec-base-chinese")
    )
phase = BasePhase(
    phase_name, sandbox_server=SANDBOX_SERVER, jupyter_work_path=JUPYTER_WORK_PATH,
    embed_config=embed_config, llm_config=llm_config, kb_root_path=KB_ROOT_PATH,
)

query_content = "查询贵州茅台的股票代码，并查询截止到当前日期(2023年12月24日)的最近10天的每日时序数据，然后用代码画出折线图并分析"

query = Message(role_name="human", role_type="user", input_query=query_content, role_content=query_content, origin_query=query_content, tools=tools)

output_message, output_memory = phase.step(query)
print(output_memory.to_str_messages(return_all=True, content_key="parsed_output_list"))