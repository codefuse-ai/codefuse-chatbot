from typing import List, Union, Dict
import os

# from configs.model_config import EMBEDDING_MODEL, KB_ROOT_PATH
from coagent.base_configs.env_config import KB_ROOT_PATH

from .faiss_db_service import FaissKBService
from .base_service import KBService, SupportedVSType
from coagent.orm.commands import *
from coagent.utils.path_utils import *
from coagent.llm_models.llm_config import EmbedConfig


class KBServiceFactory:

    @staticmethod
    def get_service(kb_name: str,
                    vector_store_type: Union[str, SupportedVSType],
                    # embed_model: str = "text2vec-base-chinese",
                    embed_config: EmbedConfig,
                    kb_root_path: str = KB_ROOT_PATH
                    ) -> KBService:
        if isinstance(vector_store_type, str):
            vector_store_type = getattr(SupportedVSType, vector_store_type.upper())
        if SupportedVSType.FAISS == vector_store_type:
            return FaissKBService(kb_name, embed_config=embed_config, kb_root_path=kb_root_path)
        # if SupportedVSType.PG == vector_store_type:
        #     from server.knowledge_base.kb_service.pg_kb_service import PGKBService
        #     return PGKBService(kb_name, embed_model=embed_model)
        # elif SupportedVSType.MILVUS == vector_store_type:
        #     from server.knowledge_base.kb_service.milvus_kb_service import MilvusKBService
        #     return MilvusKBService(kb_name, embed_model=embed_model) # other milvus parameters are set in model_config.kbs_config
        # elif SupportedVSType.DEFAULT == vector_store_type: # kb_exists of default kbservice is False, to make validation easier.
        #     from server.knowledge_base.kb_service.default_kb_service import DefaultKBService
        #     return DefaultKBService(kb_name)

    @staticmethod
    def get_service_by_name(kb_name: str,
                            embed_config: EmbedConfig,
                            kb_root_path: str = KB_ROOT_PATH
                            ) -> KBService:
        _, vs_type, embed_model = load_kb_from_db(kb_name)
        if vs_type is None and os.path.isdir(get_kb_path(kb_name, kb_root_path)): # faiss knowledge base not in db
            vs_type = "faiss"
        return KBServiceFactory.get_service(kb_name, vs_type, embed_config, kb_root_path)

    @staticmethod
    def get_default():
        return KBServiceFactory.get_service("default", SupportedVSType.DEFAULT, EmbedConfig(), kb_root_path=KB_ROOT_PATH)


def get_kb_details(kb_root_path: str) -> List[Dict]:
    kbs_in_folder = list_kbs_from_folder(kb_root_path)
    kbs_in_db = KBService.list_kbs()
    result = {}

    for kb in kbs_in_folder:
        result[kb] = {
            "kb_name": kb,
            "vs_type": "",
            "embed_model": "",
            "file_count": 0,
            "create_time": None,
            "in_folder": True,
            "in_db": False,
        }

    for kb in kbs_in_db:
        kb_detail = get_kb_detail(kb)
        if kb_detail:
            kb_detail["in_db"] = True
            if kb in result:
                result[kb].update(kb_detail)
            else:
                kb_detail["in_folder"] = False
                result[kb] = kb_detail

    data = []
    # filter not in db' knowledge base docs
    result = {k: v for k, v in result.items() if v.get("in_db", False)}
    for i, v in enumerate(result.values()):
        v['No'] = i + 1
        data.append(v)
   
    return data

def get_cb_details() -> List[Dict]:
    '''
    get codebase details
    @return: list of data
    '''
    res = {}
    cbs_in_db = list_cbs_from_db()
    for cb in cbs_in_db:
        cb_detail = get_cb_detail(cb)
        res[cb] = cb_detail

    data = []
    for i, v in enumerate(res.values()):
        v['No'] = i + 1
        data.append(v)
    return data

def get_cb_details_by_cb_name(cb_name) -> dict:
    '''
    get codebase details by cb_name
    @return: list of data
    '''
    cb_detail = get_cb_detail(cb_name)
    return cb_detail




def get_kb_doc_details(kb_name: str, kb_root_path) -> List[Dict]:
    kb = KBServiceFactory.get_service_by_name(kb_name, kb_root_path)
    docs_in_folder = list_docs_from_folder(kb_name, kb_root_path)
    docs_in_db = kb.list_docs()
    result = {}

    for doc in docs_in_folder:
        result[doc] = {
            "kb_name": kb_name,
            "file_name": doc,
            "file_ext": os.path.splitext(doc)[-1],
            "file_version": 0,
            "document_loader": "",
            "text_splitter": "",
            "create_time": None,
            "in_folder": True,
            "in_db": False,
        }
    for doc in docs_in_db:
        doc_detail = get_file_detail(kb_name, doc)
        if doc_detail:
            doc_detail["in_db"] = True
            if doc in result:
                result[doc].update(doc_detail)
            else:
                doc_detail["in_folder"] = False
                result[doc] = doc_detail

    data = []
    for i, v in enumerate(result.values()):
        v['No'] = i + 1
        data.append(v)
   
    return data
