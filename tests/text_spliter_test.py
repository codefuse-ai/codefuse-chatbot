
import os, sys


src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
sys.path.append(src_dir)

from dev_opsgpt.text_splitter import LCTextSplitter

filepath = "D:/project/gitlab/llm/DevOpsGpt/knowledge_base/SAMPLES/content/test.txt" 
lcTextSplitter = LCTextSplitter(filepath)
docs = lcTextSplitter.file2text()

print(docs[0])