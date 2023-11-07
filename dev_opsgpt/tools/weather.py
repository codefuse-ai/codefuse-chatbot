
import json
import os
import re
from pydantic import BaseModel, Field
from typing import List, Dict
import requests
from loguru import logger

from .base_tool import BaseToolModel



class WeatherInfo(BaseToolModel):
    """
    Tips:
        default control Required, e.g.  key1 is not Required/key2 is Required
    """

    name: str = "WeatherInfo"
    description: str = "According to the user's input adcode, it can query the current/future weather conditions of the target area."

    class ToolInputArgs(BaseModel):
        """Input for Weather."""

        # key: str = Field(..., description="用户在高德地图官网申请web服务API类型KEY")
        city: str = Field(..., description="城市编码，输入城市的adcode，adcode信息可参考城市编码表")
        extensions: str = Field(default=None, enum=["base", "all"], description="气象类型，输入城市的adcode，adcode信息可参考城市编码表")

    class ToolOutputArgs(BaseModel):
        """Output for Weather."""

        lives: str = Field(default=None, description="实况天气数据")

    # @classmethod
    # def run(cls, tool_input_args: ToolInputArgs) -> ToolOutputArgs:
    #     """excute your tool!"""
    #     url = "https://restapi.amap.com/v3/weather/weatherInfo"
    #     try:
    #         json_data = tool_input_args.dict()
    #         json_data["key"] = "4ceb2ef6257a627b72e3be6beab5b059"
    #         res = requests.get(url, json_data)
    #         return res.json()
    #     except Exception as e:
    #         return e
        
    @staticmethod
    def run(city, extensions) -> ToolOutputArgs:
        """excute your tool!"""
        url = "https://restapi.amap.com/v3/weather/weatherInfo"
        try:
            json_data = {}
            json_data["city"] = city
            json_data["key"] = "4ceb2ef6257a627b72e3be6beab5b059"
            json_data["extensions"] = extensions
            logger.debug(f"json_data: {json_data}")
            res = requests.get(url, params=json_data)
            return res.json()
        except Exception as e:
            return e


class DistrictInfo(BaseToolModel):
    """
    Tips:
        default control Required, e.g.  key1 is not Required/key2 is Required
    """

    name: str = "DistrictInfo"
    description: str = "用户希望通过得到行政区域信息，进行开发工作。"

    class ToolInputArgs(BaseModel):
        """Input for district."""
        keywords: str = Field(default=None, description="规则：只支持单个关键词语搜索关键词支持：行政区名称、citycode、adcode例如，在subdistrict=2，搜索省份（例如山东），能够显示市（例如济南），区（例如历下区）")
        subdistrict: str = Field(default=None, enums=[1,2,3], description="""规则：设置显示下级行政区级数（行政区级别包括：国家、省/直辖市、市、区/县、乡镇/街道多级数据）

可选值：0、1、2、3等数字，并以此类推

0：不返回下级行政区；

1：返回下一级行政区；

2：返回下两级行政区；

3：返回下三级行政区；""")
        page: int = Field(default=1, examples=["page=2", "page=3"], description="最外层的districts最多会返回20个数据，若超过限制，请用page请求下一页数据。")
        extensions: str = Field(default=None, enum=["base", "all"], description="气象类型，输入城市的adcode，adcode信息可参考城市编码表")

    class ToolOutputArgs(BaseModel):
        """Output for district."""

        districts: str = Field(default=None, description="行政区列表")

    @staticmethod
    def run(keywords=None, subdistrict=None, page=1, extensions=None) -> ToolOutputArgs:
        """excute your tool!"""
        url = "https://restapi.amap.com/v3/config/district"
        try:
            json_data = {}
            json_data["keywords"] = keywords
            json_data["key"] = "4ceb2ef6257a627b72e3be6beab5b059"
            json_data["subdistrict"] = subdistrict
            json_data["page"] = page
            json_data["extensions"] = extensions
            logger.debug(f"json_data: {json_data}")
            res = requests.get(url, params=json_data)
            return res.json()
        except Exception as e:
            return e
