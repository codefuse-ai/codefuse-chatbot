import streamlit as st
import docker
import torch, os, sys, json
from loguru import logger 

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(src_dir)
from configs.default_config import *

import platform
system_name = platform.system()


VERSION = "v0.1.0"

MODEL_WORKER_SETS = [
    "ChatGLMWorker", "MiniMaxWorker", "XingHuoWorker", "QianFanWorker", "FangZhouWorker",
    "QwenWorker", "BaiChuanWorker", "AzureWorker", "TianGongWorker", "ExampleWorker"
]

openai_models = ["gpt-3.5-turbo", "gpt-3.5-turbo-1106", "gpt-3.5-turbo-16k", "gpt-4", 'yi-34b-chat-0205']
embedding_models = ["openai"]


st.write("启动配置页面！")

st.write("如果你要使用语言模型，请将LLM放到 ~/Codefuse-chatbot/llm_models")

st.write("如果你要使用向量模型，请将向量模型放到 ~/Codefuse-chatbot/embedding_models")

with st.container():

    col1, col2 = st.columns(2)
    with col1.container():
        llm_model_name = st.selectbox('LLM Model Name', openai_models + [i for i in os.listdir(LOCAL_LLM_MODEL_DIR) if os.path.isdir(os.path.join(LOCAL_LLM_MODEL_DIR, i))])

        llm_apikey = st.text_input('Give Your LLM API Key', 'EMPTY')
        llm_apiurl = st.text_input('Give Your LLM API Url', 'http://localhost:8888/v1')

        llm_engine = st.selectbox('选择哪个llm引擎', ["online", "fastchat", "fastchat-vllm"])
        llm_model_port = st.text_input('LLM Model Port，非fastchat模式可无视', '20006')
        llm_provider_option = st.selectbox('选择哪个online模型加载器，非online可无视', ["openai", "lingyiwanwu"] + MODEL_WORKER_SETS)

        if llm_engine == "online" and llm_provider_option == "openai":
            try:
                from zdatafront.client import ZDF_COMMON_QUERY_URL
                OPENAI_API_BASE = ZDF_COMMON_QUERY_URL
            except:
                OPENAI_API_BASE = "https://api.openai.com/v1"
            llm_apiurl = OPENAI_API_BASE

        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

        FSCHAT_MODEL_WORKERS = {
            llm_model_name: {
                'host': "127.0.0.1", 'port': llm_model_port,
                "device": device,
                # todo: 多卡加载需要配置的参数
                "gpus": None,
                "numgpus": 1,},
        }


        ONLINE_LLM_MODEL, llm_model_dict, VLLM_MODEL_DICT = {}, {}, {}
        if llm_engine == "online":
            ONLINE_LLM_MODEL = {
                llm_model_name: {
                    "model_name": llm_model_name,
                    "version": llm_model_name,
                    "api_base_url": llm_apiurl, # "https://api.openai.com/v1",
                    "api_key": llm_apikey,
                    "openai_proxy": "",
                    "provider": llm_provider_option,
                },
            }
        
        if llm_engine == "fastchat":
            llm_model_dict = {
                llm_model_name: {
                    "local_model_path": llm_model_name,
                    "api_base_url": llm_apiurl,  # "name"修改为fastchat服务中的"api_base_url"
                    "api_key": llm_apikey
                    }}


        if llm_engine == "fastchat-vllm":
            VLLM_MODEL_DICT = {
                llm_model_name: {
                    "local_model_path": llm_model_name,
                    "api_base_url": llm_apiurl,  # "name"修改为fastchat服务中的"api_base_url"
                    "api_key": llm_apikey
                    }
            }
            llm_model_dict = {
                llm_model_name: {
                    "local_model_path": llm_model_name,
                    "api_base_url": llm_apiurl,  # "name"修改为fastchat服务中的"api_base_url"
                    "api_key": llm_apikey
                    }}
            

    with col2.container():
        em_model_name = st.selectbox('Embedding Model Name', [i for i in os.listdir(LOCAL_EM_MODEL_DIR) if os.path.isdir(os.path.join(LOCAL_EM_MODEL_DIR, i))] + embedding_models)
        em_engine = st.selectbox('选择哪个embedding引擎', ["model", "openai"])
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        embedding_model_dict = {em_model_name: em_model_name}
        em_apikey = st.text_input("Embedding API KEY (it can't work now)", 'EMPTY')
        em_apiurl = st.text_input("Embedding API URL (it can't work now)", 'http://localhost:8888/v1')

# 
try:
    client = docker.from_env()
    has_docker = True
except:
    has_docker = False

if has_docker:
    with st.container():
        DOCKER_SERVICE = st.toggle('DOCKER_SERVICE', True)
        SANDBOX_DO_REMOTE = st.toggle('SANDBOX_DO_REMOTE', True)
else:
    DOCKER_SERVICE = False
    SANDBOX_DO_REMOTE = False


with st.container():
    cols = st.columns(3)

    if cols[0].button(
        "重启服务，按前配置生效",
        use_container_width=True,
    ):
        from start import start_main
        from stop import stop_main
        stop_main()
        start_main()
    if cols[1].button(
        "停止服务",
        use_container_width=True,
    ):
        from stop import stop_main
        stop_main()

    if cols[2].button(
        "启动对话服务",
        use_container_width=True
    ):
        
        os.environ["API_BASE_URL"] = llm_apiurl
        os.environ["OPENAI_API_KEY"] = llm_apikey

        os.environ["EMBEDDING_ENGINE"] = em_engine
        os.environ["EMBEDDING_MODEL"] = em_model_name
        os.environ["LLM_MODEL"] = llm_model_name

        embedding_model_dict = {k: f"/home/user/chatbot/embedding_models/{v}" if DOCKER_SERVICE else f"{LOCAL_EM_MODEL_DIR}/{v}" for k, v in embedding_model_dict.items()}
        os.environ["embedding_model_dict"] = json.dumps(embedding_model_dict)

        os.environ["ONLINE_LLM_MODEL"] = json.dumps(ONLINE_LLM_MODEL)

        # 模型路径重置
        llm_model_dict_c = {}
        for k, v in llm_model_dict.items():
            v_c = {}
            for kk, vv in v.items():
                if k=="local_model_path":
                    v_c[kk] = f"/home/user/chatbot/llm_models/{vv}" if DOCKER_SERVICE else f"{LOCAL_LLM_MODEL_DIR}/{vv}" 
                else:
                    v_c[kk] = vv
            llm_model_dict_c[k] = v_c

        llm_model_dict = llm_model_dict_c
        os.environ["llm_model_dict"] = json.dumps(llm_model_dict)
        # 
        VLLM_MODEL_DICT_c = {}
        for k, v in VLLM_MODEL_DICT.items():
            VLLM_MODEL_DICT_c[k] = f"/home/user/chatbot/llm_models/{v}" if DOCKER_SERVICE else f"{LOCAL_LLM_MODEL_DIR}/{v}" 
        VLLM_MODEL_DICT = VLLM_MODEL_DICT_c
        os.environ["VLLM_MODEL_DICT"] = json.dumps(VLLM_MODEL_DICT)

        # server config
        os.environ["DOCKER_SERVICE"] = json.dumps(DOCKER_SERVICE)
        os.environ["SANDBOX_DO_REMOTE"] = json.dumps(SANDBOX_DO_REMOTE)
        os.environ["FSCHAT_MODEL_WORKERS"] = json.dumps(FSCHAT_MODEL_WORKERS)

        update_json = {
            "API_BASE_URL": llm_apiurl,
            "OPENAI_API_KEY": llm_apikey,
            "model_engine": llm_provider_option,
            "EMBEDDING_ENGINE": em_engine,
            "EMBEDDING_MODEL": em_model_name,
            "em_apikey": em_apikey,
            "em_apiurl": em_apiurl,
            "LLM_MODEL": llm_model_name,
            "embedding_model_dict": embedding_model_dict,
            "llm_model_dict": llm_model_dict,
            "ONLINE_LLM_MODEL": ONLINE_LLM_MODEL,
            "VLLM_MODEL_DICT": VLLM_MODEL_DICT,
            "DOCKER_SERVICE": DOCKER_SERVICE,
            "SANDBOX_DO_REMOTE": SANDBOX_DO_REMOTE,
            "FSCHAT_MODEL_WORKERS": FSCHAT_MODEL_WORKERS
        }

        with open(os.path.join(src_dir, "configs/local_config.json"), "w") as f:
            json.dump(update_json, f)

        from start import start_main
        from stop import stop_main
        stop_main()
        start_main()
