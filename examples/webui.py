# 运行方式：
# 1. 安装必要的包：pip install streamlit-option-menu streamlit-chatbox>=1.1.6
# 2. 运行本机fastchat服务：python server\llm_api.py 或者 运行对应的sh文件
# 3. 运行API服务器：python server/api.py。如果使用api = ApiRequest(no_remote_api=True)，该步可以跳过。
# 4. 运行WEB UI：streamlit run webui.py --server.port 7860

import os
import sys
import streamlit as st
from streamlit_option_menu import option_menu

import multiprocessing

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(src_dir)

from webui import *
from configs.model_config import VERSION, LLM_MODEL
from configs.server_config import NO_REMOTE_API
from configs.model_config import CB_ROOT_PATH

from configs.model_config import embedding_model_dict, kbs_config, EMBEDDING_MODEL, DEFAULT_VS_TYPE, WEB_CRAWL_PATH


api = ApiRequest(base_url="http://127.0.0.1:7861", no_remote_api=NO_REMOTE_API, cb_root_path=CB_ROOT_PATH)


if __name__ == "__main__":
    st.set_page_config(
        "CodeFuse-ChatBot WebUI",
        os.path.join("../sources/imgs", "devops-chatbot.png"),
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/codefuse-ai/codefuse-chatbot',
            'Report a bug': "https://github.com/codefuse-ai/codefuse-chatbot/issues",
            'About': f"""欢迎使用 CodeFuse-ChatBot WebUI {VERSION}！"""
        }
    )

    if not chat_box.chat_inited:
        st.toast(
            f"欢迎使用 [`CodeFuse-ChatBot`](https://github.com/codefuse-ai/codefuse-chatbot) ! \n\n"
            f"当前使用模型`{LLM_MODEL}`, 您可以开始提问了."
        )

    pages = {
        "对话": {
            "icon": "chat",
            "func": dialogue_page,
        },
        "知识库管理": {
            "icon": "hdd-stack",
            "func": knowledge_page,
        },
        "代码知识库管理": {
            "icon": "hdd-stack",
            "func": code_page,
        },
        # "Prompt管理": {
        #     "icon": "hdd-stack",
        #     "func": prompt_page,
        # },
    }

    with st.sidebar:
        st.image(
            os.path.join(
                "../sources/imgs",
                "devops-chatbot.png"
            ),
            use_column_width=True
        )
        st.caption(
            f"""<p align="right"> CodeFuse-ChatBot 当前版本：{VERSION}</p>""",
            unsafe_allow_html=True,
        )
        options = list(pages)
        icons = [x["icon"] for x in pages.values()]

        default_index = 0
        selected_page = option_menu(
            "",
            options=options,
            icons=icons,
            # menu_icon="chat-quote",
            default_index=default_index,
        )

    if selected_page in pages:
        pages[selected_page]["func"](api)
    # pages["对话"]["func"](api, )
    # pages["知识库管理"]["func"](api, embedding_model_dict, kbs_config, EMBEDDING_MODEL, DEFAULT_VS_TYPE, WEB_CRAWL_PATH)
    # pages["代码知识库管理"]["func"](api, )
