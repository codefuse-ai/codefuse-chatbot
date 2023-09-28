import logging
from utils.WebCrawler import WebCrawler

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    # 保存地址，分别保存html源文件、处理后text文件
    html_dir = "data/html/tmp_csdn_122513786_html.jsonl"
    text_dir = "data/text/tmp_csdn_122513786_text.jsonl"
    # 下载网页数据
    # https://www.langchain.asia/
    # https://blog.csdn.net/weixin_43791511/article/details/122513786
    # https://zhuanlan.zhihu.com/p/645400277
    # https://www.aliyun.com/?utm_content=se_1014243503
    # 'https://cloud.tencent.com/developer/article/1004500?from=15425'
    base_url = 'https://www.langchain.asia/'
    # 爬取方式：
    ## requests和selenium两种方式；requests为简单请求静态网址html内容，js动态数据无法获取；
    ## selenium为模拟人行为请求，可获取全部html数据，但请求时间较长10-20s单网页，尽量设置5s以上的time_sleep。
    reptile_lib = "requests"
    method = "get"  # 目前只支持get请求
    time_sleep = 4  # 每两次请求间隔时间s
    wc = WebCrawler()
    # 爬取base_url单网址
    wc.webcrawler_single(html_dir=html_dir,
                         text_dir=text_dir,
                         base_url=base_url,
                         reptile_lib=reptile_lib,
                         method=method,
                         time_sleep=time_sleep
                         )

    # # 爬取base_url页面所有网址，限制target_url_prefix为前缀，默认target_url_prefix=base_url
    # wc.webcrawler_1_degree(html_dir=html_dir,
    #                        text_dir=text_dir,
    #                        base_url=base_url,
    #                        reptile_lib=reptile_lib,
    #                        method=method,
    #                        time_sleep=time_sleep
    #                        )
