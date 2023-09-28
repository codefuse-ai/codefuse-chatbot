# <p align="center">Codefuse-ChatBot: Development by Private Knowledge Augmentation</p>

<p align="center">
    <a href="README.md"><img src="https://img.shields.io/badge/文档-中文版-yellow.svg" alt="ZH doc"></a>
    <a href="README_EN.md"><img src="https://img.shields.io/badge/document-英文版-yellow.svg" alt="EN doc"></a>
    <img src="https://img.shields.io/github/license/codefuse-ai/codefuse-chatbot" alt="License">
    <a href="https://github.com/codefuse-ai/codefuse-chatbot/issues">
      <img alt="Open Issues" src="https://img.shields.io/github/issues-raw/codefuse-ai/codefuse-chatbot" />
    </a>
    <br><br>
</p>
This project is an open-source AI intelligent assistant, specifically designed for the entire lifecycle of software development, covering design, coding, testing, deployment, and operations. Through knowledge retrieval, tool utilization, and sandbox execution, Codefuse-ChatBot can answer various professional questions during your development process and perform question-answering operations on standalone, disparate platforms.


## 🔔 Updates
- [2023.09.15] Sandbox features for local/isolated environments are now available, implementing specified URL knowledge retrieval based on web crawling.

## 📜 Contents
- [🤝 Introduction](#-introduction)
- [🧭 Technical Route](#-technical-route)
- [🌐 模型接入](#-模型接入)
- [🚀 Quick Start](#-quick-start)
- [🤗 Acknowledgements](#-acknowledgements)

## 🤝 Introduction

💡 The aim of this project is to construct an AI intelligent assistant for the entire lifecycle of software development, covering design, coding, testing, deployment, and operations, through Retrieval Augmented Generation (RAG), Tool Learning, and sandbox environments. It transitions gradually from the traditional development and operations mode of querying information from various sources and operating on standalone, disparate platforms to an intelligent development and operations mode based on large-model Q&A, changing people's development and operations habits.

- 📚 Knowledge Base Management: Professional high-quality Codefuse knowledge base + enterprise-level knowledge base self-construction + dialogue-based fast retrieval of open-source/private technical documents.
- 🐳 Isolated Sandbox Environment: Enables quick compilation, execution, and testing of code.
- 🔄 React Paradigm: Supports code self-iteration and automatic execution.
- 🛠️ Prompt Management: Manages prompts for various development and operations tasks.
- 🚀 Conversation Driven: Automates requirement design, system analysis design, code generation, development testing, deployment, and operations.

🌍 Relying on open-source LLM and Embedding models, this project can achieve offline private deployments based on open-source models. Additionally, this project also supports the use of the OpenAI API.

👥 The core development team has been long-term focused on research in the AIOps + NLP domain. We initiated the CodefuseGPT project, hoping that everyone could contribute high-quality development and operations documents widely, jointly perfecting this solution to achieve the goal of "Making Development Seamless for Everyone."


<div align=center>
  <img src="sources/docs_imgs/objective_v4.png" alt="Image" width="600" height="333">
</div>

🌍 Relying on open-source LLM and Embedding models, this project can achieve offline private deployments based on open-source models. Additionally, this project also supports the use of the OpenAI API.

👥 The core development team has been long-term focused on research in the AIOps + NLP domain. We initiated the DevOpsGPT project, hoping that everyone could contribute high-quality development and operations documents widely, jointly perfecting this solution to achieve the goal of "Making Development Seamless for Everyone."

## 🧭 Technical Route
<div align=center>
  <img src="sources/docs_imgs/devops-chatbot-module.png" alt="Image" width="600" height="503">
</div>

- 🕷️ **Web Crawl**: Implements periodic web document crawling to ensure data timeliness and relies on continuous supplementation from the open-source community.
- 🗂️ **DocLoader & TextSplitter**: Cleans, deduplicates, and categorizes data crawled from various sources and supports the import of private documents.
- 🗄️ **Vector Database**: Integrates Text Embedding models to embed documents and store them in Milvus.
- 🔌 **Connector**: Acts as the scheduling center, responsible for coordinating interactions between LLM and Vector Database, implemented based on Langchain technology.
- 📝 **Prompt Control**: Designs from development and operations perspectives, categorizes different problems, and adds backgrounds to prompts to ensure the controllability and completeness of answers.
- 💬 **LLM**: Uses GPT-3.5-turbo by default and provides proprietary model options for private deployments and other privacy-related scenarios.
- 🔤 **Text Embedding**: Uses OpenAI's Text Embedding model by default, supports private deployments and other privacy-related scenarios, and provides proprietary model options.
- 🚧 **SandBox**: For generated outputs, like code, to help users judge their authenticity, an interactive verification environment is provided (based on FaaS), allowing user adjustments.

For implementation details, see: [Technical Route Details](sources/readme_docs/roadmap.md)


## 模型接入

有需要接入的model，可以提issue

|      model_name    | model_size | gpu_memory | quantize | HFhub | ModelScope |
| ------------------ | ---------- | ---------- | -------- | ----- | ---------- |
|        chatgpt     |    -       |    -       |     -    | -     | -          |
| codellama-34b-int4 |     34b    |    20g     |    int4  | coming soon| [link](https://modelscope.cn/models/codefuse-ai/CodeFuse-CodeLlama-34B-4bits/summary) |



## 🚀 Quick Start

Please install the Nvidia driver yourself; this project has been tested on Python 3.9.18, CUDA 11.7, Windows, and X86 architecture macOS systems.

1. Preparation of Python environment

- It is recommended to use conda to manage the python environment (optional)
```bash
# Prepare conda environment
conda create --name Codefusegpt python=3.9
conda activate Codefusegpt
```

- Install related dependencies
```bash
cd Codefuse-ChatBot
# python=3.9，use notebook-latest，python=3.8 use notebook==6.5.5
pip install -r requirements.txt
```

2. Preparation of Sandbox Environment
- Windows Docker installation:
[Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) supports 64-bit versions of Windows 10 Pro, with Hyper-V enabled (not required for versions v1903 and above), or 64-bit versions of Windows 10 Home v1903 and above.
  
  - [Comprehensive Detailed Windows 10 Docker Installation Tutorial](https://zhuanlan.zhihu.com/p/441965046)
  - [Docker: From Beginner to Practitioner](https://yeasy.gitbook.io/docker_practice/install/windows)
  - [Handling Docker Desktop requires the Server service to be enabled](https://blog.csdn.net/sunhy_csdn/article/details/106526991)
  - [Install wsl or wait for error prompt](https://learn.microsoft.com/en-us/windows/wsl/install)

- Linux Docker Installation:
Linux installation is relatively simple, please search Baidu/Google for installation instructions.

- Mac Docker Installation
  - [Docker: From Beginner to Practitioner](https://yeasy.gitbook.io/docker_practice/install/mac)

```bash
# Build images for the sandbox environment, see above for notebook version issues
bash docker_build.sh
```

3. Model Download (Optional)

If you need to use open-source LLM and Embed

ding models, you can download them from HuggingFace.
Here, we use THUDM/chatglm2-6b and text2vec-base-chinese as examples:

```
# install git-lfs
git lfs install

# install LLM-model
git lfs clone https://huggingface.co/THUDM/chatglm2-6b

# install Embedding-model
git lfs clone https://huggingface.co/shibing624/text2vec-base-chinese
```

4. Basic Configuration

```bash
# Modify the basic configuration for service startup
cd configs
cp model_config.py.example model_config.py
cp server_config.py.example server_config.py

# model_config#11~12 If you need to use the openai interface, openai interface key
os.environ["OPENAI_API_KEY"] = "sk-xxx"
# You can replace the api_base_url yourself
os.environ["API_BASE_URL"] = "https://api.openai.com/v1"

# vi model_config#95 You need to choose the language model
LLM_MODEL = "gpt-3.5-turbo"

# vi model_config#33 You need to choose the vector model
EMBEDDING_MODEL = "text2vec-base"

# vi model_config#19 Modify to your local path, if you can directly connect to huggingface, no modification is needed
"text2vec-base": "/home/user/xx/text2vec-base-chinese",

# Whether to start the local notebook for code interpretation, start the docker notebook by default
# vi server_config#35, True to start the docker notebook, false to start the local notebook
"do_remote": False,  /  "do_remote": True,
```

5. Start the Service

By default, only webui related services are started, and fastchat is not started (optional).
```bash
# if use codellama-34b-int4, you should replace fastchat's gptq.py
# cp examples/gptq.py ~/site-packages/fastchat/modules/gptq.py
# dev_opsgpt/service/llm_api.py#258 => kwargs={"gptq_wbits": 4},

# start llm-service（可选）
python dev_opsgpt/service/llm_api.py
```

```bash
cd examples
# python ../dev_opsgpt/service/llm_api.py If you need to use the local large language model, you can execute this command
bash start_webui.sh
```

## 🤗 Acknowledgements

This project is based on [langchain-chatchat](https://github.com/chatchat-space/Langchain-Chatchat) and [codebox-api](https://github.com/shroominic/codebox-api). We deeply appreciate their contributions to open source!