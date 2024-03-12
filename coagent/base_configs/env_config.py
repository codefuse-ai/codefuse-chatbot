import os
import platform

system_name = platform.system()
executable_path = os.getcwd()

# 日志存储路径
LOG_PATH = os.environ.get("LOG_PATH", None) or os.path.join(executable_path, "logs")

# 知识库默认存储路径
SOURCE_PATH = os.environ.get("SOURCE_PATH", None) or os.path.join(executable_path, "sources")

# 知识库默认存储路径
KB_ROOT_PATH = os.environ.get("KB_ROOT_PATH", None) or os.path.join(executable_path, "knowledge_base")

# 代码库默认存储路径
CB_ROOT_PATH = os.environ.get("CB_ROOT_PATH", None) or os.path.join(executable_path, "code_base")

# nltk 模型存储路径
NLTK_DATA_PATH = os.environ.get("NLTK_DATA_PATH", None) or os.path.join(executable_path, "nltk_data")

# 代码存储路径
JUPYTER_WORK_PATH = os.environ.get("JUPYTER_WORK_PATH", None) or os.path.join(executable_path, "jupyter_work")

# WEB_CRAWL存储路径
WEB_CRAWL_PATH = os.environ.get("WEB_CRAWL_PATH", None) or os.path.join(executable_path, "knowledge_base")

# NEBULA_DATA存储路径
NEBULA_PATH = os.environ.get("NEBULA_PATH", None) or os.path.join(executable_path, "data/nebula_data")

# CHROMA 存储路径
CHROMA_PERSISTENT_PATH = os.environ.get("CHROMA_PERSISTENT_PATH", None) or os.path.join(executable_path, "data/chroma_data")

for _path in [LOG_PATH, SOURCE_PATH, KB_ROOT_PATH, CB_ROOT_PATH, NLTK_DATA_PATH, JUPYTER_WORK_PATH, WEB_CRAWL_PATH, NEBULA_PATH, CHROMA_PERSISTENT_PATH]:
    if not os.path.exists(_path):
        os.makedirs(_path, exist_ok=True)

# 数据库默认存储路径。
# 如果使用sqlite，可以直接修改DB_ROOT_PATH；如果使用其它数据库，请直接修改SQLALCHEMY_DATABASE_URI。
DB_ROOT_PATH = os.path.join(KB_ROOT_PATH, "info.db")
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_ROOT_PATH}"

kbs_config = {
    "faiss": {
    },}


# GENERAL SERVER CONFIG
DEFAULT_BIND_HOST = os.environ.get("DEFAULT_BIND_HOST", None) or "127.0.0.1"

# NEBULA SERVER CONFIG
NEBULA_HOST = DEFAULT_BIND_HOST
NEBULA_PORT = 9669
NEBULA_STORAGED_PORT = 9779
NEBULA_USER = 'root'
NEBULA_PASSWORD = ''
NEBULA_GRAPH_SERVER = {
    "host": DEFAULT_BIND_HOST,
    "port": NEBULA_PORT,
    "docker_port": NEBULA_PORT
}

# CHROMA CONFIG
# CHROMA_PERSISTENT_PATH = '/home/user/chatbot/data/chroma_data'
# CHROMA_PERSISTENT_PATH = '/Users/bingxu/Desktop/工作/大模型/chatbot/codefuse-chatbot-antcode/data/chroma_data'


# 默认向量库类型。可选：faiss, milvus, pg.
DEFAULT_VS_TYPE = os.environ.get("DEFAULT_VS_TYPE") or "faiss"

# 缓存向量库数量
CACHED_VS_NUM = os.environ.get("CACHED_VS_NUM") or 1

# 知识库中单段文本长度
CHUNK_SIZE = os.environ.get("CHUNK_SIZE") or 500

# 知识库中相邻文本重合长度
OVERLAP_SIZE = os.environ.get("OVERLAP_SIZE") or 50

# 知识库匹配向量数量
VECTOR_SEARCH_TOP_K = os.environ.get("VECTOR_SEARCH_TOP_K") or 5

# 知识库匹配相关度阈值，取值范围在0-1之间，SCORE越小，相关度越高，取到1相当于不筛选，建议设置在0.5左右
# Mac 可能存在无法使用normalized_L2的问题，因此调整SCORE_THRESHOLD至 0~1100
FAISS_NORMALIZE_L2 = True if system_name in ["Linux", "Windows"] else False
SCORE_THRESHOLD = 1 if system_name in ["Linux", "Windows"] else 1100

# 搜索引擎匹配结题数量
SEARCH_ENGINE_TOP_K = os.environ.get("SEARCH_ENGINE_TOP_K") or 5

# 代码引擎匹配结题数量
CODE_SEARCH_TOP_K = os.environ.get("CODE_SEARCH_TOP_K") or 1