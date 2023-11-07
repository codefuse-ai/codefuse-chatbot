# encoding: utf-8
'''
@author: 温进
@file: local_codedb_handler.py
@time: 2023/10/23 下午5:05
@desc:
'''
import pickle


class LocalCodeDBHandler:
    def __init__(self, tagged_code: dict = {}, db_path: str = ''):
        if db_path:
            with open(db_path, 'rb') as f:
                self.data = pickle.load(f)
        else:
            self.data = {}
            for code, tag in tagged_code.items():
                self.data[code] = str(tag)

    def search_by_single_tag(self, tag, lim):
        res = list()
        for k, v in self.data.items():
            if tag in v and k not in res:
                res.append(k)

                if len(res) > lim:
                    break
        return res

    def search_by_multi_tag(self, tag_list, lim=3):
        res = list()
        res_related_node = []
        for tag in tag_list:
            single_tag_res = self.search_by_single_tag(tag, lim)
            for code in single_tag_res:
                if code not in res:
                    res.append(code)
                    res_related_node.append(tag)
            if len(res) >= lim:
                break

        # reverse order so that most relevant one is close to the query
        res = res[0:lim]
        res.reverse()

        return res, res_related_node

    def save_db(self, save_path):
        with open(save_path, 'wb') as f:
            pickle.dump(self.data, f)

    def __len__(self):
        return len(self.data)

