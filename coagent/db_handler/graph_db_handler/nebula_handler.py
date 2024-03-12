# encoding: utf-8
'''
@author: 温进
@file: nebula_handler.py
@time: 2023/11/16 下午3:15
@desc:
'''
import time
from loguru import logger

from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config


class NebulaHandler:
    def __init__(self, host: str, port: int, username: str, password: str = '', space_name: str = ''):
        '''
        init nebula connection_pool
        @param host: host
        @param port: port
        @param username: username
        @param password: password
        '''
        config = Config()

        self.connection_pool = ConnectionPool()
        self.connection_pool.init([(host, port)], config)
        self.username = username
        self.password = password
        self.space_name = space_name

    def execute_cypher(self, cypher: str, space_name: str = '', format_res: bool = False, use_space_name: bool = True):
        '''

        @param space_name: space_name, if provided, will execute use space_name first
        @param cypher:
        @return:
        '''
        with self.connection_pool.session_context(self.username, self.password) as session:
            if use_space_name:
                if space_name:
                    cypher = f'USE {space_name};{cypher}'
                elif self.space_name:
                    cypher = f'USE {self.space_name};{cypher}'

            # logger.debug(cypher)
            resp = session.execute(cypher)

            if format_res:
                resp = self.result_to_dict(resp)
        return resp

    def close_connection(self):
        self.connection_pool.close()

    def create_space(self, space_name: str, vid_type: str, comment: str = ''):
        '''
        create space
        @param space_name: cannot startwith number
        @return:
        '''
        cypher = f'CREATE SPACE IF NOT EXISTS {space_name} (vid_type={vid_type}) comment="{comment}";'
        resp = self.execute_cypher(cypher, use_space_name=False)

        return resp

    def show_space(self):
        cypher = 'SHOW SPACES'
        resp = self.execute_cypher(cypher)
        return resp

    def drop_space(self, space_name):
        cypher = f'DROP SPACE {space_name}'
        return self.execute_cypher(cypher)

    def create_tag(self, tag_name: str, prop_dict: dict = {}):
        '''
        创建 tag
        @param tag_name: tag 名称
        @param prop_dict: 属性字典 {'prop 名字': 'prop 类型'}
        @return:
        '''
        cypher = f'CREATE TAG IF NOT EXISTS {tag_name}'
        cypher += '('
        for k, v in prop_dict.items():
            cypher += f'{k} {v},'
        cypher = cypher.rstrip(',')
        cypher += ')'
        cypher += ';'

        res = self.execute_cypher(cypher, self.space_name)
        return res

    def show_tags(self):
        '''
        查看 tag
        @return:
        '''
        cypher = 'SHOW TAGS'
        resp = self.execute_cypher(cypher, self.space_name)
        return resp

    def insert_vertex(self, tag_name: str, value_dict: dict):
        '''
         insert vertex
        @param tag_name:
        @param value_dict: {'properties_name': [], values: {'vid':[]}} order should be the same in properties_name and values
        @return:
        '''
        cypher = f'INSERT VERTEX {tag_name} ('

        properties_name = value_dict['properties_name']

        for property_name in properties_name:
            cypher += f'{property_name},'
        cypher = cypher.rstrip(',')

        cypher += ') VALUES '

        for vid, properties in value_dict['values'].items():
            cypher += f'"{vid}":('
            for property in properties:
                if type(property) == str:
                    cypher += f'"{property}",'
                else:
                    cypher += f'{property}'
            cypher = cypher.rstrip(',')
            cypher += '),'
        cypher = cypher.rstrip(',')
        cypher += ';'

        res = self.execute_cypher(cypher, self.space_name)
        return res

    def create_edge_type(self, edge_type_name: str, prop_dict: dict = {}):
        '''
        创建 tag
        @param edge_type_name: tag 名称
        @param prop_dict: 属性字典 {'prop 名字': 'prop 类型'}
        @return:
        '''
        cypher = f'CREATE EDGE IF NOT EXISTS {edge_type_name}'

        cypher += '('
        for k, v in prop_dict.items():
            cypher += f'{k} {v},'
        cypher = cypher.rstrip(',')
        cypher += ')'
        cypher += ';'

        res = self.execute_cypher(cypher, self.space_name)
        return res

    def show_edge_type(self):
        '''
        查看 tag
        @return:
        '''
        cypher = 'SHOW EDGES'
        resp = self.execute_cypher(cypher, self.space_name)
        return resp

    def drop_edge_type(self, edge_type_name: str):
        cypher = f'DROP EDGE {edge_type_name}'
        return self.execute_cypher(cypher, self.space_name)

    def insert_edge(self, edge_type_name: str, value_dict: dict):
        '''
        insert edge
        @param edge_type_name:
        @param value_dict: value_dict: {'properties_name': [], values: {(src_vid, dst_vid):[]}} order should be the
                            same in properties_name and values
        @return:
        '''
        cypher = f'INSERT EDGE {edge_type_name} ('

        properties_name = value_dict['properties_name']

        for property_name in properties_name:
            cypher += f'{property_name},'
        cypher = cypher.rstrip(',')

        cypher += ') VALUES '

        for (src_vid, dst_vid), properties in value_dict['values'].items():
            cypher += f'"{src_vid}"->"{dst_vid}":('
            for property in properties:
                if type(property) == str:
                    cypher += f'"{property}",'
                else:
                    cypher += f'{property}'
            cypher = cypher.rstrip(',')
            cypher += '),'
        cypher = cypher.rstrip(',')
        cypher += ';'

        res = self.execute_cypher(cypher, self.space_name)
        return res

    def set_space_name(self, space_name):
        self.space_name = space_name

    def add_host(self, host: str, port: str):
        '''
        add host
        @return:
        '''
        cypher = f'ADD HOSTS {host}:{port}'
        res = self.execute_cypher(cypher)
        return res

    def get_stat(self):
        '''

        @return:
        '''
        submit_cypher = 'SUBMIT JOB STATS;'
        self.execute_cypher(cypher=submit_cypher, space_name=self.space_name)
        time.sleep(2)

        stats_cypher = 'SHOW STATS;'
        stats_res = self.execute_cypher(cypher=stats_cypher, space_name=self.space_name)

        res = {'vertices': -1, 'edges': -1}

        stats_res_dict = self.result_to_dict(stats_res)
        logger.info(stats_res_dict)
        for idx in range(len(stats_res_dict['Type'])):
            t = stats_res_dict['Type'][idx].as_string()
            name = stats_res_dict['Name'][idx].as_string()
            count = stats_res_dict['Count'][idx].as_int()

            if t == 'Space' and name in res:
                res[name] = count
        return res

    def get_vertices(self, tag_name: str = '', limit: int = 10000):
        '''
        get all vertices
        @return:
        '''
        if tag_name:
            cypher = f'''MATCH (v:{tag_name}) RETURN v LIMIT {limit};'''
        else:
            cypher = f'MATCH (v) RETURN v LIMIT {limit};'

        res = self.execute_cypher(cypher, self.space_name)
        return self.result_to_dict(res)

    def get_all_vertices(self,):
        '''
        get all vertices
        @return:
        '''
        cypher = "MATCH (v) RETURN v;"
        res = self.execute_cypher(cypher, self.space_name)
        return self.result_to_dict(res)
    
    def get_relative_vertices(self, vertice):
        '''
        get all vertices
        @return:
        '''
        cypher = f'''MATCH (v1)--(v2) WHERE id(v1) == '{vertice}' RETURN id(v2) as id;'''
        res = self.execute_cypher(cypher, self.space_name)
        return self.result_to_dict(res)

    def result_to_dict(self, result) -> dict:
        """
        build list for each column, and transform to dataframe
        """
        # logger.info(result.error_msg())
        assert result.is_succeeded()
        columns = result.keys()
        d = {}
        for col_num in range(result.col_size()):
            col_name = columns[col_num]
            col_list = result.column_values(col_name)
            d[col_name] = [x for x in col_list]
        return d





