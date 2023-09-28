import time
import docker

st = time.time()
client = docker.from_env()
print(time.time()-st)


st = time.time()
client.containers.run("ubuntu:latest", "echo hello world")
print(time.time()-st)