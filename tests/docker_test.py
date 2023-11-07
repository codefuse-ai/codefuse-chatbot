import time
import docker

st = time.time()
client = docker.from_env()
print(time.time()-st)


st = time.time()
client.containers.run("ubuntu:latest", "echo hello world")
print(time.time()-st)


import socket


def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

def get_ipv4_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 使用一个临时套接字连接到公共的 DNS 服务器
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    finally:
        s.close()
    return ip_address

# print(get_ipv4_address())
# import docker
# client = docker.from_env()

# containers = client.containers.list(all=True)
# for container in containers:
#     container_a_info = client.containers.get(container.id)
#     container1_networks = container.attrs['NetworkSettings']['Networks']
#     container_a_ip = container_a_info.attrs['NetworkSettings']['IPAddress']

#     print(container_a_info.name, container_a_ip, [[k, v["IPAddress"]] for k,v in container1_networks.items() ])


