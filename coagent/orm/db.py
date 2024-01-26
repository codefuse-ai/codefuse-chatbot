from contextlib import contextmanager
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from coagent.base_configs.env_config import SQLALCHEMY_DATABASE_URI
# from configs.model_config import SQLALCHEMY_DATABASE_URI


_engine = create_engine(SQLALCHEMY_DATABASE_URI)

session_factory = sessionmaker(bind=_engine)

Base = declarative_base()



def init_session():
    session = session_factory()

    try:
        yield session
    finally:
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()



def with_session(func):
    def wrapper(*args, **kwargs):
        session = session_factory()
        try:
            return func(session, *args, **kwargs)
        finally:
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
    return wrapper


@contextmanager
def session_scope():
    """上下文管理器用于自动获取 Session, 避免错误"""
    session = session_factory(autoflush=True)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
