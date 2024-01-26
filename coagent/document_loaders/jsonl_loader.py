import json
from pathlib import Path
from typing import AnyStr, Callable, Dict, List, Optional, Union

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, TextSplitter

from coagent.utils.common_utils import read_jsonl_file


class JSONLLoader(BaseLoader):

    def __init__(
            self,
            file_path: Union[str, Path],
            schema_key: str = "all_text",
            content_key: Optional[str] = None,
            metadata_func: Optional[Callable[[Dict, Dict], Dict]] = None,
            text_content: bool = True,
    ):
        self.file_path = Path(file_path).resolve()
        self.schema_key = schema_key
        self._content_key = content_key
        self._metadata_func = metadata_func
        self._text_content = text_content

    def load(self, ) -> List[Document]:
        """Load and return documents from the JSON file."""
        docs: List[Document] = []
        datas = read_jsonl_file(self.file_path)
        self._parse(datas, docs)
        return docs
    
    def _parse(self, datas: List, docs: List[Document]) -> None:
        for idx, sample in enumerate(datas):
            metadata = dict(
                source=str(self.file_path),
                seq_num=idx,
            )
            text = sample.get(self.schema_key, "")
            docs.append(Document(page_content=text, metadata=metadata))

    def load_and_split(
        self, text_splitter: Optional[TextSplitter] = None
    ) -> List[Document]:
        """Load Documents and split into chunks. Chunks are returned as Documents.

        Args:
            text_splitter: TextSplitter instance to use for splitting documents.
              Defaults to RecursiveCharacterTextSplitter.

        Returns:
            List of Documents.
        """
        if text_splitter is None:
            _text_splitter: TextSplitter = RecursiveCharacterTextSplitter()
        else:
            _text_splitter = text_splitter

        docs = self.load()
        return _text_splitter.split_documents(docs)