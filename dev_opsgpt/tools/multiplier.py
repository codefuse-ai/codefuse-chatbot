from pydantic import BaseModel, Field
from typing import List, Dict
import requests
from loguru import logger

from .base_tool import BaseToolModel



class Multiplier(BaseToolModel):
    """
    Tips:
        default control Required, e.g.  key1 is not Required/key2 is Required
    """

    name: str = "Multiplier"
    description: str = """useful for when you need to multiply two numbers together. \
    The input to this tool should be a comma separated list of numbers of length two, representing the two numbers you want to multiply together. \
    For example, `1,2` would be the input if you wanted to multiply 1 by 2."""

    class ToolInputArgs(BaseModel):
        """Input for Multiplier."""

        # key: str = Field(..., description="用户在高德地图官网申请web服务API类型KEY")
        a: int = Field(..., description="num a")
        b: int = Field(..., description="num b")

    class ToolOutputArgs(BaseModel):
        """Output for Multiplier."""

        res: int = Field(..., description="the result of two nums")
    
    @staticmethod
    def run(a, b):
        return a * b
    
def multi_run(a, b):
    return a * b