from .model_config import LLM_MODEL, LLM_DEVICE
import os

# API 是否开启跨域，默认为False，如果需要开启，请设置为True
# is open cross domain
OPEN_CROSS_DOMAIN = False
# 是否用容器来启动服务
DOCKER_SERVICE = True
# 是否采用容器沙箱
SANDBOX_DO_REMOTE = True
# 是否采用api服务来进行
NO_REMOTE_API = True
# 各服务器默认绑定host
DEFAULT_BIND_HOST = "127.0.0.1"
os.environ["DEFAULT_BIND_HOST"] = DEFAULT_BIND_HOST

# 
CONTRAINER_NAME = "devopsgpt_webui"
IMAGE_NAME = "devopsgpt:py39"

# webui.py server
WEBUI_SERVER = {
    "host": DEFAULT_BIND_HOST,
    "port": 8501,
    "docker_port": 8501
}

# api.py server
API_SERVER = {
    "host": DEFAULT_BIND_HOST,
    "port": 7861,
    "docker_port": 7861
}

# sdfile_api.py server
SDFILE_API_SERVER = {
    "host": DEFAULT_BIND_HOST,
    "port": 7862,
    "docker_port": 7862
}

# fastchat openai_api server
FSCHAT_OPENAI_API = {
    "host": DEFAULT_BIND_HOST,
    "port": 8888,  # model_config.llm_model_dict中模型配置的api_base_url需要与这里一致。
    "docker_port": 8888,  # model_config.llm_model_dict中模型配置的api_base_url需要与这里一致。
}

# nebula conf
NEBULA_HOST = DEFAULT_BIND_HOST
NEBULA_PORT = 9669
NEBULA_STORAGED_PORT = 9779
NEBULA_USER = 'root'
NEBULA_PASSWORD = ''
NEBULA_GRAPH_SERVER = {
    "host": DEFAULT_BIND_HOST,
    "port": NEBULA_PORT,
    "docker_port": NEBULA_PORT
}

# chroma conf
CHROMA_PERSISTENT_PATH = '/home/user/chatbot/data/chroma_data'

# sandbox api server
SANDBOX_CONTRAINER_NAME = "devopsgpt_sandbox"
SANDBOX_IMAGE_NAME = "devopsgpt:py39"
SANDBOX_HOST = os.environ.get("SANDBOX_HOST") or DEFAULT_BIND_HOST # "172.25.0.3"
SANDBOX_SERVER = {
    "host": f"http://{SANDBOX_HOST}",
    "port": 5050,
    "docker_port": 5050,
    "url": f"http://{SANDBOX_HOST}:5050",
    "do_remote": SANDBOX_DO_REMOTE,
}

# fastchat model_worker server
# 这些模型必须是在model_config.llm_model_dict中正确配置的。
# 在启动startup.py时，可用通过`--model-worker --model-name xxxx`指定模型，不指定则为LLM_MODEL
FSCHAT_MODEL_WORKERS = {
    "default": {
        "host": DEFAULT_BIND_HOST,
        "port": 20002,
        "device": LLM_DEVICE,
        # todo: 多卡加载需要配置的参数
        "gpus": None,
        "numgpus": 1,
        # 以下为非常用参数，可根据需要配置
        # "max_gpu_memory": "20GiB",
        # "load_8bit": False,
        # "cpu_offloading": None,
        # "gptq_ckpt": None,
        # "gptq_wbits": 16,
        # "gptq_groupsize": -1,
        # "gptq_act_order": False,
        # "awq_ckpt": None,
        # "awq_wbits": 16,
        # "awq_groupsize": -1,
        # "model_names": [LLM_MODEL],
        # "conv_template": None,
        # "limit_worker_concurrency": 5,
        # "stream_interval": 2,
        # "no_register": False,
    },
    'codellama_34b': {'host': DEFAULT_BIND_HOST, 'port': 20002},
    'Baichuan2-13B-Base': {'host': DEFAULT_BIND_HOST, 'port': 20003},
    'Baichuan2-13B-Chat': {'host': DEFAULT_BIND_HOST, 'port': 20004},
    'baichuan2-7b-base': {'host': DEFAULT_BIND_HOST, 'port': 20005},
    'baichuan2-7b-chat': {'host': DEFAULT_BIND_HOST, 'port': 20006},
    'internlm-7b-base': {'host': DEFAULT_BIND_HOST, 'port': 20007},
    'internlm-chat-7b': {'host': DEFAULT_BIND_HOST, 'port': 20008},
    'chatglm2-6b': {'host': DEFAULT_BIND_HOST, 'port': 20009},
    'qwen-14b-base': {'host': DEFAULT_BIND_HOST, 'port': 20010},
    'qwen-14b-chat': {'host': DEFAULT_BIND_HOST, 'port': 20011},
    'qwen-1-8B-Chat': {'host': DEFAULT_BIND_HOST, 'port': 20012},
    'Qwen-7B': {'host': DEFAULT_BIND_HOST, 'port': 20013},
    'Qwen-7B-Chat': {'host': DEFAULT_BIND_HOST, 'port': 20014},
    'qwen-7b-base-v1.1': {'host': DEFAULT_BIND_HOST, 'port': 20015},
    'qwen-7b-chat-v1.1': {'host': DEFAULT_BIND_HOST, 'port': 20016},
    'chatglm3-6b': {'host': DEFAULT_BIND_HOST, 'port': 20017},
    'chatglm3-6b-32k': {'host': DEFAULT_BIND_HOST, 'port': 20018},
    'chatglm3-6b-base': {'host': DEFAULT_BIND_HOST, 'port': 20019},
    'Qwen-72B-Chat-Int4': {'host': DEFAULT_BIND_HOST, 'port': 20020},
    'gpt-3.5-turbo': {'host': DEFAULT_BIND_HOST, 'port': 20021}
}
# fastchat multi model worker server
FSCHAT_MULTI_MODEL_WORKERS = {
    # todo
}

# fastchat controller server
FSCHAT_CONTROLLER = {
    "host": DEFAULT_BIND_HOST,
    "port": 20001,
    "dispatch_method": "shortest_queue",
}


# 以下不要更改
def fschat_controller_address() -> str:
    host = FSCHAT_CONTROLLER["host"]
    port = FSCHAT_CONTROLLER["port"]
    return f"http://{host}:{port}"


def fschat_model_worker_address(model_name: str = LLM_MODEL) -> str:
    if model := FSCHAT_MODEL_WORKERS.get(model_name):
        host = model["host"]
        port = model["port"]
        return f"http://{host}:{port}"


def fschat_openai_api_address() -> str:
    host = FSCHAT_OPENAI_API["host"]
    port = FSCHAT_OPENAI_API["port"]
    return f"http://{host}:{port}"


def api_address() -> str:
    host = API_SERVER["host"]
    port = API_SERVER["port"]
    return f"http://{host}:{port}"


def webui_address() -> str:
    host = WEBUI_SERVER["host"]
    port = WEBUI_SERVER["port"]
    return f"http://{host}:{port}"
