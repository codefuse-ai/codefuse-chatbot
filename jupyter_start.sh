#!/bin/bash

nohup jupyter-notebook --NotebookApp.token=mytoken --port=5050 --allow-root --ip=0.0.0.0 --no-browser --ServerApp.disable_check_xsrf=True &