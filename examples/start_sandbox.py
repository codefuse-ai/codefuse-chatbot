import docker, sys, os, time, requests

from loguru import logger

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(src_dir)

from configs.server_config import SANDBOX_SERVER, SANDBOX_IMAGE_NAME, SANDBOX_CONTRAINER_NAME


if SANDBOX_SERVER["do_remote"]:
    client = docker.from_env()
    for i  in client.containers.list(all=True):
        if i.name == SANDBOX_CONTRAINER_NAME:
            container = i
            container.stop()
            container.remove()
        break
    # 启动容器
    logger.info("start ot init container & notebook")
    container = client.containers.run(
        image=SANDBOX_IMAGE_NAME,
        command="bash",
        name=SANDBOX_CONTRAINER_NAME,
        ports={f"{SANDBOX_SERVER['docker_port']}/tcp": SANDBOX_SERVER["port"]},
        stdin_open=True,
        detach=True,
        tty=True,
    )

    # 启动notebook
    exec_command = container.exec_run("bash jupyter_start.sh")

    # 判断notebook是否启动
    retry_nums = 3
    while retry_nums>0:
        response = requests.get(f"http://localhost:{SANDBOX_SERVER['port']}", timeout=270)
        if response.status_code == 200:
            logger.info("container & notebook init success")
            break
        else:
            retry_nums -= 1
            logger.info(client.containers.list())
            logger.info("wait container running ...")
        time.sleep(5)
else:
    logger.info("启动local的notebook环境支持代码执行")
