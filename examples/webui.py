# 运行方式：
# 1. 安装必要的包：pip install streamlit-option-menu streamlit-chatbox>=1.1.6
# 2. 运行本机fastchat服务：python server\llm_api.py 或者 运行对应的sh文件
# 3. 运行API服务器：python server/api.py。如果使用api = ApiRequest(no_remote_api=True)，该步可以跳过。
# 4. 运行WEB UI：streamlit run webui.py --server.port 7860

import os, sys
import streamlit as st
from streamlit_option_menu import option_menu

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(src_dir)

from dev_opsgpt.webui import *
from configs import VERSION, LLM_MODEL



api = ApiRequest(base_url="http://127.0.0.1:7861", no_remote_api=True)


if __name__ == "__main__":
    st.set_page_config(
        "DevOpsGPT-Chat WebUI",
        os.path.join("../sources/imgs", "devops-chatbot.png"),
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/lightislost/devopsgpt',
            'Report a bug': "https://github.com/lightislost/devopsgpt/issues",
            'About': f"""欢迎使用 DevOpsGPT-Chat WebUI {VERSION}！"""
        }
    )

    if not chat_box.chat_inited:
        st.toast(
            f"欢迎使用 [`DevOpsGPT-Chat`](https://github.com/lightislost/devopsgpt) ! \n\n"
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
            f"""<p align="right">当前版本：{VERSION}</p>""",
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
