from langchain.agents import Tool
from langchain.tools import StructuredTool
from langchain.tools.base import ToolException
from pydantic import BaseModel, Field
from typing import List, Dict
# import jsonref
import json


class BaseToolModel:
    name = "BaseToolModel"
    description = "Tool Description"

    class ToolInputArgs(BaseModel):
        """
        Input for MoveFileTool.
        Tips:
            default control Required, e.g.  key1 is not Required/key2 is Required
        """

        key1: str = Field(default=None, description="hello world!")
        key2: str = Field(..., description="hello world!!")

    class ToolOutputArgs(BaseModel):
        """
        Input for MoveFileTool.
        Tips:
            default control Required, e.g.  key1 is not Required/key2 is Required
        """

        key1: str = Field(default=None, description="hello world!")
        key2: str = Field(..., description="hello world!!")

    @classmethod
    def run(cls, tool_input_args: ToolInputArgs) -> ToolOutputArgs:
        """excute your tool!"""
        pass


class BaseTools:
    tools: List[BaseToolModel]


def get_tool_schema(tool: BaseToolModel) -> Dict:
    '''转json schema结构'''
    data = jsonref.loads(tool.schema_json())
    _ = json.dumps(data, indent=4)
    del data["definitions"]
    return data


def _handle_error(error: ToolException) -> str:
    return (
        "The following errors occurred during tool execution:"
        + error.args[0]
        + "Please try again."
    )

import requests
from loguru import logger
def fff(city, extensions):
    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    json_data = {"key": "4ceb2ef6257a627b72e3be6beab5b059", "city": city, "extensions": extensions}
    logger.debug(f"json_data: {json_data}")
    res = requests.get(url, params={"key": "4ceb2ef6257a627b72e3be6beab5b059", "city": city, "extensions": extensions})
    return res.json()


def toLangchainTools(tools: BaseTools) -> List:
    ''''''
    return [
        StructuredTool(
            name=tool.name,
            func=tool.run,
            description=tool.description,
            args_schema=tool.ToolInputArgs,
            handle_tool_error=_handle_error,
        ) for tool in tools
    ]
