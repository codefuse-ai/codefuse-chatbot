import streamlit as st
from streamlit_chatbox import *
from typing import List, Dict
from datetime import datetime

from .utils import *
from dev_opsgpt.utils import *
from dev_opsgpt.chat.search_chat import SEARCH_ENGINES

chat_box = ChatBox(
    assistant_avatar="../sources/imgs/devops-chatbot2.png"
)

GLOBAL_EXE_CODE_TEXT = ""


def get_messages_history(history_len: int) -> List[Dict]:
    def filter(msg):
        '''
        针对当前简单文本对话，只返回每条消息的第一个element的内容
        '''
        content = [x._content for x in msg["elements"] if x._output_method in ["markdown", "text"]]
        return {
            "role": msg["role"],
            "content": content[0] if content else "",
        }

    history = chat_box.filter_history(100000, filter)  # workaround before upgrading streamlit-chatbox.
    user_count = 0
    i = 1
    for i in range(1, len(history) + 1):
        if history[-i]["role"] == "user":
            user_count += 1
            if user_count >= history_len:
                break
    return history[-i:]


def dialogue_page(api: ApiRequest):
    global GLOBAL_EXE_CODE_TEXT
    chat_box.init_session()

    with st.sidebar:
        # TODO: 对话模型与会话绑定
        def on_mode_change():
            mode = st.session_state.dialogue_mode
            text = f"已切换到 {mode} 模式。"
            if mode == "知识库问答":
                cur_kb = st.session_state.get("selected_kb")
                if cur_kb:
                    text = f"{text} 当前知识库： `{cur_kb}`。"
            st.toast(text)
            # sac.alert(text, description="descp", type="success", closable=True, banner=True)

        dialogue_mode = st.selectbox("请选择对话模式",
                                     ["LLM 对话",
                                      "知识库问答",
                                      "搜索引擎问答",
                                      ],
                                     on_change=on_mode_change,
                                     key="dialogue_mode",
                                     )
        history_len = st.number_input("历史对话轮数：", 0, 10, 3)

        # todo: support history len

        def on_kb_change():
            st.toast(f"已加载知识库： {st.session_state.selected_kb}")

        if dialogue_mode == "知识库问答":
            with st.expander("知识库配置", True):
                kb_list = api.list_knowledge_bases(no_remote_api=True)
                selected_kb = st.selectbox(
                    "请选择知识库：",
                    kb_list,
                    on_change=on_kb_change,
                    key="selected_kb",
                )
                kb_top_k = st.number_input("匹配知识条数：", 1, 20, 3)
                score_threshold = st.number_input("知识匹配分数阈值：", 0.0, float(SCORE_THRESHOLD), float(SCORE_THRESHOLD), float(SCORE_THRESHOLD//100))
                # chunk_content = st.checkbox("关联上下文", False, disabled=True)
                # chunk_size = st.slider("关联长度：", 0, 500, 250, disabled=True)
        elif dialogue_mode == "搜索引擎问答":
            with st.expander("搜索引擎配置", True):
                search_engine = st.selectbox("请选择搜索引擎", SEARCH_ENGINES.keys(), 0)
                se_top_k = st.number_input("匹配搜索结果条数：", 1, 20, 3)

        code_interpreter_on = st.toggle("开启代码解释器")
        code_exec_on = st.toggle("自动执行代码")

    # Display chat messages from history on app rerun

    chat_box.output_messages()

    chat_input_placeholder = "请输入对话内容，换行请使用Ctrl+Enter "
    code_text = "" or GLOBAL_EXE_CODE_TEXT
    codebox_res = None

    if prompt := st.chat_input(chat_input_placeholder, key="prompt"):
        history = get_messages_history(history_len)
        chat_box.user_say(prompt)
        if dialogue_mode == "LLM 对话":
            chat_box.ai_say("正在思考...")
            text = ""
            r = api.chat_chat(prompt, history)
            for t in r:
                if error_msg := check_error_msg(t): # check whether error occured
                    st.error(error_msg)
                    break
                text += t["answer"]
                chat_box.update_msg(text)
            logger.debug(f"text: {text}")
            chat_box.update_msg(text, streaming=False)  # 更新最终的字符串，去除光标
            # 判断是否存在代码, 并提高编辑功能，执行功能
            code_text = api.codebox.decode_code_from_text(text)
            GLOBAL_EXE_CODE_TEXT = code_text
            if code_text and code_exec_on:
                codebox_res = api.codebox_chat("```"+code_text+"```", do_code_exe=True)

        elif dialogue_mode == "知识库问答":
            history = get_messages_history(history_len)
            chat_box.ai_say([
                f"正在查询知识库 `{selected_kb}` ...",
                Markdown("...", in_expander=True, title="知识库匹配结果"),
            ])
            text = ""
            for idx_count, d in enumerate(api.knowledge_base_chat(prompt, selected_kb, kb_top_k, score_threshold, history)):
                if error_msg := check_error_msg(d): # check whether error occured
                    st.error(error_msg)
                text += d["answer"]
                if idx_count%10 == 0:
                    chat_box.update_msg(text, element_index=0)
                # chat_box.update_msg("知识库匹配结果: \n\n".join(d["docs"]), element_index=1, streaming=False, state="complete")
            chat_box.update_msg(text, element_index=0, streaming=False)  # 更新最终的字符串，去除光标
            chat_box.update_msg("知识库匹配结果: \n\n".join(d["docs"]), element_index=1, streaming=False, state="complete")
            # 判断是否存在代码, 并提高编辑功能，执行功能
            code_text = api.codebox.decode_code_from_text(text)
            GLOBAL_EXE_CODE_TEXT = code_text
            if code_text and code_exec_on:
                codebox_res = api.codebox_chat("```"+code_text+"```", do_code_exe=True)
        elif dialogue_mode == "搜索引擎问答":
            chat_box.ai_say([
                f"正在执行 `{search_engine}` 搜索...",
                Markdown("...", in_expander=True, title="网络搜索结果"),
            ])
            text = ""
            d = {"docs": []}
            for d in api.search_engine_chat(prompt, search_engine, se_top_k):
                if error_msg := check_error_msg(d): # check whether error occured
                    st.error(error_msg)
                text += d["answer"]
                if idx_count%10 == 0:
                    chat_box.update_msg(text, element_index=0)
                # chat_box.update_msg("搜索匹配结果: \n\n".join(d["docs"]), element_index=1, streaming=False)
            chat_box.update_msg(text, element_index=0, streaming=False)  # 更新最终的字符串，去除光标
            chat_box.update_msg("搜索匹配结果: \n\n".join(d["docs"]), element_index=1, streaming=False, state="complete")
            # 判断是否存在代码, 并提高编辑功能，执行功能
            code_text = api.codebox.decode_code_from_text(text)
            GLOBAL_EXE_CODE_TEXT = code_text
            if code_text and code_exec_on:
                codebox_res = api.codebox_chat("```"+code_text+"```", do_code_exe=True)

    if code_interpreter_on:
        with st.expander("代码编辑执行器", False):
            code_part = st.text_area("代码片段", code_text, key="code_text")
            cols = st.columns(2)
            if cols[0].button(
                "修改对话",
                use_container_width=True,
            ):
                code_text = code_part
                GLOBAL_EXE_CODE_TEXT = code_text
                st.toast("修改对话成功")

            if cols[1].button(
                "执行代码",
                use_container_width=True
            ):
                if code_text:
                    codebox_res = api.codebox_chat("```"+code_text+"```", do_code_exe=True)
                    st.toast("正在执行代码")
                else:
                    st.toast("code 不能为空")

    #TODO 这段信息会被记录到history里
    if codebox_res is not None and codebox_res.code_exe_status != 200:
        st.toast(f"{codebox_res.code_exe_response}")

    if codebox_res is not None and codebox_res.code_exe_status == 200:
        st.toast(f"codebox_chajt {codebox_res}")
        chat_box.ai_say(Markdown(code_text, in_expander=True, title="code interpreter", unsafe_allow_html=True), )
        if codebox_res.code_exe_type == "image/png":
            base_text = f"```\n{code_text}\n```\n\n"
            img_html = "<img src='data:image/png;base64,{}' class='img-fluid'>".format(
                codebox_res.code_exe_response
            )
            chat_box.update_msg(base_text + img_html, streaming=False, state="complete")
        else:
            chat_box.update_msg('```\n'+code_text+'\n```'+"\n\n"+'```\n'+codebox_res.code_exe_response+'\n```', 
                                streaming=False, state="complete")

    now = datetime.now()
    with st.sidebar:

        cols = st.columns(2)
        export_btn = cols[0]
        if cols[1].button(
                "清空对话",
                use_container_width=True,
        ):
            chat_box.reset_history()
            GLOBAL_EXE_CODE_TEXT = ""
            st.experimental_rerun()

    export_btn.download_button(
        "导出记录",
        "".join(chat_box.export2md()),
        file_name=f"{now:%Y-%m-%d %H.%M}_对话记录.md",
        mime="text/markdown",
        use_container_width=True,
    )
