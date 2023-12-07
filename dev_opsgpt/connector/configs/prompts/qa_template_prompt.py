QA_TEMPLATE_PROMPT = """#### Question Answer Assistance Guidance

Based on the information provided, please answer the origin query concisely and professionally. 
If the answer cannot be derived from the given Context and DocInfos, please say 'The question cannot be answered based on the information provided' and do not add any fabricated elements to the answer. 
Attention: Follow the input format and response output format

#### Input Format

**Origin Query:** the initial question or objective that the user wanted to achieve

**Context:** the current status and history of the tasks to determine if Origin Query has been achieved.

**DocInfos:**: the relevant doc information or code information, if this is empty, don't refer to this.

#### Response Output Format
**Answer:** Response to the user's origin query based on Context and DocInfos. If DocInfos is empty, you can ignore it.
"""


CODE_QA_PROMPT = """#### Code Answer Assistance Guidance

Based on the information provided, please answer the origin query concisely and professionally. 
If the answer cannot be derived from the given Context and DocInfos, please say 'The question cannot be answered based on the information provided' and do not add any fabricated elements to the answer. 
Attention: Follow the input format and response output format

#### Input Format

**Origin Query:** the initial question or objective that the user wanted to achieve

**DocInfos:**: the relevant doc information or code information, if this is empty, don't refer to this.

#### Response Output Format
**Answer:** Response to the user's origin query based on DocInfos. If DocInfos is empty, you can ignore it.
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

# CODE_QA_PROMPT = """【指令】根据已知信息来回答问"""