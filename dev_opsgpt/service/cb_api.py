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
from dev_opsgpt.utils.server_utils import BaseResponse, ListResponse
from dev_opsgpt.utils.path_utils import *
from dev_opsgpt.orm.commands import *
from dev_opsgpt.db_handler.graph_db_handler.nebula_handler import NebulaHandler
from dev_opsgpt.db_handler.vector_db_handler.chroma_handler import ChromaHandler
from configs.server_config import NEBULA_HOST, NEBULA_PORT, NEBULA_USER, NEBULA_PASSWORD, NEBULA_STORAGED_PORT
from configs.server_config import CHROMA_PERSISTENT_PATH

from configs.model_config import (
    CB_ROOT_PATH
)

# from dev_opsgpt.codebase_handler.codebase_handler import CodeBaseHandler

from dev_opsgpt.codechat.codebase_handler.codebase_handler import CodeBaseHandler

from loguru import logger


async def list_cbs():
    # Get List of Knowledge Base
    return ListResponse(data=list_cbs_from_db())


async def create_cb(zip_file,
                    cb_name: str = Body(..., examples=["samples"]),
                    code_path: str = Body(..., examples=["samples"]),
                    do_interpret: bool = Body(..., examples=["samples"])
                    ) -> BaseResponse:
    logger.info('cb_name={}, zip_path={}, do_interpret={}'.format(cb_name, code_path, do_interpret))

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
        cbh = CodeBaseHandler(cb_name, code_path)
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


async def delete_cb(cb_name: str = Body(..., examples=["samples"])) -> BaseResponse:
    logger.info('cb_name={}'.format(cb_name))
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
            cbh = CodeBaseHandler(cb_name)
            cbh.delete_codebase(codebase_name=cb_name)

        except Exception as e:
            print(e)
            return BaseResponse(code=500, msg=f"删除代码知识库出错： {e}")

    return BaseResponse(code=200, msg=f"已删除代码知识库 {cb_name}")


def search_code(cb_name: str = Body(..., examples=["sofaboot"]),
                query: str = Body(..., examples=['你好']),
                code_limit: int = Body(..., examples=['1']),
                search_type: str = Body(..., examples=['你好']),
                history_node_list: list = Body(...)) -> dict:

    logger.info('cb_name={}'.format(cb_name))
    logger.info('query={}'.format(query))
    logger.info('code_limit={}'.format(code_limit))
    logger.info('search_type={}'.format(search_type))
    logger.info('history_node_list={}'.format(history_node_list))

    try:
        # load codebase
        cbh = CodeBaseHandler(codebase_name=cb_name)

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

        cypher = f'''MATCH (v1)--(v2) WHERE id(v1) == '{vertex}' RETURN id(v2) as id;'''

        cypher_res = nh.execute_cypher(cypher=cypher, format_res=True)

        related_vertices = cypher_res.get('id', [])

        res = {
            'vertices': related_vertices
        }

        return res
    except Exception as e:
        logger.exception(e)
        return {}


def search_code_by_vertex(cb_name: str = Body(..., examples=["sofaboot"]),
                            vertex: str = Body(..., examples=['***'])) -> dict:

    logger.info('cb_name={}'.format(cb_name))
    logger.info('vertex={}'.format(vertex))

    try:
        ch = ChromaHandler(path=CHROMA_PERSISTENT_PATH, collection_name=cb_name)

        # fix vertex
        vertex_use = '#'.join(vertex.split('#')[0:2])
        ids = [vertex_use]

        chroma_res = ch.get(ids=ids)

        code_text = chroma_res['result']['metadatas'][0]['code_text']

        res = {
            'code': code_text
        }

        return res
    except Exception as e:
        logger.exception(e)
        return {}


def cb_exists_api(cb_name: str = Body(..., examples=["sofaboot"])) -> bool:
    try:
        res = cb_exists(cb_name)
        return res
    except Exception as e:
        logger.exception(e)
        return False



