import os
from typing import Union, Optional, List
from loguru import logger

from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.llms.base import LLM

from .llm_config import LLMConfig
# from configs.model_config import (llm_model_dict, LLM_MODEL)


class CustomLLMModel:
    
    def __init__(self, llm: LLM):
        self.llm: LLM = llm

    def __call__(self, prompt: str,
                  stop: Optional[List[str]] = None):
        return self.llm(prompt, stop)

    def _call(self, prompt: str,
                  stop: Optional[List[str]] = None):
        return self.llm(prompt, stop)
    
    def predict(self, prompt: str,
                  stop: Optional[List[str]] = None):
        return self.llm(prompt, stop)

    def batch(self, prompts: str,
                  stop: Optional[List[str]] = None):
        return [self.llm(prompt, stop) for prompt in prompts]


def getChatModelFromConfig(llm_config: LLMConfig, callBack: AsyncIteratorCallbackHandler = None, ) -> Union[ChatOpenAI, LLM]:
    # logger.debug(f"llm type is {type(llm_config.llm)}")
    if llm_config is None:
        model = ChatOpenAI(
            streaming=True,
            verbose=True,
            openai_api_key=os.environ.get("api_key"),
            openai_api_base=os.environ.get("api_base_url"),
            model_name=os.environ.get("LLM_MODEL", "gpt-3.5-turbo"),
            temperature=os.environ.get("temperature", 0.5),
            stop=os.environ.get("stop", ""),
        )
        return model

    if llm_config and llm_config.llm and isinstance(llm_config.llm, LLM):
        return CustomLLMModel(llm=llm_config.llm)
    
    if callBack is None:
        model = ChatOpenAI(
                streaming=True,
                verbose=True,
                openai_api_key=llm_config.api_key,
                openai_api_base=llm_config.api_base_url,
                model_name=llm_config.model_name,
                temperature=llm_config.temperature,
                stop=llm_config.stop
            )
    else:
        model = ChatOpenAI(
                streaming=True,
                verbose=True,
                callBack=[callBack],
                openai_api_key=llm_config.api_key,
                openai_api_base=llm_config.api_base_url,
                model_name=llm_config.model_name,
                temperature=llm_config.temperature,
                stop=llm_config.stop
            )

    return model


import json, requests


def getExtraModel():
    return TestModel()

class TestModel:
    
    def predict(self, request_body):
        headers = {"Content-Type":"application/json;charset=UTF-8",
        "codegpt_user":"",
        "codegpt_token":""
                }
        xxx = requests.post(
        'https://codegencore.alipay.com/api/chat/CODE_LLAMA_INT4/completion', 
        data=json.dumps(request_body,ensure_ascii=False).encode('utf-8'), 
        headers=headers)
        return xxx.json()["data"]