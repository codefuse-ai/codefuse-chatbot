
# Local Privatization/Large Model Interface Access

Leveraging open-source LLMs (Large Language Models) and Embedding models, this project enables offline private deployment based on open-source models. 

In addition, the project supports the invocation of OpenAI API.

## Local Privatization Model Access

<br>Example of model address configuration, modification of the model_config.py configuration:

```bash
# Recommendation: Use Hugging Face models, preferably the chat models, and avoid using base models, which may not produce correct outputs.
# Note: When both `llm_model_dict` and `VLLM_MODEL_DICT` are present, the model configuration in `VLLM_MODEL_DICT` takes precedence.
# Example of `llm_model_dict` configuration:

# 1. If the model is placed under the ~/codefuse-chatbot/llm_models path
# Suppose the model address is as follows
model_dir: ~/codefuse-chatbot/llm_models/THUDM/chatglm-6b

# The reference configuration is as follows
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

# or If the model address is as follows
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

# 2. If you do not wish to move the model to ~/codefuse-chatbot/llm_models
# Also, delete the related code below `Model Path Reset`, see model_config.py for details.
# Suppose the model address is as follows
model_dir: ~/THUDM/chatglm-6b
# The reference configuration is as follows
llm_model_dict = {
    "chatglm-6b": {
        "local_model_path": "your personl dir/THUDM/chatglm-6b",
        "api_base_url": "http://localhost:8888/v1",  # "name"修改为fastchat服务中的"api_base_url"
        "api_key": "EMPTY"
    }
}

VLLM_MODEL_DICT = {
 'chatglm2-6b':  "your personl dir/THUDM/chatglm-6b",
}
```

```bash
# 3. Specify the model service to be launched, keeping both consistent
LLM_MODEL = "chatglm-6b"
LLM_MODELs = ["chatglm-6b"]
```

```bash
# Modification of server_config.py configuration, if LLM_MODELS does not have multiple model configurations, no additional settings are needed.
# Modify the configuration of server_config.py#FSCHAT_MODEL_WORKERS
"model_name": {'host': DEFAULT_BIND_HOST, 'port': 20057}
```



<br>量化模型接入

```bash
# If you need to support the codellama-34b-int4 model, you need to patch fastchat
cp examples/gptq.py ~/site-packages/fastchat/modules/gptq.py
# If you need to support the qwen-72b-int4 model, you need to patch fastchat
cp examples/gptq.py ~/site-packages/fastchat/modules/gptq.py

# Quantization requires modification of the llm_api.py configuration
# Uncomment `kwargs["gptq_wbits"] = 4` in examples/llm_api.py#559
```

## Public Large Model Interface Access

```bash
# Modification of model_config.py configuration
# ONLINE_LLM_MODEL
# Other interface development comes from the langchain-chatchat project, untested due to lack of relevant accounts.
# Specify the model service to be launched, keeping both consistent
LLM_MODEL = "gpt-3.5-turbo"
LLM_MODELs = ["gpt-3.5-turbo"]
```

外部大模型接口接入示例

```bash
# 1. Implement a new model access class
# Refer to ~/examples/model_workers/openai.py#ExampleWorker
# Implementing the do_chat function will enable the use of LLM capabilities

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


# Finally, complete the registration in ~/examples/model_workers/__init__.py
# from .xx import XXWorker

# 2. Complete access through an existing model access class
# Or directly use the existing relevant large model class for use (lacking relevant account testing, community contributions after testing are welcome)
```


```bash
# Modification of model_config.py#ONLINE_LLM_MODEL configuration
# Enter exclusive model details: version, api_base_url, api_key, provider (consistent with the class name above)
ONLINE_LLM_MODEL = {
    # Online models. Please set different ports for each online API in server_config.
    "openai-api": {
        "model_name": "gpt-3.5-turbo",
        "api_base_url": "https://api.openai.com/v1",
        "api_key": "",
        "openai_proxy": "",
    },
    "example": {
        "version": "gpt-3.5",  # Using openai interface as an example
        "api_base_url": "https://api.openai.com/v1",
        "api_key": "",
        "provider": "ExampleWorker",
    },
}
```

## Launching Large Model Services
```bash
# start llm-service (optional)  - Launch the large model service separately
python examples/llm_api.py
```

```bash
# Test
import openai
# openai.api_key = "EMPTY" # Not support yet
openai.api_base = "http://127.0.0.1:8888/v1"
# Select the model you launched
model = "example"
# create a chat completion
completion = openai.ChatCompletion.create(
    model=model,
    messages=[{"role": "user", "content": "Hello! What is your name? "}],
    max_tokens=100,
)
# print the completion
print(completion.choices[0].message.content)
# Once the correct output is confirmed, LLM can be accessed normally.
```



or

```bash
# model_config.py#USE_FASTCHAT - Determine whether to integrate local models via fastchat
USE_FASTCHAT = "gpt" not in LLM_MODEL
python start.py #221 Automatically executes python llm_api.py
```