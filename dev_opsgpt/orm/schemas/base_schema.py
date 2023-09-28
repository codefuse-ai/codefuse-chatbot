from sqlalchemy import Column, Integer, String, DateTime, func

from dev_opsgpt.orm.db import Base


class KnowledgeBaseSchema(Base):
    """
    知识库模型
    """
    __tablename__ = 'knowledge_base'
    id = Column(Integer, primary_key=True, autoincrement=True, comment='知识库ID')
    kb_name = Column(String, comment='知识库名称')
    vs_type = Column(String, comment='嵌入模型类型')
    embed_model = Column(String, comment='嵌入模型名称')
    file_count = Column(Integer, default=0, comment='文件数量')
    create_time = Column(DateTime, default=func.now(), comment='创建时间')

    def __repr__(self):
        return f"""<KnowledgeBase(id='{self.id}', 
        kb_name='{self.kb_name}', 
        vs_type='{self.vs_type}', 
        embed_model='{self.embed_model}', 
        file_count='{self.file_count}', 
        create_time='{self.create_time}')>"""

class KnowledgeFileSchema(Base):
    """
    知识文件模型
    """
    __tablename__ = 'knowledge_file'
    id = Column(Integer, primary_key=True, autoincrement=True, comment='知识文件ID')
    file_name = Column(String, comment='文件名')
    file_ext = Column(String, comment='文件扩展名')
    kb_name = Column(String, comment='所属知识库名称')
    document_loader_name = Column(String, comment='文档加载器名称')
    text_splitter_name = Column(String, comment='文本分割器名称')
    file_version = Column(Integer, default=1, comment='文件版本')
    create_time = Column(DateTime, default=func.now(), comment='创建时间')

    def __repr__(self):
        return f"""<KnowledgeFile(id='{self.id}', 
        file_name='{self.file_name}', 
        file_ext='{self.file_ext}', 
        kb_name='{self.kb_name}', 
        document_loader_name='{self.document_loader_name}', 
        text_splitter_name='{self.text_splitter_name}', 
        file_version='{self.file_version}', 
        create_time='{self.create_time}')>"""
