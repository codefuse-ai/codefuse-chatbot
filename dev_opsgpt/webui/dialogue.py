import streamlit as st
from streamlit_chatbox import *
from typing import List, Dict
from datetime import datetime
from random import randint
from .utils import *

from dev_opsgpt.utils import *
from dev_opsgpt.tools import TOOL_SETS
from dev_opsgpt.chat.search_chat import SEARCH_ENGINES
from dev_opsgpt.connector import PHASE_LIST, PHASE_CONFIGS

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
                                      "代码知识库问答",
                                      "搜索引擎问答",
                                      "工具问答",
                                      "数据分析",
                                      "Agent问答"
                                      ],
                                     on_change=on_mode_change,
                                     key="dialogue_mode",
                                     )
        history_len = st.number_input("历史对话轮数：", 0, 10, 3)

        # todo: support history len

        def on_kb_change():
            st.toast(f"已加载知识库： {st.session_state.selected_kb}")

        def on_cb_change():
            st.toast(f"已加载代码知识库： {st.session_state.selected_cb}")

        not_agent_qa = True
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
        elif dialogue_mode == '代码知识库问答':
            with st.expander('代码知识库配置', True):
                cb_list = api.list_cb(no_remote_api=True)
                logger.debug('codebase_list={}'.format(cb_list))
                selected_cb = st.selectbox(
                    "请选择代码知识库：",
                    cb_list,
                    on_change=on_cb_change,
                    key="selected_cb",
                )
                st.toast(f"已加载代码知识库： {st.session_state.selected_cb}")
                cb_code_limit = st.number_input("匹配代码条数：", 1, 20, 1)
        elif dialogue_mode == "搜索引擎问答":
            with st.expander("搜索引擎配置", True):
                search_engine = st.selectbox("请选择搜索引擎", SEARCH_ENGINES.keys(), 0)
                se_top_k = st.number_input("匹配搜索结果条数：", 1, 20, 3)
        elif dialogue_mode == "工具问答":
            with st.expander("工具军火库", True):
                tool_selects = st.multiselect(
                    '请选择待使用的工具', TOOL_SETS, ["WeatherInfo"])
                
        elif dialogue_mode == "数据分析":
            with st.expander("沙盒文件管理", False):
                def _upload(upload_file):
                    res = api.web_sd_upload(upload_file)
                    logger.debug(res)
                    if res["msg"]:
                        st.success("上文件传成功")
                    else:
                        st.toast("文件上传失败")

                interpreter_file = st.file_uploader(
                    "上传沙盒文件",
                    [i for ls in LOADER2EXT_DICT.values() for i in ls],
                    accept_multiple_files=False,
                    key="interpreter_file",
                )

                if interpreter_file:
                    _upload(interpreter_file)
                    interpreter_file = None
                # 
                files = api.web_sd_list_files()
                files = files["data"]
                download_file = st.selectbox("选择要处理文件", files,
                                        key="download_file",)

                cols = st.columns(2)
                file_url, file_name = api.web_sd_download(download_file)
                cols[0].download_button("点击下载", file_url, file_name)
                if cols[1].button("点击删除", ):
                    api.web_sd_delete(download_file)

        elif dialogue_mode == "Agent问答":
            not_agent_qa = False
            with st.expander("Phase管理", True):
                choose_phase = st.selectbox(
                    '请选择待使用的执行链路', PHASE_LIST, 0)

            is_detailed = st.toggle("返回明细的Agent交互", False)
            tool_using_on = st.toggle("开启工具使用", PHASE_CONFIGS[choose_phase]["do_using_tool"])
            tool_selects = []
            if tool_using_on:
                with st.expander("工具军火库", True):
                    tool_selects = st.multiselect(
                        '请选择待使用的工具', TOOL_SETS, ["WeatherInfo"])
            
            search_on = st.toggle("开启搜索增强", PHASE_CONFIGS[choose_phase]["do_search"])
            search_engine, top_k = None, 3
            if search_on:
                with st.expander("搜索引擎配置", True):
                    search_engine = st.selectbox("请选择搜索引擎", SEARCH_ENGINES.keys(), 0)
                    top_k = st.number_input("匹配搜索结果条数：", 1, 20, 3)

            doc_retrieval_on = st.toggle("开启知识库检索增强", PHASE_CONFIGS[choose_phase]["do_doc_retrieval"])
            selected_kb, top_k, score_threshold = None, 3, 1.0
            if doc_retrieval_on:
                with st.expander("知识库配置", True):
                    kb_list = api.list_knowledge_bases(no_remote_api=True)
                    selected_kb = st.selectbox(
                        "请选择知识库：",
                        kb_list,
                        on_change=on_kb_change,
                        key="selected_kb",
                    )
                    top_k = st.number_input("匹配知识条数：", 1, 20, 3)
                    score_threshold = st.number_input("知识匹配分数阈值：", 0.0, float(SCORE_THRESHOLD), float(SCORE_THRESHOLD), float(SCORE_THRESHOLD//100))

            code_retrieval_on = st.toggle("开启代码检索增强", PHASE_CONFIGS[choose_phase]["do_code_retrieval"])
            selected_cb, top_k = None, 1
            if code_retrieval_on:
                with st.expander('代码知识库配置', True):
                    cb_list = api.list_cb(no_remote_api=True)
                    logger.debug('codebase_list={}'.format(cb_list))
                    selected_cb = st.selectbox(
                        "请选择代码知识库：",
                        cb_list,
                        on_change=on_cb_change,
                        key="selected_cb",
                    )
                    st.toast(f"已加载代码知识库： {st.session_state.selected_cb}")
                    top_k = st.number_input("匹配代码条数：", 1, 20, 1)

            with st.expander("沙盒文件管理", False):
                def _upload(upload_file):
                    res = api.web_sd_upload(upload_file)
                    logger.debug(res)
                    if res["msg"]:
                        st.success("上文件传成功")
                    else:
                        st.toast("文件上传失败")

                interpreter_file = st.file_uploader(
                    "上传沙盒文件",
                    [i for ls in LOADER2EXT_DICT.values() for i in ls],
                    accept_multiple_files=False,
                    key="interpreter_file",
                )

                if interpreter_file:
                    _upload(interpreter_file)
                    interpreter_file = None
                # 
                files = api.web_sd_list_files()
                files = files["data"]
                download_file = st.selectbox("选择要处理文件", files,
                                        key="download_file",)

                cols = st.columns(2)
                file_url, file_name = api.web_sd_download(download_file)
                cols[0].download_button("点击下载", file_url, file_name)
                if cols[1].button("点击删除", ):
                    api.web_sd_delete(download_file)

        code_interpreter_on = st.toggle("开启代码解释器") and not_agent_qa
        code_exec_on = st.toggle("自动执行代码") and not_agent_qa

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
            r = api.chat_chat(prompt, history, no_remote_api=True)
            for t in r:
                if error_msg := check_error_msg(t):  # check whether error occured
                    st.error(error_msg)
                    break
                text += t["answer"]

                # text = replace_lt_gt(text)

                chat_box.update_msg(text)
            # logger.debug(f"text: {text}")

            # text = replace_lt_gt(text)

            chat_box.update_msg(text, streaming=False)  # 更新最终的字符串，去除光标
            # 判断是否存在代码, 并提高编辑功能，执行功能
            code_text = api.codebox.decode_code_from_text(text)
            GLOBAL_EXE_CODE_TEXT = code_text
            if code_text and code_exec_on:
                codebox_res = api.codebox_chat("```"+code_text+"```", do_code_exe=True)
        elif dialogue_mode == "Agent问答":
            display_infos = [f"正在思考..."]
            if search_on:
                display_infos.append(Markdown("...", in_expander=True, title="网络搜索结果"))
            if doc_retrieval_on:
                display_infos.append(Markdown("...", in_expander=True, title="知识库匹配结果"))
            chat_box.ai_say(display_infos)

            if 'history_node_list' in st.session_state:
                history_node_list: List[str] = st.session_state['history_node_list']
            else:
                history_node_list: List[str] = []

            input_kargs = {"query": prompt,
                "phase_name": choose_phase,
                "history": history,
                "doc_engine_name": selected_kb,
                "search_engine_name": search_engine,
                "code_engine_name": selected_cb,
                "top_k": top_k,
                "score_threshold": score_threshold,
                "do_search": search_on,
                "do_doc_retrieval": doc_retrieval_on,
                "do_code_retrieval": code_retrieval_on,
                "do_tool_retrieval": False,
                "custom_phase_configs": {},
                "custom_chain_configs": {},
                "custom_role_configs": {},
                "choose_tools": tool_selects,
                "history_node_list": history_node_list,
                "isDetailed": is_detailed,
            }
            text = ""
            d = {"docs": []}
            for idx_count, d in enumerate(api.agent_chat(**input_kargs)):
                if error_msg := check_error_msg(d): # check whether error occured
                    st.error(error_msg)
                text += d["answer"]
                if idx_count%20 == 0:
                    chat_box.update_msg(text, element_index=0)

            for k, v in d["figures"].items():
                logger.debug(f"figure: {k}")
                if k in text:
                    img_html = "\n<img src='data:image/png;base64,{}' class='img-fluid'>\n".format(v)
                    text = text.replace(k, img_html).replace(".png", "")
            chat_box.update_msg(text, element_index=0, streaming=False, state="complete")  # 更新最终的字符串，去除光标
            if search_on:
                chat_box.update_msg("搜索匹配结果:\n\n" + "\n\n".join(d["search_docs"]), element_index=search_on, streaming=False, state="complete")
            if doc_retrieval_on:
                chat_box.update_msg("知识库匹配结果:\n\n" + "\n\n".join(d["db_docs"]), element_index=search_on+doc_retrieval_on, streaming=False, state="complete")
            
            history_node_list.extend([node[0] for node in d.get("related_nodes", [])])
            history_node_list = list(set(history_node_list))
            st.session_state['history_node_list'] = history_node_list

        elif dialogue_mode == "工具问答":
            chat_box.ai_say("正在思考...")
            text = ""
            r = api.tool_chat(prompt, history, tool_sets=tool_selects)
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
        elif dialogue_mode == "数据分析":
            chat_box.ai_say("正在思考...")
            text = ""
            r = api.data_chat(prompt, history)
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
            d = {"docs": []}
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
        elif dialogue_mode == '代码知识库问答':
            logger.info('prompt={}'.format(prompt))
            logger.info('history={}'.format(history))
            if 'history_node_list' in st.session_state:
                api.codeChat.history_node_list = st.session_state['history_node_list']

            chat_box.ai_say([
                f"正在查询代码知识库 `{selected_cb}` ...",
                Markdown("...", in_expander=True, title="代码库匹配结果"),
            ])
            text = ""
            d = {"codes": []}

            for idx_count, d in enumerate(api.code_base_chat(query=prompt, code_base_name=selected_cb,
                                                             code_limit=cb_code_limit, history=history,
                                                             no_remote_api=True)):
                if error_msg := check_error_msg(d):
                    st.error(error_msg)
                text += d["answer"]
                if idx_count % 10 == 0:
                    # text = replace_lt_gt(text)
                    chat_box.update_msg(text, element_index=0)
            # postprocess
            # text = replace_lt_gt(text)
            chat_box.update_msg(text, element_index=0, streaming=False)  # 更新最终的字符串，去除光标
            logger.debug('text={}'.format(text))
            chat_box.update_msg("\n".join(d["codes"]), element_index=1, streaming=False, state="complete")

            # session state update
            st.session_state['history_node_list'] = api.codeChat.history_node_list

        elif dialogue_mode == "搜索引擎问答":
            chat_box.ai_say([
                f"正在执行 `{search_engine}` 搜索...",
                Markdown("...", in_expander=True, title="网络搜索结果"),
            ])
            text = ""
            d = {"docs": []}
            for idx_count, d in enumerate(api.search_engine_chat(prompt, search_engine, se_top_k)):
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
            chat_box.update_msg(img_html, streaming=False, state="complete")
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
            if 'history_node_list' in st.session_state:
                st.session_state['history_node_list'] = []
            st.experimental_rerun()

    export_btn.download_button(
        "导出记录",
        "".join(chat_box.export2md()),
        file_name=f"{now:%Y-%m-%d %H.%M}_对话记录.md",
        mime="text/markdown",
        use_container_width=True,
    )
