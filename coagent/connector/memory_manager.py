from abc import abstractmethod, ABC
from typing import List
import os, sys, copy, json
from jieba.analyse import extract_tags
from collections import Counter
from loguru import logger

from langchain.docstore.document import Document


from .schema import Memory, Message
from coagent.service.service_factory import KBServiceFactory
from coagent.llm_models import getChatModel, getChatModelFromConfig
from coagent.llm_models.llm_config import EmbedConfig, LLMConfig
from coagent.embeddings.utils import load_embeddings_from_path
from coagent.utils.common_utils import save_to_json_file, read_json_file, addMinutesToTime
from coagent.connector.configs.prompts import CONV_SUMMARY_PROMPT_SPEC
from coagent.orm import table_init
# from configs.model_config import KB_ROOT_PATH, EMBEDDING_MODEL, EMBEDDING_DEVICE, SCORE_THRESHOLD
# from configs.model_config import embedding_model_dict


class BaseMemoryManager(ABC):
    """
    This class represents a local memory manager that inherits from BaseMemoryManager.

    Attributes:
    - user_name: A string representing the user name. Default is "default".
    - unique_name: A string representing the unique name. Default is "default".
    - memory_type: A string representing the memory type. Default is "recall".
    - do_init: A boolean indicating whether to initialize. Default is False.
    - current_memory: An instance of Memory class representing the current memory.
    - recall_memory: An instance of Memory class representing the recall memory.
    - summary_memory: An instance of Memory class representing the summary memory.
    - save_message_keys: A list of strings representing the keys for saving messages.

    Methods:
    - __init__: Initializes the LocalMemoryManager with the given user_name, unique_name, memory_type, and do_init.
    - init_vb: Initializes the vb.
    - append: Appends a message to the recall memory, current memory, and summary memory.
    - extend: Extends the recall memory, current memory, and summary memory.
    - save: Saves the memory to the specified directory.
    - load: Loads the memory from the specified directory and returns a Memory instance.
    - save_new_to_vs: Saves new messages to the vector space.
    - save_to_vs: Saves the memory to the vector space.
    - router_retrieval: Routes the retrieval based on the retrieval type.
    - embedding_retrieval: Retrieves messages based on embedding.
    - text_retrieval: Retrieves messages based on text.
    - datetime_retrieval: Retrieves messages based on datetime.
    - recursive_summary: Performs recursive summarization of messages.
    """
    
    def __init__(
            self,
            user_name: str = "default",
            unique_name: str = "default",
            memory_type: str = "recall",
            do_init: bool = False,
        ):
        """
        Initializes the LocalMemoryManager with the given parameters.

        Args:
        - user_name: A string representing the user name. Default is "default".
        - unique_name: A string representing the unique name. Default is "default".
        - memory_type: A string representing the memory type. Default is "recall".
        - do_init: A boolean indicating whether to initialize. Default is False.
        """
        self.user_name = user_name
        self.unique_name = unique_name
        self.memory_type = memory_type
        self.do_init = do_init
        self.current_memory = Memory(messages=[])
        self.recall_memory = Memory(messages=[])
        self.summary_memory = Memory(messages=[])
        self.save_message_keys = [
            'chat_index', 'role_name', 'role_type', 'role_prompt', 'input_query', 'origin_query',
            'datetime', 'role_content', 'step_content', 'parsed_output', 'spec_parsed_output', 'parsed_output_list', 
            'task', 'db_docs', 'code_docs', 'search_docs', 'phase_name', 'chain_name', 'customed_kargs']
        self.init_vb()

    def init_vb(self):
        """
        Initializes the vb.
        """
        pass

    def append(self, message: Message):
        """
        Appends a message to the recall memory, current memory, and summary memory.

        Args:
        - message: An instance of Message class representing the message to be appended.
        """
        pass

    def extend(self, memory: Memory):
        """
        Extends the recall memory, current memory, and summary memory.

        Args:
        - memory: An instance of Memory class representing the memory to be extended.
        """
        pass

    def save(self, save_dir: str = ""):
        """
        Saves the memory to the specified directory.

        Args:
        - save_dir: A string representing the directory to save the memory. Default is KB_ROOT_PATH.
        """
        pass

    def load(self, load_dir: str = "") -> Memory:
        """
        Loads the memory from the specified directory and returns a Memory instance.

        Args:
        - load_dir: A string representing the directory to load the memory from. Default is KB_ROOT_PATH.

        Returns:
        - An instance of Memory class representing the loaded memory.
        """
        pass

    def save_new_to_vs(self, messages: List[Message]):
        """
        Saves new messages to the vector space.

        Args:
        - messages: A list of Message instances representing the messages to be saved.
        - embed_model: A string representing the embedding model. Default is EMBEDDING_MODEL.
        - embed_device: A string representing the embedding device. Default is EMBEDDING_DEVICE.
        """
        pass

    def save_to_vs(self, embed_model="", embed_device=""):
        """
        Saves the memory to the vector space.

        Args:
        - embed_model: A string representing the embedding model. Default is EMBEDDING_MODEL.
        - embed_device: A string representing the embedding device. Default is EMBEDDING_DEVICE.
        """
        pass

    def router_retrieval(self, text: str=None, datetime: str = None, n=5, top_k=5, retrieval_type: str = "embedding", **kwargs) -> List[Message]:
        """
        Routes the retrieval based on the retrieval type.

        Args:
        - text: A string representing the text for retrieval. Default is None.
        - datetime: A string representing the datetime for retrieval. Default is None.
        - n: An integer representing the number of messages. Default is 5.
        - top_k: An integer representing the top k messages. Default is 5.
        - retrieval_type: A string representing the retrieval type. Default is "embedding".
        - **kwargs: Additional keyword arguments for retrieval.

        Returns:
        - A list of Message instances representing the retrieved messages.
        """
        pass

    def embedding_retrieval(self, text: str, embed_model="", top_k=1, score_threshold=1.0, **kwargs) -> List[Message]:
        """
        Retrieves messages based on embedding.

        Args:
        - text: A string representing the text for retrieval.
        - embed_model: A string representing the embedding model. Default is EMBEDDING_MODEL.
        - top_k: An integer representing the top k messages. Default is 1.
        - score_threshold: A float representing the score threshold. Default is SCORE_THRESHOLD.
        - **kwargs: Additional keyword arguments for retrieval.

        Returns:
        - A list of Message instances representing the retrieved messages.
        """
        pass

    def text_retrieval(self, text: str, **kwargs) -> List[Message]:
        """
        Retrieves messages based on text.

        Args:
        - text: A string representing the text for retrieval.
        - **kwargs: Additional keyword arguments for retrieval.

        Returns:
        - A list of Message instances representing the retrieved messages.
        """
        pass

    def datetime_retrieval(self, datetime: str, text: str = None, n: int = 5, **kwargs) -> List[Message]:
        """
        Retrieves messages based on datetime.

        Args:
        - datetime: A string representing the datetime for retrieval.
        - text: A string representing the text for retrieval. Default is None.
        - n: An integer representing the number of messages. Default is 5.
        - **kwargs: Additional keyword arguments for retrieval.

        Returns:
        - A list of Message instances representing the retrieved messages.
        """
        pass

    def recursive_summary(self, messages: List[Message], split_n: int = 20) -> List[Message]:
        """
        Performs recursive summarization of messages.

        Args:
        - messages: A list of Message instances representing the messages to be summarized.
        - split_n: An integer representing the split n. Default is 20.

        Returns:
        - A list of Message instances representing the summarized messages.
        """
        pass


class LocalMemoryManager(BaseMemoryManager):

    def __init__(
            self,
            embed_config: EmbedConfig,
            llm_config: LLMConfig,
            user_name: str = "default",
            unique_name: str = "default",
            memory_type: str = "recall",
            do_init: bool = False,
            kb_root_path: str = "",
        ):
        self.user_name = user_name
        self.unique_name = unique_name
        self.memory_type = memory_type
        self.do_init = do_init
        self.kb_root_path = kb_root_path
        self.embed_config: EmbedConfig = embed_config
        self.llm_config: LLMConfig = llm_config
        self.current_memory = Memory(messages=[])
        self.recall_memory = Memory(messages=[])
        self.summary_memory = Memory(messages=[])
        self.save_message_keys = [
            'chat_index', 'role_name', 'role_type', 'role_prompt', 'input_query', 'origin_query',
            'datetime', 'role_content', 'step_content', 'parsed_output', 'spec_parsed_output', 'parsed_output_list', 
            'task', 'db_docs', 'code_docs', 'search_docs', 'phase_name', 'chain_name', 'customed_kargs']
        self.init_vb()

    def init_vb(self):
        vb_name = f"{self.user_name}/{self.unique_name}/{self.memory_type}"
        # default to recreate a new vb
        table_init()
        vb = KBServiceFactory.get_service_by_name(vb_name, self.embed_config, self.kb_root_path)
        if vb:
            status = vb.clear_vs()

        if not self.do_init:
            self.load(self.kb_root_path)
            self.save_to_vs()

    def append(self, message: Message):
        self.recall_memory.append(message)
        # 
        if message.role_type == "summary":
            self.summary_memory.append(message)
        else:
            self.current_memory.append(message)

        self.save(self.kb_root_path)
        self.save_new_to_vs([message])

    def extend(self, memory: Memory):
        self.recall_memory.extend(memory)
        self.current_memory.extend(self.recall_memory.filter_by_role_type(["summary"]))
        self.summary_memory.extend(self.recall_memory.select_by_role_type(["summary"]))
        self.save(self.kb_root_path)
        self.save_new_to_vs(memory.messages)

    def save(self, save_dir: str = "./"):
        file_path = os.path.join(save_dir, f"{self.user_name}/{self.unique_name}/{self.memory_type}/converation.jsonl")
        memory_messages = self.recall_memory.dict()
        memory_messages = {k: [
                {kkk: vvv for kkk, vvv in vv.items() if kkk in self.save_message_keys}
                for vv in v ] 
            for k, v in memory_messages.items()
        }
        # 
        save_to_json_file(memory_messages, file_path)

    def load(self, load_dir: str = "./") -> Memory:
        file_path = os.path.join(load_dir, f"{self.user_name}/{self.unique_name}/{self.memory_type}/converation.jsonl")

        if os.path.exists(file_path):
            self.recall_memory = Memory(**read_json_file(file_path))
            self.current_memory = Memory(messages=self.recall_memory.filter_by_role_type(["summary"]))
            self.summary_memory = Memory(messages=self.recall_memory.select_by_role_type(["summary"]))

    def save_new_to_vs(self, messages: List[Message]):
        if self.embed_config:
            vb_name = f"{self.user_name}/{self.unique_name}/{self.memory_type}"
            # default to faiss, todo: add new vstype
            vb = KBServiceFactory.get_service(vb_name, "faiss", self.embed_config, self.kb_root_path)
            embeddings = load_embeddings_from_path(self.embed_config.embed_model_path, self.embed_config.model_device,)
            messages = [
                    {k: v for k, v in m.dict().items() if k in self.save_message_keys}
                    for m in messages] 
            docs = [{"page_content": m["step_content"] or m["role_content"] or m["input_query"] or m["origin_query"], "metadata": m} for m in messages]
            docs = [Document(**doc) for doc in docs]
            vb.do_add_doc(docs, embeddings)

    def save_to_vs(self):
        vb_name = f"{self.user_name}/{self.unique_name}/{self.memory_type}"
        # default to recreate a new vb
        vb = KBServiceFactory.get_service_by_name(vb_name, self.embed_config, self.kb_root_path)
        if vb:
            status = vb.clear_vs()
        # create_kb(vb_name, "faiss", embed_model)

        # default to faiss, todo: add new vstype
        vb = KBServiceFactory.get_service(vb_name, "faiss", self.embed_config, self.kb_root_path)
        embeddings = load_embeddings_from_path(self.embed_config.embed_model_path, self.embed_config.model_device,)
        messages = self.recall_memory.dict()
        messages = [
                {kkk: vvv for kkk, vvv in vv.items() if kkk in self.save_message_keys}
                for k, v in messages.items() for vv in v] 
        docs = [{"page_content": m["step_content"] or m["role_content"] or m["input_query"] or m["origin_query"], "metadata": m} for m in messages]
        docs = [Document(**doc) for doc in docs]
        vb.do_add_doc(docs, embeddings)

    # def load_from_vs(self, embed_model=EMBEDDING_MODEL) -> Memory:
    #     vb_name = f"{self.user_name}/{self.unique_name}/{self.memory_type}"

    #     create_kb(vb_name, "faiss", embed_model)
    #     # default to faiss, todo: add new vstype
    #     vb = KBServiceFactory.get_service(vb_name, "faiss", embed_model)
    #     docs =  vb.get_all_documents()
    #     print(docs)

    def router_retrieval(self, text: str=None, datetime: str = None, n=5, top_k=5, retrieval_type: str = "embedding", **kwargs) -> List[Message]:
        retrieval_func_dict = {
            "embedding": self.embedding_retrieval, "text": self.text_retrieval, "datetime": self.datetime_retrieval
            }
        
        # 确保提供了合法的检索类型
        if retrieval_type not in retrieval_func_dict:
            raise ValueError(f"Invalid retrieval_type: '{retrieval_type}'. Available types: {list(retrieval_func_dict.keys())}")

        retrieval_func = retrieval_func_dict[retrieval_type]
        # 
        params = locals()
        params.pop("self")
        params.pop("retrieval_type")
        params.update(params.pop('kwargs', {}))
        # 
        return retrieval_func(**params)
        
    def embedding_retrieval(self, text: str, top_k=1, score_threshold=1.0, **kwargs) -> List[Message]:
        if text is None: return []
        vb_name = f"{self.user_name}/{self.unique_name}/{self.memory_type}"
        vb = KBServiceFactory.get_service(vb_name, "faiss", self.embed_config, self.kb_root_path)
        docs = vb.search_docs(text, top_k=top_k, score_threshold=score_threshold)
        return [Message(**doc.metadata) for doc, score in docs]
    
    def text_retrieval(self, text: str, **kwargs)  -> List[Message]:
        if text is None: return []
        return self._text_retrieval_from_cache(self.recall_memory.messages, text, score_threshold=0.3, topK=5, **kwargs)

    def datetime_retrieval(self, datetime: str, text: str = None, n: int = 5, **kwargs) -> List[Message]:
        if datetime is None: return []
        return self._datetime_retrieval_from_cache(self.recall_memory.messages, datetime, text, n, **kwargs)
    
    def _text_retrieval_from_cache(self, messages: List[Message], text: str = None, score_threshold=0.3, topK=5, tag_topK=5, **kwargs) -> List[Message]:
        keywords = extract_tags(text, topK=tag_topK)

        matched_messages = []
        for message in messages:
            message_keywords = extract_tags(message.step_content or message.role_content or message.input_query, topK=tag_topK)
            # calculate jaccard similarity
            intersection = Counter(keywords) & Counter(message_keywords)
            union = Counter(keywords) | Counter(message_keywords)
            similarity = sum(intersection.values()) / sum(union.values())
            if similarity >= score_threshold:
                matched_messages.append((message, similarity))
        matched_messages = sorted(matched_messages, key=lambda x:x[1])
        return [m for m, s in matched_messages][:topK]   
     
    def _datetime_retrieval_from_cache(self, messages: List[Message], datetime: str, text: str = None, n: int = 5, **kwargs) -> List[Message]:
        # select message by datetime
        datetime_before, datetime_after = addMinutesToTime(datetime, n)
        select_messages = [
            message for message in messages 
            if datetime_before<=message.datetime<=datetime_after
        ]
        return self._text_retrieval_from_cache(select_messages, text)
    
    def recursive_summary(self, messages: List[Message], split_n: int = 20) -> List[Message]:

        if len(messages) == 0:
            return messages
        
        newest_messages = messages[-split_n:]
        summary_messages = messages[:len(messages)-split_n]
        
        while (len(newest_messages) != 0) and (newest_messages[0].role_type != "user"):
            message = newest_messages.pop(0)
            summary_messages.append(message)
        
        # summary
        # model = getChatModel(temperature=0.2)
        model = getChatModelFromConfig(self.llm_config)
        summary_content = '\n\n'.join([
            m.role_type + "\n" + "\n".join(([f"*{k}* {v}" for parsed_output in m.parsed_output_list for k, v in parsed_output.items() if k not in ['Action Status']]))
            for m in summary_messages if m.role_type not in  ["summary"]
        ])
        
        summary_prompt = CONV_SUMMARY_PROMPT_SPEC.format(conversation=summary_content)
        content = model.predict(summary_prompt)
        summary_message = Message(
            role_name="summaryer",
            role_type="summary",
            role_content=content,
            step_content=content,
            parsed_output_list=[],
            customed_kargs={}
            )
        summary_message.parsed_output_list.append({"summary": content})
        newest_messages.insert(0, summary_message)
        return newest_messages