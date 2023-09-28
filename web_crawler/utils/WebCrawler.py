from .WebHtmlExtractor import WebHtmlExtractor
import logging
from .Html2Text import Html2Text


class WebCrawler():
    '''爬取url内容，分为requests和selenium两种方式；selenium需提前下载chrome浏览器与chromedriver，并配置路径。
    安装selenium模拟访问网站，需安装并调试chromedriver，版本与电脑chrome需一致，且正确配置路径。mac电脑路径：打开finder,再按command+shift+G进入/usr/local/bin；windows可配置路径。
    '''

    def __init__(self):
        pass

    def webcrawler_single(self,
                          html_dir=None,
                          text_dir=None,
                          base_url=None,
                          reptile_lib="requests",
                          method="get",
                          mode="w",
                          time_sleep=4,
                          time_out=10,
                          target_content_tag={},
                          target_tag_list=[]
                          ):
        '''
        爬取base_url页网址，分别保存html与解析处理的text
        :param html_dir: 保存html地址，jsonl文件
        :param text_dir: 将提取的text内容保存的地址，同样是jsonl格式。
        :param base_url: 目标网址
        :param reptile_lib: requests和selenium两种方式；requests为简单请求静态网址html内容，js动态数据无法获取；selenium为模拟人行为请求，可获取全部html数据，但请求时间较长，尽量设置5s以上的time_sleep，selenium需提前下载chrome浏览器与chromedriver，并配置路径。。
        :param method: requests请求有get/post两种，selenium只支持get
        :param time_sleep: 等待时间s
        :param time_out: 超时时长s
        :param target_content_tag: html中正文content所在tag，字典格式限制长度为1，key为选中便签类型name/class/id，vaule为标签取值如div/title/article等
        :param target_tag_list: 指定提取html对应的tag文本，列表，每个元素都与target_content_tag格式相同
        :return: None
        '''
        assert method=="get","只支持get请求！"
        # 发送请求获取base_url结果：包含相关页面全部网址
        whe = WebHtmlExtractor(time_sleep=time_sleep, time_out=time_out)
        whe.save_url_html(base_url=base_url, reptile_lib=reptile_lib, method=method, html_dir=html_dir, mode=mode)
        # 读取文件
        h2t = Html2Text()
        # 读取并处理，只按照指定tag获取text，不获取全部text内容
        h2t.html2text(target_content_tag=target_content_tag,
                      target_tag_list=target_tag_list,
                      html_dir=html_dir,
                      text_dir=text_dir,
                      mode="w",
                      is_get_all_text=True)

    def webcrawler_batch(self,
                          html_dir=None,
                          text_dir=None,
                          target_url_list=[],
                          reptile_lib="requests",
                          method="get",
                          mode="w",
                          time_sleep=4,
                          time_out=10,
                          target_content_tag={},
                          target_tag_list=[]
                          ):
        '''
        爬取base_url页网址，分别保存html与解析处理的text
        :param html_dir: 保存html地址，jsonl文件
        :param text_dir: 将提取的text内容保存的地址，同样是jsonl格式。
        :param base_url: 目标网址
        :param reptile_lib: requests和selenium两种方式；requests为简单请求静态网址html内容，js动态数据无法获取；selenium为模拟人行为请求，可获取全部html数据，但请求时间较长，尽量设置5s以上的time_sleep，selenium需提前下载chrome浏览器与chromedriver，并配置路径。。
        :param method: requests请求有get/post两种，selenium只支持get
        :param time_sleep: 等待时间s
        :param time_out: 超时时长s
        :param target_content_tag: html中正文content所在tag，字典格式限制长度为1，key为选中便签类型name/class/id，vaule为标签取值如div/title/article等
        :param target_tag_list: 指定提取html对应的tag文本，列表，每个元素都与target_content_tag格式相同
        :return: None
        '''
        assert method=="get","只支持get请求！"
        # 发送请求获取base_url结果：包含相关页面全部网址
        whe = WebHtmlExtractor(time_sleep=time_sleep, time_out=time_out)
        # 循环调用
        try:
            for k,url in enumerate(target_url_list):
                mode_batch = mode if k==0 else "a"
                whe.save_url_html(base_url=url, reptile_lib=reptile_lib, method=method, html_dir=html_dir, mode=mode_batch)
        except:
            logging.warning("爬取停止！")
        # html中提取text信息，并对doc做基础处理
        h2t = Html2Text()
        h2t.html2text(target_content_tag=target_content_tag,
                      target_tag_list=target_tag_list,
                      html_dir=html_dir,
                      text_dir=text_dir,
                      mode="w",
                      is_get_all_text=True)

    def webcrawler_1_degree(self,
                            html_dir=None,
                            text_dir=None,
                            base_url=None,
                            reptile_lib="requests",
                            method="get",
                            mode="w",
                            time_sleep=4,
                            time_out=10,
                            target_content_tag={},
                            target_tag_list=[],
                            target_url_prefix=None
                            ):
        '''
        爬取base_url页面所有<a href=>网址，限制target_url_prefix为前缀，默认target_url_prefix=base_url，分别保存html与解析处理的text。
        :param html_dir: 保存html地址，jsonl文件
        :param text_dir: 将提取的text内容保存的地址，同样是jsonl格式。
        :param base_url: 目标站点
        :param target_url_prefix: 基于base_url网址，1度跳转链接 且 以target_url_prefix开头。默认为target_url_prefix=base_url（请求返回的当前网址url，中文会自动转为编码）。
        :param reptile_lib: requests和selenium两种方式；requests为简单请求静态网址html内容，js动态数据无法获取；selenium为模拟人行为请求，可获取全部html数据，但请求时间较长，尽量设置5s以上的time_sleep。
        :param method: requests请求有get/post两种，selenium只支持get
        :param time_sleep: 等待时间s
        :param time_out: 超时时长s
        :param target_content_tag: html中正文content所在tag，字典格式限制长度为1，key为选中便签类型name/class/id，vaule为标签取值如div/title/article等
        :param target_tag_list: 指定提取html对应的tag文本，列表，每个元素都与target_content_tag格式相同
        :return: None
        '''
        assert method == "get", "只支持get请求！"
        # 发送请求获取base_url结果：包含相关页面全部网址
        whe = WebHtmlExtractor(time_sleep=time_sleep, time_out=time_out)
        try:
            whe.save_1_jump_url_in_base(base_url=base_url, target_url_prefix=target_url_prefix, reptile_lib=reptile_lib,
                                        method=method, html_dir=html_dir, mode=mode)
        except:
            logging.warning("爬取停止！")
        # 读取文件
        h2t = Html2Text()
        # 读取并处理，只按照指定tag获取text，不获取全部text内容
        h2t.html2text(target_content_tag=target_content_tag,
                      target_tag_list=target_tag_list,
                      html_dir=html_dir,
                      text_dir=text_dir,
                      mode="w",
                      is_get_all_text=True)
