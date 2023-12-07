from pydantic import BaseModel, Field
from typing import List, Dict
import requests
import base64
import urllib
import os
from loguru import logger
from .base_tool import BaseToolModel

from configs.model_config import JUPYTER_WORK_PATH


class BaiduOcrTool(BaseToolModel):
    """
    Tips:
        百度ocr tool
    
    example：
        API_KEY = ""
        SECRET_KEY = ""
        image_path = ''
        ocr_result = BaiduOcrTool.run(API_KEY=API_KEY , SECRET_KEY=SECRET_KEY, image_path=image_path)
    """

    name: str = "Baidu_orc_tool"
    description: str = """ 百度OCR手写字符识别调用器。 输入一张图片位置，返回图片中的文本"""

    class ToolInputArgs(BaseModel):
        """Input for Multiplier."""
        image_name : str = Field(..., description="待提取文本信息的图片名称")

    class ToolOutputArgs(BaseModel):
        """Output for Multiplier."""

        ocr_result: str = Field(..., description="OCR分析提取的自然语言文本")

    @classmethod
    def ocr_baidu_main(cls, API_KEY, SECRET_KEY, image_path):
        '''
        根据图片地址，返回OCR识别结果
        OCR的结果不仅包含了文字，也包含了文字的位置。但可以根据简单的提取方法，只将文字提前取出来
        下面是ocr的返回结果
        '{"words_result":[{"location":{"top":17,"left":33,"width":227,"height":24},"words":"手写识别测试图片样例:"},
                        {"location":{"top":91,"left":190,"width":713,"height":70},"words":"每一个人的生命中,都应该有一次,"},
                        {"location":{"top":177,"left":87,"width":831,"height":65},"words":"为了某个人而忘了自己,不求有结果."},
                        {"location":{"top":263,"left":80,"width":842,"height":76},"words":"不求同行,不求曾经拥有,甚至不求"}],
                        "words_result_num":4,"log_id":1722502064951792680}'
        '''
        url = "https://aip.baidubce.com/rest/2.0/ocr/v1/handwriting?access_token=" + BaiduOcrTool.get_access_token(API_KEY, SECRET_KEY)
        
        # image 可以通过 get_file_content_as_base64("C:\fakepath\ocr_input_example.png",True) 方法获取
        image = BaiduOcrTool.get_file_content_as_base64(image_path, True)
        payload = 'image=' + image + '&detect_direction=false&probability=false'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        response = requests.request("POST", url, headers=headers, data=payload)
        s = ""
        try:
            for word_result in response.json()["words_result"]:
                s += "\n" + word_result["words"]
        except Exception as e:
            logger.exception(e)
            s = "无法识别图片内容"
        return s
        
    @classmethod
    def get_file_content_as_base64(cls, image_path, urlencoded=False):
        """
        获取文件base64编码
        :param path: 文件路径
        :param urlencoded: 是否对结果进行urlencoded 
        :return: base64编码信息
        """
        with open(image_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf8")
            if urlencoded:
                content = urllib.parse.quote_plus(content)
        return content
    
    @classmethod
    def get_access_token(cls, API_KEY, SECRET_KEY):
        """
        使用 AK，SK 生成鉴权签名（Access Token）
        :return: access_token，或是None(如果错误)
        """
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
        return str(requests.post(url, params=params).json().get("access_token"))
    
    @classmethod
    def run(cls, image_name, image_path=JUPYTER_WORK_PATH, API_KEY=os.environ.get("BAIDU_OCR_API_KEY"), SECRET_KEY=os.environ.get("BAIDU_OCR_SECRET_KEY")):
        image_file = os.path.join(image_path, image_name)
        return cls.ocr_baidu_main(API_KEY, SECRET_KEY, image_file)