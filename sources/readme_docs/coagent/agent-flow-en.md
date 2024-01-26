
## Introduction to Core Connectors
To facilitate everyone's understanding of the entire CoAgent link, we use a Flow format to detail how to build through configuration settings.

<div align=center>
  <img src="/sources//docs_imgs/agent-flow.png" alt="图片">
</div>


<br>Below, we will first introduce the related core components<br>

### Agent
At the design level of the Agent, we provide four basic types of Agents, which allows for the basic role settings of these Agents to meet the interaction and usage of a variety of common scenarios.
1. BaseAgent: Provides basic question and answer, tool usage, and code execution functions. It implements Input => Output according to the Prompt format.

<div align=center>
  <img src="/sources//docs_imgs/BaseAgent.png" alt="图片" style="width: 500px;  height:auto;">
</div>

2. ExecutorAgent: Executes tasks in sequence from a task list based on the plan arranged by the User or the previous Agent, completing the related tasks.
3. ReactAgent: Provides standard React functionality, based on the issue to perform the current task.
4. electorAgent: Provides the functionality of choosing an Agent. 

It selects the appropriate Agent to respond based on the question from the User or the previous Agent. After output, the message is pushed into the memory pool, which is subsequently managed by the Memory Manager.

### Chain
Basic Chain: BaseChain, which connects the interaction of agents, completing the management of related messages and memory.

### Phase
Basic Phase: BasePhase, which connects the interaction of chains, completing the management of related messages and memory.

### Prompt Manager
Creation of prompts for each agent in a Multi-Agent link:

- By simply setting prompt_input_keys and prompt_output_keys, one can reuse the preset Prompt Context creation logic, thus achieving rapid configuration of the agent prompt.
- The prompt manager module can also be redesigned with new key-context designs to implement a personalized Agent Prompt.

### Memory Manager
Mainly used for the management of chat history, which is not yet completed:

- Manages the reading and writing of chat history in the database, including user input, llm output, doc retrieval, code retrieval, search retrieval.
- Summarizes key information from the chat history to form a summary context, which serves as prompt context.
- Provides a search function to retrieve information related to the question from the chat history or the summary context, aiding in question and answer sessions.
