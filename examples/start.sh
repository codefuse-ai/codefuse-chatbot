#!/bin/bash


cp ../configs/model_config.py.example ../configs/model_config.py
cp ../configs/server_config.py.example ../configs/server_config.py

streamlit run webui_config.py --server.port 8510
