
## 简介
To enhance the performance of large language models (LLMs) in terms of inference accuracy, the industry has seen various innovative approaches to utilizing LLMs. From the earliest Chain of Thought (CoT), Text of Thought (ToT), to Graph of Thought (GoT), these methods have continually expanded the capability boundaries of LLMs. In dealing with complex problems, we can use the ReAct process to select, invoke, and execute tool feedback, achieving multi-round tool usage and multi-step execution.

However, for more complex scenarios, such as the development of intricate code, single-function LLM Agents are clearly insufficient. Thus, the community has begun to develop combinations of multiple Agents, such as projects focused on metaGPT, GPT-Engineer, chatDev in the development domain, and AutoGen projects focused on automating the construction of Agents and Agent dialogue.

After in-depth analysis of these frameworks, it has been found that most Agent frameworks are highly coupled, with poor usability and extensibility. They achieve specific scenarios in preset environments, but expanding these scenarios is fraught with difficulty.

Therefore, we aim to build an extensible, user-friendly Multi-Agent framework to support ChatBots in retrieving knowledge base information while assisting with various common tasks such as daily office work, data analysis, and development operations.

This Multi-Agent framework project incorporates excellent design elements from multiple frameworks, such as the message pool from metaGPT and the agent selector from autogen.

<div align=center>
  <img src="/sources/docs_imgs/luban.png" alt="图片">
</div>

The following modules will introduce the necessary components of the Multi Agent framework from five aspects:

- **Agent Communication:** In the Multi-Agent framework, ensuring effective information exchange among Agents is crucial for managing context and improving Q&A efficiency. 
  - Follow a straightforward and intuitive chain-based dialogue principle, arranging Agents in a linear fashion to form an execution chain. 
  - Drawing from the Message Pool framework in metaGPT, Agents are allowed to push and subscribe to the Message Pool, making the chain more flexible. This is beneficial for fine-tuning the scenario of Prompt engineering but challenging to manage complex chain relationship analysis.

- **Standard Operation Process (SOP)**: Standardizing the parsing and handling of LLM's generated results. 
  - Define the input and output scope of an Agent, assembling and parsing relevant Actions and Statuses to ensure the stability of the framework. 
  - Encapsulate a variety of fundamental Action execution modules, such as Tool Using, Planning, Coding, Direct Answering, final answer, etc., to meet the basic work requirements of an Agent.

- **Plan and Executor**: Enhance LLM's tool usage, Agent scheduling, and code generation. Several basic chains have been set up, for example: 
  - a. Single-round Q&A, which can also be expanded to forms like CoT, ToT, GoT, etc. 
  - b. ReAct, a basic response decision-making process where the model sets SOP status to terminate the loop. 
  - c. Task Planning - Executor, where the task is completed and can end.
- **Long-short term memory Management**: The key difference between Multi-Agent and single Agent is that Multi-Agent needs to handle a large amount of communication information, similar to the process of human teamwork collaboration. Add an Agent specifically responsible for content summarization (similar to a meeting assistant) to summarize long-term memories and provide more effective information to the next Agent, rather than passing all content to the next one.
- **Human-agent interaction**: In the face of complex scenarios, human intervention is required in the Agent interaction process to provide feedback. Through the aforementioned Long-short term memory Management and Agent Communication processes, enable the LLM to accurately understand human intentions, thereby completing tasks more effectively.

In summary, these five elements together construct a Multi-Agent framework, ensuring closer and more efficient cooperation between Agents while also adapting to more complex task requirements and a variety of interaction scenarios. By combining multiple Agent chains to implement a complete and complex project launch scenario (Dev Phase), such as Demand Chain (CEO), Product Argument Chain (CPO, CFO, CTO), Engineer Group Chain (Selector, Developer1~N), QA Engineer Chain (Developer, Tester), Deploy Chain (Developer, Deployer).

## 模块分类
- [connector](/sources/readme_docs/coagent/connector.md)
- document_loaders
- embeddings
- llm_models
- orm
- sandbox
- service
- text_splitter
- tools
- utils

