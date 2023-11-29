import docker, sys, os
from loguru import logger

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(src_dir)

from configs.server_config import (
    SANDBOX_CONTRAINER_NAME, CONTRAINER_NAME, SANDBOX_SERVER, DOCKER_SERVICE
)


from start import check_docker, check_process

try:
    client = docker.from_env()
except:
    client = None

# 
check_docker(client, SANDBOX_CONTRAINER_NAME, do_stop=True, )
check_process(f"port={SANDBOX_SERVER['port']}", do_stop=True)
check_process(f"port=5050", do_stop=True)

# 
check_docker(client, CONTRAINER_NAME, do_stop=True, )
check_process("service/api.py", do_stop=True)
check_process("service/sdfile_api.py", do_stop=True)
check_process("service/llm_api.py", do_stop=True)
check_process("webui.py", do_stop=True)
