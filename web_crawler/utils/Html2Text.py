import time
from bs4 import BeautifulSoup
import logging
import json
import os
from tqdm import tqdm
import re
from .DocTokenizer import DocTokenizer

logging.basicConfig(level=logging.INFO)


class Html2Text():
    '''从html中提取text文本内容。
    '''

    def __init__(self):
        pass

    def html2text(self,
                  target_content_tag={},
                  target_tag_list=[],
                  html_dir=None,
                  text_dir=None,
                  mode="w",
                  is_get_all_text=False
                  ):
        '''
        从html中提取text文本内容，需要指定提取html中的tag标签。输入为地址，html文件保存在jsonl文件中，输出也需要指定地址。
        :param target_content_tag: html中正文content所在tag，字典格式限制长度为1，key为选中便签类型name/class/id，vaule为标签取值如div/title/article等
        :param target_tag_list: 指定提取html对应的tag文本，列表，每个元素都与target_content_tag格式相同
        :param is_get_all_text: True则将html页面所有text内容保存到all_text字典中；False不保存all_text
        :param html_dir: html数据地址，注意需要时jsonl格式，一行为一个json字典，有text/url/host_url三个字段
        :param text_dir: 将提取的text内容保存的地址，同样是jsonl格式。
        :return: None
        '''
        assert isinstance(target_content_tag,dict), "target_content_tag请输入字典格式！"
        assert len(target_content_tag.keys()) <= 1,"target_content_tag属性字典只能指定唯一元素！"
        for _ in target_tag_list:
            assert isinstance(_, dict), "target_tag_list列表元素需要字典格式！"
            assert len(_.keys()) <= 1, "target_tag_list列表中的属性字典只能指定唯一元素！"
        # 创建保存目录
        os.makedirs(os.path.dirname(text_dir), exist_ok=True)
        # 读取文件
        logging.info("读取文件中……")
        html_dict_list = self.read_html_jsonl(html_dir)
        url_nums = len(html_dict_list)
        logging.info("共{url_nums}个html网址".format(url_nums=url_nums))
        # 循环处理每行html数据：html提取content正文、指定tag内容
        text_dict_list = []
        for html_dict in tqdm(html_dict_list, mininterval=1):
            # 是否获取全部text内容
            text_dict = self.get_text_dict(
                html_dict=html_dict,
                target_content_tag=target_content_tag,
                target_tag_list=target_tag_list,
                is_get_all_text=is_get_all_text
            )
            text_dict_list.append(text_dict)
        logging.info("保存html提取的text内容……")
        self.save_text_jsonl(json_list=text_dict_list,
                             file_path=text_dir,
                             mode=mode)
        logging.info("保存成功！地址：%s" % text_dir)

    def get_text_dict(self,
                      html_dict={},
                      target_content_tag={},
                      target_tag_list=[],
                      is_get_all_text=True
                      ):
        '''{"name":"div"}
        提取html网页字符中的纯文本内容，采用BeautifulSoup.get_text()获取全部text文本，target_tag_list指定要提取文本的标签。
        :param html_dict: 网页返回的全部文本内容response.text和url
        :param target_content_tag: html中正文content所在tag，字典格式限制长度为1，key为选中便签类型name/class/id，vaule为标签取值如div/title/article等
        :param target_tag_list: 指定提取html对应的tag文本，列表，每个元素都与target_content_tag格式相同
        :return: text_content:{} 提取的text文本内容
        '''
        # 格式定义
        assert isinstance(target_content_tag,dict), "target_content_tag请输入字典格式！"
        assert len(target_content_tag.keys()) <= 1,"target_content_tag属性字典只能指定唯一元素！"
        for _ in target_tag_list:
            assert isinstance(_, dict), "target_tag_list列表元素需要字典格式！"
            assert len(_.keys()) <= 1, "target_tag_list列表中的属性字典只能指定唯一元素！"
        # 提取html的内容
        html_content = html_dict['text']
        url = html_dict['url']
        host_url = html_dict['host_url']
        # 创建BeautifulSoup对象
        soup = BeautifulSoup(html_content, 'html.parser')
        # 处理pre引用代码块，添```引用
        pre_tags = soup.find_all('code')
        for pre_tag in pre_tags:
            pre_tag.string = '\n```code\n' + pre_tag.get_text() + '\n```\n'
        # 提取HTML中的文本内容
        doc_tokenizer = DocTokenizer()
        text_dict = {}
        text_dict['url'] = url
        text_dict['host_url'] = host_url
        # 提取网页的title，不存在则置空
        try:
            text_dict['title'] = soup.title.text
        except:
            text_dict['title'] = None
        # 是否提取全部text，不区分标签
        if is_get_all_text:
            all_text = soup.get_text(separator="", strip=False)
            text_dict['all_text'] = doc_tokenizer.doc_process(all_text)
        # 提取正文tag，可以按照标签的class提取，或按照tag名提取
        if target_content_tag:
            text_dict["content"] = self.soup_find_all_text(soup=soup,doc_tokenizer=doc_tokenizer,attrs=target_content_tag)
        # 提取html中tag内容，每个tag独立作为字段保存
        for target_tag in target_tag_list:
            if target_tag:
                # 提取目标tag名
                tag_ = list(target_tag.values())[0]
                # 提取目标tag内容
                text_dict[tag_] = self.soup_find_all_text(soup,doc_tokenizer,attrs=target_tag)
        return text_dict

    def soup_find_all_text(self,soup,doc_tokenizer,attrs):
        assert isinstance(attrs,dict), "attrs请输入字典格式！"
        assert len(attrs.keys()) == 1,"attrs属性字典只能指定唯一元素！"
        if list(attrs.keys())[0]=="name":
            _tags = soup.find_all(name=attrs["name"])
        else:
            _tags = soup.find_all(attrs=attrs)
        tags_text = ""
        for _tag in _tags:
            tag_text = _tag.get_text(separator="", strip=False)
            tag_text = doc_tokenizer.doc_process(tag_text)
            tags_text += tag_text.strip() + "\n\n"
        return tags_text

    def read_html_jsonl(self, file_name=None):
        '''
        读取html的josnl文件
        '''
        html_dict_list = []
        with open(file_name, "r", encoding="utf-8") as f:
            for k, line in enumerate(f):
                line = json.loads(line)
                html_dict_list.append(line)
        return html_dict_list

    def save_text_jsonl(self, json_list=[], file_path=None, mode="w"):
        '''
        将json_list保存成jsonl格式文件
        '''
        with open(file_path, mode, encoding="utf-8") as f:
            for line in json_list:
                f.write(json.dumps(line, ensure_ascii=False) + "\n")
