import os
from functools import lru_cache
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.embeddings.base import Embeddings

# from configs.model_config import embedding_model_dict
from loguru import logger


@lru_cache(1)
def load_embeddings(model: str, device: str, embedding_model_dict: dict):
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model_dict[model],
                                       model_kwargs={'device': device})
    return embeddings


# @lru_cache(1)
def load_embeddings_from_path(model_path: str, device: str, langchain_embeddings: Embeddings = None):
    if langchain_embeddings:
        return langchain_embeddings
    
    embeddings = HuggingFaceEmbeddings(model_name=model_path,
                                       model_kwargs={'device': device})
    return embeddings

