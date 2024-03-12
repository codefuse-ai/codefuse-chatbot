
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig
from coagent.base_configs.env_config import KB_ROOT_PATH
from coagent.tools import DocRetrieval, CodeRetrieval


class IMRertrieval:

    def __init__(self,):
        '''
        init your personal attributes
        '''
        pass

    def run(self, ):
        '''
        execute interface, and can use init' attributes
        '''
        pass


class BaseDocRetrieval(IMRertrieval):

    def __init__(self, knowledge_base_name: str, search_top=5, score_threshold=1.0, embed_config: EmbedConfig=EmbedConfig(), kb_root_path: str=KB_ROOT_PATH):
        self.knowledge_base_name = knowledge_base_name
        self.search_top = search_top
        self.score_threshold = score_threshold
        self.embed_config = embed_config
        self.kb_root_path = kb_root_path

    def run(self, query: str, search_top=None, score_threshold=None, ):
        docs = DocRetrieval.run(
            query=query, knowledge_base_name=self.knowledge_base_name,
            search_top=search_top or self.search_top,
            score_threshold=score_threshold or self.score_threshold,
            embed_config=self.embed_config,
            kb_root_path=self.kb_root_path
        )
        return docs


class BaseCodeRetrieval(IMRertrieval):

    def __init__(self, code_base_name, embed_config: EmbedConfig, llm_config: LLMConfig, search_type = 'tag', code_limit = 1, local_graph_path: str=""):
        self.code_base_name = code_base_name
        self.embed_config = embed_config
        self.llm_config = llm_config
        self.search_type = search_type
        self.code_limit = code_limit
        self.use_nh: bool = False
        self.local_graph_path: str = local_graph_path

    def run(self, query,  history_node_list=[], search_type = None, code_limit=None):
        code_docs = CodeRetrieval.run(
            code_base_name=self.code_base_name,
            query=query, 
            history_node_list=history_node_list,
            code_limit=code_limit or self.code_limit,
            search_type=search_type or self.search_type,
            llm_config=self.llm_config,
            embed_config=self.embed_config,
            use_nh=self.use_nh,
            local_graph_path=self.local_graph_path
            )
        return code_docs



class BaseSearchRetrieval(IMRertrieval):

    def __init__(self, ):
        pass

    def run(self, ):
        pass
