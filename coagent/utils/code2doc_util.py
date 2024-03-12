import json


def class_info_decode(data):
    '''解析class的相关信息'''
    params_dict = {}

    for i in data:
        _params_dict = {}
        for ii in i:
            for k, v in ii.items():
                if k=="origin_query": continue
                
                if k == "Code Path":
                    _params_dict["code_path"] = v.split("#")[0]
                    _params_dict["function_name"] = ".".join(v.split("#")[1:])
                    
                if k == "Class Description":
                    _params_dict["ClassDescription"] = v

                if k == "Class Base":
                    _params_dict["ClassBase"] = v
                    
                if k=="Init Parameters":
                    _params_dict["Parameters"] = v
                    
                    
        code_path = _params_dict["code_path"]
        params_dict.setdefault(code_path, []).append(_params_dict)
        
    return params_dict

def method_info_decode(data):
    params_dict = {}

    for i in data:
        _params_dict = {}
        for ii in i:
            for k, v in ii.items():
                if k=="origin_query": continue
                
                if k == "Code Path":
                    _params_dict["code_path"] = v.split("#")[0]
                    _params_dict["function_name"] = ".".join(v.split("#")[1:])
                    
                if k == "Return Value Description":
                    _params_dict["Returns"] = v
                
                if k == "Return Type":
                    _params_dict["ReturnType"] = v
                    
                if k=="Parameters":
                    _params_dict["Parameters"] = v
                    
                    
        code_path = _params_dict["code_path"]
        params_dict.setdefault(code_path, []).append(_params_dict)
        
    return params_dict

def encode2md(data, md_format):
    md_dict = {}
    for code_path, params_list in data.items():
        for params in params_list:
            params["Parameters_text"] = "\n".join([f"{param['param']}({param['param_type']})-{param['param_description']}"  
                                    for param in params["Parameters"]])
    #         params.delete("Parameters")
            text=md_format.format(**params)
            md_dict.setdefault(code_path, []).append(text)
    return md_dict


method_text_md = '''> {function_name}

| Column Name | Content |
|-----------------|-----------------|
| Parameters   | {Parameters_text} |
| Returns   | {Returns} |
| Return type   | {ReturnType} |
'''

class_text_md = '''> {code_path}

Bases: {ClassBase}

{ClassDescription}

{Parameters_text}
'''