#!/bin/bash

set -x

CONTAINER_NAME=devopsgpt_default
IMAGES=devopsgpt:pypy3
WORK_DIR=$PWD

docker stop $CONTAINER_NAME
docker rm $CONTAINER_NAME
EXTERNAL_PORT=5050

# linux start
# docker run -it -p 5050:5050 --name $CONTAINER_NAME $IMAGES bash

# windows start
winpty docker run -it -d -p $EXTERNAL_PORT:5050 --name $CONTAINER_NAME $IMAGES bash
