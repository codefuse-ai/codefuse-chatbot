from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import sys
from abc import ABC, abstractclassmethod
from loguru import logger

from configs.server_config import SANDBOX_SERVER


class CodeBoxResponse(BaseModel):
    code_text: str = ""
    code_exe_response: str = ""
    code_exe_type: str = ""
    code_exe_status: int
    do_code_exe: bool

    def __str__(self,):
        return f"""status: {self.code_exe_status}, type: {self.code_exe_type}, response: {self.code_exe_response}"""


class CodeBoxStatus(BaseModel):
    status: str


class BaseBox(ABC):

    enter_status = False

    def __init__(
            self, 
            remote_url: str = "",
            remote_ip: str = SANDBOX_SERVER["host"],
            remote_port: str = SANDBOX_SERVER["port"],
            token: str = "mytoken",
            do_code_exe: bool = False,
            do_remote: bool = False
    ):
        self.token = token
        self.remote_url = remote_url or remote_ip + ":" + str(remote_port)
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.do_code_exe = do_code_exe
        self.do_remote = do_remote
        self.local_pyenv = Path(sys.executable).absolute()
        self.ws = None
        self.aiohttp_session = None
        self.kernel_url = ""

    def chat(self, text: str, file_path: str = None, do_code_exe: bool = None) -> CodeBoxResponse:
        '''执行流'''
        do_code_exe = self.do_code_exe if do_code_exe is None else do_code_exe
        if not do_code_exe:
            return CodeBoxResponse(
                code_exe_response=text, code_text=text, code_exe_type="text", code_exe_status=200,
                do_code_exe=do_code_exe
            )
        
        try:
            code_text = self.decode_code_from_text(text)
            return self.run(code_text, file_path)
        except Exception as e:
            return CodeBoxResponse(
                code_exe_response=str(e), code_text=text, code_exe_type="error", code_exe_status=500,
                do_code_exe=do_code_exe
            )
        
    async def achat(self, text: str, file_path: str = None, do_code_exe: bool = None) -> CodeBoxResponse:
        do_code_exe = self.do_code_exe if do_code_exe is None else do_code_exe
        if not do_code_exe:
            return CodeBoxResponse(
                code_exe_response=text, code_text=text, code_exe_type="text", code_exe_status=200,
                do_code_exe=do_code_exe
            )
        
        try:
            code_text = self.decode_code_from_text(text)
            return await self.arun(code_text, file_path)
        except Exception as e:
            return CodeBoxResponse(
                code_exe_response=str(e), code_text=text, code_exe_type="error", code_exe_status=500,
                do_code_exe=do_code_exe
            )
        
    def run(
            self,
            code_text: str = None,
            file_path: str = None,
            retry=3,
    ) -> CodeBoxResponse:
        '''执行代码'''
        pass

    async def arun(
            self,
            code_text: str = None,
            file_path: str = None,
            retry=3, 
    ) -> CodeBoxResponse:
        '''执行代码'''
        pass

    def decode_code_from_text(self, text):
        pass

    def start(self,):
        pass

    async def astart(self, ):
        pass

    @abstractclassmethod
    def stop(self) -> CodeBoxStatus:
        """Terminate the CodeBox instance"""

    def __enter__(self, ) -> "BaseBox":
        if not self.enter_status:
            self.start()
        return self
    
    async def __aenter__(self, ) -> "BaseBox":
        if not self.enter_status:
            await self.astart()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()

