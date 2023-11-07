import docker, sys, os, time, requests
from docker.types import Mount

from loguru import logger

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(src_dir)

from configs.server_config import WEBUI_SERVER, API_SERVER, SDFILE_API_SERVER, CONTRAINER_NAME, IMAGE_NAME
from configs.model_config import USE_FASTCHAT



logger.info(f"IMAGE_NAME: {IMAGE_NAME}, CONTRAINER_NAME: {CONTRAINER_NAME}, ")


client = docker.from_env()
for i  in client.containers.list(all=True):
    if i.name == CONTRAINER_NAME:
        container = i
        container.stop()
        container.remove()
    break



# 启动容器
logger.info("start service")

mount = Mount(
    type='bind',
    source=src_dir,
    target='/home/user/chatbot/',
    read_only=True  # 如果需要只读访问，将此选项设置为True
)

container = client.containers.run(
    image=IMAGE_NAME,
    command="bash",
    mounts=[mount],
    name=CONTRAINER_NAME,
    ports={
        f"{WEBUI_SERVER['docker_port']}/tcp": API_SERVER['port'], 
        f"{API_SERVER['docker_port']}/tcp": WEBUI_SERVER['port'],
        f"{SDFILE_API_SERVER['docker_port']}/tcp": SDFILE_API_SERVER['port'],
        },
    stdin_open=True,
    detach=True,
    tty=True,
)

# 启动notebook
exec_command = container.exec_run("bash jupyter_start.sh")
# 
exec_command = container.exec_run("cd /homse/user/chatbot && nohup python devops_gpt/service/sdfile_api.py > /homse/user/logs/sdfile_api.log &")
# 
exec_command = container.exec_run("cd /homse/user/chatbot && nohup python devops_gpt/service/api.py > /homse/user/logs/api.log &")

if USE_FASTCHAT:
    # 启动fastchat的服务
    exec_command = container.exec_run("cd /homse/user/chatbot && nohup python devops_gpt/service/llm_api.py > /homse/user/logs/llm_api.log &")
# 
exec_command = container.exec_run("cd /homse/user/chatbot/examples && nohup bash start_webui.sh > /homse/user/logs/start_webui.log &")



