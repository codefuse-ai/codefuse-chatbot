import os, asyncio
from typing import List, Optional, Dict

from langchain import LLMChain
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.utilities import BingSearchAPIWrapper, DuckDuckGoSearchAPIWrapper
from langchain.prompts.chat import ChatPromptTemplate
from langchain.docstore.document import Document

# from configs.model_config import (
#     PROMPT_TEMPLATE, SEARCH_ENGINE_TOP_K, BING_SUBSCRIPTION_KEY, BING_SEARCH_URL,
#     VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD)
from coagent.connector.configs.prompts import ORIGIN_TEMPLATE_PROMPT
from coagent.chat.utils import History, wrap_done
from coagent.utils import BaseResponse
from coagent.llm_models.llm_config import LLMConfig, EmbedConfig
from .base_chat import Chat

from loguru import logger

from duckduckgo_search import DDGS


# def bing_search(text, result_len=5):
#     if not (BING_SEARCH_URL and BING_SUBSCRIPTION_KEY):
#         return [{"snippet": "please set BING_SUBSCRIPTION_KEY and BING_SEARCH_URL in os ENV",
#                  "title": "env info is not found",
#                  "link": "https://python.langchain.com/en/latest/modules/agents/tools/examples/bing_search.html"}]
#     search = BingSearchAPIWrapper(bing_subscription_key=BING_SUBSCRIPTION_KEY,
#                                   bing_search_url=BING_SEARCH_URL)
#     return search.results(text, result_len)


def duckduckgo_search(
        query: str,
        result_len: int = 5,
        region: Optional[str] = "wt-wt", 
        safesearch: str = "moderate", 
        time: Optional[str] = "y",
        backend: str = "api",
        ):
    with DDGS(proxies=os.environ.get("DUCKDUCKGO_PROXY")) as ddgs:
        results = ddgs.text(
            query,
            region=region,
            safesearch=safesearch,
            timelimit=time,
            backend=backend,
        )
        if results is None:
            return [{"Result": "No good DuckDuckGo Search Result was found"}]

        def to_metadata(result: Dict) -> Dict[str, str]:
            if backend == "news":
                return {
                    "date": result["date"],
                    "title": result["title"],
                    "snippet": result["body"],
                    "source": result["source"],
                    "link": result["url"],
                }
            return {
                "snippet": result["body"],
                "title": result["title"],
                "link": result["href"],
            }

        formatted_results = []
        for i, res in enumerate(results, 1):
            if res is not None:
                formatted_results.append(to_metadata(res))
            if len(formatted_results) == result_len:
                break
    return formatted_results


# def duckduckgo_search(text, result_len=SEARCH_ENGINE_TOP_K):
#     search = DuckDuckGoSearchAPIWrapper()
#     return search.results(text, result_len)


SEARCH_ENGINES = {"duckduckgo": duckduckgo_search,
                #   "bing": bing_search,
                  }


def search_result2docs(search_results):
    docs = []
    for result in search_results:
        doc = Document(page_content=result["snippet"] if "snippet" in result.keys() else "",
                       metadata={"source": result["link"] if "link" in result.keys() else "",
                                 "filename": result["title"] if "title" in result.keys() else ""})
        docs.append(doc)
    return docs


def lookup_search_engine(
        query: str,
        search_engine_name: str,
        top_k: int = 5,
):
    results = SEARCH_ENGINES[search_engine_name](query, result_len=top_k)
    docs = search_result2docs(results)
    return docs



class SearchChat(Chat):

    def __init__(
            self,
            engine_name: str = "",
            top_k: int = 5,
            stream: bool = False,
            ) -> None:
        super().__init__(engine_name, top_k, stream)

    def check_service_status(self) -> BaseResponse:
        if self.engine_name not in SEARCH_ENGINES.keys():
            return BaseResponse(code=404, msg=f"未支持搜索引擎 {self.engine_name}")
        return BaseResponse(code=200, msg=f"支持搜索引擎 {self.engine_name}")
    
    def _process(self, query: str, history: List[History], model):
        '''process'''
        docs = lookup_search_engine(query, self.engine_name, self.top_k)
        context = "\n".join([doc.page_content for doc in docs])

        source_documents = [
            f"""出处 [{inum + 1}] [{doc.metadata["source"]}]({doc.metadata["source"]}) \n\n{doc.page_content}\n\n"""
            for inum, doc in enumerate(docs)
        ]
        
        chat_prompt = ChatPromptTemplate.from_messages(
            [i.to_msg_tuple() for i in history] + [("human", ORIGIN_TEMPLATE_PROMPT)]
        )
        chain = LLMChain(prompt=chat_prompt, llm=model)
        result = {"answer": "", "docs": source_documents}
        return chain, context, result

    def create_task(self, query: str, history: List[History], model, llm_config: LLMConfig, embed_config: EmbedConfig, ):
        '''构建 llm 生成任务'''
        chain, context, result = self._process(query, history, model)
        content = chain({"context": context, "question": query})
        return result, content

    def create_atask(self, query, history, model, llm_config: LLMConfig, embed_config: EmbedConfig, callback: AsyncIteratorCallbackHandler):
        chain, context, result = self._process(query, history, model)
        task = asyncio.create_task(wrap_done(
            chain.acall({"context": context, "question": query}), callback.done
        ))
        return task, result
