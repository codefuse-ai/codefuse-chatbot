############################# Attention ########################

# Code copied from
# https://github.com/chatchat-space/Langchain-Chatchat/blob/master/server/llm_api.py

#################################################################



from multiprocessing import Process, Queue
import multiprocessing as mp
import sys
import os
from typing import List, Union, Dict
import httpx
import asyncio
import datetime
import argparse

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(src_dir)

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from configs.model_config import llm_model_dict, LLM_MODEL, LLM_DEVICE, LOG_PATH, logger, LLM_MODELs
from configs.server_config import (
    FSCHAT_CONTROLLER, FSCHAT_MODEL_WORKERS, FSCHAT_OPENAI_API
)
from examples.utils import get_model_worker_config

from muagent.utils.server_utils import (
    MakeFastAPIOffline, 
)
from fastapi import FastAPI

host_ip = "0.0.0.0"
controller_port = 20001
model_worker_port = 20002
openai_api_port = 8888
base_url = "http://127.0.0.1:{}"


os.environ['PATH'] = os.environ.get("PATH", "") + os.pathsep
log_verbose = True


def set_httpx_timeout(timeout=60.0):
    import httpx
    httpx._config.DEFAULT_TIMEOUT_CONFIG.connect = timeout
    httpx._config.DEFAULT_TIMEOUT_CONFIG.read = timeout
    httpx._config.DEFAULT_TIMEOUT_CONFIG.write = timeout


def get_all_model_worker_configs() -> dict:
    result = {}
    model_names = set(FSCHAT_MODEL_WORKERS.keys())
    for name in model_names:
        if name != "default":
            result[name] = get_model_worker_config(name)
    return result


def fschat_controller_address() -> str:
    from configs.server_config import FSCHAT_CONTROLLER

    host = FSCHAT_CONTROLLER["host"]
    if host == "0.0.0.0":
        host = "127.0.0.1"
    port = FSCHAT_CONTROLLER["port"]
    return f"http://{host}:{port}"


def fschat_model_worker_address(model_name: str = LLM_MODEL) -> str:
    if model := get_model_worker_config(model_name):  # TODO: depends fastchat
        host = model["host"]
        if host == "0.0.0.0":
            host = "127.0.0.1"
        port = model["port"]
        return f"http://{host}:{port}"
    return ""


def fschat_openai_api_address() -> str:
    from configs.server_config import FSCHAT_OPENAI_API

    host = FSCHAT_OPENAI_API["host"]
    if host == "0.0.0.0":
        host = "127.0.0.1"
    port = FSCHAT_OPENAI_API["port"]
    return f"http://{host}:{port}/v1"


def set_httpx_config(
        timeout: float = 300,
        proxy: Union[str, Dict] = None,
):
    '''
    设置httpx默认timeout。httpx默认timeout是5秒，在请求LLM回答时不够用。
    将本项目相关服务加入无代理列表，避免fastchat的服务器请求错误。(windows下无效)
    对于chatgpt等在线API，如要使用代理需要手动配置。搜索引擎的代理如何处置还需考虑。
    '''

    import httpx
    import os

    httpx._config.DEFAULT_TIMEOUT_CONFIG.connect = timeout
    httpx._config.DEFAULT_TIMEOUT_CONFIG.read = timeout
    httpx._config.DEFAULT_TIMEOUT_CONFIG.write = timeout

    # 在进程范围内设置系统级代理
    proxies = {}
    if isinstance(proxy, str):
        for n in ["http", "https", "all"]:
            proxies[n + "_proxy"] = proxy
    elif isinstance(proxy, dict):
        for n in ["http", "https", "all"]:
            if p := proxy.get(n):
                proxies[n + "_proxy"] = p
            elif p := proxy.get(n + "_proxy"):
                proxies[n + "_proxy"] = p

    for k, v in proxies.items():
        os.environ[k] = v

    # set host to bypass proxy
    no_proxy = [x.strip() for x in os.environ.get("no_proxy", "").split(",") if x.strip()]
    no_proxy += [
        # do not use proxy for locahost
        "http://127.0.0.1",
        "http://localhost",
    ]
    # do not use proxy for user deployed fastchat servers
    for x in [
        fschat_controller_address(),
        fschat_model_worker_address(),
        fschat_openai_api_address(),
    ]:
        host = ":".join(x.split(":")[:2])
        if host not in no_proxy:
            no_proxy.append(host)
    os.environ["NO_PROXY"] = ",".join(no_proxy)

    # TODO: 简单的清除系统代理不是个好的选择，影响太多。似乎修改代理服务器的bypass列表更好。
    # patch requests to use custom proxies instead of system settings
    def _get_proxies():
        return proxies

    import urllib.request
    urllib.request.getproxies = _get_proxies

    # 自动检查torch可用的设备。分布式部署时，不运行LLM的机器上可以不装torch


def get_httpx_client(
        use_async: bool = False,
        proxies: Union[str, Dict] = None,
        timeout: float = 300,
        **kwargs,
) -> Union[httpx.Client, httpx.AsyncClient]:
    '''
    helper to get httpx client with default proxies that bypass local addesses.
    '''
    default_proxies = {
        # do not use proxy for locahost
        "all://127.0.0.1": None,
        "all://localhost": None,
    }
    # do not use proxy for user deployed fastchat servers
    for x in [
        fschat_controller_address(),
        fschat_model_worker_address(),
        fschat_openai_api_address(),
    ]:
        host = ":".join(x.split(":")[:2])
        default_proxies.update({host: None})

    # get proxies from system envionrent
    # proxy not str empty string, None, False, 0, [] or {}
    default_proxies.update({
        "http://": (os.environ.get("http_proxy")
                    if os.environ.get("http_proxy") and len(os.environ.get("http_proxy").strip())
                    else None),
        "https://": (os.environ.get("https_proxy")
                     if os.environ.get("https_proxy") and len(os.environ.get("https_proxy").strip())
                     else None),
        "all://": (os.environ.get("all_proxy")
                   if os.environ.get("all_proxy") and len(os.environ.get("all_proxy").strip())
                   else None),
    })
    for host in os.environ.get("no_proxy", "").split(","):
        if host := host.strip():
            # default_proxies.update({host: None}) # Origin code
            default_proxies.update({'all://' + host: None})  # PR 1838 fix, if not add 'all://', httpx will raise error

    # merge default proxies with user provided proxies
    if isinstance(proxies, str):
        proxies = {"all://": proxies}

    if isinstance(proxies, dict):
        default_proxies.update(proxies)

    # construct Client
    kwargs.update(timeout=timeout, proxies=default_proxies)

    if log_verbose:
        logger.info(f'{get_httpx_client.__class__.__name__}:kwargs: {kwargs}')

    if use_async:
        return httpx.AsyncClient(**kwargs)
    else:
        return httpx.Client(**kwargs)


def create_controller_app(
        dispatch_method: str,
        log_level: str = "INFO",
) -> FastAPI:
    import fastchat.constants
    fastchat.constants.LOGDIR = LOG_PATH
    from fastchat.serve.controller import app, Controller, logger
    logger.setLevel(log_level)

    controller = Controller(dispatch_method)
    sys.modules["fastchat.serve.controller"].controller = controller

    MakeFastAPIOffline(app)
    app.title = "FastChat Controller"
    app._controller = controller
    return app


def create_model_worker_app(log_level: str = "INFO", **kwargs) -> FastAPI:
    """
    kwargs包含的字段如下：
    host:
    port:
    model_names:[`model_name`]
    controller_address:
    worker_address:

    对于Langchain支持的模型：
        langchain_model:True
        不会使用fschat
    对于online_api:
        online_api:True
        worker_class: `provider`
    对于离线模型：
        model_path: `model_name_or_path`,huggingface的repo-id或本地路径
        device:`LLM_DEVICE`
    """
    import fastchat.constants
    fastchat.constants.LOGDIR = LOG_PATH
    import argparse

    parser = argparse.ArgumentParser()
    args = parser.parse_args([])

    for k, v in kwargs.items():
        setattr(args, k, v)

    logger.error(f"可用模型有哪些: {args.model_names}")

    if worker_class := kwargs.get("langchain_model"): #Langchian支持的模型不用做操作
        from fastchat.serve.base_model_worker import app
        worker = ""
    # 在线模型API
    elif worker_class := kwargs.get("worker_class"):
        from fastchat.serve.base_model_worker import app

        worker = worker_class(model_names=args.model_names,
                              controller_addr=args.controller_address,
                              worker_addr=args.worker_address)
        # sys.modules["fastchat.serve.base_model_worker"].worker = worker
        sys.modules["fastchat.serve.base_model_worker"].logger.setLevel(log_level)
    # 本地模型
    else:
        from configs.model_config import VLLM_MODEL_DICT
        # if kwargs["model_names"][0] in VLLM_MODEL_DICT and args.infer_turbo == "vllm":
        if kwargs["model_names"][0] in VLLM_MODEL_DICT:
            import fastchat.serve.vllm_worker
            from fastchat.serve.vllm_worker import VLLMWorker, app, worker_id
            from vllm import AsyncLLMEngine
            from vllm.engine.arg_utils import AsyncEngineArgs,EngineArgs

            args.tokenizer = args.model_path # 如果tokenizer与model_path不一致在此处添加
            args.tokenizer_mode = 'auto'
            args.trust_remote_code= True
            args.download_dir= None
            args.load_format = 'auto'
            args.dtype = 'auto'
            args.seed = 0
            args.worker_use_ray = False
            args.pipeline_parallel_size = 1
            args.tensor_parallel_size = 1
            args.block_size = 16
            args.swap_space = 4  # GiB
            args.gpu_memory_utilization = 0.90
            args.max_num_batched_tokens = None # 一个批次中的最大令牌（tokens）数量，这个取决于你的显卡和大模型设置，设置太大显存会不够
            args.max_num_seqs = 256
            args.disable_log_stats = False
            args.conv_template = None
            args.limit_worker_concurrency = 5
            args.no_register = False
            args.num_gpus = 1 # vllm worker的切分是tensor并行，这里填写显卡的数量
            args.engine_use_ray = False
            args.disable_log_requests = False

            # 0.2.1 vllm后要加的参数, 但是这里不需要
            args.max_model_len = None
            args.revision = None
            args.quantization = None
            args.max_log_len = None
            args.tokenizer_revision = None
            args.max_parallel_loading_workers = 1
            args.enforce_eager = True
            args.max_context_len_to_capture = 8192
            
            # 0.2.2 vllm需要新加的参数
            args.max_paddings = 256
            
            if args.model_path:
                args.model = args.model_path
            if args.num_gpus > 1:
                args.tensor_parallel_size = args.num_gpus

            for k, v in kwargs.items():
                setattr(args, k, v)

            engine_args = AsyncEngineArgs.from_cli_args(args)
            engine = AsyncLLMEngine.from_engine_args(engine_args)

            worker = VLLMWorker(
                        controller_addr = args.controller_address,
                        worker_addr = args.worker_address,
                        worker_id = worker_id,
                        model_path = args.model_path,
                        model_names = args.model_names,
                        limit_worker_concurrency = args.limit_worker_concurrency,
                        no_register = args.no_register,
                        llm_engine =  engine,
                        conv_template = args.conv_template,
                        )
            sys.modules["fastchat.serve.vllm_worker"].engine = engine
            sys.modules["fastchat.serve.vllm_worker"].worker = worker
            sys.modules["fastchat.serve.vllm_worker"].logger.setLevel(log_level)

        else:
            from fastchat.serve.model_worker import app, GptqConfig, AWQConfig, ModelWorker, worker_id

            args.gpus = "0" # GPU的编号,如果有多个GPU，可以设置为"0,1,2,3"
            args.max_gpu_memory = "22GiB"
            args.num_gpus = 1  # model worker的切分是model并行，这里填写显卡的数量

            args.load_8bit = False
            args.cpu_offloading = None
            args.gptq_ckpt = None
            args.gptq_wbits = 16
            args.gptq_groupsize = -1
            args.gptq_act_order = False
            args.awq_ckpt = None
            args.awq_wbits = 16
            args.awq_groupsize = -1
            args.model_names = [""]
            args.conv_template = None
            args.limit_worker_concurrency = 5
            args.stream_interval = 2
            args.no_register = False
            args.embed_in_truncate = False
            for k, v in kwargs.items():
                setattr(args, k, v)
            if args.gpus:
                if args.num_gpus is None:
                    args.num_gpus = len(args.gpus.split(','))
                if len(args.gpus.split(",")) < args.num_gpus:
                    raise ValueError(
                        f"Larger --num-gpus ({args.num_gpus}) than --gpus {args.gpus}!"
                    )
                os.environ["CUDA_VISIBLE_DEVICES"] = args.gpus
            gptq_config = GptqConfig(
                ckpt=args.gptq_ckpt or args.model_path,
                wbits=args.gptq_wbits,
                groupsize=args.gptq_groupsize,
                act_order=args.gptq_act_order,
            )
            awq_config = AWQConfig(
                ckpt=args.awq_ckpt or args.model_path,
                wbits=args.awq_wbits,
                groupsize=args.awq_groupsize,
            )

            worker = ModelWorker(
                controller_addr=args.controller_address,
                worker_addr=args.worker_address,
                worker_id=worker_id,
                model_path=args.model_path,
                model_names=args.model_names,
                limit_worker_concurrency=args.limit_worker_concurrency,
                no_register=args.no_register,
                device=args.device,
                num_gpus=args.num_gpus,
                max_gpu_memory=args.max_gpu_memory,
                load_8bit=args.load_8bit,
                cpu_offloading=args.cpu_offloading,
                gptq_config=gptq_config,
                awq_config=awq_config,
                stream_interval=args.stream_interval,
                conv_template=args.conv_template,
                embed_in_truncate=args.embed_in_truncate,
            )
            sys.modules["fastchat.serve.model_worker"].args = args
            sys.modules["fastchat.serve.model_worker"].gptq_config = gptq_config
            # sys.modules["fastchat.serve.model_worker"].worker = worker
            sys.modules["fastchat.serve.model_worker"].logger.setLevel(log_level)

    MakeFastAPIOffline(app)
    app.title = f"FastChat LLM Server ({args.model_names[0]})"
    app._worker = worker
    return app


def create_openai_api_app(
        controller_address: str,
        api_keys: List = [],
        log_level: str = "INFO",
) -> FastAPI:
    import fastchat.constants
    fastchat.constants.LOGDIR = LOG_PATH
    from fastchat.serve.openai_api_server import app, CORSMiddleware, app_settings
    from fastchat.utils import build_logger
    logger = build_logger("openai_api", "openai_api.log")
    logger.setLevel(log_level)

    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    sys.modules["fastchat.serve.openai_api_server"].logger = logger
    app_settings.controller_address = controller_address
    app_settings.api_keys = api_keys

    MakeFastAPIOffline(app)
    app.title = "FastChat OpeanAI API Server"
    return app


def _set_app_event(app: FastAPI, started_event: mp.Event = None):
    @app.on_event("startup")
    async def on_startup():
        if started_event is not None:
            started_event.set()


def run_controller(log_level: str = "INFO", started_event: mp.Event = None):
    import uvicorn
    import httpx
    from fastapi import Body
    import time
    import sys
    # from server.utils import set_httpx_config
    set_httpx_config()

    app = create_controller_app(
        dispatch_method=FSCHAT_CONTROLLER.get("dispatch_method"),
        log_level=log_level,
    )
    _set_app_event(app, started_event)

    # add interface to release and load model worker
    @app.post("/release_worker")
    def release_worker(
            model_name: str = Body(..., description="要释放模型的名称", samples=["chatglm-6b"]),
            # worker_address: str = Body(None, description="要释放模型的地址，与名称二选一", samples=[FSCHAT_CONTROLLER_address()]),
            new_model_name: str = Body(None, description="释放后加载该模型"),
            keep_origin: bool = Body(False, description="不释放原模型，加载新模型")
    ) -> Dict:
        available_models = app._controller.list_models()
        if new_model_name in available_models:
            msg = f"要切换的LLM模型 {new_model_name} 已经存在"
            logger.info(msg)
            return {"code": 500, "msg": msg}

        if new_model_name:
            logger.info(f"开始切换LLM模型：从 {model_name} 到 {new_model_name}")
        else:
            logger.info(f"即将停止LLM模型： {model_name}")

        if model_name not in available_models:
            msg = f"the model {model_name} is not available"
            logger.error(msg)
            return {"code": 500, "msg": msg}

        worker_address = app._controller.get_worker_address(model_name)
        if not worker_address:
            msg = f"can not find model_worker address for {model_name}"
            logger.error(msg)
            return {"code": 500, "msg": msg}

        with get_httpx_client() as client:
            r = client.post(worker_address + "/release",
                        json={"new_model_name": new_model_name, "keep_origin": keep_origin})
            if r.status_code != 200:
                msg = f"failed to release model: {model_name}"
                logger.error(msg)
                return {"code": 500, "msg": msg}

        if new_model_name:
            timer = 300  # wait for new model_worker register
            while timer > 0:
                models = app._controller.list_models()
                if new_model_name in models:
                    break
                time.sleep(1)
                timer -= 1
            if timer > 0:
                msg = f"sucess change model from {model_name} to {new_model_name}"
                logger.info(msg)
                return {"code": 200, "msg": msg}
            else:
                msg = f"failed change model from {model_name} to {new_model_name}"
                logger.error(msg)
                return {"code": 500, "msg": msg}
        else:
            msg = f"sucess to release model: {model_name}"
            logger.info(msg)
            return {"code": 200, "msg": msg}

    host = FSCHAT_CONTROLLER["host"]
    port = FSCHAT_CONTROLLER["port"]

    if log_level == "ERROR":
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    uvicorn.run(app, host=host, port=port, log_level=log_level.lower())


def run_model_worker(
        model_name: str = LLM_MODEL,
        controller_address: str = "",
        log_level: str = "INFO",
        q: mp.Queue = None,
        started_event: mp.Event = None,
):
    import uvicorn
    from fastapi import Body
    import sys
    set_httpx_config()

    kwargs = get_model_worker_config(model_name)
    host = kwargs.pop("host")
    port = kwargs.pop("port")
    kwargs["model_names"] = [model_name]
    kwargs["controller_address"] = controller_address or fschat_controller_address()
    kwargs["worker_address"] = fschat_model_worker_address(model_name)
    model_path = kwargs.get("model_path", "")
    kwargs["model_path"] = model_path
    # kwargs["gptq_wbits"] = 4 # int4 模型试用这个参数

    app = create_model_worker_app(log_level=log_level, **kwargs)
    _set_app_event(app, started_event)
    if log_level == "ERROR":
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    # add interface to release and load model
    @app.post("/release")
    def release_model(
        new_model_name: str = Body(None, description="释放后加载该模型"),
        keep_origin: bool = Body(False, description="不释放原模型，加载新模型")
    ) -> Dict:
        if keep_origin:
            if new_model_name:
                q.put([model_name, "start", new_model_name])
        else:
            if new_model_name:
                q.put([model_name, "replace", new_model_name])
            else:
                q.put([model_name, "stop", None])
        return {"code": 200, "msg": "done"}

    uvicorn.run(app, host=host, port=port, log_level=log_level.lower())


def run_openai_api(log_level: str = "INFO", started_event: mp.Event = None):
    import uvicorn
    import sys
    set_httpx_config()

    controller_addr = fschat_controller_address()
    app = create_openai_api_app(controller_addr, log_level=log_level)  # TODO: not support keys yet.
    _set_app_event(app, started_event)

    host = FSCHAT_OPENAI_API["host"]
    port = FSCHAT_OPENAI_API["port"]
    if log_level == "ERROR":
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
    uvicorn.run(app, host=host, port=port)


def parse_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--all-webui",
        action="store_true",
        help="run fastchat's controller/openai_api/model_worker servers, run api.py and webui.py",
        dest="all_webui",
    )
    parser.add_argument(
        "--all-api",
        action="store_true",
        help="run fastchat's controller/openai_api/model_worker servers, run api.py",
        dest="all_api",
    )
    parser.add_argument(
        "--llm-api",
        action="store_true",
        help="run fastchat's controller/openai_api/model_worker servers",
        dest="llm_api",
    )
    parser.add_argument(
        "-o",
        "--openai-api",
        action="store_true",
        help="run fastchat's controller/openai_api servers",
        dest="openai_api",
    )
    parser.add_argument(
        "-m",
        "--model-worker",
        action="store_true",
        help="run fastchat's model_worker server with specified model name. "
             "specify --model-name if not using default LLM_MODELS",
        dest="model_worker",
    )
    parser.add_argument(
        "-n",
        "--model-name",
        type=str,
        nargs="+",
        default=LLM_MODELs,
        help="specify model name for model worker. "
             "add addition names with space seperated to start multiple model workers.",
        dest="model_name",
    )
    parser.add_argument(
        "-c",
        "--controller",
        type=str,
        help="specify controller address the worker is registered to. default is FSCHAT_CONTROLLER",
        dest="controller_address",
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="run api.py server",
        dest="api",
    )
    parser.add_argument(
        "-p",
        "--api-worker",
        action="store_true",
        help="run online model api such as zhipuai",
        dest="api_worker",
    )
    parser.add_argument(
        "-w",
        "--webui",
        action="store_true",
        help="run webui.py server",
        dest="webui",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="减少fastchat服务log信息",
        dest="quiet",
    )
    parser.add_argument(
        "-i",
        "--lite",
        action="store_true",
        help="以Lite模式运行：仅支持在线API的LLM对话、搜索引擎对话",
        dest="lite",
    )
    args = parser.parse_args()
    return args, parser


def dump_server_info(after_start=False, args=None):
    import platform
    import langchain
    import fastchat

    print("\n")
    print("=" * 30 + "Langchain-Chatchat Configuration" + "=" * 30)
    print(f"操作系统：{platform.platform()}.")
    print(f"python版本：{sys.version}")
    print(f"langchain版本：{langchain.__version__}. fastchat版本：{fastchat.__version__}")
    print("\n")

    models = LLM_MODELs
    if args and args.model_name:
        models = args.model_name

    print(f"当前启动的LLM模型：{models} @ {LLM_DEVICE}")

    for model in models:
        print(get_model_worker_config(model))

    if after_start:
        print("\n")
        print(f"服务端运行信息：")
        print(f"    OpenAI API Server: {fschat_openai_api_address()}")
    print("\n")


async def start_main_server():
    import time
    import signal

    def handler(signalname):
        """
        Python 3.9 has `signal.strsignal(signalnum)` so this closure would not be needed.
        Also, 3.8 includes `signal.valid_signals()` that can be used to create a mapping for the same purpose.
        """
        def f(signal_received, frame):
            raise KeyboardInterrupt(f"{signalname} received")
        return f

    # This will be inherited by the child process if it is forked (not spawned)
    signal.signal(signal.SIGINT, handler("SIGINT"))
    signal.signal(signal.SIGTERM, handler("SIGTERM"))

    mp.set_start_method("spawn")
    manager = mp.Manager()
    run_mode = None

    queue = manager.Queue()
    args, parser = parse_args()
    logger.debug(f"args: {args}")

    dump_server_info(args=args)

    if len(sys.argv) > 1:
        logger.info(f"正在启动服务：")
        logger.info(f"如需查看 llm_api 日志，请前往 {LOG_PATH}")

    processes = {"online_api": {}, "model_worker": {}}

    def process_count():
        return len(processes) + len(processes["online_api"]) + len(processes["model_worker"]) - 2

    if args.quiet or not log_verbose:
        log_level = "ERROR"
    else:
        log_level = "INFO"

    controller_started = manager.Event()
    process = Process(
        target=run_controller,
        name=f"controller",
        kwargs=dict(log_level=log_level, started_event=controller_started),
        daemon=True,
    )
    processes["controller"] = process

    process = Process(
        target=run_openai_api,
        name=f"openai_api",
        daemon=True,
    )
    processes["openai_api"] = process

    model_worker_started = []
    for model_name in args.model_name:
        config = get_model_worker_config(model_name)
        if not config.get("online_api"):
            e = manager.Event()
            model_worker_started.append(e)
            process = Process(
                target=run_model_worker,
                name=f"model_worker - {model_name}",
                kwargs=dict(model_name=model_name,
                            controller_address=args.controller_address,
                            log_level=log_level,
                            q=queue,
                            started_event=e),
                daemon=True,
            )
            processes["model_worker"][model_name] = process


    for model_name in args.model_name:
        config = get_model_worker_config(model_name)
        logger.error(f"config: {config}, {model_name}, {FSCHAT_MODEL_WORKERS.keys()}")
        if (config.get("online_api")
            and config.get("worker_class")
            and model_name in FSCHAT_MODEL_WORKERS):
            e = manager.Event()
            model_worker_started.append(e)
            process = Process(
                target=run_model_worker,
                name=f"api_worker - {model_name}",
                kwargs=dict(model_name=model_name,
                            controller_address=args.controller_address,
                            log_level=log_level,
                            q=queue,
                            started_event=e),
                daemon=True,
            )
            processes["online_api"][model_name] = process


    if process_count() == 0:
        parser.print_help()
    else:
        try:
            # 保证任务收到SIGINT后，能够正常退出
            if p:= processes.get("controller"):
                p.start()
                p.name = f"{p.name} ({p.pid})"
                controller_started.wait() # 等待controller启动完成

            if p:= processes.get("openai_api"):
                p.start()
                p.name = f"{p.name} ({p.pid})"

            for n, p in processes.get("model_worker", {}).items():
                p.start()
                p.name = f"{p.name} ({p.pid})"

            for n, p in processes.get("online_api", []).items():
                p.start()
                p.name = f"{p.name} ({p.pid})"

            # 等待所有model_worker启动完成
            for e in model_worker_started:
                e.wait()

            dump_server_info(after_start=True, args=args)

            while True:
                cmd = queue.get() # 收到切换模型的消息
                e = manager.Event()
                if isinstance(cmd, list):
                    model_name, cmd, new_model_name = cmd
                    if cmd == "start": # 运行新模型
                        logger.info(f"准备启动新模型进程：{new_model_name}")
                        process = Process(
                            target=run_model_worker,
                            name=f"model_worker - {new_model_name}",
                            kwargs=dict(model_name=new_model_name,
                                        controller_address=args.controller_address,
                                        log_level=log_level,
                                        q=queue,
                                        started_event=e),
                            daemon=True,
                        )
                        process.start()
                        process.name = f"{process.name} ({process.pid})"
                        processes["model_worker"][new_model_name] = process
                        e.wait()
                        logger.info(f"成功启动新模型进程：{new_model_name}")
                    elif cmd == "stop":
                        if process := processes["model_worker"].get(model_name):
                            time.sleep(1)
                            process.terminate()
                            process.join()
                            logger.info(f"停止模型进程：{model_name}")
                        else:
                            logger.error(f"未找到模型进程：{model_name}")
                    elif cmd == "replace":
                        if process := processes["model_worker"].pop(model_name, None):
                            logger.info(f"停止模型进程：{model_name}")
                            start_time = datetime.now()
                            time.sleep(1)
                            process.terminate()
                            process.join()
                            process = Process(
                                target=run_model_worker,
                                name=f"model_worker - {new_model_name}",
                                kwargs=dict(model_name=new_model_name,
                                            controller_address=args.controller_address,
                                            log_level=log_level,
                                            q=queue,
                                            started_event=e),
                                daemon=True,
                            )
                            process.start()
                            process.name = f"{process.name} ({process.pid})"
                            processes["model_worker"][new_model_name] = process
                            e.wait()
                            timing = datetime.now() - start_time
                            logger.info(f"成功启动新模型进程：{new_model_name}。用时：{timing}。")
                        else:
                            logger.error(f"未找到模型进程：{model_name}")


            # for process in processes.get("model_worker", {}).values():
            #     process.join()
            # for process in processes.get("online_api", {}).values():
            #     process.join()

            # for name, process in processes.items():
            #     if name not in ["model_worker", "online_api"]:
            #         if isinstance(p, dict):
            #             for work_process in p.values():
            #                 work_process.join()
            #         else:
            #             process.join()
        except Exception as e:
            logger.error(e)
            logger.warning("Caught KeyboardInterrupt! Setting stop event...")
        finally:
            # Send SIGINT if process doesn't exit quickly enough, and kill it as last resort
            # .is_alive() also implicitly joins the process (good practice in linux)
            # while alive_procs := [p for p in processes.values() if p.is_alive()]:

            for p in processes.values():
                logger.warning("Sending SIGKILL to %s", p)
                # Queues and other inter-process communication primitives can break when
                # process is killed, but we don't care here

                if isinstance(p, dict):
                    for process in p.values():
                        process.kill()
                else:
                    p.kill()

            for p in processes.values():
                logger.info("Process status: %s", p)


if __name__ == "__main__":

    if sys.version_info < (3, 10):
        loop = asyncio.get_event_loop()
    else:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        asyncio.set_event_loop(loop)
    # 同步调用协程代码
    loop.run_until_complete(start_main_server())


# 服务启动后接口调用示例：
# import openai
# openai.api_key = "EMPTY" # Not support yet
# openai.api_base = "http://localhost:8888/v1"

# model = "chatglm2-6b"

# # create a chat completion
# completion = openai.ChatCompletion.create(
#   model=model,
#   messages=[{"role": "user", "content": "Hello! What is your name?"}]
# )
# # print the completion
# print(completion.choices[0].message.content)
