CONV_SUMMARY_PROMPT = """尽可能地以有帮助和准确的方式回应人类，根据“背景信息”中的有效信息回答问题，
使用 JSON Blob 来指定一个返回的内容，提供一个 action（行动）。
有效的 'action' 值为：'finished'(任务已经可以通过上下文信息可以回答) or 'continue' （根据背景信息回答问题）。
在每个 $JSON_BLOB 中仅提供一个 action，如下所示：
```
{{'action': $ACTION, 'content': '根据背景信息回答问题'}}
```
按照以下格式进行回应：
问题：输入问题以回答
行动：
```
$JSON_BLOB
```
"""

CONV_SUMMARY_PROMPT = """尽可能地以有帮助和准确的方式回应人类
根据“背景信息”中的有效信息回答问题，同时展现解答的过程和内容
若能根“背景信息”回答问题，则直接回答
否则，总结“背景信息”的内容
"""


CONV_SUMMARY_PROMPT_SPEC = """
Your job is to summarize a history of previous messages in a conversation between an AI persona and a human.
The conversation you are given is a fixed context window and may not be complete.
Messages sent by the AI are marked with the 'assistant' role.
The AI 'assistant' can also make calls to functions, whose outputs can be seen in messages with the 'function' role.
Things the AI says in the message content are considered inner monologue and are not seen by the user.
The only AI messages seen by the user are from when the AI uses 'send_message'.
Messages the user sends are in the 'user' role.
The 'user' role is also used for important system events, such as login events and heartbeat events (heartbeats run the AI's program without user action, allowing the AI to act without prompting from the user sending them a message).
Summarize what happened in the conversation from the perspective of the AI (use the first person).
Keep your summary less than 100 words, do NOT exceed this word limit.
Only output the summary, do NOT include anything else in your output.

--- conversation
{conversation}
---

"""