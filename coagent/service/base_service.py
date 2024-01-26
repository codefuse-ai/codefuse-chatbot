from abc import ABC, abstractmethod
from typing import List
import os

from langchain.embeddings.base import Embeddings
from langchain.docstore.document import Document

# from configs.model_config import (
#     kbs_config, VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD,
#     EMBEDDING_MODEL, EMBEDDING_DEVICE, KB_ROOT_PATH
# )
# from configs.model_config import embedding_model_dict
from coagent.base_configs.env_config import (
    VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD, kbs_config
)
from coagent.orm.commands import *
from coagent.utils.path_utils import *
from coagent.orm.utils import DocumentFile
from coagent.embeddings.utils import load_embeddings, load_embeddings_from_path
from coagent.text_splitter import LCTextSplitter
from coagent.llm_models.llm_config import EmbedConfig


class SupportedVSType:
    FAISS = 'faiss'
    # MILVUS = 'milvus'
    # DEFAULT = 'default'
    # PG = 'pg'


class KBService(ABC):

    def __init__(self,
                 knowledge_base_name: str,
                 embed_config: EmbedConfig,
                #  embed_model: str = "text2vec-base-chinese",
                 kb_root_path: str,
                 ):
        self.kb_name = knowledge_base_name
        # self.embed_model = embed_model
        self.embed_config = embed_config
        self.kb_root_path = kb_root_path
        self.kb_path = get_kb_path(self.kb_name, kb_root_path)
        self.doc_path = get_doc_path(self.kb_name, kb_root_path)
        self.do_init()

    def _load_embeddings(self) -> Embeddings:
        # return load_embeddings(self.embed_model, embed_device, embedding_model_dict)
        return load_embeddings_from_path(self.embed_config.embed_model_path, self.embed_config.model_device)

    def create_kb(self):
        """
        创建知识库
        """
        if not os.path.exists(self.doc_path):
            os.makedirs(self.doc_path)
        self.do_create_kb()
        status = add_kb_to_db(self.kb_name, self.vs_type(), self.embed_config.embed_model)
        return status

    def clear_vs(self):
        """
        删除向量库中所有内容
        """
        self.do_clear_vs()
        status = delete_files_from_db(self.kb_name)
        return status

    def drop_kb(self):
        """
        删除知识库
        """
        self.do_drop_kb()
        status = delete_kb_from_db(self.kb_name)
        return status

    def add_doc(self, kb_file: DocumentFile, **kwargs):
        """
        向知识库添加文件
        """
        lctTextSplitter = LCTextSplitter(kb_file.filepath)
        docs = lctTextSplitter.file2text()
        if docs:
            self.delete_doc(kb_file)
            embeddings = self._load_embeddings()
            self.do_add_doc(docs, embeddings, **kwargs)
            status = add_doc_to_db(kb_file)
        else:
            status = False
        return status

    def delete_doc(self, kb_file: DocumentFile, delete_content: bool = False, **kwargs):
        """
        从知识库删除文件
        """
        self.do_delete_doc(kb_file, **kwargs)
        status = delete_file_from_db(kb_file)
        if delete_content and os.path.exists(kb_file.filepath):
            os.remove(kb_file.filepath)
        return status

    def update_doc(self, kb_file: DocumentFile, **kwargs):
        """
        使用content中的文件更新向量库
        """
        if os.path.exists(kb_file.filepath):
            self.delete_doc(kb_file, **kwargs)
            return self.add_doc(kb_file, **kwargs)
        
    def exist_doc(self, file_name: str):
        return doc_exists(DocumentFile(knowledge_base_name=self.kb_name,
                                        filename=file_name, kb_root_path=self.kb_root_path))

    def list_docs(self):
        return list_docs_from_db(self.kb_name)

    def search_docs(self,
                    query: str,
                    top_k: int = VECTOR_SEARCH_TOP_K,
                    score_threshold: float = SCORE_THRESHOLD,
                    ):
        embeddings = self._load_embeddings()
        docs = self.do_search(query, top_k, score_threshold, embeddings)
        return docs

    @abstractmethod
    def do_create_kb(self):
        """
        创建知识库子类实自己逻辑
        """
        pass

    @staticmethod
    def list_kbs_type():
        return list(kbs_config.keys())

    @classmethod
    def list_kbs(cls):
        return list_kbs_from_db()

    def exists(self, kb_name: str = None):
        kb_name = kb_name or self.kb_name
        return kb_exists(kb_name)

    @abstractmethod
    def vs_type(self) -> str:
        pass

    @abstractmethod
    def do_init(self):
        pass

    @abstractmethod
    def do_drop_kb(self):
        """
        删除知识库子类实自己逻辑
        """
        pass

    @abstractmethod
    def do_search(self,
                  query: str,
                  top_k: int,
                  embeddings: Embeddings,
                  ) -> List[Document]:
        """
        搜索知识库子类实自己逻辑
        """
        pass

    @abstractmethod
    def do_add_doc(self,
                   docs: List[Document],
                   embeddings: Embeddings,
                   ):
        """
        向知识库添加文档子类实自己逻辑
        """
        pass

    @abstractmethod
    def get_all_documents(self,
                   embeddings: Embeddings,
                   ):
        """
        获取知识库所有文档
        """
        pass

    @abstractmethod
    def do_delete_doc(self,
                      kb_file: DocumentFile):
        """
        从知识库删除文档子类实自己逻辑
        """
        pass

    @abstractmethod
    def do_clear_vs(self):
        """
        从知识库删除全部向量子类实自己逻辑
        """
        pass
