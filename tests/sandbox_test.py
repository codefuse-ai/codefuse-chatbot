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

from dev_opsgpt.service.sdfile_api import sd_upload_file
from dev_opsgpt.sandbox.pycodebox import PyCodeBox
from pathlib import Path


# python = Path(sys.executable).absolute()
# print(Path(python).as_posix())
# print(python)
# print(sys.executable)


import requests

# # 设置Jupyter Notebook服务器的URL
# url = 'http://172.25.0.3:5050'  # 或者是你自己的Jupyter服务器的URL

# # 发送GET请求来获取Jupyter Notebook的登录页面
# response = requests.get(url)

# # 检查响应状态码
# if response.status_code == 200:
#     # 打印响应内容
#     print('connect success')
# else:
#     print('connect fail')

# import subprocess 
# jupyter = subprocess.Popen(
#                     [
#                         "juptyer", "notebnook",
#                         "--NotebookApp.token=mytoken",
#                         f"--port=4949",
#                         "--no-browser",
#                         "--ServerApp.disable_check_xsrf=True",
#                     ],
#                     stderr=subprocess.PIPE,
#                     stdin=subprocess.PIPE,
#                     stdout=subprocess.PIPE,
#                 )

# # 测试1
# import time, psutil
# from loguru import logger
# import asyncio
pycodebox = PyCodeBox(remote_url="http://localhost:5050", 
               remote_ip="http://localhost", 
            remote_port="5050", 
            token="mytoken",
            do_code_exe=True, 
            do_remote=False)

# pycodebox.list_files()
# file = "./torch_test.py"
# upload_file = st_load_file(file, filename="torch_test.py")

# file_content = upload_file.read()  # 读取上传文件的内容
# print(upload_file, file_content)
# pycodebox.upload("torch_test.py", upload_file)

# asyncio.run(pycodebox.alist_files())


reuslt = pycodebox.chat("```'hello world!'```", do_code_exe=True)
print(reuslt)

# reuslt = pycodebox.chat("print('hello world!')", do_code_exe=False)
# print(reuslt)

# for process in psutil.process_iter(["pid", "name", "cmdline"]):
#     # 检查进程名是否包含"jupyter"
#     if 'port=5050' in str(process.info["cmdline"]).lower() and \
#         "jupyter" in process.info['name'].lower():

#         logger.warning(f'port=5050, {process.info}')
#         # 关闭进程
#         process.terminate()
        

# 测试2
# with PyCodeBox(remote_url="http://localhost:5050", 
#                remote_ip="http://localhost", 
#             remote_port="5050", 
#             token="mytoken",
#             do_code_exe=True, 
#             do_remote=True) as codebox:
    
#     result = codebox.run("print('hello world!')")
#     print(result)



# with PyCodeBox(
#     remote_ip="http://localhost", 
#     remote_port="5555", 
#     token="mytoken",
#     do_code_exe=True, 
#     do_remote=False
#     ) as codebox:
    
#     result = codebox.run("print('hello world!')")
    # print(result)
