# encoding: utf-8
'''
@author: 温进
@file: cb_api.py
@time: 2023/10/23 下午7:08
@desc:
'''

import urllib, os, json, traceback
from typing import List, Dict
import shutil

from fastapi.responses import StreamingResponse, FileResponse
from fastapi import File, Form, Body, Query, UploadFile
from langchain.docstore.document import Document

from .service_factory import KBServiceFactory
from coagent.utils.server_utils import BaseResponse, ListResponse
from coagent.utils.path_utils import *
from coagent.orm.commands import *
from coagent.db_handler.graph_db_handler.nebula_handler import NebulaHandler
from coagent.db_handler.vector_db_handler.chroma_handler import ChromaHandler
from coagent.base_configs.env_config import (
    CB_ROOT_PATH, 
    NEBULA_HOST, NEBULA_PORT, NEBULA_USER, NEBULA_PASSWORD, NEBULA_STORAGED_PORT,
    CHROMA_PERSISTENT_PATH
)


# from configs.model_config import (
#     CB_ROOT_PATH
# )

# from coagent.codebase_handler.codebase_handler import CodeBaseHandler
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig
from coagent.codechat.codebase_handler.codebase_handler import CodeBaseHandler

from loguru import logger


async def list_cbs():
    # Get List of Knowledge Base
    return ListResponse(data=list_cbs_from_db())


async def create_cb(zip_file,
                    cb_name: str = Body(..., examples=["samples"]),
                    code_path: str = Body(..., examples=["samples"]),
                    do_interpret: bool = Body(..., examples=["samples"]),
                    api_key: bool = Body(..., examples=["samples"]),
                    api_base_url: bool = Body(..., examples=["samples"]),
                    embed_model: bool = Body(..., examples=["samples"]),
                    embed_model_path: bool = Body(..., examples=["samples"]),
                    embed_engine: bool = Body(..., examples=["samples"]),
                    model_name: bool = Body(..., examples=["samples"]),
                    temperature: bool = Body(..., examples=["samples"]),
                    model_device: bool = Body(..., examples=["samples"]),
                    embed_config: EmbedConfig = None,
                    ) -> BaseResponse:
    logger.info('cb_name={}, zip_path={}, do_interpret={}'.format(cb_name, code_path, do_interpret))

    embed_config: EmbedConfig = EmbedConfig(**locals()) if embed_config is None else embed_config
    llm_config: LLMConfig = LLMConfig(**locals())

    # Create selected knowledge base
    if not validate_kb_name(cb_name):
        return BaseResponse(code=403, msg="Don't attack me")
    if cb_name is None or cb_name.strip() == "":
        return BaseResponse(code=404, msg="知识库名称不能为空，请重新填写知识库名称")

    cb = cb_exists(cb_name)
    if cb:
        return BaseResponse(code=404, msg=f"已存在同名代码知识库 {cb_name}")

    try:
        logger.info('start build code base')
        cbh = CodeBaseHandler(cb_name, code_path, embed_config=embed_config, llm_config=llm_config)
        vertices_num, edge_num, file_num = cbh.import_code(zip_file=zip_file, do_interpret=do_interpret)
        logger.info('build code base done')

        # create cb to table
        add_cb_to_db(cb_name, cbh.code_path, vertices_num, file_num, do_interpret)
        logger.info('add cb to mysql table success')
    except Exception as e:
        print(e)
        logger.exception(e)
        return BaseResponse(code=500, msg=f"创建代码知识库出错： {e}")

    return BaseResponse(code=200, msg=f"已新增代码知识库 {cb_name}")


async def delete_cb(
        cb_name: str = Body(..., examples=["samples"]),
        api_key: bool = Body(..., examples=["samples"]),
        api_base_url: bool = Body(..., examples=["samples"]),
        embed_model: bool = Body(..., examples=["samples"]),
        embed_model_path: bool = Body(..., examples=["samples"]),
        embed_engine: bool = Body(..., examples=["samples"]),
        model_name: bool = Body(..., examples=["samples"]),
        temperature: bool = Body(..., examples=["samples"]),
        model_device: bool = Body(..., examples=["samples"]),
        embed_config: EmbedConfig = None,
        ) -> BaseResponse:
    logger.info('cb_name={}'.format(cb_name))
    embed_config: EmbedConfig = EmbedConfig(**locals()) if embed_config is None else embed_config
    llm_config: LLMConfig = LLMConfig(**locals())
    # Create selected knowledge base
    if not validate_kb_name(cb_name):
        return BaseResponse(code=403, msg="Don't attack me")
    if cb_name is None or cb_name.strip() == "":
        return BaseResponse(code=404, msg="知识库名称不能为空，请重新填写知识库名称")

    cb = cb_exists(cb_name)
    if cb:
        try:
            delete_cb_from_db(cb_name)

            # delete local file
            shutil.rmtree(CB_ROOT_PATH + os.sep + cb_name)

            # delete from codebase
            cbh = CodeBaseHandler(cb_name, embed_config=embed_config, llm_config=llm_config)
            cbh.delete_codebase(codebase_name=cb_name)

        except Exception as e:
            print(e)
            return BaseResponse(code=500, msg=f"删除代码知识库出错： {e}")

    return BaseResponse(code=200, msg=f"已删除代码知识库 {cb_name}")


def search_code(cb_name: str = Body(..., examples=["sofaboot"]),
                query: str = Body(..., examples=['你好']),
                code_limit: int = Body(..., examples=['1']),
                search_type: str = Body(..., examples=['你好']),
                history_node_list: list = Body(...),
                api_key: bool = Body(..., examples=["samples"]),
                api_base_url: bool = Body(..., examples=["samples"]),
                embed_model: bool = Body(..., examples=["samples"]),
                embed_model_path: bool = Body(..., examples=["samples"]),
                embed_engine: bool = Body(..., examples=["samples"]),
                model_name: bool = Body(..., examples=["samples"]),
                temperature: bool = Body(..., examples=["samples"]),
                model_device: bool = Body(..., examples=["samples"]),
                use_nh: bool = True,
                local_graph_path: str = '',
                embed_config: EmbedConfig = None,
                ) -> dict:
    
    if os.environ.get("log_verbose", "0") >= "2":
        logger.info(f'local_graph_path={local_graph_path}')
        logger.info('cb_name={}'.format(cb_name))
        logger.info('query={}'.format(query))
        logger.info('code_limit={}'.format(code_limit))
        logger.info('search_type={}'.format(search_type))
        logger.info('history_node_list={}'.format(history_node_list))
    embed_config: EmbedConfig = EmbedConfig(**locals()) if embed_config is None else embed_config
    llm_config: LLMConfig = LLMConfig(**locals())
    try:
        # load codebase
        cbh = CodeBaseHandler(codebase_name=cb_name, embed_config=embed_config, llm_config=llm_config,
                              use_nh=use_nh, local_graph_path=local_graph_path)

        # search code
        context, related_vertices = cbh.search_code(query, search_type=search_type, limit=code_limit)

        res = {
            'context': context,
            'related_vertices': related_vertices
        }
        return res
    except Exception as e:
        logger.exception(e)
        return {}


def search_related_vertices(cb_name: str = Body(..., examples=["sofaboot"]),
                            vertex: str = Body(..., examples=['***'])) -> dict:

    logger.info('cb_name={}'.format(cb_name))
    logger.info('vertex={}'.format(vertex))

    try:
        # load codebase
        nh = NebulaHandler(host=NEBULA_HOST, port=NEBULA_PORT, username=NEBULA_USER,
                           password=NEBULA_PASSWORD, space_name=cb_name)
        
        if vertex.endswith(".java"):
            cypher = f'''MATCH (v1)--(v2:package) WHERE id(v1) == '{vertex}' RETURN id(v2) as id;'''
        else:
            cypher = f'''MATCH (v1)--(v2) WHERE id(v1) == '{vertex}' RETURN id(v2) as id;'''
        # cypher = f'''MATCH (v1)--(v2) WHERE id(v1) == '{vertex}' RETURN v2;'''
        cypher_res = nh.execute_cypher(cypher=cypher, format_res=True)
        related_vertices = cypher_res.get('id', [])
        related_vertices = [i.as_string() for i in related_vertices]

        res = {
            'vertices': related_vertices
        }

        return res
    except Exception as e:
        logger.exception(e)
        return {}


def search_code_by_vertex(cb_name: str = Body(..., examples=["sofaboot"]),
                            vertex: str = Body(..., examples=['***'])) -> dict:

    # logger.info('cb_name={}'.format(cb_name))
    # logger.info('vertex={}'.format(vertex))

    try:
        nh = NebulaHandler(host=NEBULA_HOST, port=NEBULA_PORT, username=NEBULA_USER,
                           password=NEBULA_PASSWORD, space_name=cb_name)

        cypher = f'''MATCH (v1:package)-[e:contain]->(v2) WHERE id(v2) == '{vertex}' RETURN id(v1) as id;'''
        cypher_res = nh.execute_cypher(cypher=cypher, format_res=True)

        related_vertices = cypher_res.get('id', [])
        related_vertices = [i.as_string() for i in related_vertices]

        if not related_vertices:
            return {'code': ''}
        ch = ChromaHandler(path=CHROMA_PERSISTENT_PATH, collection_name=cb_name)

        # logger.info(related_vertices)
        chroma_res = ch.get(ids=related_vertices, include=['metadatas'])
        # logger.info(chroma_res)

        if chroma_res['result']['ids']:
            code_text = chroma_res['result']['metadatas'][0]['code_text']
        else:
            code_text = ''

        res = {
            'code': code_text
        }

        return res
    except Exception as e:
        logger.exception(e)
        return {'code': ""}


def cb_exists_api(cb_name: str = Body(..., examples=["sofaboot"])) -> bool:
    try:
        res = cb_exists(cb_name)
        return res
    except Exception as e:
        logger.exception(e)
        return False



