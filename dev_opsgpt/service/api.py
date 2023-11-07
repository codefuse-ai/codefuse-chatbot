import nltk
import argparse
import uvicorn, os, sys
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from typing import List

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(src_dir)

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from configs import VERSION
from configs.model_config import NLTK_DATA_PATH
from configs.server_config import OPEN_CROSS_DOMAIN

from dev_opsgpt.chat import LLMChat, SearchChat, KnowledgeChat
from dev_opsgpt.service.kb_api import *
from dev_opsgpt.service.cb_api import *
from dev_opsgpt.utils.server_utils import BaseResponse, ListResponse, FastAPI, MakeFastAPIOffline

nltk.data.path = [NLTK_DATA_PATH] + nltk.data.path

from dev_opsgpt.chat import LLMChat, SearchChat, KnowledgeChat, ToolChat, DataChat, CodeChat

llmChat = LLMChat()
searchChat = SearchChat()
knowledgeChat = KnowledgeChat()
toolChat = ToolChat()
dataChat = DataChat()
codeChat = CodeChat()


async def document():
    return RedirectResponse(url="/docs")


def create_app():
    app = FastAPI(
        title="DevOps-ChatBot API Server",
        version=VERSION
    )
    MakeFastAPIOffline(app)
    # Add CORS middleware to allow all origins
    # 在config.py中设置OPEN_DOMAIN=True，允许跨域
    # set OPEN_DOMAIN=True in config.py to allow cross-domain
    if OPEN_CROSS_DOMAIN:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.get("/",
            response_model=BaseResponse,
            summary="swagger 文档")(document)

    # Tag: Chat
    # app.post("/chat/fastchat",
    #          tags=["Chat"],
    #          summary="与llm模型对话(直接与fastchat api对话)")(openai_chat)

    app.post("/chat/chat",
             tags=["Chat"],
             summary="与llm模型对话(通过LLMChain)")(llmChat.chat)

    app.post("/chat/knowledge_base_chat",
             tags=["Chat"],
             summary="与知识库对话")(knowledgeChat.chat)

    app.post("/chat/search_engine_chat",
             tags=["Chat"],
             summary="与搜索引擎对话")(searchChat.chat)
    app.post("/chat/tool_chat",
             tags=["Chat"],
             summary="与搜索引擎对话")(toolChat.chat)
    
    app.post("/chat/data_chat",
             tags=["Chat"],
             summary="与搜索引擎对话")(dataChat.chat)

    app.post("/chat/code_chat",
             tags=["Chat"],
             summary="与代码库对话")(codeChat.chat)


    # Tag: Knowledge Base Management
    app.get("/knowledge_base/list_knowledge_bases",
            tags=["Knowledge Base Management"],
            response_model=ListResponse,
            summary="获取知识库列表")(list_kbs)

    app.post("/knowledge_base/create_knowledge_base",
             tags=["Knowledge Base Management"],
             response_model=BaseResponse,
             summary="创建知识库"
             )(create_kb)

    app.post("/knowledge_base/delete_knowledge_base",
             tags=["Knowledge Base Management"],
             response_model=BaseResponse,
             summary="删除知识库"
             )(delete_kb)

    app.get("/knowledge_base/list_files",
            tags=["Knowledge Base Management"],
            response_model=ListResponse,
            summary="获取知识库内的文件列表"
            )(list_docs)

    app.post("/knowledge_base/search_docs",
             tags=["Knowledge Base Management"],
             response_model=List[DocumentWithScore],
             summary="搜索知识库"
             )(search_docs)

    app.post("/knowledge_base/upload_docs",
             tags=["Knowledge Base Management"],
             response_model=BaseResponse,
             summary="上传文件到知识库，并/或进行向量化"
             )(upload_doc)

    app.post("/knowledge_base/delete_docs",
             tags=["Knowledge Base Management"],
             response_model=BaseResponse,
             summary="删除知识库内指定文件"
             )(delete_doc)

    app.post("/knowledge_base/update_docs",
             tags=["Knowledge Base Management"],
             response_model=BaseResponse,
             summary="更新现有文件到知识库"
             )(update_doc)

    app.get("/knowledge_base/download_doc",
            tags=["Knowledge Base Management"],
            summary="下载对应的知识文件")(download_doc)

    app.post("/knowledge_base/recreate_vector_store",
             tags=["Knowledge Base Management"],
             summary="根据content中文档重建向量库，流式输出处理进度。"
             )(recreate_vector_store)

    app.post("/code_base/create_code_base",
             tags=["Code Base Management"],
             summary="新建 code_base"
             )(create_cb)

    app.post("/code_base/delete_code_base",
             tags=["Code Base Management"],
             summary="删除 code_base"
             )(delete_cb)

    app.post("/code_base/code_base_chat",
             tags=["Code Base Management"],
             summary="删除 code_base"
             )(delete_cb)

    app.get("/code_base/list_code_bases",
            tags=["Code Base Management"],
            summary="列举 code_base",
            response_model=ListResponse
            )(list_cbs)

    # # LLM模型相关接口
    # app.post("/llm_model/list_models",
    #         tags=["LLM Model Management"],
    #         summary="列出当前已加载的模型",
    #         )(list_llm_models)

    # app.post("/llm_model/stop",
    #         tags=["LLM Model Management"],
    #         summary="停止指定的LLM模型（Model Worker)",
    #         )(stop_llm_model)

    # app.post("/llm_model/change",
    #         tags=["LLM Model Management"],
    #         summary="切换指定的LLM模型（Model Worker)",
    #         )(change_llm_model)

    return app


app = create_app()


def run_api(host, port, **kwargs):
    if kwargs.get("ssl_keyfile") and kwargs.get("ssl_certfile"):
        uvicorn.run(app,
                    host=host,
                    port=port,
                    ssl_keyfile=kwargs.get("ssl_keyfile"),
                    ssl_certfile=kwargs.get("ssl_certfile"),
                    )
    else:
        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='DevOps-ChatBot',
                                     description='About DevOps-ChatBot, local knowledge based LLM with langchain'
                                                 ' ｜ 基于本地知识库的 LLM 问答')
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7861)
    parser.add_argument("--ssl_keyfile", type=str)
    parser.add_argument("--ssl_certfile", type=str)
    # 初始化消息
    args = parser.parse_args()
    args_dict = vars(args)
    run_api(host=args.host,
            port=args.port,
            ssl_keyfile=args.ssl_keyfile,
            ssl_certfile=args.ssl_certfile,
            )
