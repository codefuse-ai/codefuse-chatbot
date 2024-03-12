from pydantic import BaseModel, Field
from loguru import logger

from coagent.llm_models.llm_config import EmbedConfig
from .base_tool import BaseToolModel
from coagent.service.kb_api import search_docs


class DocRetrieval(BaseToolModel):
    name = "DocRetrieval"
    description = "采用向量化对本地知识库进行检索"

    class ToolInputArgs(BaseModel):
        query: str = Field(..., description="检索的关键字或问题")
        knowledge_base_name: str = Field(..., description="知识库名称", examples=["samples"])
        search_top: int = Field(5, description="检索返回的数量")
        score_threshold: float = Field(1.0, description="知识库匹配相关度阈值，取值范围在0-1之间，SCORE越小，相关度越高，取到1相当于不筛选，建议设置在0.5左右", ge=0, le=1)

    class ToolOutputArgs(BaseModel):
        """Output for MetricsQuery."""
        title: str  = Field(..., description="检索网页标题")
        snippet: str  = Field(..., description="检索内容的判断")
        link: str  = Field(..., description="检索网页地址")

    @classmethod
    def run(cls, query, knowledge_base_name, search_top=5, score_threshold=1.0, embed_config: EmbedConfig=EmbedConfig(), kb_root_path: str=""):
        """excute your tool!"""
        try:
            docs = search_docs(query, knowledge_base_name, search_top, score_threshold,
                               kb_root_path=kb_root_path, embed_engine=embed_config.embed_engine,
                               embed_model=embed_config.embed_model, embed_model_path=embed_config.embed_model_path,
                               model_device=embed_config.model_device
                               )
        except Exception as e:
            logger.exception(e)
        return_docs = []
        for idx, doc in enumerate(docs):
            return_docs.append({"index": idx, "snippet": doc.page_content, "title": doc.metadata.get("source"), "link": doc.metadata.get("source")})
        return return_docs
