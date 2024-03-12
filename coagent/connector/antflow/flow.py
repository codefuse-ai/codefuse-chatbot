import importlib
from typing import List, Union, Dict, Any
from loguru import logger
import os
from langchain.embeddings.base import Embeddings
from langchain.agents import Tool
from langchain.llms.base import BaseLLM, LLM

from coagent.retrieval.base_retrieval import IMRertrieval
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig
from coagent.connector.phase import BasePhase
from coagent.connector.agents import BaseAgent
from coagent.connector.chains import BaseChain
from coagent.connector.schema import Message, Role, PromptField, ChainConfig
from coagent.tools import toLangchainTools, TOOL_DICT, TOOL_SETS


class AgentFlow:
    def __init__(
        self, 
        role_name: str,
        agent_type: str,
        role_type: str = "assistant",
        agent_index: int = 0,
        role_prompt: str = "",
        prompt_config: List[Dict[str, Any]] = [],
        prompt_manager_type: str = "PromptManager",
        chat_turn: int = 3,
        focus_agents: List[str] = [],
        focus_messages: List[str] = [],
        embeddings: Embeddings = None,
        llm: BaseLLM = None,
        doc_retrieval: IMRertrieval = None,
        code_retrieval: IMRertrieval = None,
        search_retrieval: IMRertrieval = None,
        **kwargs
    ):
        self.role_type = role_type
        self.role_name = role_name
        self.agent_type = agent_type
        self.role_prompt = role_prompt
        self.agent_index = agent_index

        self.prompt_config = prompt_config
        self.prompt_manager_type = prompt_manager_type

        self.chat_turn = chat_turn
        self.focus_agents = focus_agents
        self.focus_messages = focus_messages

        self.embeddings = embeddings
        self.llm = llm
        self.doc_retrieval = doc_retrieval
        self.code_retrieval = code_retrieval
        self.search_retrieval = search_retrieval
        # self.build_config()
        # self.build_agent()

    def build_config(self, embeddings: Embeddings = None, llm: BaseLLM = None):
        self.llm_config = LLMConfig(model_name="test", llm=self.llm or llm)
        self.embed_config = EmbedConfig(embed_model="test", langchain_embeddings=self.embeddings or embeddings)

    def build_agent(self, 
                    embeddings: Embeddings = None, llm: BaseLLM = None,
                    doc_retrieval: IMRertrieval = None, 
                    code_retrieval: IMRertrieval = None, 
                    search_retrieval: IMRertrieval = None,
        ):
        # 可注册个性化的agent，仅通过start_action和end_action来注册
        # class ExtraAgent(BaseAgent):
        #     def start_action_step(self, message: Message) -> Message:
        #         pass

        #     def end_action_step(self, message: Message) -> Message:
        #         pass
        # agent_module = importlib.import_module("coagent.connector.agents")
        # setattr(agent_module, 'extraAgent', ExtraAgent)

        # 可注册个性化的prompt组装方式，
        # class CodeRetrievalPM(PromptManager):
        #     def handle_code_packages(self, **kwargs) -> str:
        #         if 'previous_agent_message' not in kwargs:
        #             return ""
        #         previous_agent_message: Message = kwargs['previous_agent_message']
        #         # 由于两个agent共用了同一个manager，所以临时性处理
        #         vertices = previous_agent_message.customed_kargs.get("RelatedVerticesRetrivalRes", {}).get("vertices", [])
        #         return ", ".join([str(v) for v in vertices])

        # prompt_manager_module = importlib.import_module("coagent.connector.prompt_manager")
        # setattr(prompt_manager_module, 'CodeRetrievalPM', CodeRetrievalPM)
        
        # agent实例化
        agent_module = importlib.import_module("coagent.connector.agents")
        baseAgent: BaseAgent = getattr(agent_module, self.agent_type)
        role = Role(
            role_type=self.agent_type, role_name=self.role_name, 
            agent_type=self.agent_type, role_prompt=self.role_prompt,
        )

        self.build_config(embeddings, llm)
        self.agent = baseAgent(
                    role=role, 
                    prompt_config = [PromptField(**config) for config in self.prompt_config],
                    prompt_manager_type=self.prompt_manager_type,
                    chat_turn=self.chat_turn,
                    focus_agents=self.focus_agents,
                    focus_message_keys=self.focus_messages,
                    llm_config=self.llm_config,
                    embed_config=self.embed_config,
                    doc_retrieval=doc_retrieval or self.doc_retrieval,
                    code_retrieval=code_retrieval or self.code_retrieval,
                    search_retrieval=search_retrieval or self.search_retrieval,
                )
        


class ChainFlow:
    def __init__(
        self, 
        chain_name: str,
        chain_index: int = 0,
        agent_flows: List[AgentFlow] = [],
        chat_turn: int = 5,
        do_checker: bool = False,
        embeddings: Embeddings = None,
        llm: BaseLLM = None,
        doc_retrieval: IMRertrieval = None,
        code_retrieval: IMRertrieval = None,
        search_retrieval: IMRertrieval = None,
        # chain_type: str = "BaseChain",
        **kwargs
    ):
        self.agent_flows = sorted(agent_flows, key=lambda x:x.agent_index)
        self.chat_turn = chat_turn
        self.do_checker = do_checker
        self.chain_name = chain_name
        self.chain_index = chain_index
        self.chain_type = "BaseChain"

        self.embeddings = embeddings
        self.llm = llm

        self.doc_retrieval = doc_retrieval
        self.code_retrieval = code_retrieval
        self.search_retrieval = search_retrieval
        # self.build_config()
        # self.build_chain()

    def build_config(self, embeddings: Embeddings = None, llm: BaseLLM = None):
        self.llm_config = LLMConfig(model_name="test", llm=self.llm or llm)
        self.embed_config = EmbedConfig(embed_model="test", langchain_embeddings=self.embeddings or embeddings)

    def build_chain(self, 
                    embeddings: Embeddings = None, llm: BaseLLM = None,
                    doc_retrieval: IMRertrieval = None, 
                    code_retrieval: IMRertrieval = None, 
                    search_retrieval: IMRertrieval = None,
        ):
        # chain 实例化
        chain_module = importlib.import_module("coagent.connector.chains")
        baseChain: BaseChain = getattr(chain_module, self.chain_type)

        agent_names = [agent_flow.role_name for agent_flow in self.agent_flows]
        chain_config = ChainConfig(chain_name=self.chain_name, agents=agent_names, do_checker=self.do_checker, chat_turn=self.chat_turn)

        # agent 实例化
        self.build_config(embeddings, llm)
        for agent_flow in self.agent_flows:
            agent_flow.build_agent(embeddings, llm)

        self.chain = baseChain(
                chain_config,
                [agent_flow.agent for agent_flow in self.agent_flows], 
                embed_config=self.embed_config,
                llm_config=self.llm_config,
                doc_retrieval=doc_retrieval or self.doc_retrieval,
                code_retrieval=code_retrieval or self.code_retrieval,
                search_retrieval=search_retrieval or self.search_retrieval,
                )

class PhaseFlow:
    def __init__(
        self, 
        phase_name: str,
        chain_flows: List[ChainFlow],
        embeddings: Embeddings = None,
        llm: BaseLLM = None,
        tools: List[Tool] = [],
        doc_retrieval: IMRertrieval = None,
        code_retrieval: IMRertrieval = None,
        search_retrieval: IMRertrieval = None,
        **kwargs
    ):
        self.phase_name = phase_name
        self.chain_flows = sorted(chain_flows, key=lambda x:x.chain_index)
        self.phase_type = "BasePhase"
        self.tools = tools

        self.embeddings = embeddings
        self.llm = llm

        self.doc_retrieval = doc_retrieval
        self.code_retrieval = code_retrieval
        self.search_retrieval = search_retrieval
        # self.build_config()
        self.build_phase()
    
    def __call__(self, params: dict) -> str:

        # tools = toLangchainTools([TOOL_DICT[i] for i in TOOL_SETS if i in TOOL_DICT])
        # query_content = "帮我确认下127.0.0.1这个服务器的在10点是否存在异常，请帮我判断一下"
        try:
            logger.info(f"params: {params}")
            query_content = params.get("query") or params.get("input")
            search_type = params.get("search_type")
            query = Message(
                role_name="human", role_type="user", tools=self.tools,
                role_content=query_content, input_query=query_content, origin_query=query_content,
                cb_search_type=search_type,
                )
            # phase.pre_print(query)
            output_message, output_memory = self.phase.step(query)
            output_content = "\n\n".join((output_memory.to_str_messages(return_all=True, content_key="parsed_output_list").split("\n\n")[1:])) or output_message.role_content
            return output_content
        except Exception as e:
            logger.exception(e)
            return f"Error {e}"

    def build_config(self, embeddings: Embeddings = None, llm: BaseLLM = None):
        self.llm_config = LLMConfig(model_name="test", llm=self.llm or llm)
        self.embed_config = EmbedConfig(embed_model="test", langchain_embeddings=self.embeddings or embeddings)

    def build_phase(self, embeddings: Embeddings = None, llm: BaseLLM = None):
        # phase 实例化
        phase_module = importlib.import_module("coagent.connector.phase")
        basePhase: BasePhase = getattr(phase_module, self.phase_type)

        # chain 实例化
        self.build_config(self.embeddings or embeddings, self.llm or llm)
        os.environ["log_verbose"] = "2"
        for chain_flow in self.chain_flows:
            chain_flow.build_chain(
                self.embeddings or embeddings, self.llm or llm,
                self.doc_retrieval, self.code_retrieval, self.search_retrieval
                )

        self.phase: BasePhase = basePhase(
                phase_name=self.phase_name,
                chains=[chain_flow.chain for chain_flow in self.chain_flows],
                embed_config=self.embed_config,
                llm_config=self.llm_config,
                doc_retrieval=self.doc_retrieval,
                code_retrieval=self.code_retrieval,
                search_retrieval=self.search_retrieval
                )
