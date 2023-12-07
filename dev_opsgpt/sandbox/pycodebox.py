import time, os, docker, requests, json, uuid, subprocess, time, asyncio, aiohttp, re, traceback
import psutil
from typing import List, Optional, Union
from loguru import logger

from websockets.sync.client import connect as ws_connect_sync
from websockets.client import connect as ws_connect
from websocket import create_connection
from websockets.client import WebSocketClientProtocol, ClientConnection
from websockets.exceptions import ConnectionClosedError

from configs.server_config import SANDBOX_SERVER
from configs.model_config import JUPYTER_WORK_PATH
from .basebox import BaseBox, CodeBoxResponse, CodeBoxStatus


class PyCodeBox(BaseBox):

    enter_status: bool = False

    def __init__(
            self, 
            remote_url: str = "",
            remote_ip: str = SANDBOX_SERVER["host"],
            remote_port: str = SANDBOX_SERVER["port"],
            token: str = "mytoken",
            do_code_exe: bool = False,
            do_remote: bool = False,
            do_check_net: bool = True,
    ):
        super().__init__(remote_url, remote_ip, remote_port, token, do_code_exe, do_remote)
        self.enter_status = True
        self.do_check_net = do_check_net
        asyncio.run(self.astart())

        # logger.info(f"""remote_url: {self.remote_url},
        #             remote_ip: {self.remote_ip},
        #             remote_port: {self.remote_port}""")

    def decode_code_from_text(self, text: str) -> str:
        pattern = r'```.*?```'
        code_blocks = re.findall(pattern, text, re.DOTALL)
        code_text: str = "\n".join([block.strip('`') for block in code_blocks])
        code_text = code_text[6:] if code_text.startswith("python") else code_text
        code_text = code_text.replace("python\n", "").replace("code", "")
        return code_text
    
    def run(
            self, code_text: Optional[str] = None,
            file_path: Optional[os.PathLike] = None,
            retry = 3,
    ) -> CodeBoxResponse:
        if not code_text and not file_path:
            return CodeBoxResponse(
                code_exe_response="Code or file_path must be specifieds!",
                code_text=code_text,
                code_exe_type="text",
                code_exe_status=502,
                do_code_exe=self.do_code_exe,
            )
        
        if code_text and file_path:
            return CodeBoxResponse(
                code_exe_response="Can only specify code or the file to read_from!",
                code_text=code_text,
                code_exe_type="text",
                code_exe_status=502,
                do_code_exe=self.do_code_exe,
            )
        
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                code_text = f.read()

        # run code in jupyter kernel
        if retry <= 0:
            raise RuntimeError("Could not connect to kernel")
        
        if not self.ws:
            raise RuntimeError("Jupyter not running. Make sure to start it first")
        
        # logger.debug(f"code_text: {len(code_text)}, {code_text}")

        self.ws.send(
            json.dumps(
                {
                    "header": {
                        "msg_id": (msg_id := uuid.uuid4().hex),
                        "msg_type": "execute_request",
                    },
                    "parent_header": {},
                    "metadata": {},
                    "content": {
                        "code": code_text,
                        "silent": False, # True，则内核会执行代码，但不会发送执行结果（如输出）
                        "store_history": True, # True，则执行的代码会被记录在交互式环境的历史记录中
                        "user_expressions": {},
                        "allow_stdin": False, # True，允许代码执行时接受用户输入
                        "stop_on_error": True, # True，当执行中遇到错误时，后续代码将不会继续执行。
                    },
                    "channel": "shell",
                    "buffers": [],
                }
            )
        )
        result = ""
        while True:
            try:
                if isinstance(self.ws, WebSocketClientProtocol):
                    raise RuntimeError("Mixing asyncio and sync code is not supported")
                received_msg = json.loads(self.ws.recv())
            except ConnectionClosedError:
                # logger.debug("box start, ConnectionClosedError!!!")
                self.start()
                return self.run(code_text, file_path, retry - 1)

            if (
                received_msg["header"]["msg_type"] == "stream"
                and received_msg["parent_header"]["msg_id"] == msg_id
            ):
                msg = received_msg["content"]["text"].strip()
                if "Requirement already satisfied:" in msg:
                    continue
                result += msg + "\n"

            elif (
                received_msg["header"]["msg_type"] == "execute_result"
                and received_msg["parent_header"]["msg_id"] == msg_id
            ):
                result += received_msg["content"]["data"]["text/plain"].strip() + "\n"

            elif received_msg["header"]["msg_type"] == "display_data":
                if "image/png" in received_msg["content"]["data"]:
                    return CodeBoxResponse(
                        code_exe_type="image/png",
                        code_text=code_text,
                        code_exe_response=received_msg["content"]["data"]["image/png"],
                        code_exe_status=200,
                        do_code_exe=self.do_code_exe
                    )
                if "text/plain" in received_msg["content"]["data"]:
                    return CodeBoxResponse(
                        code_exe_type="text",
                        code_text=code_text,
                        code_exe_response=received_msg["content"]["data"]["text/plain"],
                        code_exe_status=200,
                        do_code_exe=self.do_code_exe
                    )
                return CodeBoxResponse(
                        code_exe_type="error",
                        code_text=code_text,
                        code_exe_response=received_msg["content"]["data"]["text/plain"],
                        code_exe_status=420,
                        do_code_exe=self.do_code_exe
                    )
            elif (
                received_msg["header"]["msg_type"] == "status"
                and received_msg["parent_header"]["msg_id"] == msg_id
                and received_msg["content"]["execution_state"] == "idle"
            ):
                if len(result) > 500:
                    result = "[...]\n" + result[-500:]
                return CodeBoxResponse(
                        code_exe_type="text",
                        code_text=code_text,
                        code_exe_response=result or "Code run successfully (no output)",
                        code_exe_status=200,
                        do_code_exe=self.do_code_exe
                    )

            elif (
                received_msg["header"]["msg_type"] == "error"
                and received_msg["parent_header"]["msg_id"] == msg_id
            ):
                error = (
                    f"{received_msg['content']['ename']}: "
                    f"{received_msg['content']['evalue']}"
                )
                return CodeBoxResponse(
                        code_exe_type="error",
                        code_text=code_text,
                        code_exe_response=error,
                        code_exe_status=500,
                        do_code_exe=self.do_code_exe
                    )

    def _get_kernelid(self, ) -> None:
        headers = {"Authorization": f'Token {self.token}', 'token': self.token}
        response = requests.get(f"{self.kernel_url}?token={self.token}", headers=headers)
        if len(response.json()) > 0:
            self.kernel_id = response.json()[0]["id"]
        else:
            response = requests.post(f"{self.kernel_url}?token={self.token}", headers=headers)
            self.kernel_id = response.json()["id"]
        if self.kernel_id is None:
            raise Exception("Could not start kernel")
        
    async def _aget_kernelid(self, ) -> None:
        headers = {"Authorization": f'Token {self.token}', 'token': self.token}
        response = requests.get(f"{self.kernel_url}?token={self.token}", headers=headers)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.kernel_url}?token={self.token}", headers=headers) as resp:
                if len(await resp.json()) > 0:
                    self.kernel_id = (await resp.json())[0]["id"]
                else:
                    async with session.post(f"{self.kernel_url}?token={self.token}", headers=headers) as response:
                        self.kernel_id = (await response.json())["id"]

        # if len(response.json()) > 0:
        #     self.kernel_id = response.json()[0]["id"]
        # else:
        #     response = requests.post(f"{self.kernel_url}?token={self.token}", headers=headers)
        #     self.kernel_id = response.json()["id"]
        # if self.kernel_id is None:
        #     raise Exception("Could not start kernel")
    def _check_connect(self, ) -> bool:
        if self.kernel_url == "":
            return False

        try:
             response = requests.get(f"{self.kernel_url}?token={self.token}", timeout=270)
             return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    async def _acheck_connect(self, ) -> bool:
        if self.kernel_url == "":
            return False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.kernel_url}?token={self.token}", timeout=270) as resp:
                    return resp.status == 200
        except aiohttp.ClientConnectorError:
            pass
        except aiohttp.ServerDisconnectedError:
            pass

    def  _check_port(self, ) -> bool:
        try:
             response = requests.get(f"{self.remote_ip}:{self.remote_port}", timeout=270)
             logger.warning(f"Port is conflict, please check your codebox's port {self.remote_port}")
             return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False
        
    async def _acheck_port(self, ) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.remote_ip}:{self.remote_port}", timeout=270) as resp:
                    logger.warning(f"Port is conflict, please check your codebox's port {self.remote_port}")
                    return resp.status == 200
        except aiohttp.ClientConnectorError:
            pass
        except aiohttp.ServerDisconnectedError:
            pass

    def _check_connect_success(self, retry_nums: int = 5) -> bool:
        if not self.do_check_net: return True
        
        while retry_nums > 0:
            try:
                connect_status = self._check_connect()
                if connect_status:
                    logger.info(f"{self.remote_url} connection success")
                    return True
            except requests.exceptions.ConnectionError:
                logger.info(f"{self.remote_url} connection fail")
            retry_nums -= 1
            time.sleep(5)
        raise BaseException(f"can't connect to {self.remote_url}")
    
    async def _acheck_connect_success(self, retry_nums: int = 5) -> bool:
        if not self.do_check_net: return True
        while retry_nums > 0:
            try:
                connect_status = await self._acheck_connect()
                if connect_status:
                    logger.info(f"{self.remote_url} connection success")
                    return True
            except requests.exceptions.ConnectionError:
                logger.info(f"{self.remote_url} connection fail")
            retry_nums -= 1
            time.sleep(5)
        raise BaseException(f"can't connect to {self.remote_url}")
    
    def start(self, ):
        '''判断是从外部service执行还是内部启动notebook执行'''
        self.jupyter = None
        if self.do_remote:
            # TODO自动检测日期,并重启容器
            self.kernel_url = self.remote_url + "/api/kernels"
            self._check_connect_success()

            self._get_kernelid()
            # logger.debug(self.kernel_url.replace("http", "ws") + f"/{self.kernel_id}/channels?token={self.token}")
            self.wc_url = self.kernel_url.replace("http", "ws") + f"/{self.kernel_id}/channels?token={self.token}"
            headers = {"Authorization": f'Token {self.token}', 'token': self.token}
            self.ws = create_connection(self.wc_url, headers=headers)
        else:
            # TODO 自动检测本地接口
            port_status = self._check_port()
            connect_status = self._check_connect()
            logger.info(f"port_status: {port_status}, connect_status: {connect_status}")
            if port_status and not connect_status:
                raise BaseException(f"Port is conflict, please check your codebox's port {self.remote_port}")
            
            if not connect_status:
                self.jupyter = subprocess.run(
                    [
                        "jupyer", "notebnook",
                        f"--NotebookApp.token={self.token}",
                        f"--port={self.remote_port}",
                        "--no-browser",
                        "--ServerApp.disable_check_xsrf=True",
                        "--notebook-dir={JUPYTER_WORK_PATH}"
                    ],
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                )

            self.kernel_url = self.remote_url + "/api/kernels"
            self.do_check_net = True
            self._check_connect_success()
            self._get_kernelid()
            # logger.debug(self.kernel_url.replace("http", "ws") + f"/{self.kernel_id}/channels?token={self.token}")
            self.wc_url = self.kernel_url.replace("http", "ws") + f"/{self.kernel_id}/channels?token={self.token}"
            headers = {"Authorization": f'Token {self.token}', 'token': self.token}
            self.ws = create_connection(self.wc_url, headers=headers)

    async def astart(self, ):
        '''判断是从外部service执行还是内部启动notebook执行'''
        self.jupyter = None
        if self.do_remote:
            # TODO自动检测日期,并重启容器
            self.kernel_url = self.remote_url + "/api/kernels"

            await self._acheck_connect_success()
            await self._aget_kernelid()
            self.wc_url = self.kernel_url.replace("http", "ws") + f"/{self.kernel_id}/channels?token={self.token}"
            headers = {"Authorization": f'Token {self.token}', 'token': self.token}
            self.ws = create_connection(self.wc_url, headers=headers)
        else:
            # TODO 自动检测本地接口
            port_status = await self._acheck_port()
            self.kernel_url = self.remote_url + "/api/kernels"
            connect_status = await self._acheck_connect()
            logger.info(f"port_status: {port_status}, connect_status: {connect_status}")
            if port_status and not connect_status:
                raise BaseException(f"Port is conflict, please check your codebox's port {self.remote_port}")

            if not connect_status:
                self.jupyter = subprocess.Popen(
                    [
                        "jupyter", "notebook",
                        f"--NotebookApp.token={self.token}",
                        f"--port={self.remote_port}",
                        "--no-browser",
                        "--ServerApp.disable_check_xsrf=True"
                    ],
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                )

            self.kernel_url = self.remote_url + "/api/kernels"
            self.do_check_net = True
            await self._acheck_connect_success()
            await self._aget_kernelid()
            self.wc_url = self.kernel_url.replace("http", "ws") + f"/{self.kernel_id}/channels?token={self.token}"
            headers = {"Authorization": f'Token {self.token}', 'token': self.token}
            self.ws = create_connection(self.wc_url, headers=headers)

    def status(self,) -> CodeBoxStatus:
        if not self.kernel_id:
            self._get_kernelid()
        
        return CodeBoxStatus(
            status="running" if self.kernel_id
            and requests.get(self.kernel_url, timeout=270).status_code == 200
            else "stopped"
        )
    
    async def astatus(self,) -> CodeBoxStatus:
        if not self.kernel_id:
            await self._aget_kernelid()
        
        return CodeBoxStatus(
            status="running" if self.kernel_id
            and requests.get(self.kernel_url, timeout=270).status_code == 200
            else "stopped"
        )
    
    def restart(self, ) -> CodeBoxStatus:
        return CodeBoxStatus(status="restared")
    
    def stop(self, ) -> CodeBoxStatus:
        try:
            if self.jupyter is not None:
                for process in psutil.process_iter(["pid", "name", "cmdline"]):
                    # 检查进程名是否包含"jupyter"
                    if f'port={self.remote_port}' in str(process.info["cmdline"]).lower() and \
                        "jupyter" in process.info['name'].lower():
                        logger.warning(f'port={self.remote_port}, {process.info}')
                        # 关闭进程
                        process.terminate()

                self.jupyter = None
        except Exception as e:
            logger.error(traceback.format_exc())

        if self.ws is not None:
            try:
                if self.ws is not None:
                    self.ws.close()
                else:
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(self.ws.close())
            except Exception as e:
                logger.error(traceback.format_exc())
            self.ws = None

        # return CodeBoxStatus(status="stopped")
    
    def __del__(self):
        self.stop()
