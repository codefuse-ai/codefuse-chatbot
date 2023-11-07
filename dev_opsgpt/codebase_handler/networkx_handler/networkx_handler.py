# encoding: utf-8
'''
@author: 温进
@file: networkx_handler.py
@time: 2023/10/23 下午5:02
@desc:
'''

import networkx as nx
from loguru import logger
import matplotlib.pyplot as plt
import pickle
from collections import defaultdict
import json

QUERY_SCORE = 10
HISTORY_SCORE = 5
RATIO = 0.5


class NetworkxHandler:
    def __init__(self, graph_path: str = '', node_list: list = [], edge_list: list = []):
        if graph_path:
            self.graph_path = graph_path
            with open(graph_path, 'r') as f:
                self.G = nx.node_link_graph(json.load(f))
        else:
            self.G = nx.DiGraph()
            self.populate_graph(node_list, edge_list)
        logger.debug(
            'number of nodes={}, number of edges={}'.format(self.G.number_of_nodes(), self.G.number_of_edges()))

        self.query_score = QUERY_SCORE
        self.history_score = HISTORY_SCORE
        self.ratio = RATIO

    def populate_graph(self, node_list, edge_list):
        '''
        populate graph with node_list and edge_list
        '''
        self.G.add_nodes_from(node_list)
        for edge in edge_list:
            self.G.add_edge(edge[0], edge[-1], relation=edge[1])

    def draw_graph(self, save_path: str):
        '''
        draw and save to save_path
        '''
        sub = plt.subplot(111)
        nx.draw(self.G, with_labels=True)

        plt.savefig(save_path)

    def search_node(self, query_tag_list: list, history_node_list: list = []):
        '''
        search node by tag_list, search from history_tag neighbors first
        > query_tag_list: tag from query
        > history_node_list
        '''
        node_list = set()

        # search from history_tag_list first, then all nodes
        for tag in query_tag_list:
            add = False
            for history_node in history_node_list:
                connect_node_list: list = self.G.adj[history_node]
                connect_node_list.insert(0, history_node)
                for connect_node in connect_node_list:
                    node_name_lim = len(connect_node) if '_' not in connect_node else connect_node.index('_')
                    node_name = connect_node[0:node_name_lim]
                    if tag.lower() in node_name.lower():
                        node_list.add(connect_node)
                        add = True
            if not add:
                for node in self.G.nodes():
                    if tag.lower() in node.lower():
                        node_list.add(node)
        return node_list

    def search_node_with_score(self, query_tag_list: list, history_node_list: list = []):
        '''
        search node by tag_list, search from history_tag neighbors first
        > query_tag_list: tag from query
        > history_node_list
        '''
        logger.info('query_tag_list={}, history_node_list={}'.format(query_tag_list, history_node_list))
        node_dict = defaultdict(lambda: 0)

        # loop over query_tag_list and add node:
        for tag in query_tag_list:
            for node in self.G.nodes:
                if tag.lower() in node.lower():
                    node_dict[node] += self.query_score

        # loop over history_node and add node score
        for node in history_node_list:
            node_dict[node] += self.history_score

        logger.info('temp_res={}'.format(node_dict))

        # adj score broadcast
        for node in node_dict:
            adj_node_list = self.G.adj[node]
            for adj_node in adj_node_list:
                node_dict[node] += node_dict.get(adj_node, 0) * self.ratio

        # sort
        node_list = [(node, node_score) for node, node_score in node_dict.items()]
        node_list.sort(key=lambda x: x[1], reverse=True)
        return node_list

    def save_graph(self, save_path: str):
        to_save = nx.node_link_data(self.G)
        with open(save_path, 'w') as f:
            json.dump(to_save, f)

    def __len__(self):
        return self.G.number_of_nodes()

    def get_node_type(self, node_name):
        node_type = self.G.nodes[node_name]['type']
        return node_type

    def refresh_graph(self, ):
        with open(self.graph_path, 'r') as f:
            self.G = nx.node_link_graph(json.load(f))



