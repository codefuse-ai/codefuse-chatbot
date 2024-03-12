# encoding: utf-8
'''
@author: 温进
@file: cb_query_tool.py
@time: 2023/11/2 下午4:41
@desc:
'''
from pydantic import BaseModel, Field
from loguru import logger

from coagent.llm_models import LLMConfig, EmbedConfig
from .base_tool import BaseToolModel
from coagent.service.cb_api import search_code


class CodeRetrieval(BaseToolModel):
    name = "CodeRetrieval"
    description = "采用知识图谱从本地代码知识库获取相关代码"

    class ToolInputArgs(BaseModel):
        query: str = Field(..., description="检索的关键字或问题")
        code_base_name: str = Field(..., description="知识库名称", examples=["samples"])
        code_limit: int = Field(1, description="检索返回的数量")

    class ToolOutputArgs(BaseModel):
        """Output for MetricsQuery."""
        code: str  = Field(..., description="检索代码")

    @classmethod
    def run(cls,
            code_base_name,
            query,
            code_limit=1,
            history_node_list=[],
            search_type="tag",
            llm_config: LLMConfig=None,
            embed_config: EmbedConfig=None,
            use_nh: str=True,
            local_graph_path: str=''
            ):
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
        codes = search_code(code_base_name, query, code_limit, search_type=search_type, history_node_list=history_node_list,
                            embed_engine=embed_config.embed_engine, embed_model=embed_config.embed_model, embed_model_path=embed_config.embed_model_path,
                            model_device=embed_config.model_device, model_name=llm_config.model_name, temperature=llm_config.temperature,
                            api_base_url=llm_config.api_base_url, api_key=llm_config.api_key, use_nh=use_nh,
                            local_graph_path=local_graph_path, embed_config=embed_config
                            )
        return_codes = []
        context = codes['context']
        related_nodes = codes['related_vertices']
        logger.debug(f"{code_base_name}, {query}, {code_limit}, {search_type}")
        logger.debug(f"context: {context}, related_nodes: {related_nodes}")

        return_codes.append({'index': 0, 'code': context, "related_nodes": related_nodes})

        return return_codes


