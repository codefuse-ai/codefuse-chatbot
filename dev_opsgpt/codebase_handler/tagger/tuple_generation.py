# encoding: utf-8
'''
@author: 温进
@file: tuple_generation.py
@time: 2023/10/23 下午5:01
@desc:
'''


def node_edge_update(parse_res_list: list, node_list: list = list(), edge_list: list = list()):
    '''
    generate node and edge by parse_res
    < node: list of string node
    < edge: (node_st, relation, node_ed)
    '''
    node_dict = {i: j for i, j in node_list}

    for single_parse_res in parse_res_list:
        pac_name = single_parse_res['pac_name']

        node_dict[pac_name] = {'type': 'package'}

        # class_name
        for class_name in single_parse_res['class_name_list']:
            node_dict[class_name] = {'type': 'class'}
            edge_list.append((pac_name, 'contain', class_name))
            edge_list.append((class_name, 'inside', pac_name))

        # func_name
        for class_name, func_name_list in single_parse_res['func_name_dict'].items():
            node_list.append(class_name)
            for func_name in func_name_list:
                node_dict[func_name] = {'type': 'func'}
                edge_list.append((class_name, 'contain', func_name))
                edge_list.append((func_name, 'inside', class_name))

        # depend
        for depend_pac_name in single_parse_res['import_pac_name_list']:
            if depend_pac_name.endswith('*'):
                depend_pac_name = depend_pac_name[0:-2]

            if depend_pac_name in node_dict:
                continue
            else:
                node_dict[depend_pac_name] = {'type': 'unknown'}
            edge_list.append((pac_name, 'depend', depend_pac_name))
            edge_list.append((depend_pac_name, 'beDepended', pac_name))

    node_list = [(i, j) for i, j in node_dict.items()]

    return node_list, edge_list