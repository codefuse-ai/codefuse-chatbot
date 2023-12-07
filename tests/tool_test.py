

from langchain.agents import initialize_agent, Tool
from langchain.tools import format_tool_to_openai_function, MoveFileTool, StructuredTool
from pydantic import BaseModel, Field, create_model
from pydantic.schema import model_schema, get_flat_models_from_fields
from typing import List, Set
import jsonref
import json

import os, sys, requests

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(src_dir)

from dev_opsgpt.tools import (
    WeatherInfo, WorldTimeGetTimezoneByArea, Multiplier, KSigmaDetector,
    toLangchainTools, get_tool_schema,
    TOOL_DICT, TOOL_SETS
    )
from configs.model_config import (llm_model_dict, LLM_MODEL, VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD)

from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentType, initialize_agent
import langchain

# langchain.debug = True

tools = toLangchainTools([WeatherInfo, Multiplier, KSigmaDetector])

llm = ChatOpenAI(
            streaming=True,
            verbose=True,
            openai_api_key=llm_model_dict[LLM_MODEL]["api_key"],
            openai_api_base=llm_model_dict[LLM_MODEL]["api_base_url"],
            model_name=LLM_MODEL
        )

chat_prompt = '''if you can 
tools: {tools}
query: {query}

if you choose llm-tool, you can direct 
'''
# chain = LLMChain(prompt=chat_prompt, llm=llm)
#         content = chain({"tools": tools, "input": query})

# tool的检索

# tool参数的填充

# 函数执行

# from langchain.tools import StructuredTool

tools =  [
    StructuredTool(
            name=Multiplier.name,
            func=Multiplier.run,
            description=Multiplier.description,
            args_schema=Multiplier.ToolInputArgs,
        ), 
        StructuredTool(
            name=WeatherInfo.name,
            func=WeatherInfo.run,
            description=WeatherInfo.description,
            args_schema=WeatherInfo.ToolInputArgs,
        )
        ]

print(tools[0].func(1,2))


tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    return_intermediate_steps=True
)


# from dev_opsgpt.utils.common_utils import read_json_file
# stock_name = read_json_file("../sources/stock.json")
from dev_opsgpt.tools.ocr_tool import BaiduOcrTool

print(BaiduOcrTool.run("D:/chromeDownloads/devopschat-bot/ocr_figure.png"))

# agent.return_intermediate_steps = True
# content = agent.run("查询北京的行政编码，同时返回北京的天气情况")
# print(content)

# content = agent.run("判断这份数据是否存在异常，[0.857, 2.345, 1.234, 4.567, 3.456, 9.876, 5.678, 7.890, 6.789, 8.901, 10.987, 12.345, 11.234, 14.567, 13.456, 19.876, 15.678, 17.890, 16.789, 18.901, 20.987, 22.345, 21.234, 24.567, 23.456, 29.876, 25.678, 27.890, 26.789, 28.901, 30.987, 32.345, 31.234, 34.567, 33.456, 39.876, 35.678, 37.890, 36.789, 38.901, 40.987]")
# content = agent("我有一份时序数据，[0.857, 2.345, 1.234, 4.567, 3.456, 9.876, 5.678, 7.890, 6.789, 8.901, 10.987, 12.345, 11.234, 14.567, 13.456, 19.876, 15.678, 17.890, 16.789, 18.901, 20.987, 22.345, 21.234, 24.567, 23.456, 29.876, 25.678, 27.890, 26.789, 28.901, 30.987, 32.345, 31.234, 34.567, 33.456, 39.876, 35.678, 37.890, 36.789, 38.901, 40.987]，\我不知道这份数据是否存在问题，请帮我判断一下")
# # print(content)
# from langchain.schema import (
#     AgentAction
# )

# s = ""
# if isinstance(content, str):
#     s = content
# else:
#     for i in content["intermediate_steps"]:
#         for j in i:
#             if isinstance(j, AgentAction):
#                 s += j.log + "\n"
#             else:
#                 s += "Observation: " + str(j) + "\n"

#     s += "final answer:" + content["output"]
# print(s)

# print(content["intermediate_steps"][0][0].log)
# print( content["intermediate_steps"][0][0].log, content[""] + "\n" + content["i"] + "\n" + )
# content = agent.run("i want to know the timezone of asia/shanghai, list all timezones available for that area.")
# print(content)