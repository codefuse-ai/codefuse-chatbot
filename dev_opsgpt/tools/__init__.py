from .base_tool import toLangchainTools, get_tool_schema, BaseToolModel
from .weather import WeatherInfo, DistrictInfo
from .multiplier import Multiplier
from .world_time import WorldTimeGetTimezoneByArea
from .abnormal_detection import KSigmaDetector
from .metrics_query import MetricsQuery
from .duckduckgo_search import DDGSTool
from .docs_retrieval import DocRetrieval
from .cb_query_tool import CodeRetrieval 

TOOL_SETS = [
    "WeatherInfo", "WorldTimeGetTimezoneByArea", "Multiplier", "DistrictInfo", "KSigmaDetector", "MetricsQuery", "DDGSTool",
    "DocRetrieval", "CodeRetrieval"
    ]

TOOL_DICT = {
    "WeatherInfo": WeatherInfo,
    "WorldTimeGetTimezoneByArea": WorldTimeGetTimezoneByArea,
    "Multiplier": Multiplier,
    "DistrictInfo": DistrictInfo,
    "KSigmaDetector": KSigmaDetector,
    "MetricsQuery": MetricsQuery,
    "DDGSTool": DDGSTool,
    "DocRetrieval": DocRetrieval,
    "CodeRetrieval": CodeRetrieval
}

__all__ = [
    "WeatherInfo", "WorldTimeGetTimezoneByArea", "Multiplier", "DistrictInfo", "KSigmaDetector", "MetricsQuery", "DDGSTool",
    "DocRetrieval", "CodeRetrieval",
    "toLangchainTools", "get_tool_schema",  "tool_sets", "BaseToolModel"
]

