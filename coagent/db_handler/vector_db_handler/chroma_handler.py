# encoding: utf-8
'''
@author: 温进
@file: chroma_handler.py
@time: 2023/11/21 下午12:21
@desc:
'''
from loguru import logger
import chromadb


class ChromaHandler:
    def __init__(self, path: str, collection_name: str = ''):
        '''
        init client
        @param path: path of data
        @collection_name: name of collection
        '''
        settings = chromadb.get_settings()
        # disable the posthog telemetry mechnism that may raise the connection error, such as
        # "requests.exceptions.ConnectTimeout: HTTPSConnectionPool(host='us-api.i.posthog.com', port 443)"
        settings.anonymized_telemetry = False
        self.client = chromadb.PersistentClient(path, settings)
        self.client.heartbeat()

        if collection_name:
            self.collection = self.client.get_or_create_collection(name=collection_name)

    def create_collection(self, collection_name: str):
        '''
        create collection, if exists, will override
        @return:
        '''
        try:
            collection = self.client.create_collection(name=collection_name)
        except Exception as e:
            return {'result_code': -1, 'msg': f'fail, error={e}'}
        return {'result_code': 0, 'msg': 'success'}

    def delete_collection(self, collection_name: str):
        '''

        @param collection_name:
        @return:
        '''
        try:
            self.client.delete_collection(name=collection_name)
        except Exception as e:
            return {'result_code': -1, 'msg': f'fail, error={e}'}
        return {'result_code': 0, 'msg': 'success'}

    def set_collection(self, collection_name: str):
        '''

        @param collection_name:
        @return:
        '''
        try:
            self.collection = self.client.get_collection(collection_name)
        except Exception as e:
            return {'result_code': -1, 'msg': f'fail, error={e}'}
        return {'result_code': 0, 'msg': 'success'}

    def add_data(self, ids: list, documents: list = None, embeddings: list = None, metadatas: list = None):
        '''
        add data to chroma
        @param documents: list of doc string
        @param embeddings: list of vector
        @param metadatas: list of metadata
        @param ids: list of id
        @return:
        '''
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
        except Exception as e:
            return {'result_code': -1, 'msg': f'fail, error={e}'}
        return {'result_code': 0, 'msg': 'success'}

    def query(self, query_embeddings=None, query_texts=None, n_results=10, where=None, where_document=None,
              include=["metadatas", "documents", "distances"]):
        '''

        @param query_embeddings:
        @param query_texts:
        @param n_results:
        @param where:
        @param where_document:
        @param include:
        @return:
        '''
        try:
            query_result = self.collection.query(query_embeddings=query_embeddings, query_texts=query_texts,
                                                 n_results=n_results, where=where, where_document=where_document,
                                                 include=include)
            return {'result_code': 0, 'msg': 'success', 'result': query_result}
        except Exception as e:
            return {'result_code': -1, 'msg': f'fail, error={e}'}

    def get(self, ids=None, where=None, limit=None, offset=None, where_document=None, include=["metadatas", "documents"]):
        '''
        get by condition
        @param ids:
        @param where:
        @param limit:
        @param offset:
        @param where_document:
        @param include:
        @return:
            '''
        try:
            query_result = self.collection.get(ids=ids, where=where, where_document=where_document,
                                               limit=limit,
                                               offset=offset, include=include)
            return {'result_code': 0, 'msg': 'success', 'result': query_result}
        except Exception as e:
            return {'result_code': -1, 'msg': f'fail, error={e}'}

    def peek(self, limit: int=10):
        '''
        peek
        @param limit:
        @return:
        '''
        try:
            query_result = self.collection.peek(limit)
            return {'result_code': 0, 'msg': 'success', 'result': query_result}
        except Exception as e:
            return {'result_code': -1, 'msg': f'fail, error={e}'}

    def count(self):
        '''
        count
        @return:
        '''
        try:
            query_result = self.collection.count()
            return {'result_code': 0, 'msg': 'success', 'result': query_result}
        except Exception as e:
            return {'result_code': -1, 'msg': f'fail, error={e}'}
