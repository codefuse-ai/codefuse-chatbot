import docker, sys, os, time, requests

from loguru import logger

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(src_dir)

from configs.server_config import CONTRAINER_NAME, SANDBOX_SERVER


if SANDBOX_SERVER["do_remote"]:
    # stop and remove the container
    client = docker.from_env()
    for i  in client.containers.list(all=True):
        if i.name == CONTRAINER_NAME:
            container = i
            container.stop()
            container.remove()
        break
else:
    # stop local 
    import psutil
    for process in psutil.process_iter(["pid", "name", "cmdline"]):
        # check process name contains "jupyter" and port=xx
        if f"port={SANDBOX_SERVER['port']}" in str(process.info["cmdline"]).lower() and \
            "jupyter" in process.info['name'].lower():

            logger.warning(f"port={SANDBOX_SERVER['port']}, {process.info}")
            # 关闭进程
            process.terminate()
