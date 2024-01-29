import os
from langchain.document_loaders import CSVLoader, PyPDFLoader, UnstructuredFileLoader, TextLoader, PythonLoader

from coagent.document_loaders import JSONLLoader, JSONLoader
# from configs.model_config import (
#     embedding_model_dict,
#     KB_ROOT_PATH,
# )
from loguru import logger


LOADERNAME2LOADER_DICT = {
    "UnstructuredFileLoader": UnstructuredFileLoader,
    "CSVLoader": CSVLoader,
    "PyPDFLoader": PyPDFLoader,
    "TextLoader": TextLoader,
    "PythonLoader": PythonLoader,
    "JSONLoader": JSONLoader,
    "JSONLLoader": JSONLLoader
}

LOADER2EXT_DICT = {"UnstructuredFileLoader": ['.eml', '.html', '.md', '.msg', '.rst',
                                          '.rtf', '.xml',
                                          '.doc', '.docx', '.epub', '.odt', 
                                          '.ppt', '.pptx', '.tsv'],
               "CSVLoader": [".csv"],
               "PyPDFLoader": [".pdf"],
                "TextLoader": ['.txt'],
                "PythonLoader": ['.py'],
                "JSONLoader": ['.json'],
                "JSONLLoader": ['.jsonl']
               }

EXT2LOADER_DICT = {ext: LOADERNAME2LOADER_DICT[k] for k, exts in LOADER2EXT_DICT.items() for ext in exts}

SUPPORTED_EXTS = [ext for sublist in LOADER2EXT_DICT.values() for ext in sublist]


def validate_kb_name(knowledge_base_id: str) -> bool:
    # 检查是否包含预期外的字符或路径攻击关键字
    if "../" in knowledge_base_id:
        return False
    return True

def get_kb_path(knowledge_base_name: str, kb_root_path: str):
    return os.path.join(kb_root_path, knowledge_base_name)

def get_doc_path(knowledge_base_name: str, kb_root_path: str):
    return os.path.join(get_kb_path(knowledge_base_name, kb_root_path), "content")

def get_vs_path(knowledge_base_name: str, kb_root_path: str):
    return os.path.join(get_kb_path(knowledge_base_name, kb_root_path), "vector_store")

def get_file_path(knowledge_base_name: str, doc_name: str, kb_root_path: str):
    return os.path.join(get_doc_path(knowledge_base_name, kb_root_path), doc_name)

def list_kbs_from_folder(kb_root_path: str):
    return [f for f in os.listdir(kb_root_path)
            if os.path.isdir(os.path.join(kb_root_path, f))]

def list_docs_from_folder(kb_name: str, kb_root_path: str):
    doc_path = get_doc_path(kb_name, kb_root_path)
    if os.path.exists(doc_path):
        return [file for file in os.listdir(doc_path)
                if os.path.isfile(os.path.join(doc_path, file))]
    return []

def get_LoaderClass(file_extension):
    for LoaderClass, extensions in LOADER2EXT_DICT.items():
        if file_extension in extensions:
            return LoaderClass