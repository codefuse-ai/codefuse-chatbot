
import json
import os
import re
from pydantic import BaseModel, Field
from typing import List, Dict
import requests
import numpy as np
from loguru import logger

from .base_tool import BaseToolModel
from configs.model_config import (
    PROMPT_TEMPLATE, SEARCH_ENGINE_TOP_K, BING_SUBSCRIPTION_KEY, BING_SEARCH_URL,
    VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD)

from duckduckgo_search import DDGS


class DDGSTool(BaseToolModel):
    name = "DDGSTool"
    description = "通过duckduckgo进行资料搜索"

    class ToolInputArgs(BaseModel):
        query: str = Field(..., description="检索的关键字或问题")
        search_top: int = Field(..., description="检索返回的数量")
        region: str = Field("wt-wt", enum=["wt-wt", "us-en", "uk-en", "ru-ru"], description="搜索的区域")
        safesearch: str = Field("moderate", enum=["on", "moderate", "off"], description="")
        timelimit: str = Field(None, enum=[None, "d", "w", "m", "y"], description="查询时间方式")
        backend: str = Field("api", description="搜索的资料来源")

    class ToolOutputArgs(BaseModel):
        """Output for MetricsQuery."""
        title: str  = Field(..., description="检索网页标题")
        snippet: str  = Field(..., description="检索内容的判断")
        link: str  = Field(..., description="检索网页地址")

    @classmethod
    def run(cls, query, search_top, region="wt-wt", safesearch="moderate", timelimit=None, backend="api"):
        """excute your tool!"""
        with DDGS(proxies=os.environ.get("DUCKDUCKGO_PROXY")) as ddgs:
            results = ddgs.text(
                query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
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
                if len(formatted_results) == search_top:
                    break
        return formatted_results
