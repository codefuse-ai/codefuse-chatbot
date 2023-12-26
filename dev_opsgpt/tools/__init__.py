import  importlib

from .base_tool import toLangchainTools, get_tool_schema, BaseToolModel
from .weather import WeatherInfo, DistrictInfo
from .multiplier import Multiplier
from .world_time import WorldTimeGetTimezoneByArea
from .abnormal_detection import KSigmaDetector
from .metrics_query import MetricsQuery
from .duckduckgo_search import DDGSTool
from .docs_retrieval import DocRetrieval
from .cb_query_tool import CodeRetrieval 
from .ocr_tool import BaiduOcrTool
from .stock_tool  import StockInfo, StockName
from .codechat_tools import CodeRetrievalSingle, RelatedVerticesRetrival, Vertex2Code


IMPORT_TOOL = [
    WeatherInfo, DistrictInfo, Multiplier, WorldTimeGetTimezoneByArea,
    KSigmaDetector, MetricsQuery, DDGSTool, DocRetrieval, CodeRetrieval,
    BaiduOcrTool, StockInfo, StockName, CodeRetrievalSingle, RelatedVerticesRetrival, Vertex2Code
]

TOOL_SETS = [tool.__name__ for tool in IMPORT_TOOL]

TOOL_DICT = {tool.__name__: tool for tool in IMPORT_TOOL}


__all__ = [
    "toLangchainTools", "get_tool_schema",  "tool_sets", "BaseToolModel"
] + TOOL_SETS

