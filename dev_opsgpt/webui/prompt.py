import streamlit as st
import os
import time
from datetime import datetime
import traceback
from typing import Literal, Dict, Tuple
from st_aggrid import AgGrid, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import pandas as pd

from configs.model_config import embedding_model_dict, kbs_config, EMBEDDING_MODEL, DEFAULT_VS_TYPE
from .utils import *
from dev_opsgpt.utils.path_utils import *
from dev_opsgpt.service.service_factory import get_kb_details, get_kb_doc_details
from dev_opsgpt.orm import table_init



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
        "测试prompt",
        file_name=f"{now:%Y-%m-%d %H.%M}_对话记录.md",
        mime="text/markdown",
        use_container_width=True,
    )
