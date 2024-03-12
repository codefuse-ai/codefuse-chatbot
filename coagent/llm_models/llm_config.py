from dataclasses import dataclass
from typing import List, Union

from langchain.embeddings.base import Embeddings
from langchain.llms.base import LLM, BaseLLM



@dataclass
class LLMConfig:
    def __init__(
            self,
            model_name: str = "gpt-3.5-turbo",
            temperature: float = 0.25, 
            stop: Union[List[str], str] = None,
            api_key: str = "",
            api_base_url: str = "",
            model_device: str = "cpu", # unuse，will delete it
            llm: LLM = None,
            **kwargs
        ):

        self.model_name: str = model_name
        self.temperature: float = temperature
        self.stop: Union[List[str], str] = stop
        self.api_key: str = api_key
        self.api_base_url: str = api_base_url
        self.llm: LLM = llm
        # 
        self.check_config()

    def check_config(self, ):
        pass

    def __str__(self):
        return ', '.join(f"{k}: {v}" for k,v in vars(self).items())
    

@dataclass
class EmbedConfig:
    def __init__(
            self,
            api_key: str = "",
            api_base_url: str = "",
            embed_model: str = "",
            embed_model_path: str = "",
            embed_engine: str = "",
            model_device: str = "cpu",
            langchain_embeddings: Embeddings = None,
            **kwargs
        ):
        self.embed_model: str = embed_model
        self.embed_model_path: str = embed_model_path
        self.embed_engine: str = embed_engine
        self.model_device: str = model_device
        self.api_key: str = api_key
        self.api_base_url: str = api_base_url
        # 
        self.langchain_embeddings = langchain_embeddings
        # 
        self.check_config()

    def check_config(self, ):
        pass

    def __str__(self):
        return ', '.join(f"{k}: {v}" for k,v in vars(self).items())
    