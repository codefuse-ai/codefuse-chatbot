# encoding: utf-8
'''
@author: 温进
@file: codechat_tools.py.py
@time: 2023/12/14 上午10:24
@desc:
'''
import os
from pydantic import BaseModel, Field
from loguru import logger

from coagent.llm_models.llm_config import EmbedConfig, LLMConfig
from .base_tool import BaseToolModel

from coagent.service.cb_api import search_code, search_related_vertices, search_code_by_vertex


# 问题进来
# 调用函数 0：输入问题，输出代码文件名 1 和 代码文件 1
#
# agent 1
# 1. LLM：代码+问题 输出：是否能解决
#
# agent 2
# 1. 调用函数 1 ：输入：代码文件名 1 输出：代码文件名列表
# 2. LLM：输入代码文件 1， 问题，代码文件名列表，输出：代码文件名 2
# 3. 调用函数 2： 输入 ：代码文件名 2 输出：代码文件 2


class CodeRetrievalSingle(BaseToolModel):
    name = "CodeRetrievalOneCode"
    description = "输入用户的问题，输出一个代码文件名和代码文件"

    class ToolInputArgs(BaseModel):
        query: str = Field(..., description="检索的问题")
        code_base_name: str = Field(..., description="代码库名称", examples=["samples"])

    class ToolOutputArgs(BaseModel):
        """Output for MetricsQuery."""
        code: str = Field(..., description="检索代码")
        vertex: str = Field(..., description="代码对应 id")

    @classmethod
    def run(cls, code_base_name, query, embed_config: EmbedConfig, llm_config: LLMConfig, search_type="description", **kargs):
        """excute your tool!"""

        code_limit = 1

        # default
        search_result = search_code(code_base_name, query, code_limit, search_type=search_type,
                            history_node_list=[],
                            embed_engine=embed_config.embed_engine, embed_model=embed_config.embed_model, embed_model_path=embed_config.embed_model_path,
                            model_device=embed_config.model_device, model_name=llm_config.model_name, temperature=llm_config.temperature,
                            api_base_url=llm_config.api_base_url, api_key=llm_config.api_key, embed_config=embed_config, use_nh=kargs.get("use_nh", True),
                            local_graph_path=kargs.get("local_graph_path", "")
                            )
        if os.environ.get("log_verbose", "0") >= "3":
            logger.debug(search_result)
        code = search_result['context']
        vertex = search_result['related_vertices'][0]
        # logger.debug(f"code: {code}, vertex: {vertex}")

        res = {
            'code': code,
            'vertex': vertex
        }

        return res


class RelatedVerticesRetrival(BaseToolModel):
    name = "RelatedVerticesRetrival"
    description = "输入代码节点名，返回相连的节点名"

    class ToolInputArgs(BaseModel):
        code_base_name: str = Field(..., description="代码库名称", examples=["samples"])
        vertex: str = Field(..., description="节点名", examples=["samples"])

    class ToolOutputArgs(BaseModel):
        """Output for MetricsQuery."""
        vertices: list = Field(..., description="相连节点名")

    @classmethod
    def run(cls, code_base_name: str, vertex: str, **kargs):
        """execute your tool!"""
        related_vertices = search_related_vertices(cb_name=code_base_name, vertex=vertex)
        # logger.debug(f"related_vertices: {related_vertices}")

        return related_vertices


class Vertex2Code(BaseToolModel):
    name = "Vertex2Code"
    description = "输入代码节点名,返回对应的代码文件"

    class ToolInputArgs(BaseModel):
        code_base_name: str = Field(..., description="代码库名称", examples=["samples"])
        vertex: str = Field(..., description="节点名", examples=["samples"])

    class ToolOutputArgs(BaseModel):
        """Output for MetricsQuery."""
        code: str = Field(..., description="代码名")

    @classmethod
    def run(cls, code_base_name: str, vertex: str, **kargs):
        """execute your tool!"""
        # format vertex
        if ',' in vertex:
            vertex_list = vertex.split(',')
            vertex = vertex_list[0].strip(' "')
        else:
            vertex = vertex.strip(' "')

        # logger.info(f'vertex={vertex}')
        res = search_code_by_vertex(cb_name=code_base_name, vertex=vertex)
        return res