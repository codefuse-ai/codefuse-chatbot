<p align="left">
    <a href="README.md">中文</a>&nbsp ｜ &nbsp<a>English&nbsp </a>
</p>

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
This project is an open-source AI intelligent assistant, specifically designed for the entire lifecycle of software development, covering design, coding, testing, deployment, and operations. Through knowledge retrieval, tool utilization, and sandbox execution, Codefuse-ChatBot can not only answer professional questions you encounter during the development process but also coordinate multiple independent, dispersed platforms through a conversational interface.


## 🔔 Updates
- [2024.01.29] A configurational multi-agent framework, codefuse-muagent, has been open-sourced. For more details, please refer to [codefuse-muagent](https://codefuse-ai.github.io/docs/api-docs/MuAgent/overview/multi-agent)
- [2023.12.26] Opening the capability to integrate with open-source private large models and large model interfaces based on FastChat
- [2023.12.01] Release of Multi-Agent and codebase retrieval functionalities.
- [2023.11.15] Addition of Q&A enhancement mode based on the local codebase.
- [2023.09.15] Launch of sandbox functionality for local/isolated environments, enabling knowledge retrieval from specified URLs using web crawlers.

## 📜 Contents
- [🤝 Introduction](#-introduction)
- [🧭 Technical Route](#-technical-route)
- [🌐 Model Integration](#-model-integration)
- [🚀 Quick Start](#-quick-start)
- [🤗 Acknowledgements](#-acknowledgements)

## 🤝 Introduction

💡 The aim of this project is to construct an AI intelligent assistant for the entire lifecycle of software development, covering design, coding, testing, deployment, and operations, through Retrieval Augmented Generation (RAG), Tool Learning, and sandbox environments. It transitions gradually from the traditional development and operations mode of querying information from various sources and operating on standalone, disparate platforms to an intelligent development and operations mode based on large-model Q&A, changing people's development and operations habits.

- **🧠 Intelligent Scheduling Core:** Constructed a well-integrated scheduling core system that supports multi-mode one-click configuration, simplifying the operational process. [codefuse-muagent](https://codefuse-ai.github.io/docs/api-docs/MuAgent/overview/multi-agent)
- **💻 Comprehensive Code Repository Analysis:** Achieved in-depth understanding at the repository level and coding and generation at the project file level, enhancing development efficiency.
- **📄 Enhanced Document Analysis:** Integrated document knowledge bases with knowledge graphs, providing deeper support for document analysis through enhanced retrieval and reasoning.
- **🔧 Industry-Specific Knowledge:** Tailored a specialized knowledge base for the DevOps domain, supporting the self-service one-click construction of industry-specific knowledge bases for convenience and practicality.
- **🤖 Compatible Models for Specific Verticals:** Designed small models specifically for the DevOps field, ensuring compatibility with related DevOps platforms and promoting the integration of the technological ecosystem.

🌍 Relying on open-source LLM and Embedding models, this project can achieve offline private deployments based on open-source models. Additionally, this project also supports the use of the OpenAI API.[Access Demo](https://codefuse-ai.github.io/docs/developer-docs/CodeFuse-ChatBot/master/fastchat)

👥 The core development team has been long-term focused on research in the AIOps + NLP domain. We initiated the CodefuseGPT project, hoping that everyone could contribute high-quality development and operations documents widely, jointly perfecting this solution to achieve the goal of "Making Development Seamless for Everyone."


<div align=center>
  <img src="sources/docs_imgs/objective_v4.png" alt="Image" width="600" height="333">
</div>

🌍 Relying on open-source LLM and Embedding models, this project can achieve offline private deployments based on open-source models. Additionally, this project also supports the use of the OpenAI API.

👥 The core development team has been long-term focused on research in the AIOps + NLP domain. We initiated the DevOpsGPT project, hoping that everyone could contribute high-quality development and operations documents widely, jointly perfecting this solution to achieve the goal of "Making Development Seamless for Everyone."

## 🧭 Technical Route
<div align=center>
  <img src="sources/docs_imgs/devops-chatbot-module-v2.png" alt="Image" width="600" height="503">
</div>

- 🧠 **Multi-Agent Schedule Core:** Easily configurable to create interactive intelligent agents.
- 🕷️ **Multi Source Web Crawl:** Offers the capability to crawl specified URLs for collecting the required information.
- 🗂️ **Data Processor:** Effortlessly handles document loading, data cleansing, and text segmentation, integrating data from different sources.
- 🔤 **Text Embedding & Index:**：Users can easily upload files for document retrieval, optimizing the document analysis process.
- 🗄️ **Vector Database & Graph Database:** Provides flexible and powerful data management solutions.
- 📝 **Prompt Control & Management:**：Precisely defines the contextual environment for intelligent agents.
- 🚧 **SandBox:**：Safely executes code compilation and actions.
- 💬 **LLM:**：Supports various open-source models and LLM interfaces.
- 🛠️ **API Management:：** Enables rapid integration of open-source components and operational platforms.

For implementation details, see: [Technical Route Details](https://codefuse-ai.github.io/docs/developer-docs/CodeFuse-ChatBot/master/roadmap)
Follow Projects：[Projects](https://github.com/orgs/codefuse-ai/projects/1)

## 🌐 Model Integration

If you need to integrate a specific model, please inform us of your requirements by submitting an issue.

|      model_name    | model_size | gpu_memory | quantize | HFhub | ModelScope |
| ------------------ | ---------- | ---------- | -------- | ----- | ---------- |
|        chatgpt     |    -       |    -       |     -    | -     | -          |
| codellama-34b-int4 |     34b    |    20g     |    int4  | coming soon| [link](https://modelscope.cn/models/codefuse-ai/CodeFuse-CodeLlama-34B-4bits/summary) |



## 🚀 Quick Start
### muagent-py
More Detail see：[codefuse-muagent](https://codefuse-ai.github.io/docs/api-docs/MuAgent/overview/multi-agent)
```
pip install codefuse-muagent
```

### ChatBot-UI
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

2. Start the Service
```bash
# After configuring server_config.py, you can start with just one click.
cd examples
bash start.sh
# you can config your llm model and embedding model, then choose the "启动对话服务"
```
<div align=center>
  <img src="sources/docs_imgs/webui_config.png" alt="图片">
</div>

Or `python start.py` by [old version to start](https://codefuse-ai.github.io/docs/developer-docs/CodeFuse-ChatBot/master/start-detail)
More details about accessing LLM Moldes[More Details...](https://codefuse-ai.github.io/docs/developer-docs/CodeFuse-ChatBot/master/fastchat)
<br>

## Contribution
Thank you for your interest in the Codefuse project. We warmly welcome any suggestions, opinions (including criticisms), comments, and contributions to the Codefuse project.

Your suggestions, opinions, and comments on Codefuse can be directly submitted through GitHub Issues.

There are many ways to participate in the Codefuse project and contribute to it: code implementation, test writing, process tool improvement, documentation enhancement, and more. We welcome any contributions and will add you to our list of contributors. See [contribution guide](https://codefuse-ai.github.io/contribution/contribution)

## 🤗 Acknowledgements

This project is based on [langchain-chatchat](https://github.com/chatchat-space/Langchain-Chatchat) and [codebox-api](https://github.com/shroominic/codebox-api). We deeply appreciate their contributions to open source!