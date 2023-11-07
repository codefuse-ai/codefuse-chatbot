import os, sys

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(src_dir)

from dev_opsgpt.text_splitter import LCTextSplitter

filepath = ""
lc_textSplitter = LCTextSplitter(filepath)
docs = lc_textSplitter.file2text()

print(docs[0])