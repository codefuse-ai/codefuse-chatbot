From python:3.9-bookworm

WORKDIR /home/user

COPY ./docker_requirements.txt /home/user/docker_requirements.txt
COPY ./jupyter_start.sh /home/user/jupyter_start.sh

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install -r /home/user/docker_requirements.txt

CMD ["bash"]
