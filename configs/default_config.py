import os
import platform


#
system_name = platform.system()


# 日志存储路径
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
# 知识库默认存储路径
SOURCE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sources")
# 知识库默认存储路径
KB_ROOT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base")
# 代码库默认存储路径
CB_ROOT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code_base")
# nltk 模型存储路径
NLTK_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "nltk_data")
# 代码存储路径
JUPYTER_WORK_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jupyter_work")
# WEB_CRAWL存储路径
WEB_CRAWL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base")
# NEBULA_DATA存储路径
NEBULA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/nebula_data")

# CHROMA 存储路径
CHROMA_PERSISTENT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/chroma_data")

for _path in [LOG_PATH, SOURCE_PATH, KB_ROOT_PATH, CB_ROOT_PATH, NLTK_DATA_PATH, JUPYTER_WORK_PATH, WEB_CRAWL_PATH, NEBULA_PATH, CHROMA_PERSISTENT_PATH]:
    if not os.path.exists(_path):
        os.makedirs(_path, exist_ok=True)
        
path_envt_dict = {
    "LOG_PATH": LOG_PATH, "SOURCE_PATH": SOURCE_PATH, "KB_ROOT_PATH": KB_ROOT_PATH,
    "NLTK_DATA_PATH":NLTK_DATA_PATH, "JUPYTER_WORK_PATH": JUPYTER_WORK_PATH,
    "WEB_CRAWL_PATH": WEB_CRAWL_PATH, "NEBULA_PATH": NEBULA_PATH,
    "CHROMA_PERSISTENT_PATH": CHROMA_PERSISTENT_PATH
    }        
for path_name, _path in path_envt_dict.items():
    os.environ[path_name] = _path


# 数据库默认存储路径。
# 如果使用sqlite，可以直接修改DB_ROOT_PATH；如果使用其它数据库，请直接修改SQLALCHEMY_DATABASE_URI。
DB_ROOT_PATH = os.path.join(KB_ROOT_PATH, "info.db")
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_ROOT_PATH}"

# 可选向量库类型及对应配置
kbs_config = {
    "faiss": {
    },
    # "milvus": {
    #     "host": "127.0.0.1",
    #     "port": "19530",
    #     "user": "",
    #     "password": "",
    #     "secure": False,
    # },
    # "pg": {
    #     "connection_uri": "postgresql://postgres:postgres@127.0.0.1:5432/langchain_chatchat",
    # }
}

# 默认向量库类型。可选：faiss, milvus, pg.
DEFAULT_VS_TYPE = "faiss"

# 缓存向量库数量
CACHED_VS_NUM = 1

# 知识库中单段文本长度
CHUNK_SIZE = 500

# 知识库中相邻文本重合长度
OVERLAP_SIZE = 50

# 知识库匹配向量数量
VECTOR_SEARCH_TOP_K = 5

# 知识库匹配相关度阈值，取值范围在0-1之间，SCORE越小，相关度越高，取到1相当于不筛选，建议设置在0.5左右
# Mac 可能存在无法使用normalized_L2的问题，因此调整SCORE_THRESHOLD至 0~1100
FAISS_NORMALIZE_L2 = True if system_name in ["Linux", "Windows"] else False
SCORE_THRESHOLD = 1 if system_name in ["Linux", "Windows"] else 1100

# 搜索引擎匹配结题数量
SEARCH_ENGINE_TOP_K = 5

# 代码引擎匹配结题数量
CODE_SEARCH_TOP_K = 1


# API 是否开启跨域，默认为False，如果需要开启，请设置为True
# is open cross domain
OPEN_CROSS_DOMAIN = False

# Bing 搜索必备变量
# 使用 Bing 搜索需要使用 Bing Subscription Key,需要在azure port中申请试用bing search
# 具体申请方式请见
# https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/create-bing-search-service-resource
# 使用python创建bing api 搜索实例详见:
# https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/quickstarts/rest/python
BING_SEARCH_URL = "https://api.bing.microsoft.com/v7.0/search"
# 注意不是bing Webmaster Tools的api key，

# 此外，如果是在服务器上，报Failed to establish a new connection: [Errno 110] Connection timed out
# 是因为服务器加了防火墙，需要联系管理员加白名单，如果公司的服务器的话，就别想了GG
BING_SUBSCRIPTION_KEY = ""

# 是否开启中文标题加强，以及标题增强的相关配置
# 通过增加标题判断，判断哪些文本为标题，并在metadata中进行标记；
# 然后将文本与往上一级的标题进行拼合，实现文本信息的增强。
ZH_TITLE_ENHANCE = False

log_verbose = False