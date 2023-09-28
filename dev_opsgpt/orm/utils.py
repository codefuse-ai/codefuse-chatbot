import os
from dev_opsgpt.utils.path_utils import get_file_path, get_LoaderClass, SUPPORTED_EXTS


class DocumentFile:
    def __init__(
            self, filename: str, knowledge_base_name: str) -> None:
        self.kb_name = knowledge_base_name
        self.filename = filename
        self.ext = os.path.splitext(filename)[-1].lower()
        if self.ext not in SUPPORTED_EXTS:
            raise ValueError(f"暂未支持的文件格式 {self.ext}")
        self.filepath = get_file_path(knowledge_base_name, filename)
        self.docs = None
        self.document_loader_name = get_LoaderClass(self.ext)

        # TODO: 增加依据文件格式匹配text_splitter
        self.text_splitter_name = None