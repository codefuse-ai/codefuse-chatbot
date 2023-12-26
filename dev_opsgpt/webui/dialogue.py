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
from dev_opsgpt.service.service_factory import get_cb_details_by_cb_name

chat_box = ChatBox(
    assistant_avatar="../sources/imgs/devops-chatbot2.png"
)

cur_dir = os.path.dirname(os.path.abspath(__file__))

GLOBAL_EXE_CODE_TEXT = ""
GLOBAL_MESSAGE = {"figures": {}, "final_contents": {}}



import yaml

# 加载YAML文件
webui_yaml_filename = "webui_zh.yaml" if True else "webui_en.yaml"
with open(os.path.join(cur_dir, f"yamls/{webui_yaml_filename}"), 'r') as f:
    try:
        webui_configs = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print(exc)


def get_messages_history(history_len: int, isDetailed=False) -> List[Dict]:
    def filter(msg):
        '''
        针对当前简单文本对话，只返回每条消息的第一个element的内容
        '''
        content = [x._content for x in msg["elements"] if x._output_method in ["markdown", "text"]]
        content = content[0] if content else ""
        if isDetailed:
            for k, v in GLOBAL_MESSAGE["final_contents"].items():
                if k == content:
                    content = v[-1]
                    break

        for k, v in GLOBAL_MESSAGE["figures"].items():
            content = content.replace(v, k)

        return {
            "role": msg["role"],
            "content": content,
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


def upload2sandbox(upload_file, api: ApiRequest):
    if upload_file is None:
        res = {"msg": False}
    else:
        res = api.web_sd_upload(upload_file)

def dialogue_page(api: ApiRequest):
    global GLOBAL_EXE_CODE_TEXT
    chat_box.init_session()

    with st.sidebar:
        # TODO: 对话模型与会话绑定
        def on_mode_change():
            mode = st.session_state.dialogue_mode
            text = webui_configs["dialogue"]["text_mode_swtich"] + f"{mode}"
            if mode == webui_configs["dialogue"]["mode"][1]:
                cur_kb = st.session_state.get("selected_kb")
                if cur_kb:
                    text = text + webui_configs["dialogue"]["text_knowledgeBase_swtich"] + f'`{cur_kb}`'
            st.toast(text)

        dialogue_mode = st.selectbox(webui_configs["dialogue"]["mode_instruction"],
                                     webui_configs["dialogue"]["mode"],
                                    #  ["LLM 对话",
                                    #   "知识库问答",
                                    #   "代码知识库问答",
                                    #   "搜索引擎问答",
                                    #   "Agent问答"
                                    #   ],
                                     on_change=on_mode_change,
                                     key="dialogue_mode",
                                     )
        history_len = st.number_input(webui_configs["dialogue"]["history_length"], 0, 10, 3)

        def on_kb_change():
            st.toast(f"{webui_configs['dialogue']['text_loaded_kbase']}: {st.session_state.selected_kb}")

        def on_cb_change():
            st.toast(f"{webui_configs['dialogue']['text_loaded_cbase']}: {st.session_state.selected_cb}")
            cb_details = get_cb_details_by_cb_name(st.session_state.selected_cb)
            st.session_state['do_interpret'] = cb_details['do_interpret']

        # 
        if "interpreter_file_key" not in st.session_state:
            st.session_state["interpreter_file_key"] = 0

        not_agent_qa = True
        interpreter_file = ""
        is_detailed = False
        if dialogue_mode == webui_configs["dialogue"]["mode"][1]:
            with st.expander(webui_configs["dialogue"]["kbase_expander_name"], True):
                kb_list = api.list_knowledge_bases(no_remote_api=True)
                selected_kb = st.selectbox(
                    webui_configs["dialogue"]["kbase_selectbox_name"],
                    kb_list,
                    on_change=on_kb_change,
                    key="selected_kb",
                )
                kb_top_k = st.number_input(
                    webui_configs["dialogue"]["kbase_ninput_topk_name"], 1, 20, 3)
                score_threshold = st.number_input(
                    webui_configs["dialogue"]["kbase_ninput_score_threshold_name"], 
                    0.0, float(SCORE_THRESHOLD), float(SCORE_THRESHOLD), 
                    float(SCORE_THRESHOLD//100))

        elif dialogue_mode == webui_configs["dialogue"]["mode"][2]:
            with st.expander(webui_configs["dialogue"]["cbase_expander_name"], True):
                cb_list = api.list_cb(no_remote_api=True)
                logger.debug('codebase_list={}'.format(cb_list))
                selected_cb = st.selectbox(
                    webui_configs["dialogue"]["cbase_selectbox_name"],
                    cb_list,
                    on_change=on_cb_change,
                    key="selected_cb",
                )

                # change do_interpret
                st.toast(f"{webui_configs['dialogue']['text_loaded_cbase']}: {st.session_state.selected_cb}")
                cb_details = get_cb_details_by_cb_name(st.session_state.selected_cb)
                st.session_state['do_interpret'] = cb_details['do_interpret']

                cb_code_limit = st.number_input(
                    webui_configs["dialogue"]["cbase_ninput_topk_name"], 1, 20, 1)

                search_type_list = webui_configs["dialogue"]["cbase_search_type_v1"] if st.session_state['do_interpret'] == 'YES' \
                    else webui_configs["dialogue"]["cbase_search_type_v2"]

                cb_search_type = st.selectbox(
                    webui_configs["dialogue"]["cbase_selectbox_type_name"],
                    search_type_list,
                    key='cb_search_type'
                )
        elif dialogue_mode == webui_configs["dialogue"]["mode"][3]:
            with st.expander(webui_configs["dialogue"]["expander_search_name"], True):
                search_engine = st.selectbox(
                    webui_configs["dialogue"]["selectbox_search_name"], 
                    SEARCH_ENGINES.keys(), 0)
                se_top_k = st.number_input(
                    webui_configs["dialogue"]["ninput_search_topk_name"], 1, 20, 3)
        elif dialogue_mode == webui_configs["dialogue"]["mode"][4]:
            not_agent_qa = False
            with st.expander(webui_configs["dialogue"]["phase_expander_name"], True):
                choose_phase = st.selectbox(
                    webui_configs["dialogue"]["phase_selectbox_name"], PHASE_LIST, 0)

            is_detailed = st.toggle(webui_configs["dialogue"]["phase_toggle_detailed_name"], False)
            tool_using_on = st.toggle(
                webui_configs["dialogue"]["phase_toggle_doToolUsing"], 
                PHASE_CONFIGS[choose_phase]["do_using_tool"])
            tool_selects = []
            if tool_using_on:
                with st.expander("工具军火库", True):
                    tool_selects = st.multiselect(
                        webui_configs["dialogue"]["phase_multiselect_tools"], 
                        TOOL_SETS, ["WeatherInfo"])
            
            search_on = st.toggle(webui_configs["dialogue"]["phase_toggle_doSearch"], 
                                  PHASE_CONFIGS[choose_phase]["do_search"])
            search_engine, top_k = None, 3
            if search_on:
                with st.expander(webui_configs["dialogue"]["expander_search_name"], True):
                    search_engine = st.selectbox(
                        webui_configs["dialogue"]["selectbox_search_name"], 
                        SEARCH_ENGINES.keys(), 0)
                    se_top_k = st.number_input(
                        webui_configs["dialogue"]["ninput_search_topk_name"], 1, 20, 3)

            doc_retrieval_on = st.toggle(
                webui_configs["dialogue"]["phase_toggle_doDocRetrieval"], 
                  PHASE_CONFIGS[choose_phase]["do_doc_retrieval"])
            selected_kb, top_k, score_threshold = None, 3, 1.0
            if doc_retrieval_on:
                with st.expander(webui_configs["dialogue"]["kbase_expander_name"], True):
                    kb_list = api.list_knowledge_bases(no_remote_api=True)
                    selected_kb = st.selectbox(
                        webui_configs["dialogue"]["kbase_selectbox_name"],
                        kb_list,
                        on_change=on_kb_change,
                        key="selected_kb",
                    )
                    top_k = st.number_input(
                        webui_configs["dialogue"]["kbase_ninput_topk_name"], 1, 20, 3)
                    score_threshold = st.number_input(
                        webui_configs["dialogue"]["kbase_ninput_score_threshold_name"], 
                        0.0, float(SCORE_THRESHOLD), float(SCORE_THRESHOLD), 
                        float(SCORE_THRESHOLD//100))
                    
            code_retrieval_on = st.toggle(
                webui_configs["dialogue"]["phase_toggle_doCodeRetrieval"], 
                  PHASE_CONFIGS[choose_phase]["do_code_retrieval"])
            selected_cb, top_k = None, 1
            cb_search_type = "tag"
            if code_retrieval_on:
                with st.expander(webui_configs["dialogue"]["cbase_expander_name"], True):
                    cb_list = api.list_cb(no_remote_api=True)
                    logger.debug('codebase_list={}'.format(cb_list))
                    selected_cb = st.selectbox(
                        webui_configs["dialogue"]["cbase_selectbox_name"],
                        cb_list,
                        on_change=on_cb_change,
                        key="selected_cb",
                    )
                    # change do_interpret
                    st.toast(f"{webui_configs['dialogue']['text_loaded_cbase']}: {st.session_state.selected_cb}")
                    cb_details = get_cb_details_by_cb_name(st.session_state.selected_cb)
                    st.session_state['do_interpret'] = cb_details['do_interpret']

                    top_k = st.number_input(
                        webui_configs["dialogue"]["cbase_ninput_topk_name"], 1, 20, 1)

                    search_type_list = webui_configs["dialogue"]["cbase_search_type_v1"] if st.session_state['do_interpret'] == 'YES' \
                        else webui_configs["dialogue"]["cbase_search_type_v2"]

                    cb_search_type = st.selectbox(
                        webui_configs["dialogue"]["cbase_selectbox_type_name"],
                        search_type_list,
                        key='cb_search_type'
                    )

        with st.expander(webui_configs["sandbox"]["expander_name"], False):

            interpreter_file = st.file_uploader(
                webui_configs["sandbox"]["file_upload_name"],
                [i for ls in LOADER2EXT_DICT.values() for i in ls] + ["jpg", "png"],
                accept_multiple_files=False,
                key=st.session_state.interpreter_file_key,
            )

            files = api.web_sd_list_files()
            files = files["data"]
            download_file = st.selectbox(webui_configs["sandbox"]["selectbox_name"], files,
                                    key="download_file",)

            cols = st.columns(3)
            file_url, file_name = api.web_sd_download(download_file)
            if cols[0].button(webui_configs["sandbox"]["button_upload_name"],):
                upload2sandbox(interpreter_file, api)
                st.session_state["interpreter_file_key"] += 1
                interpreter_file = ""
                st.experimental_rerun()
                
            cols[1].download_button(webui_configs["sandbox"]["button_download_name"], 
                                    file_url, file_name)
            if cols[2].button(webui_configs["sandbox"]["button_delete_name"],):
                api.web_sd_delete(download_file)

        code_interpreter_on = st.toggle(
            webui_configs["sandbox"]["toggle_doCodeInterpreter"]) and not_agent_qa
        code_exec_on = st.toggle(webui_configs["sandbox"]["toggle_doAutoCodeExec"]) and not_agent_qa

    # Display chat messages from history on app rerun

    chat_box.output_messages()

    chat_input_placeholder = webui_configs["chat"]["chat_placeholder"]
    code_text = "" or GLOBAL_EXE_CODE_TEXT
    codebox_res = None

    if prompt := st.chat_input(chat_input_placeholder, key="prompt"):
        upload2sandbox(interpreter_file, api)
        logger.debug(f"prompt: {prompt}")

        history = get_messages_history(history_len, is_detailed)
        chat_box.user_say(prompt)
        if dialogue_mode == webui_configs["dialogue"]["mode"][0]:
            chat_box.ai_say(webui_configs["chat"]["chatbox_saying"])
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
        elif dialogue_mode == webui_configs["dialogue"]["mode"][4]:
            display_infos = [webui_configs["chat"]["chatbox_saying"]]
            if search_on:
                display_infos.append(Markdown("...", in_expander=True, 
                                              title=webui_configs["chat"]["chatbox_search_result"]))
            if doc_retrieval_on:
                display_infos.append(Markdown("...", in_expander=True,
                                              title=webui_configs["chat"]["chatbox_doc_result"]))
            if code_retrieval_on:
                display_infos.append(Markdown("...", in_expander=True,
                                              title=webui_configs["chat"]["chatbox_code_result"]))
                
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
                "cb_search_type": cb_search_type,
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
                "upload_file": interpreter_file,
            }
            text = ""
            d = {"docs": []}
            for idx_count, d in enumerate(api.agent_achat(**input_kargs)):
                if error_msg := check_error_msg(d): # check whether error occured
                    st.error(error_msg)
                # logger.debug(f"d: {d['answer']}")
                text = d["answer"]
                for text_length in range(0, len(text)+1, 10):
                    chat_box.update_msg(text[:text_length+10], element_index=0, streaming=True)

            GLOBAL_MESSAGE.setdefault("final_contents", {}).setdefault(d.get("answer", ""), []).append(d.get("final_content", ""))

            for k, v in d["figures"].items():
                if k in text:
                    img_html = "\n<img src='data:image/png;base64,{}' class='img-fluid'>\n".format(v)
                    text = text.replace(k, img_html).replace(".png", "")
                    GLOBAL_MESSAGE.setdefault("figures", {}).setdefault(k, v)

            chat_box.update_msg(text, element_index=0, streaming=False, state="complete")  # 更新最终的字符串，去除光标
            if search_on:
                chat_box.update_msg(f"{webui_configs['chat']['chatbox_search_result']}:\n\n" + "\n\n".join(d["search_docs"]), element_index=search_on, streaming=False, state="complete")
            if doc_retrieval_on:
                chat_box.update_msg(f"{webui_configs['chat']['chatbox_doc_result']}:\n\n" + "\n\n".join(d["db_docs"]), element_index=search_on+doc_retrieval_on, streaming=False, state="complete")
            if code_retrieval_on:
                chat_box.update_msg(f"{webui_configs['chat']['chatbox_code_result']}:\n\n" + "\n\n".join(d["code_docs"]), 
                                    element_index=search_on+doc_retrieval_on+code_retrieval_on, streaming=False, state="complete")
            
            history_node_list.extend([node[0] for node in d.get("related_nodes", [])])
            history_node_list = list(set(history_node_list))
            st.session_state['history_node_list'] = history_node_list
        elif dialogue_mode == webui_configs["dialogue"]["mode"][1]:
            history = get_messages_history(history_len)
            chat_box.ai_say([
                f"{webui_configs['chat']['chatbox_doc_querying']} `{selected_kb}` ...",
                Markdown("...", in_expander=True, title=webui_configs['chat']['chatbox_doc_result']),
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
            chat_box.update_msg("{webui_configs['chat']['chatbox_doc_result']}: \n\n".join(d["docs"]), element_index=1, streaming=False, state="complete")
            # 判断是否存在代码, 并提高编辑功能，执行功能
            code_text = api.codebox.decode_code_from_text(text)
            GLOBAL_EXE_CODE_TEXT = code_text
            if code_text and code_exec_on:
                codebox_res = api.codebox_chat("```"+code_text+"```", do_code_exe=True)
        elif dialogue_mode == webui_configs["dialogue"]["mode"][2]:
            logger.info('prompt={}'.format(prompt))
            logger.info('history={}'.format(history))
            if 'history_node_list' in st.session_state:
                api.codeChat.history_node_list = st.session_state['history_node_list']

            chat_box.ai_say([
                f"{webui_configs['chat']['chatbox_code_querying']} `{selected_cb}` ...",
                Markdown("...", in_expander=True, title=webui_configs['chat']['chatbox_code_result']),
            ])
            text = ""
            d = {"codes": []}

            for idx_count, d in enumerate(api.code_base_chat(query=prompt, code_base_name=selected_cb,
                                                             code_limit=cb_code_limit, history=history,
                                                             cb_search_type=cb_search_type,
                                                             no_remote_api=True)):
                if error_msg := check_error_msg(d):
                    st.error(error_msg)
                text += d["answer"]
                if idx_count % 10 == 0:
                    # text = replace_lt_gt(text)
                    chat_box.update_msg(text, element_index=0)

            # postprocess
            text = replace_lt_gt(text)
            chat_box.update_msg(text, element_index=0, streaming=False)  # 更新最终的字符串，去除光标
            logger.debug('text={}'.format(text))
            chat_box.update_msg("\n".join(d["codes"]), element_index=1, streaming=False, state="complete")

            # session state update
            # st.session_state['history_node_list'] = api.codeChat.history_node_list

        elif dialogue_mode == webui_configs["dialogue"]["mode"][3]:
            chat_box.ai_say([
                webui_configs['chat']['chatbox_searching'],
                Markdown("...", in_expander=True, title=webui_configs['chat']['chatbox_search_result']),
            ])
            text = ""
            d = {"docs": []}
            for idx_count, d in enumerate(api.search_engine_chat(prompt, search_engine, se_top_k, history)):
                if error_msg := check_error_msg(d): # check whether error occured
                    st.error(error_msg)
                text += d["answer"]
                if idx_count%10 == 0:
                    chat_box.update_msg(text, element_index=0)
                # chat_box.update_msg("搜索匹配结果: \n\n".join(d["docs"]), element_index=1, streaming=False)
            chat_box.update_msg(text, element_index=0, streaming=False)  # 更新最终的字符串，去除光标
            chat_box.update_msg(f"{webui_configs['chat']['chatbox_search_result']}: \n\n".join(d["docs"]), element_index=1, streaming=False, state="complete")
            # 判断是否存在代码, 并提高编辑功能，执行功能
            code_text = api.codebox.decode_code_from_text(text)
            GLOBAL_EXE_CODE_TEXT = code_text
            if code_text and code_exec_on:
                codebox_res = api.codebox_chat("```"+code_text+"```", do_code_exe=True)

        # 将上传文件清空
        st.session_state["interpreter_file_key"] += 1
        st.experimental_rerun()

    if code_interpreter_on:
        with st.expander(webui_configs['sandbox']['expander_code_name'], False):
            code_part = st.text_area(
                webui_configs['sandbox']['textArea_code_name'], code_text, key="code_text")
            cols = st.columns(2)
            if cols[0].button(
                webui_configs['sandbox']['button_modify_code_name'],
                use_container_width=True,
            ):
                code_text = code_part
                GLOBAL_EXE_CODE_TEXT = code_text
                st.toast(webui_configs['sandbox']['text_modify_code'])

            if cols[1].button(
                webui_configs['sandbox']['button_exec_code_name'],
                use_container_width=True
            ):
                if code_text:
                    codebox_res = api.codebox_chat("```"+code_text+"```", do_code_exe=True)
                    st.toast(webui_configs['sandbox']['text_execing_code'],)
                else:
                    st.toast(webui_configs['sandbox']['text_error_exec_code'],)

    #TODO 这段信息会被记录到history里
    if codebox_res is not None and codebox_res.code_exe_status != 200:
        st.toast(f"{codebox_res.code_exe_response}")

    if codebox_res is not None and codebox_res.code_exe_status == 200:
        st.toast(f"codebox_chat {codebox_res}")
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
                webui_configs['export']['button_clear_conversation_name'],
                use_container_width=True,
        ):
            chat_box.reset_history()
            GLOBAL_EXE_CODE_TEXT = ""
            if 'history_node_list' in st.session_state:
                st.session_state['history_node_list'] = []
            st.experimental_rerun()

    export_btn.download_button(
        webui_configs['export']['download_button_export_name'],
        "".join(chat_box.export2md()),
        file_name=f"{now:%Y-%m-%d %H.%M}_conversations.md",
        mime="text/markdown",
        use_container_width=True,
    )
