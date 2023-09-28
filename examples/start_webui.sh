#!/bin/bash


set -e

# python ../dev_opsgpt/service/llm_api.py

# 启动独立的沙箱环境
python start_sandbox.py

# python ../dev_opsgpt/service/llm_api.py
streamlit run webui.py
