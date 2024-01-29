
If you need to deploy a privatized model, please install the NVIDIA driver yourself.

### Preparation of Python environment
- It is recommended to use conda to manage the python environment (optional)
```bash
# Prepare conda environment
conda create --name Codefusegpt python=3.9
conda activate Codefusegpt
```

- Install related dependencies
```bash
cd Codefuse-ChatBot
pip install -r requirements.txt
```

### Sandbox Environment Preparation
- Windows Docker installation:
[Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) supports 64-bit versions of Windows 10 Pro with Hyper-V enabled (Hyper-V is not required for versions v1903 and above), or 64-bit versions of Windows 10 Home v1903 and above.
  - [【全面详细】Windows10 Docker安装详细教程](https://zhuanlan.zhihu.com/p/441965046)
  - [Docker 从入门到实践](https://yeasy.gitbook.io/docker_practice/install/windows)
  - [Handling 'Docker Desktop requires the Server service to be enabled'](https://blog.csdn.net/sunhy_csdn/article/details/106526991)
  - [安装wsl或者等报错提示](https://learn.microsoft.com/zh-cn/windows/wsl/install)

- Linux Docker installation：
Linux installation is relatively simple, please search Baidu/Google for installation guides.

- Mac Docker installation
  - [Docker 从入门到实践](https://yeasy.gitbook.io/docker_practice/install/mac)

```bash
# Build the image for the sandbox environment, see above for notebook version issues
bash docker_build.sh
```

### Model Download (Optional)

If you need to use open-source LLM and Embedding models, you can download them from HuggingFace.
Here we take THUDM/chatglm2-6b and text2vec-base-chinese as examples:

```
# install git-lfs
git lfs install

# install LLM-model
git lfs clone https://huggingface.co/THUDM/chatglm2-6b
cp ~/THUDM/chatglm2-6b ~/codefuse-chatbot/llm_models/

# install Embedding-model
git lfs clone https://huggingface.co/shibing624/text2vec-base-chinese
cp ~/shibing624/text2vec-base-chinese ~/codefuse-chatbot/embedding_models/
```



### Basic Configuration

```bash
# Modify the basic configuration for service startup
cd configs
cp model_config.py.example model_config.py
cp server_config.py.example server_config.py

# model_config#11~12 If you need to use the OpenAI interface, the OpenAI interface key
os.environ["OPENAI_API_KEY"] = "sk-xxx"
# Replace with the api_base_url you need
os.environ["API_BASE_URL"] = "https://api.openai.com/v1"

# vi model_config#LLM_MODEL The language model you need to choose
LLM_MODEL = "gpt-3.5-turbo"
LLM_MODELs = ["gpt-3.5-turbo"]

# vi model_config#EMBEDDING_MODEL The private vector model you need to choose
EMBEDDING_ENGINE = 'model'
EMBEDDING_MODEL = "text2vec-base"

# Example of vector model access, modify model_config#embedding_model_dict
# If the model directory is:
model_dir: ~/codefuse-chatbot/embedding_models/shibing624/text2vec-base-chinese
# Configure as follows
"text2vec-base": "shibing624/text2vec-base-chinese"


# vi server_config#8~14, It's recommended to use a container to start the service to prevent environment conflicts when installing other dependencies using the codeInterpreter feature
DOCKER_SERVICE = True
# Whether to use a container sandbox
SANDBOX_DO_REMOTE = True
```



### Starting the Service

By default, only the webui-related services are started, and fastchat is not started (optional).

```bash
# If you need to support the codellama-34b-int4 model, you need to patch fastchat
# cp examples/gptq.py ~/site-packages/fastchat/modules/gptq.py
# Modify examples/llm_api.py#258 to kwargs={"gptq_wbits": 4},

# start llm-service (optional)
python examples/llm_api.py
```
For more LLM integration methods, see[more details...](sources/readme_docs/fastchat-en.md)
<br>

```bash
# After completing the server_config.py configuration, you can start with one click
cd examples
python start.py
```