# encoding: utf-8
'''
@author: 温进
@file: code_base_cds.py.py
@time: 2023/10/23 下午4:34
@desc:
'''
from loguru import logger
from dev_opsgpt.orm.db import with_session, _engine
from dev_opsgpt.orm.schemas.base_schema import CodeBaseSchema


@with_session
def add_cb_to_db(session, code_name, code_path, code_graph_node_num, code_file_num):
    # 增：创建知识库实例
    cb = session.query(CodeBaseSchema).filter_by(code_name=code_name).first()
    if not cb:
        cb = CodeBaseSchema(code_name=code_name, code_path=code_path, code_graph_node_num=code_graph_node_num,
                            code_file_num=code_file_num)
        session.add(cb)
    else:
        cb.code_path = code_path
        cb.code_graph_node_num = code_graph_node_num
    return True


@with_session
def list_cbs_from_db(session):
    '''
    查：查询实例
    '''
    cbs = session.query(CodeBaseSchema.code_name).all()
    cbs = [cb[0] for cb in cbs]
    return cbs


@with_session
def cb_exists(session, code_name):
    '''
    判断是否存在
    '''
    cb = session.query(CodeBaseSchema).filter_by(code_name=code_name).first()
    status = True if cb else False
    return status

@with_session
def load_cb_from_db(session, code_name):
    cb = session.query(CodeBaseSchema).filter_by(code_name=code_name).first()
    if cb:
        code_name, code_path, code_graph_node_num = cb.code_name, cb.code_path, cb.code_graph_node_num
    else:
        code_name, code_path, code_graph_node_num = None, None, None
    return code_name, code_path, code_graph_node_num


@with_session
def delete_cb_from_db(session, code_name):
    cb = session.query(CodeBaseSchema).filter_by(code_name=code_name).first()
    if cb:
        session.delete(cb)
    return True


@with_session
def get_cb_detail(session, code_name: str) -> dict:
    cb: CodeBaseSchema = session.query(CodeBaseSchema).filter_by(code_name=code_name).first()
    logger.info(cb)
    logger.info('code_name={}'.format(cb.code_name))
    if cb:
        return {
            "code_name": cb.code_name,
            "code_path": cb.code_path,
            "code_graph_node_num": cb.code_graph_node_num,
            'code_file_num': cb.code_file_num
        }
    else:
        return {
        }

