import os

from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.chat_models import ChatOpenAI

from .llm_config import LLMConfig
# from configs.model_config import (llm_model_dict, LLM_MODEL)


def getChatModel(callBack: AsyncIteratorCallbackHandler = None, temperature=0.3, stop=None):
    if callBack is None:
        model = ChatOpenAI(
            streaming=True,
            verbose=True,
            openai_api_key=llm_model_dict[LLM_MODEL]["api_key"],
            openai_api_base=llm_model_dict[LLM_MODEL]["api_base_url"],
            model_name=LLM_MODEL,
            temperature=temperature,
            stop=stop
        )
    else:
        model = ChatOpenAI(
            streaming=True,
            verbose=True,
            callBack=[callBack],
            openai_api_key=llm_model_dict[LLM_MODEL]["api_key"],
            openai_api_base=llm_model_dict[LLM_MODEL]["api_base_url"],
            model_name=LLM_MODEL,
            temperature=temperature,
            stop=stop
        )
    return model


def getChatModelFromConfig(llm_config: LLMConfig, callBack: AsyncIteratorCallbackHandler = None, ):
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