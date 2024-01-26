import urllib, os, json, traceback
from typing import List, Dict
from loguru import logger

from fastapi.responses import StreamingResponse, FileResponse
from fastapi import Body, File, Form, Body, Query, UploadFile
from langchain.docstore.document import Document

from .service_factory import KBServiceFactory
from coagent.utils.server_utils import BaseResponse, ListResponse
from coagent.utils.path_utils import *
from coagent.orm.commands import *
from coagent.orm.utils import DocumentFile
# from configs.model_config import (
#     DEFAULT_VS_TYPE, EMBEDDING_MODEL, VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD, KB_ROOT_PATH
# )
from coagent.llm_models.llm_config import EmbedConfig


async def list_kbs():
    # Get List of Knowledge Base
    return ListResponse(data=list_kbs_from_db())


async def create_kb(knowledge_base_name: str = Body(..., examples=["samples"]),
                    vector_store_type: str = Body("faiss"),
                    kb_root_path: str =Body(""),
                    api_key: bool = Body(..., examples=["samples"]),
                    api_base_url: bool = Body(..., examples=["samples"]),
                    embed_model: bool = Body(..., examples=["samples"]),
                    embed_model_path: bool = Body(..., examples=["samples"]),
                    model_device: bool = Body(..., examples=["samples"]),
                    embed_engine: bool = Body(..., examples=["samples"]),
                    ) -> BaseResponse:
    embed_config: EmbedConfig = EmbedConfig(**locals())
    # Create selected knowledge base
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")
    if knowledge_base_name is None or knowledge_base_name.strip() == "":
        return BaseResponse(code=404, msg="知识库名称不能为空，请重新填写知识库名称")

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name, embed_config, kb_root_path)
    if kb is not None:
        return BaseResponse(code=404, msg=f"已存在同名知识库 {knowledge_base_name}")

    kb = KBServiceFactory.get_service(knowledge_base_name, vector_store_type, embed_config, kb_root_path)
    try:
        kb.create_kb()
    except Exception as e:
        logger.exception(e)
        return BaseResponse(code=500, msg=f"创建知识库出错： {e}")

    return BaseResponse(code=200, msg=f"已新增知识库 {knowledge_base_name}")


async def delete_kb(
        knowledge_base_name: str = Body(..., examples=["samples"]),
        kb_root_path: str =Body(""),
        ) -> BaseResponse:
    # Delete selected knowledge base
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")
    knowledge_base_name = urllib.parse.unquote(knowledge_base_name)

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name, None, kb_root_path)

    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")

    try:
        status = kb.clear_vs()
        status = kb.drop_kb()
        if status:
            return BaseResponse(code=200, msg=f"成功删除知识库 {knowledge_base_name}")
    except Exception as e:
        print(e)
        return BaseResponse(code=500, msg=f"删除知识库时出现意外： {e}")

    return BaseResponse(code=500, msg=f"删除知识库失败 {knowledge_base_name}")



class DocumentWithScore(Document):
    score: float = None


def search_docs(query: str = Body(..., description="用户输入", examples=["你好"]),
                knowledge_base_name: str = Body(..., description="知识库名称", examples=["samples"]),
                top_k: int = Body(5, description="匹配向量数"),
                score_threshold: float = Body(1.0, description="知识库匹配相关度阈值，取值范围在0-1之间，SCORE越小，相关度越高，取到1相当于不筛选，建议设置在0.5左右", ge=0, le=1),
                kb_root_path: str =Body(""),
                api_key: bool = Body(..., examples=["samples"]),
                api_base_url: bool = Body(..., examples=["samples"]),
                embed_model: bool = Body(..., examples=["samples"]),
                embed_model_path: bool = Body(..., examples=["samples"]),
                model_device: bool = Body(..., examples=["samples"]),
                embed_engine: bool = Body(..., examples=["samples"]),
        ) -> List[DocumentWithScore]:
    
    embed_config: EmbedConfig = EmbedConfig(**locals())
    kb = KBServiceFactory.get_service_by_name(knowledge_base_name, embed_config, kb_root_path)
    if kb is None:
        return []
    docs = kb.search_docs(query, top_k, score_threshold)
    data = [DocumentWithScore(**x[0].dict(), score=x[1]) for x in docs]

    return data


async def list_docs(
    knowledge_base_name: str,
    kb_root_path: str =Body(""),
) -> ListResponse:
    if not validate_kb_name(knowledge_base_name):
        return ListResponse(code=403, msg="Don't attack me", data=[])

    knowledge_base_name = urllib.parse.unquote(knowledge_base_name)
    kb = KBServiceFactory.get_service_by_name(knowledge_base_name, None, kb_root_path)
    if kb is None:
        return ListResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}", data=[])
    else:
        all_doc_names = kb.list_docs()
        return ListResponse(data=all_doc_names)


async def upload_doc(file: UploadFile = File(..., description="上传文件"),
                     knowledge_base_name: str = Form(..., description="知识库名称", examples=["kb1"]),
                     override: bool = Form(False, description="覆盖已有文件"),
                     not_refresh_vs_cache: bool = Form(False, description="暂不保存向量库（用于FAISS）"),
                     kb_root_path: str =Body(""),
                    api_key: bool = Body(..., examples=["samples"]),
                    api_base_url: bool = Body(..., examples=["samples"]),
                    embed_model: bool = Body(..., examples=["samples"]),
                    embed_model_path: bool = Body(..., examples=["samples"]),
                    model_device: bool = Body(..., examples=["samples"]),
                    embed_engine: bool = Body(..., examples=["samples"]),
                     ) -> BaseResponse:
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")

    embed_config: EmbedConfig = EmbedConfig(**locals())
    kb = KBServiceFactory.get_service_by_name(knowledge_base_name, embed_config, kb_root_path)
    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")

    file_content = await file.read()  # 读取上传文件的内容

    try:
        kb_file = DocumentFile(filename=file.filename,
                                knowledge_base_name=knowledge_base_name,
                                kb_root_path=kb_root_path
                                )

        if (os.path.exists(kb_file.filepath)
                and not override
                and os.path.getsize(kb_file.filepath) == len(file_content)
        ):
            # TODO: filesize 不同后的处理
            file_status = f"文件 {kb_file.filename} 已存在。"
            return BaseResponse(code=404, msg=file_status)

        with open(kb_file.filepath, "wb") as f:
            f.write(file_content)
    except Exception as e:
        logger.error(traceback.format_exc())
        return BaseResponse(code=500, msg=f"{kb_file.filename} 文件上传失败，报错信息为: {e}")

    try:
        kb.add_doc(kb_file, not_refresh_vs_cache=not_refresh_vs_cache)
    except Exception as e:
        logger.error(traceback.format_exc())
        return BaseResponse(code=500, msg=f"{kb_file.filename} 文件向量化失败，报错信息为: {e}")

    return BaseResponse(code=200, msg=f"成功上传文件 {kb_file.filename}")


async def delete_doc(knowledge_base_name: str = Body(..., examples=["samples"]),
                     doc_name: str = Body(..., examples=["file_name.md"]),
                     delete_content: bool = Body(False),
                     not_refresh_vs_cache: bool = Body(False, description="暂不保存向量库（用于FAISS）"),
                     kb_root_path: str =Body(""),
                    api_key: bool = Body(..., examples=["samples"]),
                    api_base_url: bool = Body(..., examples=["samples"]),
                    embed_model: bool = Body(..., examples=["samples"]),
                    embed_model_path: bool = Body(..., examples=["samples"]),
                    model_device: bool = Body(..., examples=["samples"]),
                    embed_engine: bool = Body(..., examples=["samples"]),
                    ) -> BaseResponse:
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")

    embed_config: EmbedConfig = EmbedConfig(**locals())
    knowledge_base_name = urllib.parse.unquote(knowledge_base_name)
    kb = KBServiceFactory.get_service_by_name(knowledge_base_name, embed_config, kb_root_path)
    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")

    if not kb.exist_doc(doc_name):
        return BaseResponse(code=404, msg=f"未找到文件 {doc_name}")

    try:
        kb_file = DocumentFile(filename=doc_name,
                                knowledge_base_name=knowledge_base_name,
                                kb_root_path=kb_root_path)
        kb.delete_doc(kb_file, delete_content, not_refresh_vs_cache=not_refresh_vs_cache)
    except Exception as e:
        logger.exception(e)
        return BaseResponse(code=500, msg=f"{kb_file.filename} 文件删除失败，错误信息：{e}")

    return BaseResponse(code=200, msg=f"{kb_file.filename} 文件删除成功")


async def update_doc(
        knowledge_base_name: str = Body(..., examples=["samples"]),
        file_name: str = Body(..., examples=["file_name"]),
        not_refresh_vs_cache: bool = Body(False, description="暂不保存向量库（用于FAISS）"),
        kb_root_path: str =Body(""),
        api_key: bool = Body(..., examples=["samples"]),
        api_base_url: bool = Body(..., examples=["samples"]),
        embed_model: bool = Body(..., examples=["samples"]),
        embed_model_path: bool = Body(..., examples=["samples"]),
        model_device: bool = Body(..., examples=["samples"]),
        embed_engine: bool = Body(..., examples=["samples"]),
    ) -> BaseResponse:
    '''
    更新知识库文档
    '''
    embed_config: EmbedConfig = EmbedConfig(**locals())
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name, embed_config, kb_root_path)
    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")

    try:
        kb_file = DocumentFile(filename=file_name,
                                knowledge_base_name=knowledge_base_name,
                                kb_root_path=kb_root_path)
        if os.path.exists(kb_file.filepath):
            kb.update_doc(kb_file, not_refresh_vs_cache=not_refresh_vs_cache)
            return BaseResponse(code=200, msg=f"成功更新文件 {kb_file.filename}")
    except Exception as e:
        logger.error(traceback.format_exc())
        return BaseResponse(code=500, msg=f"{kb_file.filename} 文件更新失败，错误信息是：{e}")

    return BaseResponse(code=500, msg=f"{kb_file.filename} 文件更新失败")


async def download_doc(
        knowledge_base_name: str = Query(..., examples=["samples"]),
        file_name: str = Query(..., examples=["test.txt"]),
        kb_root_path: str =Body(""),
    ):
    '''
    下载知识库文档
    '''
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name, None, kb_root_path)
    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")

    try:
        kb_file = DocumentFile(filename=file_name,
                                knowledge_base_name=knowledge_base_name,
                                kb_root_path=kb_root_path)

        if os.path.exists(kb_file.filepath):
            return FileResponse(
                path=kb_file.filepath,
                filename=kb_file.filename,
                media_type="multipart/form-data")
    except Exception as e:
        print(e)
        return BaseResponse(code=500, msg=f"{kb_file.filename} 读取文件失败，错误信息是：{e}")

    return BaseResponse(code=500, msg=f"{kb_file.filename} 读取文件失败")


async def recreate_vector_store(
        knowledge_base_name: str = Body(..., examples=["samples"]),
        allow_empty_kb: bool = Body(True),
        vs_type: str = Body("faiss"),
        kb_root_path: str = Body(""),
        api_key: bool = Body(..., examples=["samples"]),
        api_base_url: bool = Body(..., examples=["samples"]),
        embed_model: bool = Body(..., examples=["samples"]),
        embed_model_path: bool = Body(..., examples=["samples"]),
        model_device: bool = Body(..., examples=["samples"]),
        embed_engine: bool = Body(..., examples=["samples"]),
    ):
    '''
    recreate vector store from the content.
    this is usefull when user can copy files to content folder directly instead of upload through network.
    by default, get_service_by_name only return knowledge base in the info.db and having document files in it.
    set allow_empty_kb to True make it applied on empty knowledge base which it not in the info.db or having no documents.
    '''
    embed_config: EmbedConfig = EmbedConfig(**locals())
    async def output():
        kb = KBServiceFactory.get_service(knowledge_base_name, vs_type, embed_config, kb_root_path)
        if not kb.exists() and not allow_empty_kb:
            yield {"code": 404, "msg": f"未找到知识库 ‘{knowledge_base_name}’"}
        else:
            kb.create_kb()
            kb.clear_vs()
            docs = list_docs_from_folder(knowledge_base_name, kb_root_path)
            for i, doc in enumerate(docs):
                try:
                    kb_file = DocumentFile(doc, knowledge_base_name,
                                kb_root_path=kb_root_path)
                    yield json.dumps({
                        "code": 200,
                        "msg": f"({i + 1} / {len(docs)}): {doc}",
                        "total": len(docs),
                        "finished": i,
                        "doc": doc,
                    }, ensure_ascii=False)
                    if i == len(docs) - 1:
                        not_refresh_vs_cache = False
                    else:
                        not_refresh_vs_cache = True
                    kb.add_doc(kb_file, not_refresh_vs_cache=not_refresh_vs_cache)
                except Exception as e:
                    print(e)
                    yield json.dumps({
                        "code": 500,
                        "msg": f"添加文件‘{doc}’到知识库‘{knowledge_base_name}’时出错：{e}。已跳过。",
                    })

    return StreamingResponse(output(), media_type="text/event-stream")
