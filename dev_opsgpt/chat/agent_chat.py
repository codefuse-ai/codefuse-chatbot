from fastapi import Body, Request
from fastapi.responses import StreamingResponse
from typing import List, Union, Dict
from loguru import logger
import importlib
import copy
import json
from pathlib import Path

from configs.model_config import (
    llm_model_dict, LLM_MODEL, PROMPT_TEMPLATE, 
    VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD)

from dev_opsgpt.tools import (
    toLangchainTools, 
    TOOL_DICT, TOOL_SETS
)

from dev_opsgpt.connector.phase import BasePhase
from dev_opsgpt.connector.agents import BaseAgent, ReactAgent
from dev_opsgpt.connector.chains import BaseChain
from dev_opsgpt.connector.schema import (
    Message,
    load_phase_configs, load_chain_configs, load_role_configs
    )
from dev_opsgpt.connector.schema import Memory
from dev_opsgpt.utils.common_utils import file_normalize
from dev_opsgpt.chat.utils import History, wrap_done
from dev_opsgpt.connector.configs import PHASE_CONFIGS, AGETN_CONFIGS, CHAIN_CONFIGS

PHASE_MODULE = importlib.import_module("dev_opsgpt.connector.phase")



class AgentChat:

    def __init__(
            self,
            engine_name: str = "",
            top_k: int = 1,
            stream: bool = False,
            ) -> None:
        self.top_k = top_k
        self.stream = stream
        self.chatPhase_dict: Dict[str, BasePhase] = {}

    def chat(
            self, 
            query: str = Body(..., description="用户输入", examples=["hello"]),
            phase_name: str = Body(..., description="执行场景名称", examples=["chatPhase"]),
            chain_name: str = Body(..., description="执行链的名称", examples=["chatChain"]),
            history: List[History] = Body(
                [], description="历史对话",
                examples=[[{"role": "user", "content": "我们来玩成语接龙，我先来，生龙活虎"}]]
                ),
            doc_engine_name: str = Body(..., description="知识库名称", examples=["samples"]),
            search_engine_name: str = Body(..., description="搜索引擎名称", examples=["duckduckgo"]),
            code_engine_name: str = Body(..., description="代码引擎名称", examples=["samples"]),
            top_k: int = Body(VECTOR_SEARCH_TOP_K, description="匹配向量数"),
            score_threshold: float = Body(SCORE_THRESHOLD, description="知识库匹配相关度阈值，取值范围在0-1之间，SCORE越小，相关度越高，取到1相当于不筛选，建议设置在0.5左右", ge=0, le=1),
            stream: bool = Body(False, description="流式输出"),
            local_doc_url: bool = Body(False, description="知识文件返回本地路径(true)或URL(false)"),
            choose_tools: List[str] = Body([], description="选择tool的集合"),
            do_search: bool = Body(False, description="是否进行搜索"),
            do_doc_retrieval: bool = Body(False, description="是否进行知识库检索"),
            do_code_retrieval: bool = Body(False, description="是否执行代码检索"),
            do_tool_retrieval: bool = Body(False, description="是否执行工具检索"),
            custom_phase_configs: dict = Body({}, description="自定义phase配置"),
            custom_chain_configs: dict = Body({}, description="自定义chain配置"),
            custom_role_configs: dict = Body({}, description="自定义role配置"),
            history_node_list: List = Body([], description="代码历史相关节点"),
            isDetailed: bool = Body(False, description="是否输出完整的agent相关内容"),
            upload_file: Union[str, Path, bytes] = "",
            **kargs
            ) -> Message:
        
        # update configs
        phase_configs, chain_configs, agent_configs = self.update_configs(
            custom_phase_configs, custom_chain_configs, custom_role_configs)

        logger.info('phase_configs={}'.format(phase_configs))
        logger.info('chain_configs={}'.format(chain_configs))
        logger.info('agent_configs={}'.format(agent_configs))
        logger.info('phase_name')
        logger.info('chain_name')

        # choose tools
        tools = toLangchainTools([TOOL_DICT[i] for i in choose_tools if i in TOOL_DICT])
        logger.debug(f"upload_file: {upload_file}")

        if upload_file:
            upload_file_name = upload_file if upload_file and isinstance(upload_file, str) else upload_file.name
            for _filename_idx in range(len(upload_file_name), 0, -1):
                if upload_file_name[:_filename_idx] in query:
                    query = query.replace(upload_file_name[:_filename_idx], upload_file_name)
                    break

        input_message = Message(
            role_content=query,
            role_type="human",
            role_name="user",
            input_query=query,
            origin_query=query,
            phase_name=phase_name,
            chain_name=chain_name,
            do_search=do_search,
            do_doc_retrieval=do_doc_retrieval,
            do_code_retrieval=do_code_retrieval,
            do_tool_retrieval=do_tool_retrieval,
            doc_engine_name=doc_engine_name, search_engine_name=search_engine_name,
            code_engine_name=code_engine_name,
            score_threshold=score_threshold, top_k=top_k,
            history_node_list=history_node_list,
            tools=tools
        )
        # history memory mangemant
        history = Memory(messages=[
            Message(role_name=i["role"], role_type=i["role"], role_content=i["content"]) 
            for i in history
            ])
        # start to execute
        phase_class = getattr(PHASE_MODULE, phase_configs[input_message.phase_name]["phase_type"])
        phase = phase_class(input_message.phase_name,
            task = input_message.task,
            phase_config = phase_configs,
            chain_config = chain_configs,
            role_config = agent_configs,
            do_summary=phase_configs[input_message.phase_name]["do_summary"],
            do_code_retrieval=input_message.do_code_retrieval,
            do_doc_retrieval=input_message.do_doc_retrieval,
            do_search=input_message.do_search,
            )
        output_message, local_memory = phase.step(input_message, history)
        # logger.debug(f"local_memory: {local_memory.to_str_messages(content_key='step_content')}")

        # return {
        #         "answer": output_message.role_content,
        #         "db_docs": output_message.db_docs,
        #         "search_docs": output_message.search_docs,
        #         "code_docs":  output_message.code_docs,
        #         "figures": output_message.figures
        #         }

        def chat_iterator(message: Message, local_memory: Memory, isDetailed=False):
            step_content = local_memory.to_str_messages(content_key='step_content', filter_roles=["user"])
            final_content = message.role_content
            result = {
                "answer": "",
                "db_docs": [str(doc) for doc in message.db_docs],
                "search_docs": [str(doc) for doc in message.search_docs],
                "code_docs":  [str(doc) for doc in message.code_docs],
                "related_nodes": [doc.get_related_node() for idx, doc in enumerate(message.code_docs) if idx==0],
                "figures": message.figures,
                "step_content": step_content,
                "final_content": final_content,
                }
            

            related_nodes, has_nodes = [], [ ]
            for nodes in result["related_nodes"]:
                for node in nodes:
                    if node not in has_nodes:
                        related_nodes.append(node)
            result["related_nodes"] = related_nodes
            
            # logger.debug(f"{result['figures'].keys()}, isDetailed: {isDetailed}")
            message_str = step_content
            if self.stream:
                for token in message_str:
                    result["answer"] = token
                    yield json.dumps(result, ensure_ascii=False)
            else:
                for token in message_str:
                    result["answer"] += token
                yield json.dumps(result, ensure_ascii=False)
            
        return StreamingResponse(chat_iterator(output_message, local_memory, isDetailed), media_type="text/event-stream")


    def achat(
            self, 
            query: str = Body(..., description="用户输入", examples=["hello"]),
            phase_name: str = Body(..., description="执行场景名称", examples=["chatPhase"]),
            chain_name: str = Body(..., description="执行链的名称", examples=["chatChain"]),
            history: List[History] = Body(
                [], description="历史对话",
                examples=[[{"role": "user", "content": "我们来玩成语接龙，我先来，生龙活虎"}]]
                ),
            doc_engine_name: str = Body(..., description="知识库名称", examples=["samples"]),
            search_engine_name: str = Body(..., description="搜索引擎名称", examples=["duckduckgo"]),
            code_engine_name: str = Body(..., description="代码引擎名称", examples=["samples"]),
            cb_search_type: str = Body(..., description="代码查询模式", examples=["tag"]),
            top_k: int = Body(VECTOR_SEARCH_TOP_K, description="匹配向量数"),
            score_threshold: float = Body(SCORE_THRESHOLD, description="知识库匹配相关度阈值，取值范围在0-1之间，SCORE越小，相关度越高，取到1相当于不筛选，建议设置在0.5左右", ge=0, le=1),
            stream: bool = Body(False, description="流式输出"),
            local_doc_url: bool = Body(False, description="知识文件返回本地路径(true)或URL(false)"),
            choose_tools: List[str] = Body([], description="选择tool的集合"),
            do_search: bool = Body(False, description="是否进行搜索"),
            do_doc_retrieval: bool = Body(False, description="是否进行知识库检索"),
            do_code_retrieval: bool = Body(False, description="是否执行代码检索"),
            do_tool_retrieval: bool = Body(False, description="是否执行工具检索"),
            custom_phase_configs: dict = Body({}, description="自定义phase配置"),
            custom_chain_configs: dict = Body({}, description="自定义chain配置"),
            custom_role_configs: dict = Body({}, description="自定义role配置"),
            history_node_list: List = Body([], description="代码历史相关节点"),
            isDetailed: bool = Body(False, description="是否输出完整的agent相关内容"),
            upload_file: Union[str, Path, bytes] = "",
            **kargs
            ) -> Message:
        
        # update configs
        phase_configs, chain_configs, agent_configs = self.update_configs(
            custom_phase_configs, custom_chain_configs, custom_role_configs)
        # choose tools
        tools = toLangchainTools([TOOL_DICT[i] for i in choose_tools if i in TOOL_DICT])
        logger.debug(f"upload_file: {upload_file}")

        if upload_file:
            upload_file_name = upload_file if upload_file and isinstance(upload_file, str) else upload_file.name
            for _filename_idx in range(len(upload_file_name), 0, -1):
                if upload_file_name[:_filename_idx] in query:
                    query = query.replace(upload_file_name[:_filename_idx], upload_file_name)
                    break

        input_message = Message(
            role_content=query,
            role_type="human",
            role_name="user",
            input_query=query,
            origin_query=query,
            phase_name=phase_name,
            chain_name=chain_name,
            do_search=do_search,
            do_doc_retrieval=do_doc_retrieval,
            do_code_retrieval=do_code_retrieval,
            do_tool_retrieval=do_tool_retrieval,
            doc_engine_name=doc_engine_name, 
            search_engine_name=search_engine_name,
            code_engine_name=code_engine_name,
            cb_search_type=cb_search_type,
            score_threshold=score_threshold, top_k=top_k,
            history_node_list=history_node_list,
            tools=tools
        )
        # history memory mangemant
        history = Memory(messages=[
            Message(role_name=i["role"], role_type=i["role"], role_content=i["content"]) 
            for i in history
            ])
        # start to execute
        if  phase_configs[input_message.phase_name]["phase_type"] not in self.chatPhase_dict:
            phase_class = getattr(PHASE_MODULE, phase_configs[input_message.phase_name]["phase_type"])
            phase = phase_class(input_message.phase_name,
                task = input_message.task,
                phase_config = phase_configs,
                chain_config = chain_configs,
                role_config = agent_configs,
                do_summary=phase_configs[input_message.phase_name]["do_summary"],
                do_code_retrieval=input_message.do_code_retrieval,
                do_doc_retrieval=input_message.do_doc_retrieval,
                do_search=input_message.do_search,
                )
            self.chatPhase_dict[phase_configs[input_message.phase_name]["phase_type"]] = phase
        else:
            phase = self.chatPhase_dict[phase_configs[input_message.phase_name]["phase_type"]]
        
        def chat_iterator(message: Message, local_memory: Memory, isDetailed=False):
            step_content = local_memory.to_str_messages(content_key='step_content', filter_roles=["user"])
            step_content = "\n\n".join([f"{v}" for parsed_output in local_memory.get_parserd_output_list() for k, v in parsed_output.items() if k not in ["Action Status"]])
            final_content = message.role_content
            result = {
                "answer": "",
                "db_docs": [str(doc) for doc in message.db_docs],
                "search_docs": [str(doc) for doc in message.search_docs],
                "code_docs":  [str(doc) for doc in message.code_docs],
                "related_nodes": [doc.get_related_node() for idx, doc in enumerate(message.code_docs) if idx==0],
                "figures": message.figures,
                "step_content": step_content or final_content,
                "final_content": final_content,
                }
            

            related_nodes, has_nodes = [], [ ]
            for nodes in result["related_nodes"]:
                for node in nodes:
                    if node not in has_nodes:
                        related_nodes.append(node)
            result["related_nodes"] = related_nodes
            
            # logger.debug(f"{result['figures'].keys()}, isDetailed: {isDetailed}")
            message_str = step_content
            if self.stream:
                for token in message_str:
                    result["answer"] = token
                    yield json.dumps(result, ensure_ascii=False)
            else:
                for token in message_str:
                    result["answer"] += token
                yield json.dumps(result, ensure_ascii=False)
            

        for output_message, local_memory in phase.astep(input_message, history):

            # logger.debug(f"output_message: {output_message.role_content}")
            # output_message = Message(**output_message)
            # local_memory = Memory(**local_memory)
            for result in chat_iterator(output_message, local_memory, isDetailed):
                yield result


    def _chat(self, ):
        pass

    def update_configs(self, custom_phase_configs, custom_chain_configs, custom_role_configs):
        '''update phase/chain/agent configs'''
        phase_configs = copy.deepcopy(PHASE_CONFIGS)
        phase_configs.update(custom_phase_configs)
        chain_configs = copy.deepcopy(CHAIN_CONFIGS)
        chain_configs.update(custom_chain_configs)
        agent_configs = copy.deepcopy(AGETN_CONFIGS)
        agent_configs.update(custom_role_configs)
        # phase_configs = load_phase_configs(new_phase_configs)
        # chian_configs = load_chain_configs(new_chain_configs)
        # agent_configs = load_role_configs(new_agent_configs)
        return phase_configs, chain_configs, agent_configs