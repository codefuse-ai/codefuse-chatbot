import streamlit as st
import os
import time
from datetime import datetime
import traceback
from typing import Literal, Dict, Tuple
from st_aggrid import AgGrid, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import pandas as pd

from .utils import *
from muagent.utils.path_utils import *
from muagent.service.service_factory import get_kb_details, get_kb_doc_details
from muagent.orm import table_init

from .dialogue import chat_box

def list_to_converted_strings(lst: list) -> str:
    converted_list = []
    for item in lst:
        role = item.get('role')
        elements = item.get('elements')
        if elements:
            markdown_element = elements[0]
            markdown_text = markdown_element.text if hasattr(markdown_element, 'text') else str(markdown_element)
            # 将角色和文本组合成一个字符串，并添加到转换列表中
            converted_list.append(f"{role}: {markdown_text}")
    # 将转换后的列表连接成一个字符串，每个元素之间用换行符分隔
    return '\n'.join(converted_list)

def prompt_page(api: ApiRequest):
    # 判断表是否存在并进行初始化
    table_init()

    now = datetime.now()
    with st.sidebar:

        cols = st.columns(2)
        export_btn = cols[0]
        if cols[1].button(
                "清空prompt",
                use_container_width=True,
        ):
            st.experimental_rerun()

    export_btn.download_button(
        "导出记录",
        list_to_converted_strings(chat_box.history),
        file_name=f"{now:%Y-%m-%d %H.%M}_对话记录.md",
        mime="text/markdown",
        use_container_width=True,
    )
