import asyncio
from typing import List

from langchain import LLMChain
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.prompts.chat import ChatPromptTemplate
from langchain.agents import AgentType, initialize_agent

from dev_opsgpt.tools import (
    WeatherInfo, WorldTimeGetTimezoneByArea, Multiplier,
    toLangchainTools, get_tool_schema
    )
from .utils import History, wrap_done
from .base_chat import Chat
from loguru import logger
import json, re

from dev_opsgpt.sandbox import PyCodeBox, CodeBoxResponse
from configs.server_config import SANDBOX_SERVER

def get_tool_agent(tools, llm):
    return initialize_agent(
        tools,
        llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
    )

PROMPT_TEMPLATE = """
`角色`
你是一个数据分析师，借鉴下述步骤，逐步完成数据分析任务的拆解和代码编写，尽可能帮助和准确地回答用户的问题。

数据文件的存放路径为 `./`

`数据分析流程`
- 判断文件是否存在，并读取文件数据
- 输出数据的基本信息，包括但不限于字段、文本、数据类型等
- 输出数据的详细统计信息
- 判断是否需要画图分析，选择合适的字段进行画图
- 判断数据是否需要进行清洗
- 判断数据或图片是否需要保存
...
- 结合数据统计分析结果和画图结果，进行总结和分析这份数据的价值

`要求`
- 每轮选择一个数据分析流程，需要综合考虑上轮和后续的可能影响
- 数据分析流程只提供参考，不要拘泥于它的具体流程，要有自己的思考
- 使用JSON blob来指定一个计划，通过提供task_status关键字（任务状态）、plan关键字（数据分析计划）和code关键字（可执行代码）。

合法的 "task_status" 值: "finished" 表明当前用户问题已被准确回答 或者 "continued" 表明用户问题仍需要进一步分析
 
`$JSON_BLOB如下所示`
```
{{
  "task_status": $TASK_STATUS,
  "plan": $PLAN,
  "code": ```python\n$CODE```
}}
```

`跟随如下示例`
问题: 输入待回答的问题
行动：$JSON_BLOB

... (重复 行动 N 次，每次只生成一个行动)

行动:
```
{{
  "task_status": "finished",
  "plan": 我已经可以回答用户问题了，最后回答用户的内容
}}

```

`数据分析，开始`

问题：{query}
"""


PROMPT_TEMPLATE_2 = """
`角色`
你是一个数据分析师，借鉴下述步骤，逐步完成数据分析任务的拆解和代码编写，尽可能帮助和准确地回答用户的问题。

数据文件的存放路径为 `./`

`数据分析流程`
- 判断文件是否存在，并读取文件数据
- 输出数据的基本信息，包括但不限于字段、文本、数据类型等
- 输出数据的详细统计信息
- 判断数据是否需要进行清洗
- 判断是否需要画图分析，选择合适的字段进行画图
- 判断清洗后数据或图片是否需要保存
...
- 结合数据统计分析结果和画图结果，进行总结和分析这份数据的价值

`要求`
- 每轮选择一个数据分析流程，需要综合考虑上轮和后续的可能影响
- 数据分析流程只提供参考，不要拘泥于它的具体流程，要有自己的思考
- 使用JSON blob来指定一个计划，通过提供task_status关键字（任务状态）、plan关键字（数据分析计划）和code关键字（可执行代码）。

合法的 "task_status" 值: "finished" 表明当前用户问题已被准确回答 或者 "continued" 表明用户问题仍需要进一步分析
 
`$JSON_BLOB如下所示`
```
{{
  "task_status": $TASK_STATUS,
  "plan": $PLAN,
  "code": ```python\n$CODE```
}}
```

`跟随如下示例`
问题: 输入待回答的问题
行动：$JSON_BLOB

... (重复 行动 N 次，每次只生成一个行动)

行动:
```
{{
  "task_status": "finished",
  "plan": 我已经可以回答用户问题了，最后回答用户的内容
}}

`数据分析，开始`

问题：上传了一份employee_data.csv文件，请对它进行数据分析

问题：{query}
{history}

"""

class DataChat(Chat):

    def __init__(
            self,
            engine_name: str = "",
            top_k: int = 1,
            stream: bool = False,
            ) -> None:
        super().__init__(engine_name, top_k, stream)
        self.tool_prompt = """结合上下文信息，{tools} {input}"""
        self.codebox = PyCodeBox(
            remote_url=SANDBOX_SERVER["url"],
            remote_ip=SANDBOX_SERVER["host"], # "http://localhost",
            remote_port=SANDBOX_SERVER["port"],
            token="mytoken",
            do_code_exe=True,
            do_remote=SANDBOX_SERVER["do_remote"]
            )

    def create_task(self, query: str, history: List[History], model):
        '''构建 llm 生成任务'''
        logger.debug("content:{}".format([i.to_msg_tuple() for i in history] + [("human", PROMPT_TEMPLATE)]))
        chat_prompt = ChatPromptTemplate.from_messages(
            [i.to_msg_tuple() for i in history] + [("human", PROMPT_TEMPLATE)]
        )
        pattern = re.compile(r"```(?:json)?\n(.*?)\n", re.DOTALL)
        internal_history = []
        retry_nums = 2
        while retry_nums >= 0:
            if len(internal_history) == 0:
                chat_prompt = ChatPromptTemplate.from_messages(
                    [i.to_msg_tuple() for i in history] + [("human", PROMPT_TEMPLATE)]
                )
            else:
                chat_prompt = ChatPromptTemplate.from_messages(
                    [i.to_msg_tuple() for i in history] + [("human", PROMPT_TEMPLATE_2)]
                )
                
            chain = LLMChain(prompt=chat_prompt, llm=model)
            content = chain({"query": query, "history": "\n".join(internal_history)})["text"]

            # content = pattern.search(content)
            # logger.info(f"content: {content}")
            # content = json.loads(content.group(1).strip(), strict=False)

            internal_history.append(f"{content}")
            refer_info = "\n".join(internal_history)
            logger.info(f"refer_info: {refer_info}")
            try:
                content = content.split("行动:")[-1].split("行动：")[-1]
                content = json.loads(content)
            except:
                content = content.split("行动:")[-1].split("行动：")[-1]
                content = eval(content)

            if "finished" == content["task_status"]:
                break
            elif "code" in content:
            # elif "```code" in content or "```python" in content:
                # code_text = self.codebox.decode_code_from_text(content)
                code_text = content["code"]
                codebox_res = self.codebox.chat("```"+code_text+"```", do_code_exe=True)

                if codebox_res is not None and codebox_res.code_exe_status != 200:
                    logger.warning(f"{codebox_res.code_exe_response}")
                    internal_history.append(f"观察： 根据这个报错信息 {codebox_res.code_exe_response}，进行代码修复")

                if codebox_res is not None and codebox_res.code_exe_status == 200:
                    if codebox_res.code_exe_type == "image/png":
                        base_text = f"```\n{code_text}\n```\n\n"
                        img_html = "<img src='data:image/png;base64,{}' class='img-fluid'>".format(
                            codebox_res.code_exe_response
                        )
                        internal_history.append(f"观察： {img_html}")
                        # logger.info('```\n'+code_text+'\n```'+"\n\n"+'```\n'+codebox_res.code_exe_response+'\n```')
                    else:
                        internal_history.append(f"观察： {codebox_res.code_exe_response}")
                        # logger.info('```\n'+code_text+'\n```'+"\n\n"+'```\n'+codebox_res.code_exe_response+'\n```')
            else:
                internal_history.append(f"观察：下一步应该怎么做？")
            retry_nums -= 1


        return {"answer": "", "docs": ""}, {"text": "\n".join(internal_history)}

    def create_atask(self, query, history, model, callback: AsyncIteratorCallbackHandler):
        chat_prompt = ChatPromptTemplate.from_messages(
            [i.to_msg_tuple() for i in history] + [("human", PROMPT_TEMPLATE)]
        )
        chain = LLMChain(prompt=chat_prompt, llm=model)
        task = asyncio.create_task(wrap_done(
            chain.acall({"input": query}), callback.done
        ))
        return task, {"answer": "", "docs": ""}