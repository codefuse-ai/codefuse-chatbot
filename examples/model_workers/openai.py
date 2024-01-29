import sys, os
from fastchat.conversation import Conversation
from .base import *
from fastchat import conversation as conv
import json
from typing import List, Dict
from loguru import logger
# from configs import logger, log_verbose
log_verbose = os.environ.get("log_verbose", False)
import openai

from langchain import PromptTemplate, LLMChain
from langchain.prompts.chat import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage


class ExampleWorker(ApiModelWorker):
    def __init__(
            self,
            *,
            controller_addr: str = None,
            worker_addr: str = None,
            model_names: List[str] = ["gpt-3.5-turbo"],
            version: str = "gpt-3.5",
            **kwargs,
    ):
        kwargs.update(model_names=model_names, controller_addr=controller_addr, worker_addr=worker_addr)
        kwargs.setdefault("context_len", 16384) #TODO 16K模型需要改成16384
        super().__init__(**kwargs)
        self.version = version

    def do_chat(self, params: ApiChatParams) -> Dict:
        '''
        yield output: {"error_code": 0, "text": ""}
        '''
        params.load_config(self.model_names[0])
        openai.api_key = params.api_key
        openai.api_base = params.api_base_url

        logger.error(f"{params.api_key}, {params.api_base_url}, {params.messages} {params.max_tokens},")
        # just for example
        prompt = "\n".join([f"{m['role']}:{m['content']}" for m in params.messages])
        logger.error(f"{prompt}, {params.temperature}, {params.max_tokens}")
        try:
            model = ChatOpenAI(
                streaming=True,
                verbose=True,
                openai_api_key= params.api_key,
                openai_api_base=params.api_base_url,
                model_name=params.version
            )
            chat_prompt = ChatPromptTemplate.from_messages([("human", "{input}")])
            chain = LLMChain(prompt=chat_prompt, llm=model)
            content = chain({"input": prompt})
            logger.info(content)
        except Exception as e:
            logger.error(f"{e}")
            yield {"error_code": 500, "text": "request error"}

        # return the text by yield for stream
        try:
            yield {"error_code": 0, "text": content["text"]}
        except:
            yield {"error_code": 500, "text": "request error"}

    def get_embeddings(self, params):
        # TODO: 支持embeddings
        print("embedding")
        print(params)

    def make_conv_template(self, conv_template: str = None, model_path: str = None) -> Conversation:
        # TODO: 确认模板是否需要修改
        return conv.Conversation(
            name=self.model_names[0],
            system_message="You are a helpful, respectful and honest assistant.",
            messages=[],
            roles=["user", "assistant", "system"],
            sep="\n### ",
            stop_str="###",
        )


if __name__ == "__main__":
    import uvicorn
    from coagent.utils.server_utils import MakeFastAPIOffline
    from fastchat.serve.base_model_worker import app

    worker = ExampleWorker(
        controller_addr="http://127.0.0.1:20001",
        worker_addr="http://127.0.0.1:21008",
    )
    sys.modules["fastchat.serve.model_worker"].worker = worker
    uvicorn.run(app, port=21008)
