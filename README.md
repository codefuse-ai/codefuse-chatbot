# <p align="center">Codefuse-ChatBot: Development by Private Knowledge Augmentation</p>

<p align="center">
    <a href="README.md"><img src="https://img.shields.io/badge/文档-中文版-yellow.svg" alt="ZH doc"></a>
    <a href="README_en.md"><img src="https://img.shields.io/badge/document-英文版-yellow.svg" alt="EN doc"></a>
    <img src="https://img.shields.io/github/license/codefuse-ai/codefuse-chatbot" alt="License">
    <a href="https://github.com/codefuse-ai/codefuse-chatbot/issues">
      <img alt="Open Issues" src="https://img.shields.io/github/issues-raw/codefuse-ai/codefuse-chatbot" />
    </a>
    <br><br>
</p>

本项目是一个开源的 AI 智能助手，专为软件开发的全生命周期而设计，涵盖设计、编码、测试、部署和运维等阶段。通过知识检索、工具使用和沙箱执行，Codefuse-ChatBot 能解答您开发过程中的各种专业问题、问答操作周边独立分散平台。


## 🔔 更新
- [2023.09.15] 本地/隔离环境的沙盒功能开放，基于爬虫实现指定url知识检索

## 📜 目录
- [🤝 介绍](#-介绍)
- [🎥 演示视频](#-演示视频)
- [🧭 技术路线](#-技术路线)
- [🌐 模型接入](#-模型接入)
- [🚀 快速使用](#-快速使用)
- [🤗 致谢](#-致谢)

## 🤝 介绍

💡 本项目旨在通过检索增强生成（Retrieval Augmented Generation，RAG）、工具学习（Tool Learning）和沙盒环境来构建软件开发全生命周期的AI智能助手，涵盖设计、编码、测试、部署和运维等阶段。 逐渐从各处资料查询、独立分散平台操作的传统开发运维模式转变到大模型问答的智能化开发运维模式，改变人们的开发运维习惯。

- 📚 知识库管理：DevOps专业高质量知识库 + 企业级知识库自助构建 + 对话实现快速检索开源/私有技术文档
- 🐳 隔离沙盒环境：实现代码的快速编译执行测试
- 🔄 React范式：支撑代码的自我迭代、自动执行
- 🛠️ Prompt管理：实现各种开发、运维任务的prompt管理
- 🔌 丰富的领域插件：执行各种定制开发任务
- 🚀 对话驱动：需求设计、系分设计、代码生成、开发测试、部署运维自动化

🌍 依托于开源的 LLM 与 Embedding 模型，本项目可实现基于开源模型的离线私有部署。此外，本项目也支持 OpenAI API 的调用。

👥 核心研发团队长期专注于 AIOps + NLP 领域的研究。我们发起了 Codefuse-ai 项目，希望大家广泛贡献高质量的开发和运维文档，共同完善这套解决方案，以实现“让天下没有难做的开发”的目标。

<div align=center>
  <img src="sources/docs_imgs/objective_v4.png" alt="图片" width="600" height="333">
</div>


## 🎥 演示视频

为了帮助您更直观地了解 Codefuse-ChatBot 的功能和使用方法，我们录制了一个演示视频。您可以通过观看此视频，快速了解本项目的主要特性和操作流程。


[演示视频](https://www.youtube.com/watch?v=UGJdTGaVnNY&t=2s&ab_channel=HaotianZhu)


## 🧭 技术路线
<div align=center>
  <img src="sources/docs_imgs/devops-chatbot-module.png" alt="图片" width="600" height="503">
</div>

- 🕷️ **Web Crawl**：实现定期网络文档爬取，确保数据的及时性，并依赖于开源社区的持续补充。
- 🗂️ **DocLoader & TextSplitter**：对从多种来源爬取的数据进行数据清洗、去重和分类，并支持私有文档的导入。
- 🗄️ **Vector Database**：结合Text Embedding模型对文档进行Embedding并在Milvus中存储。
- 🔌 **Connector**：作为调度中心，负责LLM与Vector Database之间的交互调度，基于Langchain技术实现。
- 📝 **Prompt Control**：从开发和运维角度设计，为不同问题分类并为Prompt添加背景，确保答案的可控性和完整性。
- 💬 **LLM**：默认使用GPT-3.5-turbo，并为私有部署和其他涉及隐私的场景提供专有模型选择。
- 🔤 **Text Embedding**：默认采用OpenAI的Text Embedding模型，支持私有部署和其他隐私相关场景，并提供专有模型选择。
- 🚧 **SandBox**：对于生成的输出，如代码，为帮助用户判断其真实性，提供了一个交互验证环境（基于FaaS），并支持用户进行调整。


具体实现明细见：[技术路线明细](sources/readme_docs/roadmap.md)



## 模型接入

有需要接入的model，可以提issue

|      model_name    | model_size | gpu_memory | quantize | HFhub | ModelScope |
| ------------------ | ---------- | ---------- | -------- | ----- | ---------- |
|        chatgpt     |    -       |    -       |     -    | -     | -          |
| codellama-34b-int4 |     34b    |    20g     |    int4  | coming soon| [link](https://modelscope.cn/models/codefuse-ai/CodeFuse-CodeLlama-34B-4bits/summary) |



## 🚀 快速使用

请自行安装 nvidia 驱动程序，本项目已在 Python 3.9.18，CUDA 11.7 环境下，Windows、X86 架构的 macOS 系统中完成测试。

1、python 环境准备

- 推荐采用 conda 对 python 环境进行管理（可选）
```bash
# 准备 conda 环境
conda create --name devopsgpt python=3.9
conda activate devopsgpt
```

- 安装相关依赖
```bash
cd codefuse-chatbot
# python=3.9，notebook用最新即可，python=3.8用notebook=6.5.6
pip install -r requirements.txt
```

2、沙盒环境准备
- windows Docker 安装：
[Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) 支持 64 位版本的 Windows 10 Pro，且必须开启 Hyper-V（若版本为 v1903 及以上则无需开启 Hyper-V），或者 64 位版本的 Windows 10 Home v1903 及以上版本。

  - [【全面详细】Windows10 Docker安装详细教程](https://zhuanlan.zhihu.com/p/441965046)
  - [Docker 从入门到实践](https://yeasy.gitbook.io/docker_practice/install/windows)
  - [Docker Desktop requires the Server service to be enabled 处理](https://blog.csdn.net/sunhy_csdn/article/details/106526991)
  - [安装wsl或者等报错提示](https://learn.microsoft.com/zh-cn/windows/wsl/install)

- Linux Docker 安装：
Linux 安装相对比较简单，请自行 baidu/google 相关安装

- Mac Docker 安装
  - [Docker 从入门到实践](https://yeasy.gitbook.io/docker_practice/install/mac)

```bash
# 构建沙盒环境的镜像，notebook版本问题见上述
bash docker_build.sh
```

3、模型下载（可选）

如需使用开源 LLM 与 Embedding 模型可以从 HuggingFace 下载。
此处以 THUDM/chatglm2-6bm 和 text2vec-base-chinese 为例：

```
# install git-lfs
git lfs install

# install LLM-model
git lfs clone https://huggingface.co/THUDM/chatglm2-6b

# install Embedding-model
git lfs clone https://huggingface.co/shibing624/text2vec-base-chinese
```


4、基础配置

```bash
# 修改服务启动的基础配置
cd configs
cp model_config.py.example model_config.py
cp server_config.py.example server_config.py

# model_config#11~12 若需要使用openai接口，openai接口key
os.environ["OPENAI_API_KEY"] = "sk-xxx"
# 可自行替换自己需要的api_base_url
os.environ["API_BASE_URL"] = "https://api.openai.com/v1"

# vi model_config#95 你需要选择的语言模型
LLM_MODEL = "gpt-3.5-turbo"

# vi model_config#33 你需要选择的向量模型
EMBEDDING_MODEL = "text2vec-base"

# vi model_config#19 修改成你的本地路径，如果能直接连接huggingface则无需修改
"text2vec-base": "/home/user/xx/text2vec-base-chinese",

# 是否启动本地的notebook用于代码解释，默认启动docker的notebook
# vi server_config#35，True启动docker的notebook，false启动local的notebook
"do_remote": False,  /  "do_remote": True,
```

5、启动服务

默认只启动webui相关服务，未启动fastchat（可选）。
```bash
# 若需要支撑codellama-34b-int4模型，需要给fastchat打一个补丁
# cp examples/gptq.py ~/site-packages/fastchat/modules/gptq.py
# dev_opsgpt/service/llm_api.py#258 修改为 kwargs={"gptq_wbits": 4},

# start llm-service（可选）
python dev_opsgpt/service/llm_api.py
```

```bash
cd examples
# python ../dev_opsgpt/service/llm_api.py 若需使用本地大语言模型，可执行该命令
bash start_webui.sh
```

## 🤗 致谢

本项目基于[langchain-chatchat](https://github.com/chatchat-space/Langchain-Chatchat)和[codebox-api](https://github.com/shroominic/codebox-api)，在此深深感谢他们的开源贡献！
