import os

def is_running_in_docker():
    """
    检查当前代码是否在 Docker 容器中运行
    """
    # 检查是否存在 /.dockerenv 文件
    if os.path.exists('/.dockerenv'):
        return True

    # 检查 cgroup 文件系统是否为 /docker/ 开头
    if os.path.exists("/proc/1/cgroup"):
        with open('/proc/1/cgroup', 'rt') as f:
            return '/docker/' in f.read()
    return False