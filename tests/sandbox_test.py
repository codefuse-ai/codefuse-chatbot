import json
from uuid import uuid4
import uuid 

import requests
from websockets.sync.client import connect as ws_connect_sync
from websocket import create_connection
from websockets.client import connect as ws_connect

import sys, os
src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(src_dir)


from configs.model_config import JUPYTER_WORK_PATH
from coagent.sandbox.pycodebox import PyCodeBox
import requests


# import subprocess 
# import time
# from loguru import logger

# class PyCodeBox:

#     enter_status: bool = False

#     def __init__(
#             self, 
#             remote_url: str = "",
#             remote_ip: str = "localhost",
#             remote_port: str = "5050",
#             token: str = "mytoken",
#             do_code_exe: bool = False,
#             do_remote: bool = False,
#             do_check_net: bool = True,
#     ):
#         self.enter_status = True
#         self.do_check_net = do_check_net
#         self.start()


#     def start(self, ):
#         logger.debug("start!")
#         jupyter = subprocess.Popen(
#             [
#                 "jupyter", "notebook",
#                 "--NotebookApp.token=mytoken",
#                 "--port=5050",
#                 "--no-browser",
#                 "--ServerApp.disable_check_xsrf=True",
#             ],
#             stderr=subprocess.PIPE,
#             # stdin=subprocess.PIPE,
#             stdout=subprocess.PIPE,
#         )
#         logger.debug("start over")

# pycodebox = PyCodeBox()

# logger.debug("start to sleep")
# idx = 0
# while True:
#     time.sleep(5)
#     logger.debug(f"sleep {idx}")
#     idx+=1

# # 测试1
# import time, psutil
# from loguru import logger
# import asyncio
pycodebox = PyCodeBox(remote_url="http://localhost:5050", 
               remote_ip="http://localhost", 
            remote_port="5050", 
            token="mytoken",
            jupyter_work_path=JUPYTER_WORK_PATH,
            do_code_exe=True, 
            do_remote=False,
            use_stop=True,
            do_check_net=False
            )


reuslt = pycodebox.chat("```import os\nos.getcwd()```", do_code_exe=True)
print(reuslt)

# reuslt = pycodebox.chat("```print('hello world!')```", do_code_exe=True)
reuslt = pycodebox.chat("print('hello world!')", do_code_exe=True)
print(reuslt)

    
# 测试2
# with PyCodeBox(remote_url="http://localhost:5050", 
#                remote_ip="http://localhost", 
#             remote_port="5050", 
#             token="mytoken",
#             do_code_exe=True, 
#             do_remote=False) as codebox:
    
#     result = codebox.run("'hello world!'")
#     print(result)