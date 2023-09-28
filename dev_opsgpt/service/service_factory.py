from typing import List, Union, Dict
import os

from configs.model_config import EMBEDDING_MODEL

from .faiss_db_service import FaissKBService
from .base_service import KBService, SupportedVSType
from dev_opsgpt.orm.commands import *
from dev_opsgpt.utils.path_utils import *



class KBServiceFactory:

    @staticmethod
    def get_service(kb_name: str,
                    vector_store_type: Union[str, SupportedVSType],
                    embed_model: str = EMBEDDING_MODEL,
                    ) -> KBService:
        if isinstance(vector_store_type, str):
            vector_store_type = getattr(SupportedVSType, vector_store_type.upper())
        if SupportedVSType.FAISS == vector_store_type:
            return FaissKBService(kb_name, embed_model=embed_model)
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
    def get_service_by_name(kb_name: str
                            ) -> KBService:
        _, vs_type, embed_model = load_kb_from_db(kb_name)
        if vs_type is None and os.path.isdir(get_kb_path(kb_name)): # faiss knowledge base not in db
            vs_type = "faiss"
        return KBServiceFactory.get_service(kb_name, vs_type, embed_model)

    @staticmethod
    def get_default():
        return KBServiceFactory.get_service("default", SupportedVSType.DEFAULT)


def get_kb_details() -> List[Dict]:
    kbs_in_folder = list_kbs_from_folder()
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
    for i, v in enumerate(result.values()):
        v['No'] = i + 1
        data.append(v)
   
    return data


def get_kb_doc_details(kb_name: str) -> List[Dict]:
    kb = KBServiceFactory.get_service_by_name(kb_name)
    docs_in_folder = list_docs_from_folder(kb_name)
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
