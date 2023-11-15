# encoding: utf-8
'''
@author: 温进
@file: code.py.py
@time: 2023/10/23 下午5:31
@desc:
'''

import streamlit as st
import os
import time
import traceback
from typing import Literal, Dict, Tuple
from st_aggrid import AgGrid, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import pandas as pd

from configs.model_config import embedding_model_dict, kbs_config, EMBEDDING_MODEL, DEFAULT_VS_TYPE, WEB_CRAWL_PATH
from .utils import *
from dev_opsgpt.utils.path_utils import *
from dev_opsgpt.service.service_factory import get_cb_details, get_cb_details_by_cb_name
from dev_opsgpt.orm import table_init

# SENTENCE_SIZE = 100

cell_renderer = JsCode("""function(params) {if(params.value==true){return '✓'}else{return '×'}}""")


def file_exists(cb: str, selected_rows: List) -> Tuple[str, str]:
    '''
    check whether the dir exist in local file
    return the dir's name and path if it exists.
    '''
    if selected_rows:
        file_name = selected_rows[0]["code_name"]
        file_path = get_file_path(cb, file_name)
        if os.path.isfile(file_path):
            return file_name, file_path
    return "", ""


def code_page(api: ApiRequest):
    # 判断表是否存在并进行初始化
    table_init()

    try:
        logger.info(get_cb_details())
        cb_list = {x["code_name"]: x for x in get_cb_details()}
    except Exception as e:
        logger.exception(e)
        st.error("获取知识库信息错误，请检查是否已按照 `README.md` 中 `4 知识库初始化与迁移` 步骤完成初始化或迁移，或是否为数据库连接错误。")
        st.stop()
    cb_names = list(cb_list.keys())

    if "selected_cb_name" in st.session_state and st.session_state["selected_cb_name"] in cb_names:
        selected_cb_index = cb_names.index(st.session_state["selected_cb_name"])
    else:
        selected_cb_index = 0

    def format_selected_cb(cb_name: str) -> str:
        if cb := cb_list.get(cb_name):
            return f"{cb_name} ({cb['code_path']})"
        else:
            return cb_name

    selected_cb = st.selectbox(
        "请选择或新建代码知识库：",
        cb_names + ["新建代码知识库"],
        format_func=format_selected_cb,
        index=selected_cb_index
    )

    if selected_cb == "新建代码知识库":
        with st.form("新建代码知识库"):

            cb_name = st.text_input(
                "新建代码知识库名称",
                placeholder="新代码知识库名称，不支持中文命名",
                key="cb_name",
            )

            file = st.file_uploader("上传代码库 zip 文件",
                                     ['.zip'],
                                     accept_multiple_files=False,
                                     )

            submit_create_kb = st.form_submit_button(
                "新建",
                use_container_width=True,
            )

        if submit_create_kb:
            # unzip file
            logger.info('files={}'.format(file))

            if not cb_name or not cb_name.strip():
                st.error(f"知识库名称不能为空！")
            elif cb_name in cb_list:
                st.error(f"名为 {cb_name} 的知识库已经存在！")
            elif file.type not in ['application/zip', 'application/x-zip-compressed']:
                logger.error(f"{file.type}")
                st.error('请先上传 zip 文件，再新建代码知识库')
            else:
                ret = api.create_code_base(
                    cb_name,
                    file,
                    no_remote_api=True
                )
                st.toast(ret.get("msg", " "))
                st.session_state["selected_cb_name"] = cb_name
                st.experimental_rerun()
    elif selected_cb:
        cb = selected_cb

        # 知识库详情
        cb_details = get_cb_details_by_cb_name(cb)
        if not len(cb_details):
            st.info(f"代码知识库 `{cb}` 中暂无信息")
        else:
            logger.info(cb_details)
            st.write(f"代码知识库 `{cb}` 加载成功，中含有以下信息:")

            st.write('代码知识库 `{}` 代码文件数=`{}`'.format(cb_details['code_name'],
                                                    cb_details.get('code_file_num', 'unknown')))

            st.write('代码知识库 `{}` 知识图谱节点数=`{}`'.format(cb_details['code_name'], cb_details['code_graph_node_num']))

        st.divider()

        cols = st.columns(3)

        if cols[2].button(
                "删除知识库",
                use_container_width=True,
        ):
            ret = api.delete_code_base(cb,
                    no_remote_api=True)
            st.toast(ret.get("msg", "删除成功"))
            time.sleep(0.5)
            st.experimental_rerun()
