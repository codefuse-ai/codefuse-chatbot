<p align="left">
    <a>中文</a>&nbsp ｜ &nbsp<a href="README_en.md">English&nbsp </a>
</p>

# <p align="center">CodeFuse-ChatBot: Development by Private Knowledge Augmentation</p>

<p align="center">
    <a href="README.md"><img src="https://img.shields.io/badge/文档-中文版-yellow.svg" alt="ZH doc"></a>
    <a href="README_en.md"><img src="https://img.shields.io/badge/document-English-yellow.svg" alt="EN doc"></a>
    <img src="https://img.shields.io/github/license/codefuse-ai/codefuse-chatbot" alt="License">
    <a href="https://github.com/codefuse-ai/codefuse-chatbot/issues">
      <img alt="Open Issues" src="https://img.shields.io/github/issues-raw/codefuse-ai/codefuse-chatbot" />
    </a>
    <br><br>
</p>

DevOps-ChatBot是由蚂蚁CodeFuse团队开发的开源AI智能助手，致力于简化和优化软件开发生命周期中的各个环节。该项目结合了Multi-Agent的协同调度机制，并集成了丰富的工具库、代码库、知识库和沙盒环境，使得LLM模型能够在DevOps领域内有效执行和处理复杂任务。


## 🔔 更新
- [2024.01.29] 开放可配置化的multi-agent框架：coagent，详情见[使用说明](sources/readme_docs/coagent/coagent.md)
- [2023.12.26] 基于FastChat接入开源私有化大模型和大模型接口的能力开放
- [2023.12.14] 量子位公众号专题报道：[文章链接](https://mp.weixin.qq.com/s/MuPfayYTk9ZW6lcqgMpqKA)
- [2023.12.01] Multi-Agent和代码库检索功能开放
- [2023.11.15] 增加基于本地代码库的问答增强模式
- [2023.09.15] 本地/隔离环境的沙盒功能开放，基于爬虫实现指定url知识检索

## 📜 目录
- [🤝 介绍](#-介绍)
- [🎥 演示视频](#-演示视频)
- [🧭 技术路线](#-技术路线)
- [🌐 模型接入](#-模型接入)
- [🚀 快速使用](#-快速使用)
- [🤗 致谢](#-致谢)
- [🗂 其他](#-其他)
  - [📱 联系我们](#-联系我们)
  - [✨ 点赞历史](#-点赞历史)

## 🤝 介绍

💡 本项目旨在通过检索增强生成（Retrieval Augmented Generation，RAG）、工具学习（Tool Learning）和沙盒环境来构建软件开发全生命周期的AI智能助手，涵盖设计、编码、测试、部署和运维等阶段。 逐渐从各处资料查询、独立分散平台操作的传统开发运维模式转变到大模型问答的智能化开发运维模式，改变人们的开发运维习惯。

本项目核心差异技术、功能点：
- **🧠 智能调度核心：** 构建了体系链路完善的调度核心，支持多模式一键配置，简化操作流程。 [使用说明](sources/readme_docs/coagent/coagent.md)
- **💻 代码整库分析：** 实现了仓库级的代码深入理解，以及项目文件级的代码编写与生成，提升了开发效率。
- **📄 文档分析增强：** 融合了文档知识库与知识图谱，通过检索和推理增强，为文档分析提供了更深层次的支持。
- **🔧 垂类专属知识：** 为DevOps领域定制的专属知识库，支持垂类知识库的自助一键构建，便捷实用。
- **🤖 垂类模型兼容：** 针对DevOps领域的小型模型，保证了与DevOps相关平台的兼容性，促进了技术生态的整合。

🌍 依托于开源的 LLM 与 Embedding 模型，本项目可实现基于开源模型的离线私有部署。此外，本项目也支持 OpenAI API 的调用。[接入Demo](sources/readme_docs/fastchat.md)

👥 核心研发团队长期专注于 AIOps + NLP 领域的研究。我们发起了 Codefuse-ai 项目，希望大家广泛贡献高质量的开发和运维文档，共同完善这套解决方案，以实现“让天下没有难做的开发”的目标。

<div align=center>
  <img src="sources/docs_imgs/objective_v4.png" alt="图片" width="600" height="333">
</div>


## 🎥 演示视频

为了帮助您更直观地了解 Codefuse-ChatBot 的功能和使用方法，我们录制了一系列演示视频。您可以通过观看这些视频，快速了解本项目的主要特性和操作流程。


- 知识库导入和问答：[演示视频](https://www.youtube.com/watch?v=UGJdTGaVnNY&t=2s&ab_channel=HaotianZhu)
- 本地代码库导入和问答：[演示视频](https://www.youtube.com/watch?v=ex5sbwGs3Kg)


## 🧭 技术路线
<div align=center>
  <img src="sources/docs_imgs/devops-chatbot-module-v2.png" alt="图片" width="600" height="503">
</div>

- 🧠 **Multi-Agent Schedule Core:** 多智能体调度核心，简易配置即可打造交互式智能体。
- 🕷️ **Multi Source Web Crawl:** 多源网络爬虫，提供对指定 URL 的爬取功能，以搜集所需信息。
- 🗂️ **Data Processor:** 数据处理器，轻松完成文档载入、数据清洗，及文本切分，整合不同来源的数据。
- 🔤 **Text Embedding & Index:**：文本嵌入索引，用户可以轻松上传文件进行文档检索，优化文档分析过程。
- 🗄️ **Vector Database & Graph Database:** 向量与图数据库，提供灵活强大的数据管理解决方案。
- 📝 **Prompt Control & Management:**：Prompt 控制与管理，精确定义智能体的上下文环境。
- 🚧 **SandBox:**：沙盒环境，安全地执行代码编译和动作。
- 💬 **LLM:**：智能体大脑，支持多种开源模型和 LLM 接口。
- 🛠️ **API Management:：** API 管理工具，实现对开源组件和运维平台的快速集成。

具体实现明细见：[技术路线明细](sources/readme_docs/roadmap.md)



## 🌐 模型接入

如果您需要集成特定的模型，请通过提交issue来告知我们您的需求。

|      model_name    | model_size | gpu_memory | quantize | HFhub | ModelScope |
| ------------------ | ---------- | ---------- | -------- | ----- | ---------- |
|        chatgpt     |    -       |    -       |     -    | -     | -          |
| codellama-34b-int4 |     34b    |    20g     |    int4  | coming soon| [link](https://modelscope.cn/models/codefuse-ai/CodeFuse-CodeLlama-34B-4bits/summary) |



## 🚀 快速使用
### coagent-py
完整文档见：[coagent](sources/readme_docs/coagent/coagent.md)
```
pip install coagent
```

### 使用ChatBot
请自行安装 nvidia 驱动程序，本项目已在 Python 3.9.18，CUDA 11.7 环境下，Windows、X86 架构的 macOS 系统中完成测试。

Docker安装、私有化LLM接入及相关启动问题见：[快速使用明细](sources/readme_docs/start.md)

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

2、启动服务
```bash
# 完成server_config.py配置后，可一键启动
cd examples
bash start.sh
# 开始在页面进行配置即可
```
<div align=center>
  <img src="sources/docs_imgs/webui_config.png" alt="图片">
</div>


或者通过`start.py`进行启动[老版启动方式](sources/readme_docs/start.md)
更多LLM接入方法见[更多细节...](sources/readme_docs/fastchat.md)
<br>


## 贡献指南
非常感谢您对 Codefuse 项目感兴趣，我们非常欢迎您对 Codefuse 项目的各种建议、意见（包括批评）、评论和贡献。

您对 Codefuse 的各种建议、意见、评论可以直接通过 GitHub 的 Issues 提出。

参与 Codefuse 项目并为其作出贡献的方法有很多：代码实现、测试编写、流程工具改进、文档完善等等。任何贡献我们都会非常欢迎，并将您加入贡献者列表。详见[Contribution Guide...](sources/readme_docs/contribution/contribute_guide.md)

## 🤗 致谢

本项目基于[langchain-chatchat](https://github.com/chatchat-space/Langchain-Chatchat)和[codebox-api](https://github.com/shroominic/codebox-api)，在此深深感谢他们的开源贡献！

## 🗂 其他

### 📱 联系我们
<div align=center>
  <img src="sources/docs_imgs/wechat.png" alt="图片", width="360">
</div>

### ✨ 点赞历史
[![Star History Chart](https://api.star-history.com/svg?repos=codefuse-ai/codefuse-chatbot&type=Date)](https://star-history.com/#codefuse-ai/codefuse-chatbot&Date)
