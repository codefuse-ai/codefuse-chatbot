
## 核心Connector介绍
为了便于大家理解整个 CoAgent 的链路，我们采取 Flow 的形式来详细介绍如何通过配置构建

<div align=center>
  <img src="/sources/docs_imgs/agent-flow.png" alt="图片">
</div>


<br>下面，我们先介绍相关的核心组件<br>

### Agent
在Agent设计层面，我们提供了四种基本的Agent类型，对这些Agent进行Role的基础设定，可满足多种通用场景的交互和使用
1. BaseAgent：提供基础问答、工具使用、代码执行的功能，根据Prompt格式实现 输入 => 输出

<div align=center>
  <img src="/sources/docs_imgs/BaseAgent.png" alt="图片" style="width: 500px;  height:auto;">
</div>

2. ExecutorAgent：对任务清单进行顺序执行，根据 User 或 上一个Agent编排的计划，完成相关任务
3. ReactAgent：提供标准React的功能，根据问题实现当前任务
4. SelectorAgent：提供选择Agent的功能，根据User 或 上一个 Agent的问题选择合适的Agent来进行回答.

输出后将 message push 到 memory pool 之中，后续通过Memory Manager进行管理

### Chain
基础链路：BaseChain，串联agent的交互，完成相关message和memory的管理

### Phase
基础场景：BasePhase，串联chain的交互，完成相关message和memory的管理

### Prompt Manager
Mutli-Agent链路中每一个agent的prompt创建
- 通过对promtp_input_keys和promtp_output_keys对的简单设定，可以沿用预设 Prompt Context 创建逻辑，从而实现agent prompt快速配置
- 也可以对prompt manager模块进行新的 key-context 设计，实现个性化的 Agent Prompt

### Memory Manager
主要用于 chat history 的管理，暂未完成
- 将chat history在数据库进行读写管理，包括user input、 llm output、doc retrieval、code retrieval、search retrieval
- 对 chat history 进行关键信息总结 summary context，作为 prompt context
- 提供检索功能，检索 chat history 或者 summary context 中与问题相关信息，辅助问答
