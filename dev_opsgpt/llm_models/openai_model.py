from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.chat_models import ChatOpenAI

from configs.model_config import (llm_model_dict, LLM_MODEL)


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