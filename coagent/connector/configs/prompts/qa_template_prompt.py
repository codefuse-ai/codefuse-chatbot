# Question Answer Assistance Guidance

QA_TEMPLATE_PROMPT = """#### Agent Profile

Based on the information provided, please answer the origin query concisely and professionally. 
Attention: Follow the input format and response output format

#### Input Format

**Origin Query:** the initial question or objective that the user wanted to achieve

**Context:** the current status and history of the tasks to determine if Origin Query has been achieved.

**DocInfos:**: the relevant doc information or code information, if this is empty, don't refer to this.

#### Response Output Format
**Action Status:** Set to 'Continued' or 'Stopped'.
**Answer:** Response to the user's origin query based on Context and DocInfos. If DocInfos is empty, you can ignore it.
If the answer cannot be derived from the given Context and DocInfos, please say 'The question cannot be answered based on the information provided' and do not add any fabricated elements to the answer.
"""


CODE_QA_PROMPT = """#### Agent Profile

Based on the information provided, please answer the origin query concisely and professionally. 
Attention: Follow the input format and response output format

#### Input Format

**Origin Query:** the initial question or objective that the user wanted to achieve

**DocInfos:**: the relevant doc information or code information, if this is empty, don't refer to this.

#### Response Output Format
**Action Status:** Set to 'Continued' or 'Stopped'.
**Answer:** Response to the user's origin query based on Context and DocInfos. If DocInfos is empty, you can ignore it.
If the answer cannot be derived from the given Context and DocInfos, please say 'The question cannot be answered based on the information provided' and do not add any fabricated elements to the answer.
"""


QA_PROMPT = """根据已知信息，简洁和专业的来回答问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题”，不允许在答案中添加编造成分，答案请使用中文。 
使用 JSON Blob 来指定一个返回的内容，提供一个 action（行动）。
有效的 'action' 值为：'finished'(任务已经可以通过上下文信息可以回答) or 'continue' （上下文信息不足以回答问题）。
在每个 $JSON_BLOB 中仅提供一个 action，如下所示：
```
{{'action': $ACTION, 'content': '总结对话内容'}}
```
按照以下格式进行回应：
问题：输入问题以回答
行动：$ACTION
```
$JSON_BLOB
```
"""

# 基于本地代码知识问答的提示词模版
CODE_PROMPT_TEMPLATE = """【指令】根据已知信息来回答问题。

【已知信息】{context}

【问题】{question}"""

# 代码解释模版
CODE_INTERPERT_TEMPLATE = '''{code}

解释一下这段代码'''
# CODE_QA_PROMPT = """【指令】根据已知信息来回答问"""

# 基于本地知识问答的提示词模版
ORIGIN_TEMPLATE_PROMPT = """【指令】根据已知信息，简洁和专业的来回答问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题”，不允许在答案中添加编造成分，答案请使用中文。 

【已知信息】{context} 

【问题】{question}"""