# encoding: utf-8
'''
@author: 温进
@file: cb_query_tool.py
@time: 2023/11/2 下午4:41
@desc:
'''
import json
import os
import re
from pydantic import BaseModel, Field
from typing import List, Dict
import requests
import numpy as np
from loguru import logger

from configs.model_config import (
    CODE_SEARCH_TOP_K)
from .base_tool import BaseToolModel

from dev_opsgpt.service.cb_api import search_code


class CodeRetrieval(BaseToolModel):
    name = "CodeRetrieval"
    description = "采用知识图谱从本地代码知识库获取相关代码"

    class ToolInputArgs(BaseModel):
        query: str = Field(..., description="检索的关键字或问题")
        code_base_name: str = Field(..., description="知识库名称", examples=["samples"])
        code_limit: int = Field(CODE_SEARCH_TOP_K, description="检索返回的数量")

    class ToolOutputArgs(BaseModel):
        """Output for MetricsQuery."""
        code: str  = Field(..., description="检索代码")

    @classmethod
    def run(cls, code_base_name, query, code_limit=CODE_SEARCH_TOP_K, history_node_list=[], search_type="tag"):
        """excute your tool!"""
        
        search_type = {
            '基于 cypher': 'cypher',
            '基于标签': 'tag',
            '基于描述': 'description',
            'tag': 'tag',
            'description': 'description',
            'cypher': 'cypher'
        }.get(search_type, 'tag')

        # default
        codes = search_code(code_base_name, query, code_limit, search_type=search_type, history_node_list=history_node_list)
        return_codes = []
        context = codes['context']
        related_nodes = codes['related_vertices']
        logger.debug(f"{code_base_name}, {query}, {code_limit}, {search_type}")
        logger.debug(f"context: {context}, related_nodes: {related_nodes}")

        return_codes.append({'index': 0, 'code': context, "related_nodes": related_nodes})

        return return_codes


