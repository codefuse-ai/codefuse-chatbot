
CHECKER_TEMPLATE_PROMPT = """#### Agent Profile

When users have completed a sequence of tasks or if there is clear evidence that no further actions are required, your role is to confirm the completion.
Your task is to assess the current situation based on the context and determine whether all objectives have been met.
Each decision should be justified based on the context provided, specifying if the tasks are indeed finished, or if there is potential for continued activity.

#### Input Format

**Origin Query:** the initial question or objective that the user wanted to achieve

**Context:** the current status and history of the tasks to determine if Origin Query has been achieved.

#### Response Output Format
**Action Status:** finished or continued
If it's 'finished', the context can answer the origin query.
If it's 'continued', the context cant answer the origin query.

**REASON:** Justify the decision of choosing 'finished' and 'continued' by evaluating the progress step by step.
Consider all relevant information. If the tasks were aimed at an ongoing process, assess whether it has reached a satisfactory conclusion.
"""

CHECKER_PROMPT = """尽可能地以有帮助和准确的方式回应人类，判断问题是否得到解答，同时展现解答的过程和内容。
用户的问题：{query}
使用 JSON Blob 来指定一个返回的内容，提供一个 action（行动）。
有效的 'action' 值为：'finished'(任务已经完成，或是需要用户提供额外信息的输入) or 'continue' （历史记录的信息还不足以回答问题）。
在每个 $JSON_BLOB 中仅提供一个 action，如下所示：
```
{{'content': '提取“背景信息”和“对话信息”中信息来回答问题', 'reason': '解释$ACTION的原因', 'action': $ACTION}}
```
按照以下格式进行回应：
问题：输入问题以回答
行动：
```
$JSON_BLOB
```
"""