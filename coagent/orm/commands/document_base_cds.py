from coagent.orm.db import with_session
from coagent.orm.schemas.base_schema import KnowledgeBaseSchema


# @with_session
# def _query_by_condition(session, schema, query_kargs, query_type="first"):
#     if len(query_kargs) >0:
#         if query_type == "first":
#             return session.query(schema).filter_by(query_kargs).first()
#         elif query_type == "all":
#             return session.query(schema).filter_by(query_kargs).first()

# @with_session    
# def _add_to_db(session, schema, query_kargs):
#     kb = schema(**query_kargs)
#     session.add(kb)
#     return True

# @with_session
# def add_to_db(session, schema, query_kargs):
#     kb = _query_by_condition(session, schema, query_kargs, query_type="first")
#     if not kb:
#         _add_to_db(session, schema, query_kargs)
#     else: # update kb with new vs_type and embed_model
#         for k, v in query_kargs.items():
#             if k in kb:
#                 kb[k] = v
#     return True



@with_session
def add_kb_to_db(session, kb_name, vs_type, embed_model):
    # 创建知识库实例
    kb = session.query(KnowledgeBaseSchema).filter_by(kb_name=kb_name).first()
    if not kb:
        kb = KnowledgeBaseSchema(kb_name=kb_name, vs_type=vs_type, embed_model=embed_model)
        session.add(kb)
    else: # update kb with new vs_type and embed_model
        kb.vs_type = vs_type
        kb.embed_model = embed_model
    return True


@with_session
def list_kbs_from_db(session, min_file_count: int = -1):
    kbs = session.query(KnowledgeBaseSchema.kb_name).filter(KnowledgeBaseSchema.file_count > min_file_count).all()
    kbs = [kb[0] for kb in kbs]
    return kbs


@with_session
def kb_exists(session, kb_name):
    kb = session.query(KnowledgeBaseSchema).filter_by(kb_name=kb_name).first()
    status = True if kb else False
    return status


@with_session
def load_kb_from_db(session, kb_name):
    kb = session.query(KnowledgeBaseSchema).filter_by(kb_name=kb_name).first()
    if kb:
        kb_name, vs_type, embed_model = kb.kb_name, kb.vs_type, kb.embed_model
    else:
        kb_name, vs_type, embed_model = None, None, None
    return kb_name, vs_type, embed_model


@with_session
def delete_kb_from_db(session, kb_name):
    kb = session.query(KnowledgeBaseSchema).filter_by(kb_name=kb_name).first()
    if kb:
        session.delete(kb)
    return True


@with_session
def get_kb_detail(session, kb_name: str) -> dict:
    kb: KnowledgeBaseSchema = session.query(KnowledgeBaseSchema).filter_by(kb_name=kb_name).first()
    if kb:
        return {
            "kb_name": kb.kb_name,
            "vs_type": kb.vs_type,
            "embed_model": kb.embed_model,
            "file_count": kb.file_count,
            "create_time": kb.create_time,
        }
    else:
        return {}
