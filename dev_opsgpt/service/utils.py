import os

from configs.model_config import ONLINE_LLM_MODEL
from configs.server_config import FSCHAT_MODEL_WORKERS
from configs.model_config import llm_model_dict, LLM_DEVICE

from loguru import logger



def get_model_worker_config(model_name: str = None) -> dict:
    '''
    加载model worker的配置项。
    优先级:FSCHAT_MODEL_WORKERS[model_name] > ONLINE_LLM_MODEL[model_name] > FSCHAT_MODEL_WORKERS["default"]
    '''
    from dev_opsgpt.service import model_workers
    
    config = FSCHAT_MODEL_WORKERS.get("default", {}).copy()
    config.update(ONLINE_LLM_MODEL.get(model_name, {}).copy())
    config.update(FSCHAT_MODEL_WORKERS.get(model_name, {}).copy())

    if model_name in ONLINE_LLM_MODEL:
        config["online_api"] = True
        if provider := config.get("provider"):
            try:
                config["worker_class"] = getattr(model_workers, provider)
            except Exception as e:
                msg = f"在线模型 ‘{model_name}’ 的provider没有正确配置"
                logger.error(f'{e.__class__.__name__}: {msg}')
    # 本地模型
    if model_name in llm_model_dict:
        path = llm_model_dict[model_name]["local_model_path"]
        config["model_path"] = path
        if path and os.path.isdir(path):
            config["model_path_exists"] = True
        config["device"] = LLM_DEVICE

    # logger.debug(f"config: {config}")
    return config