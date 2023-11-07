from .db import _engine, Base
from loguru import logger

__all__ = [

]

def create_tables():
    Base.metadata.create_all(bind=_engine)

def reset_tables():
    Base.metadata.drop_all(bind=_engine)
    create_tables()


def check_tables_exist(table_name) -> bool:
    table_exist = _engine.dialect.has_table(_engine.connect(), table_name, schema=None)
    return table_exist

def table_init():
    if (not check_tables_exist("knowledge_base")) or (not check_tables_exist ("knowledge_file")) or \
            (not check_tables_exist ("code_base")):
        create_tables()
