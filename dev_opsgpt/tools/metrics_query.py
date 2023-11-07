
import json
import os
import re
from pydantic import BaseModel, Field
from typing import List, Dict
import requests
import numpy as np
from loguru import logger

from .base_tool import BaseToolModel



class MetricsQuery(BaseToolModel):
    name = "MetricsQuery"
    description = "查询机器的监控数据"

    class ToolInputArgs(BaseModel):
        machine_ip: str = Field(..., description="machine_ip")
        time: int = Field(..., description="time period")

    class ToolOutputArgs(BaseModel):
        """Output for MetricsQuery."""

        datas: List[float] = Field(..., description="监控时序数组")

    def run(machine_ip, time):
        """excute your tool!"""
        data = [0.857, 2.345, 1.234, 4.567, 3.456, 9.876, 5.678, 7.890, 6.789, 8.901, 10.987, 12.345, 11.234, 14.567, 13.456, 19.876, 15.678, 17.890, 
                16.789, 18.901, 20.987, 22.345, 21.234, 24.567, 23.456, 29.876, 25.678, 27.890, 26.789, 28.901, 30.987, 32.345, 31.234, 34.567, 
                33.456, 39.876, 35.678, 37.890, 36.789, 38.901, 40.987]
        return data[:30]