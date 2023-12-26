# 本地私有化/大模型接口接入

依托于开源的 LLM 与 Embedding 模型，本项目可实现基于开源模型的离线私有部署。此外，本项目也支持 OpenAI API 的调用。

## 📜 目录
- [ 本地私有化模型接入](#本地私有化模型接入)
- [ 公开大模型接口接入](#公开大模型接口接入)
- [ 启动大模型服务](#启动大模型服务)

## 本地私有化模型接入

<br>模型地址配置示例，model_config.py配置修改

```bash
# 建议：走huggingface接入，尽量使用chat模型，不要使用base，无法获取正确输出
# 注意：当llm_model_dict和VLLM_MODEL_DICT同时存在时，优先启动VLLM_MODEL_DICT中的模型配置

# llm_model_dict 配置接入示例如下
llm_model_dict = {
    "chatglm-6b": {
        "local_model_path": "THUDM/chatglm-6b",
        "api_base_url": "http://localhost:8888/v1",  # "name"修改为fastchat服务中的"api_base_url"
        "api_key": "EMPTY"
    }
}

# VLLM_MODEL_DICT 配置接入示例如下
VLLM_MODEL_DICT = {
 'chatglm2-6b':  "THUDM/chatglm-6b",
}

```

<br>模型路径填写示例

```bash
# 1、若把模型放到 ~/codefuse-chatbot/llm_models 路径下
# 若模型地址如下
model_dir: ~/codefuse-chatbot/llm_models/THUDM/chatglm-6b

# 参考配置如下
llm_model_dict = {
    "chatglm-6b": {
        "local_model_path": "THUDM/chatglm-6b",
        "api_base_url": "http://localhost:8888/v1",  # "name"修改为fastchat服务中的"api_base_url"
        "api_key": "EMPTY"
    }
}

VLLM_MODEL_DICT = {
 'chatglm2-6b':  "THUDM/chatglm-6b",
}

# or 若模型地址如下
model_dir: ~/codefuse-chatbot/llm_models/chatglm-6b
llm_model_dict = {
    "chatglm-6b": {
        "local_model_path": "chatglm-6b",
        "api_base_url": "http://localhost:8888/v1",  # "name"修改为fastchat服务中的"api_base_url"
        "api_key": "EMPTY"
    }
}

VLLM_MODEL_DICT = {
 'chatglm2-6b':  "chatglm-6b",
}

# 2、若不想移动相关模型到 ~/codefuse-chatbot/llm_models
# 同时删除 `模型路径重置` 以下的相关代码，具体见model_config.py
# 若模型地址如下
model_dir: ~/THUDM/chatglm-6b
# 参考配置如下
llm_model_dict = {
    "chatglm-6b": {
        "local_model_path": "~/THUDM/chatglm-6b",
        "api_base_url": "http://localhost:8888/v1",  # "name"修改为fastchat服务中的"api_base_url"
        "api_key": "EMPTY"
    }
}

VLLM_MODEL_DICT = {
 'chatglm2-6b':  "~/THUDM/chatglm-6b",
}
```

```bash
# 3、指定启动的模型服务，两者保持一致
LLM_MODEL = "gpt-3.5-turbo-16k"
LLM_MODELs = ["gpt-3.5-turbo-16k"]
```

```bash
# server_config.py配置修改， 若LLM_MODELS无多个模型配置不需要额外进行设置
# 修改server_config.py#FSCHAT_MODEL_WORKERS的配置
"model_name": {'host': DEFAULT_BIND_HOST, 'port': 20057}
```



<br>量化模型接入

```bash
# 若需要支撑codellama-34b-int4模型，需要给fastchat打一个补丁
cp examples/gptq.py ~/site-packages/fastchat/modules/gptq.py

# 若需要支撑qwen-72b-int4模型，需要给fastchat打一个补丁
cp examples/gptq.py ~/site-packages/fastchat/modules/gptq.py
# 量化需修改llm_api.py的配置
# dev_opsgpt/service/llm_api.py#559 取消注释 kwargs["gptq_wbits"] = 4
```

## 公开大模型接口接入

```bash
# model_config.py配置修改
# ONLINE_LLM_MODEL
# 其它接口开发来自于langchain-chatchat项目，缺少相关账号未经测试

# 指定启动的模型服务，两者保持一致
LLM_MODEL = "gpt-3.5-turbo-16k"
LLM_MODELs = ["gpt-3.5-turbo-16k"]
```

外部大模型接口接入示例

```bash
# 1、实现新的模型接入类
# 参考  ~/dev_opsgpt/service/model_workers/openai.py#ExampleWorker
# 实现do_chat函数即可使用LLM的能力

class XXWorker(ApiModelWorker):
    def __init__(
            self,
            *,
            controller_addr: str = None,
            worker_addr: str = None,
            model_names: List[str] = ["gpt-3.5-turbo"],
            version: str = "gpt-3.5",
            **kwargs,
    ):
        kwargs.update(model_names=model_names, controller_addr=controller_addr, worker_addr=worker_addr)
        kwargs.setdefault("context_len", 16384) #TODO 16K模型需要改成16384
        super().__init__(**kwargs)
        self.version = version

    def do_chat(self, params: ApiChatParams) -> Dict:
        '''
        执行Chat的方法，默认使用模块里面的chat函数。
        :params.messages : [
            {"role": "user", "content": "hello"}, 
            {"role": "assistant", "content": "hello"}
            ]
        :params.xx: 详情见 ApiChatParams 
        要求返回形式：{"error_code": int, "text": str}
        '''
        return {"error_code": 500, "text": f"{self.model_names[0]}未实现chat功能"}


# 最后在 ~/dev_opsgpt/service/model_workers/__init__.py 中完成注册
# from .xx import XXWorker

# 2、通过已有模型接入类完成接入
# 或者直接使用已有的相关大模型类进行使用（缺少相关账号测试，欢迎大家测试后提PR）
```


```bash
# model_config.py#ONLINE_LLM_MODEL 配置修改
# 填写专属模型的 version、api_base_url、api_key、provider（与上述类名一致）
ONLINE_LLM_MODEL = {
    # 线上模型。请在server_config中为每个在线API设置不同的端口

    "openai-api": {
        "model_name": "gpt-3.5-turbo",
        "api_base_url": "https://api.openai.com/v1",
        "api_key": "",
        "openai_proxy": "",
    },
    "example": {
        "version": "gpt-3.5",  # 采用openai接口做示例
        "api_base_url": "https://api.openai.com/v1",
        "api_key": "",
        "provider": "ExampleWorker",
    },
}
```

## 启动大模型服务
```bash
# start llm-service（可选）  单独启动大模型服务
python dev_opsgpt/service/llm_api.py
```

```bash
# 启动测试
import openai
# openai.api_key = "EMPTY" # Not support yet
openai.api_base = "http://127.0.0.1:8888/v1"

# 选择你启动的模型
model = "example"

# create a chat completion
completion = openai.ChatCompletion.create(
    model=model,
    messages=[{"role": "user", "content": "Hello! What is your name? "}],
    max_tokens=100,
)
# print the completion
print(completion.choices[0].message.content)

# 正确输出后则确认LLM可正常接入
```



or

```bash
# model_config.py#USE_FASTCHAT 判断是否进行fastchat接入本地模型
USE_FASTCHAT = "gpt" not in LLM_MODEL
python start.py #224 自动执行 python service/llm_api.py
```