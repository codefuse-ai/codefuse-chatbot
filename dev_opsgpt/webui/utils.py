# 该文件包含webui通用工具，可以被不同的webui使用
from typing import *
from pathlib import Path
from io import BytesIO
import httpx
import asyncio
from fastapi.responses import StreamingResponse
import contextlib
import json
import nltk
import traceback
from loguru import logger


from configs.model_config import (
    EMBEDDING_MODEL,
    DEFAULT_VS_TYPE,
    KB_ROOT_PATH,
    CB_ROOT_PATH,
    LLM_MODEL,
    SCORE_THRESHOLD,
    VECTOR_SEARCH_TOP_K,
    SEARCH_ENGINE_TOP_K,
    NLTK_DATA_PATH,
    logger,
)

from configs.server_config import SANDBOX_SERVER

from dev_opsgpt.utils.server_utils import run_async, iter_over_async
from dev_opsgpt.service.kb_api import *
from dev_opsgpt.service.cb_api import *
from dev_opsgpt.chat import LLMChat, SearchChat, KnowledgeChat, CodeChat, AgentChat
from dev_opsgpt.sandbox import PyCodeBox, CodeBoxResponse
from dev_opsgpt.utils.common_utils import file_normalize, get_uploadfile

from dev_opsgpt.codechat.code_crawler.zip_crawler import ZipCrawler

from web_crawler.utils.WebCrawler import WebCrawler

nltk.data.path = [NLTK_DATA_PATH] + nltk.data.path


def set_httpx_timeout(timeout=60.0):
    '''
    设置httpx默认timeout到60秒。
    httpx默认timeout是5秒，在请求LLM回答时不够用。
    '''
    httpx._config.DEFAULT_TIMEOUT_CONFIG.connect = timeout
    httpx._config.DEFAULT_TIMEOUT_CONFIG.read = timeout
    httpx._config.DEFAULT_TIMEOUT_CONFIG.write = timeout


KB_ROOT_PATH = Path(KB_ROOT_PATH)
set_httpx_timeout()


class ApiRequest:
    '''
    api.py调用的封装,主要实现:
    1. 简化api调用方式
    2. 实现无api调用(直接运行server.chat.*中的视图函数获取结果),无需启动api.py
    '''
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:7861",
        sandbox_file_url: str = "http://127.0.0.1:7862",
        timeout: float = 60.0,
        no_remote_api: bool = False,   # call api view function directly
    ):
        self.base_url = base_url
        self.sandbox_file_url = sandbox_file_url
        self.timeout = timeout
        self.no_remote_api = no_remote_api
        self.llmChat = LLMChat()
        self.searchChat = SearchChat()
        self.knowledgeChat = KnowledgeChat()
        self.codeChat = CodeChat()
        self.agentChat = AgentChat()

        self.codebox = PyCodeBox(
            remote_url=SANDBOX_SERVER["url"],
            remote_ip=SANDBOX_SERVER["host"], # "http://localhost",
            remote_port=SANDBOX_SERVER["port"],
            token="mytoken",
            do_code_exe=True,
            do_remote=SANDBOX_SERVER["do_remote"]
            )

    def codebox_chat(self, text: str, file_path: str = None, do_code_exe: bool = None) -> CodeBoxResponse:
        return self.codebox.chat(text, file_path, do_code_exe=do_code_exe)

    def _parse_url(self, url: str) -> str:
        if (not url.startswith("http")
                    and self.base_url
                ):
            part1 = self.sandbox_file_url.strip(" /") \
                if "sdfiles" in url else self.base_url.strip(" /")
            part2 = url.strip(" /")
            return f"{part1}/{part2}"
        else:
            return url

    def get(
        self,
        url: str,
        params: Union[Dict, List[Tuple], bytes] = None,
        retry: int = 3,
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[httpx.Response, None]:
        url = self._parse_url(url)
        kwargs.setdefault("timeout", self.timeout)
        while retry > 0:
            try:
                if stream:
                    return httpx.stream("GET", url, params=params, **kwargs)
                else:
                    return httpx.get(url, params=params, **kwargs)
            except Exception as e:
                logger.error(e)
                retry -= 1

    async def aget(
        self,
        url: str,
        params: Union[Dict, List[Tuple], bytes] = None,
        retry: int = 3,
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[httpx.Response, None]:
        url = self._parse_url(url)
        kwargs.setdefault("timeout", self.timeout)
        async with httpx.AsyncClient() as client:
            while retry > 0:
                try:
                    if stream:
                        return await client.stream("GET", url, params=params, **kwargs)
                    else:
                        return await client.get(url, params=params, **kwargs)
                except Exception as e:
                    logger.error(e)
                    retry -= 1

    def post(
        self,
        url: str,
        data: Dict = None,
        json: Dict = None,
        retry: int = 3,
        stream: bool = False,
        **kwargs: Any
    ) -> Union[httpx.Response, None]:
        url = self._parse_url(url)
        kwargs.setdefault("timeout", self.timeout)
        while retry > 0:
            try:
                # return requests.post(url, data=data, json=json, stream=stream, **kwargs)
                if stream:
                    return httpx.stream("POST", url, data=data, json=json, **kwargs)
                else:
                    return httpx.post(url, data=data, json=json, **kwargs)
            except Exception as e:
                logger.error(e)
                retry -= 1

    async def apost(
        self,
        url: str,
        data: Dict = None,
        json: Dict = None,
        retry: int = 3,
        stream: bool = False,
        **kwargs: Any
    ) -> Union[httpx.Response, None]:
        url = self._parse_url(url)
        kwargs.setdefault("timeout", self.timeout)
        async with httpx.AsyncClient() as client:
            while retry > 0:
                try:
                    if stream:
                        return await client.stream("POST", url, data=data, json=json, **kwargs)
                    else:
                        return await client.post(url, data=data, json=json, **kwargs)
                except Exception as e:
                    logger.error(e)
                    retry -= 1

    def delete(
        self,
        url: str,
        data: Dict = None,
        json: Dict = None,
        retry: int = 3,
        stream: bool = False,
        **kwargs: Any
    ) -> Union[httpx.Response, None]:
        url = self._parse_url(url)
        kwargs.setdefault("timeout", self.timeout)
        while retry > 0:
            try:
                if stream:
                    return httpx.stream("DELETE", url, data=data, json=json, **kwargs)
                else:
                    return httpx.delete(url, data=data, json=json, **kwargs)
            except Exception as e:
                logger.error(e)
                retry -= 1

    async def adelete(
        self,
        url: str,
        data: Dict = None,
        json: Dict = None,
        retry: int = 3,
        stream: bool = False,
        **kwargs: Any
    ) -> Union[httpx.Response, None]:
        url = self._parse_url(url)
        kwargs.setdefault("timeout", self.timeout)
        async with httpx.AsyncClient() as client:
            while retry > 0:
                try:
                    if stream:
                        return await client.stream("DELETE", url, data=data, json=json, **kwargs)
                    else:
                        return await client.delete(url, data=data, json=json, **kwargs)
                except Exception as e:
                    logger.error(e)
                    retry -= 1

    def _fastapi_stream2generator(self, response: StreamingResponse, as_json: bool =False):
        '''
        将api.py中视图函数返回的StreamingResponse转化为同步生成器
        '''
        try:
            loop = asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
        
        try:
            for chunk in  iter_over_async(response.body_iterator, loop):
                if as_json and chunk:
                    yield json.loads(chunk)
                elif chunk.strip():
                    yield chunk
        except Exception as e:
            logger.error(traceback.format_exc())

    def _stream2generator(self, response: str, as_json: bool =False):
        '''
        将api.py中视图函数返回的StreamingResponse转化为同步生成器
        '''
        try:
            if as_json and response:
                return json.loads(response)
            elif response.strip():
                return response
        except Exception as e:
            logger.error(traceback.format_exc())

    def _httpx_stream2generator(
        self,
        response: contextlib._GeneratorContextManager,
        as_json: bool = False,
    ):
        '''
        将httpx.stream返回的GeneratorContextManager转化为普通生成器
        '''
        try:
            with response as r:
                for chunk in r.iter_text(None):
                    if as_json and chunk:
                        yield json.loads(chunk)
                    elif chunk.strip():
                        yield chunk
        except httpx.ConnectError as e:
            msg = f"无法连接API服务器，请确认 ‘api.py’ 已正常启动。"
            logger.error(msg)
            logger.error(e)
            yield {"code": 500, "msg": msg}
        except httpx.ReadTimeout as e:
            msg = f"API通信超时，请确认已启动FastChat与API服务（详见RADME '5. 启动 API 服务或 Web UI'）"
            logger.error(msg)
            logger.error(e)
            yield {"code": 500, "msg": msg}
        except Exception as e:
            logger.error(e)
            yield {"code": 500, "msg": str(e)}

    def chat_chat(
        self,
        query: str,
        history: List[Dict] = [],
        stream: bool = True,
        no_remote_api: bool = None,
    ):
        '''
        对应api.py/chat/chat接口
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        data = {
            "query": query,
            "history": history,
            "stream": stream,
        }

        if no_remote_api:
            response = self.llmChat.chat(**data)
            return self._fastapi_stream2generator(response, as_json=True)
        else:
            response = self.post("/chat/chat", json=data, stream=True)
            return self._httpx_stream2generator(response)

    def knowledge_base_chat(
        self,
        query: str,
        knowledge_base_name: str,
        top_k: int = VECTOR_SEARCH_TOP_K,
        score_threshold: float = SCORE_THRESHOLD,
        history: List[Dict] = [],
        stream: bool = True,
        no_remote_api: bool = None,
    ):
        '''
        对应api.py/chat/knowledge_base_chat接口
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        data = {
            "query": query,
            "engine_name": knowledge_base_name,
            "top_k": top_k,
            "score_threshold": score_threshold,
            "history": history,
            "stream": stream,
            "local_doc_url": no_remote_api,
        }

        if no_remote_api:
            response = self.knowledgeChat.chat(**data)
            return self._fastapi_stream2generator(response, as_json=True)
        else:
            response = self.post(
                "/chat/knowledge_base_chat",
                json=data,
                stream=True,
            )
            return self._httpx_stream2generator(response, as_json=True)

    def search_engine_chat(
        self,
        query: str,
        search_engine_name: str,
        top_k: int,
        history: List[Dict] = [],
        stream: bool = True,
        no_remote_api: bool = None,
    ):
        '''
        对应api.py/chat/search_engine_chat接口
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        data = {
            "query": query,
            "engine_name": search_engine_name,
            "top_k": top_k,
            "history": history,
            "stream": stream,
        }

        if no_remote_api:
            response = self.searchChat.chat(**data)
            return self._fastapi_stream2generator(response, as_json=True)
        else:
            response = self.post(
                "/chat/search_engine_chat",
                json=data,
                stream=True,
            )
            return self._httpx_stream2generator(response, as_json=True)

    def code_base_chat(
        self,
        query: str,
        code_base_name: str,
        code_limit: int = 1,
        history: List[Dict] = [],
        cb_search_type: str = 'tag',
        stream: bool = True,
        no_remote_api: bool = None,
    ):
        '''
        对应api.py/chat/knowledge_base_chat接口
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        cb_search_type = {
            '基于 cypher': 'cypher',
            '基于标签': 'tag',
            '基于描述': 'description',
            'tag': 'tag',
            'description': 'description',
            'cypher': 'cypher'
        }.get(cb_search_type, 'tag')


        data = {
            "query": query,
            "history": history,
            "engine_name": code_base_name,
            "code_limit": code_limit,
            "cb_search_type": cb_search_type,
            "stream": stream,
            "local_doc_url": no_remote_api,
        }
        logger.info('data={}'.format(data))

        if no_remote_api:
            # logger.info('history_node_list before={}'.format(self.codeChat.history_node_list))
            response = self.codeChat.chat(**data)
            # logger.info('history_node_list after={}'.format(self.codeChat.history_node_list))
            return self._fastapi_stream2generator(response, as_json=True)
        else:
            response = self.post(
                "/chat/code_chat",
                json=data,
                stream=True,
            )
            return self._httpx_stream2generator(response, as_json=True)

    def agent_chat(
        self,
        query: str,
        phase_name: str,
        doc_engine_name: str,
        code_engine_name: str,
        search_engine_name: str,
        top_k: int = 3,
        score_threshold: float = 1.0,
        history: List[Dict] = [],
        stream: bool = True,
        local_doc_url: bool = False,
        do_search: bool = False,
        do_doc_retrieval: bool = False,
        do_code_retrieval: bool = False,
        do_tool_retrieval: bool = False,
        choose_tools: List[str] = [],
        custom_phase_configs =  {},
        custom_chain_configs = {},
        custom_role_configs = {},
        no_remote_api: bool = None,
        history_node_list: List[str] = [],
        isDetailed: bool = False,
        upload_file: Union[str, Path, bytes] = "",
    ):
        '''
        对应api.py/chat/chat接口
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        data = {
            "query": query,
            "phase_name": phase_name,
            "chain_name": "",
            "history": history,
            "doc_engine_name": doc_engine_name,
            "code_engine_name": code_engine_name,
            "search_engine_name": search_engine_name,
            "top_k": top_k,
            "score_threshold": score_threshold,
            "stream": stream,
            "local_doc_url": local_doc_url,
            "do_search": do_search,
            "do_doc_retrieval": do_doc_retrieval,
            "do_code_retrieval": do_code_retrieval,
            "do_tool_retrieval": do_tool_retrieval,
            "custom_phase_configs": custom_phase_configs,
            "custom_chain_configs": custom_phase_configs,
            "custom_role_configs": custom_role_configs,
            "choose_tools": choose_tools,
            "history_node_list": history_node_list,
            "isDetailed": isDetailed,
            "upload_file": upload_file
        }
        if no_remote_api:
            response = self.agentChat.chat(**data)
            return self._fastapi_stream2generator(response, as_json=True)
        else:
            response = self.post("/chat/data_chat", json=data, stream=True)
            return self._httpx_stream2generator(response)

    def agent_achat(
        self,
        query: str,
        phase_name: str,
        doc_engine_name: str,
        code_engine_name: str,
        cb_search_type: str,
        search_engine_name: str,
        top_k: int = 3,
        score_threshold: float = 1.0,
        history: List[Dict] = [],
        stream: bool = True,
        local_doc_url: bool = False,
        do_search: bool = False,
        do_doc_retrieval: bool = False,
        do_code_retrieval: bool = False,
        do_tool_retrieval: bool = False,
        choose_tools: List[str] = [],
        custom_phase_configs =  {},
        custom_chain_configs = {},
        custom_role_configs = {},
        no_remote_api: bool = None,
        history_node_list: List[str] = [],
        isDetailed: bool = False,
        upload_file: Union[str, Path, bytes] = "",
    ):
        '''
        对应api.py/chat/chat接口
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        data = {
            "query": query,
            "phase_name": phase_name,
            "chain_name": "",
            "history": history,
            "doc_engine_name": doc_engine_name,
            "code_engine_name": code_engine_name,
            "cb_search_type": cb_search_type,
            "search_engine_name": search_engine_name,
            "top_k": top_k,
            "score_threshold": score_threshold,
            "stream": stream,
            "local_doc_url": local_doc_url,
            "do_search": do_search,
            "do_doc_retrieval": do_doc_retrieval,
            "do_code_retrieval": do_code_retrieval,
            "do_tool_retrieval": do_tool_retrieval,
            "custom_phase_configs": custom_phase_configs,
            "custom_chain_configs": custom_chain_configs,
            "custom_role_configs": custom_role_configs,
            "choose_tools": choose_tools,
            "history_node_list": history_node_list,
            "isDetailed": isDetailed,
            "upload_file": upload_file
        }

        if no_remote_api:
            for response in self.agentChat.achat(**data):
                yield self._stream2generator(response, as_json=True)
        else:
            response = self.post("/chat/data_chat", json=data, stream=True)
            yield self._httpx_stream2generator(response)
        
    def _check_httpx_json_response(
            self,
            response: httpx.Response,
            errorMsg: str = f"无法连接API服务器，请确认已执行python server\\api.py",
        ) -> Dict:
        '''
        check whether httpx returns correct data with normal Response.
        error in api with streaming support was checked in _httpx_stream2enerator
        '''
        try:
            return response.json()
        except Exception as e:
            logger.error(e)
            return {"code": 500, "msg": errorMsg or str(e)}

    def _check_httpx_file_response(
            self,
            response: httpx.Response,
            errorMsg: str = f"无法连接API服务器，请确认已执行python server\\api.py",
        ) -> Dict:
        '''
        check whether httpx returns correct data with normal Response.
        error in api with streaming support was checked in _httpx_stream2enerator
        '''
        try:
            return response.content
        except Exception as e:
            logger.error(e)
            return {"code": 500, "msg": errorMsg or str(e)}
        
    def list_knowledge_bases(
        self,
        no_remote_api: bool = None,
    ):
        '''
        对应api.py/knowledge_base/list_knowledge_bases接口
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        if no_remote_api:
            response = run_async(list_kbs())
            return response.data
        else:
            response = self.get("/knowledge_base/list_knowledge_bases")
            data = self._check_httpx_json_response(response)
            return data.get("data", [])

    def create_knowledge_base(
        self,
        knowledge_base_name: str,
        vector_store_type: str = "faiss",
        embed_model: str = EMBEDDING_MODEL,
        no_remote_api: bool = None,
    ):
        '''
        对应api.py/knowledge_base/create_knowledge_base接口
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        data = {
            "knowledge_base_name": knowledge_base_name,
            "vector_store_type": vector_store_type,
            "embed_model": embed_model,
        }

        if no_remote_api:
            response = run_async(create_kb(**data))
            return response.dict()
        else:
            response = self.post(
                "/knowledge_base/create_knowledge_base",
                json=data,
            )
            return self._check_httpx_json_response(response)

    def delete_knowledge_base(
        self,
        knowledge_base_name: str,
        no_remote_api: bool = None,
    ):
        '''
        对应api.py/knowledge_base/delete_knowledge_base接口
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        if no_remote_api:
            response = run_async(delete_kb(knowledge_base_name))
            return response.dict()
        else:
            response = self.post(
                "/knowledge_base/delete_knowledge_base",
                json=f"{knowledge_base_name}",
            )
            return self._check_httpx_json_response(response)

    def list_kb_docs(
        self,
        knowledge_base_name: str,
        no_remote_api: bool = None,
    ):
        '''
        对应api.py/knowledge_base/list_docs接口
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        if no_remote_api:
            response = run_async(list_docs(knowledge_base_name))
            return response.data
        else:
            response = self.get(
                "/knowledge_base/list_docs",
                params={"knowledge_base_name": knowledge_base_name}
            )
            data = self._check_httpx_json_response(response)
            return data.get("data", [])

    def upload_kb_doc(
        self,
        file: Union[str, Path, bytes],
        knowledge_base_name: str,
        filename: str = None,
        override: bool = False,
        not_refresh_vs_cache: bool = False,
        no_remote_api: bool = None,
    ):
        '''
        对应api.py/knowledge_base/upload_docs接口
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        if isinstance(file, bytes): # raw bytes
            file = BytesIO(file)
        elif hasattr(file, "read"): # a file io like object
            filename = filename or file.name
        else: # a local path
            file = Path(file).absolute().open("rb")
            filename = filename or file.name

        if no_remote_api:
            from fastapi import UploadFile
            from tempfile import SpooledTemporaryFile

            temp_file = SpooledTemporaryFile(max_size=10 * 1024 * 1024)
            temp_file.write(file.read())
            temp_file.seek(0)
            response = run_async(upload_doc(
                UploadFile(file=temp_file, filename=filename),
                knowledge_base_name,
                override,
                not_refresh_vs_cache
            ))
            return response.dict()
        else:
            response = self.post(
                "/knowledge_base/upload_doc",
                data={
                    "knowledge_base_name": knowledge_base_name,
                    "override": override,
                    "not_refresh_vs_cache": not_refresh_vs_cache,
                },
                files={"file": (filename, file)},
            )
            return self._check_httpx_json_response(response)

    def delete_kb_doc(
        self,
        knowledge_base_name: str,
        doc_name: str,
        delete_content: bool = False,
        not_refresh_vs_cache: bool = False,
        no_remote_api: bool = None,
    ):
        '''
        对应api.py/knowledge_base/delete_doc接口
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        data = {
            "knowledge_base_name": knowledge_base_name,
            "doc_name": doc_name,
            "delete_content": delete_content,
            "not_refresh_vs_cache": not_refresh_vs_cache,
        }

        if no_remote_api:
            response = run_async(delete_doc(**data))
            return response.dict()
        else:
            response = self.post(
                "/knowledge_base/delete_doc",
                json=data,
            )
            return self._check_httpx_json_response(response)

    def update_kb_doc(
        self,
        knowledge_base_name: str,
        file_name: str,
        not_refresh_vs_cache: bool = False,
        no_remote_api: bool = None,
    ):
        '''
        对应api.py/knowledge_base/update_doc接口
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        if no_remote_api:
            response = run_async(update_doc(knowledge_base_name, file_name, not_refresh_vs_cache))
            return response.dict()
        else:
            response = self.post(
                "/knowledge_base/update_doc",
                json={
                    "knowledge_base_name": knowledge_base_name,
                    "file_name": file_name,
                    "not_refresh_vs_cache": not_refresh_vs_cache,
                },
            )
            return self._check_httpx_json_response(response)

    def recreate_vector_store(
        self,
        knowledge_base_name: str,
        allow_empty_kb: bool = True,
        vs_type: str = DEFAULT_VS_TYPE,
        embed_model: str = EMBEDDING_MODEL,
        no_remote_api: bool = None,
    ):
        '''
        对应api.py/knowledge_base/recreate_vector_store接口
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        data = {
            "knowledge_base_name": knowledge_base_name,
            "allow_empty_kb": allow_empty_kb,
            "vs_type": vs_type,
            "embed_model": embed_model,
        }

        if no_remote_api:
            response = run_async(recreate_vector_store(**data))
            return self._fastapi_stream2generator(response, as_json=True)
        else:
            response = self.post(
                "/knowledge_base/recreate_vector_store",
                json=data,
                stream=True,
                timeout=None,
            )
            return self._httpx_stream2generator(response, as_json=True)

    def web_crawl(
            self, 
            base_url: str,
            html_dir: str,
            text_dir: str,
            do_dfs: bool = False,
            reptile_lib: str = "requests",
            method: str = "get",
            time_sleep: float = 2,
            no_remote_api: bool = None
    ):
        '''
        根据url来检索
        '''
        async def _web_crawl(html_dir, text_dir, base_url, reptile_lib, method, time_sleep, do_dfs):
            wc = WebCrawler()
            try:
                if not do_dfs:
                    wc.webcrawler_single(html_dir=html_dir,
                                    text_dir=text_dir,
                                    base_url=base_url,
                                    reptile_lib=reptile_lib,
                                    method=method,
                                    time_sleep=time_sleep
                                    )
                else:
                    wc.webcrawler_1_degree(html_dir=html_dir,
                            text_dir=text_dir,
                            base_url=base_url,
                            reptile_lib=reptile_lib,
                            method=method,
                            time_sleep=time_sleep
                            )
                return {"status": 200, "response": "success"}
            except Exception as e:
                return {"status": 500, "response": str(e)}
                
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        data = {
            "base_url": base_url,
            "html_dir": html_dir,
            "text_dir": text_dir,
            "do_dfs": do_dfs,
            "reptile_lib": reptile_lib,
            "method": method,
            "time_sleep": time_sleep,
        }
        if no_remote_api:
            response = run_async(_web_crawl(**data))
            return response
        else:
            raise Exception("not impletenion")
    
    def web_sd_upload(self, file: str = None, filename: str = None):
        '''对应file_service/sd_upload_file'''
        file, filename = file_normalize(file, filename)
        response = self.post(
            "/sdfiles/upload",
            files={"file": (filename, file)},
        )
        return self._check_httpx_json_response(response)

    def web_sd_download(self, filename: str, save_filename: str = None):
        '''对应file_service/sd_download_file'''
        save_filename = save_filename or filename
        response = self.get(
            f"/sdfiles/download",
            params={"filename": filename, "save_filename": save_filename}
        )
        # logger.debug(f"response: {response.json()}")
        if filename:
            file_content, _ = file_normalize(response.json()["data"])
            return file_content, save_filename
        return "", save_filename

    def web_sd_delete(self, filename: str):
        '''对应file_service/sd_delete_file'''
        response = self.get(
            f"/sdfiles/delete",
            params={"filename": filename}
        )
        return self._check_httpx_json_response(response)
    
    def web_sd_list_files(self, ):
        '''对应对应file_service/sd_list_files接口'''
        response = self.get("/sdfiles/list",)
        return self._check_httpx_json_response(response)

    # code base 相关操作
    def create_code_base(self, cb_name, zip_file, do_interpret: bool, no_remote_api: bool = None,):
        '''
        创建 code_base
        @param cb_name:
        @param zip_path:
        @return:
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        # mkdir
        cb_root_path = CB_ROOT_PATH
        mkdir_dir = [
            cb_root_path,
            cb_root_path + os.sep + cb_name,
            raw_code_path := cb_root_path + os.sep + cb_name + os.sep + 'raw_code'
        ]
        for dir in mkdir_dir:
            if not os.path.exists(dir):
                os.makedirs(dir)

        data = {
            "zip_file": zip_file,
            "cb_name": cb_name,
            "code_path": raw_code_path,
            "do_interpret": do_interpret
        }
        logger.info('create cb data={}'.format(data))

        if no_remote_api:
            response = run_async(create_cb(**data))
            return response.dict()
        else:
            response = self.post(
                "/code_base/create_code_base",
                json=data,
            )
            logger.info('response={}'.format(response.json()))
            return self._check_httpx_json_response(response)

    def delete_code_base(self, cb_name: str, no_remote_api: bool = None,):
        '''
        删除 code_base
        @param cb_name:
        @return:
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        data = {
            "cb_name": cb_name
        }

        if no_remote_api:
            response = run_async(delete_cb(**data))
            return response.dict()
        else:
            response = self.post(
                "/code_base/delete_code_base",
                json=cb_name
            )
            logger.info(response.json())
            return self._check_httpx_json_response(response)

    def list_cb(self, no_remote_api: bool = None):
        '''
        列举 code_base
        @return:
        '''
        if no_remote_api is None:
            no_remote_api = self.no_remote_api

        if no_remote_api:
            response = run_async(list_cbs())
            return response.data
        else:
            response = self.get("/code_base/list_code_bases")
            data = self._check_httpx_json_response(response)
            return data.get("data", [])



def check_error_msg(data: Union[str, dict, list], key: str = "errorMsg") -> str:
    '''
    return error message if error occured when requests API
    '''
    if isinstance(data, dict):
        if key in data:
            return data[key]
        if "code" in data and data["code"] != 200:
            return data["msg"]
    return ""


def check_success_msg(data: Union[str, dict, list], key: str = "msg") -> str:
    '''
    return error message if error occured when requests API
    '''
    if (isinstance(data, dict)
        and key in data
        and "code" in data
        and data["code"] == 200):
        return data[key]
    return ""


if __name__ == "__main__":
    api = ApiRequest(no_remote_api=True)

    # print(api.chat_fastchat(
    #     messages=[{"role": "user", "content": "hello"}]
    # ))

    # with api.chat_chat("你好") as r:
    #     for t in r.iter_text(None):
    #         print(t)

    # r = api.chat_chat("你好", no_remote_api=True)
    # for t in r:
    #     print(t)

    # r = api.duckduckgo_search_chat("室温超导最新研究进展", no_remote_api=True)
    # for t in r:
    #     print(t)

    # print(api.list_knowledge_bases())
