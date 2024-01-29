import sys, os, json, traceback, uvicorn, argparse

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(src_dir)

from loguru import logger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import File, UploadFile

from coagent.utils.server_utils import BaseResponse, ListResponse, DataResponse
from configs.server_config import OPEN_CROSS_DOMAIN, SDFILE_API_SERVER
from configs.model_config import JUPYTER_WORK_PATH


VERSION = "v0.1.0"

async def sd_upload_file(file: UploadFile = File(...), work_dir: str = JUPYTER_WORK_PATH):
    # 保存上传的文件到服务器
    try:
        content = await file.read()
        with open(os.path.join(work_dir, file.filename), "wb") as f:
            f.write(content)
        return {"data": True}
    except:
        return {"data": False}


async def sd_download_file(filename: str, save_filename: str = "filename_to_download.ext", work_dir: str = JUPYTER_WORK_PATH):
    # 从服务器下载文件
    logger.debug(f"{os.path.join(work_dir, filename)}")
    return {"data": os.path.join(work_dir, filename), "filename": save_filename}
    # return {"data": FileResponse(os.path.join(work_dir, filename), filename=save_filename)}


async def sd_list_files(work_dir: str = JUPYTER_WORK_PATH):
    # 去除目录
    return {"data": os.listdir(work_dir)}


async def sd_delete_file(filename: str, work_dir: str = JUPYTER_WORK_PATH):
    # 去除目录
    try:
        os.remove(os.path.join(work_dir, filename))
        return {"data": True}
    except:
        return {"data": False}


def create_app(open_cross_domain, version=VERSION):
    app = FastAPI(
        title="DevOps-ChatBot API Server",
        version=version
    )
    # MakeFastAPIOffline(app)
    # Add CORS middleware to allow all origins
    # 在config.py中设置OPEN_DOMAIN=True，允许跨域
    # set OPEN_DOMAIN=True in config.py to allow cross-domain
    if open_cross_domain:
    # if OPEN_CROSS_DOMAIN:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.post("/sdfiles/upload",
            tags=["files upload and download"],
            response_model=BaseResponse,
            summary="上传文件到沙盒"
            )(sd_upload_file)
    
    app.get("/sdfiles/download",
            tags=["files upload and download"],
            response_model=DataResponse,
            summary="从沙盒下载文件"
            )(sd_download_file)

    app.get("/sdfiles/list",
            tags=["files upload and download"],
            response_model=ListResponse,
            summary="从沙盒工作目录展示文件"
            )(sd_list_files)
    
    app.get("/sdfiles/delete",
            tags=["files upload and download"],
            response_model=BaseResponse,
            summary="从沙盒工作目录中删除文件"
            )(sd_delete_file)
    return app



def run_api(host, port, open_cross_domain, **kwargs):
    app = create_app(open_cross_domain)
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
    parser.add_argument("--port", type=int, default="7862")
    # parser.add_argument("--port", type=int, default=SDFILE_API_SERVER["port"])
    parser.add_argument("--open_cross_domain", type=bool, default=False)
    parser.add_argument("--ssl_keyfile", type=str)
    parser.add_argument("--ssl_certfile", type=str)
    # 初始化消息
    args = parser.parse_args()
    args_dict = vars(args)
    run_api(host=args.host,
            port=args.port,
            open_cross_domain=args.open_cross_domain,
            ssl_keyfile=args.ssl_keyfile,
            ssl_certfile=args.ssl_certfile,
            )