import docker, sys, os, time, requests

from loguru import logger

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(src_dir)

# from configs.server_config import CONTRAINER_NAME, SANDBOX_SERVER, IMAGE_NAME

CONTRAINER_NAME = "devopsgpt-chatbot_default"
SANDBOX_SERVER = {
    "port": "8501"
}
IMAGE_NAME = "devopsgpt-chatbot:pypy"

client = docker.from_env()
for i  in client.containers.list(all=True):
    if i.name == CONTRAINER_NAME:
        container = i
        container.stop()
        container.remove()
    break
# 启动容器
logger.info("start ot init container & notebook")
container = client.containers.run(
    image=IMAGE_NAME,
    command="bash",
    name=CONTRAINER_NAME,
    ports={"8501/tcp": SANDBOX_SERVER["port"]},
    stdin_open=True,
    detach=True,
    tty=True,
)

# 启动notebook
# exec_command = container.exec_run("bash jupyter_start.sh")

