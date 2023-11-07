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

from configs.model_config import (
    CB_ROOT_PATH
)

from dev_opsgpt.codebase_handler.codebase_handler import CodeBaseHandler

from loguru import logger


async def list_cbs():
    # Get List of Knowledge Base
    return ListResponse(data=list_cbs_from_db())


async def create_cb(cb_name: str = Body(..., examples=["samples"]),
                    code_path: str = Body(..., examples=["samples"])
                    ) -> BaseResponse:
    logger.info('cb_name={}, zip_path={}'.format(cb_name, code_path))

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
        cbh = CodeBaseHandler(cb_name, code_path, cb_root_path=CB_ROOT_PATH)
        cbh.import_code(do_save=True)
        code_graph_node_num = len(cbh.nh)
        code_file_num = len(cbh.lcdh)
        logger.info('build code base done')

        # create cb to table
        add_cb_to_db(cb_name, cbh.code_path, code_graph_node_num, code_file_num)
        logger.info('add cb to mysql table success')
    except Exception as e:
        print(e)
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
        except Exception as e:
            print(e)
            return BaseResponse(code=500, msg=f"删除代码知识库出错： {e}")

    return BaseResponse(code=200, msg=f"已删除代码知识库 {cb_name}")


def search_code(cb_name: str = Body(..., examples=["sofaboot"]),
                query: str = Body(..., examples=['你好']),
                code_limit: int = Body(..., examples=['1']),
                history_node_list: list = Body(...)) -> dict:

    logger.info('cb_name={}'.format(cb_name))
    logger.info('query={}'.format(query))
    logger.info('code_limit={}'.format(code_limit))
    logger.info('history_node_list={}'.format(history_node_list))

    try:
        # load codebase
        cbh = CodeBaseHandler(code_name=cb_name, cb_root_path=CB_ROOT_PATH)
        cbh.import_code(do_load=True)

        # search code
        related_code, related_node = cbh.search_code(query, code_limit=code_limit, history_node_list=history_node_list)

        res = {
            'related_code': related_code,
            'related_node': related_node
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



