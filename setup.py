import setuptools

# with open("README.md", "r", encoding="utf-8") as fh:
#     long_description = fh.read()

setuptools.setup(
    name="coagent",
    # version="0.0.3_beta",
    version="0.0.1",
    author="shanshi",
    author_email="wyp311395@antgroup.com",
    description="A multi-agent framework that facilitates the rapid construction of collaborative teams of agents.",
    # long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/codefuse-ai/codefuse-chatbot",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "openai==0.28.1",
        "langchain==0.0.266",
        "sentence_transformers",
        "loguru",
        "fastapi~=0.99.1",
        "pandas",
        "jieba",
        "psutil",
        "faiss-cpu",
        "notebook",
        # 
        "chromadb==0.4.17",
        "javalang==0.13.0",
        "nebula3-python==3.1.0",
        # 
        "duckduckgo-search",
    ],
)