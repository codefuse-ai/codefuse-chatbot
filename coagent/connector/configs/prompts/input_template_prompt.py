

BASE_PROMPT_INPUT = '''#### Begin!!!
'''

PLAN_PROMPT_INPUT = '''#### Begin!!!
**Question:** {query}
'''

REACT_PROMPT_INPUT = '''#### Begin!!!
{query}
'''


CONTEXT_PROMPT_INPUT = '''#### Begin!!!
**Context:** {context}
'''

QUERY_CONTEXT_DOC_PROMPT_INPUT = '''#### Begin!!!
**Origin Query:** {query}

**Context:** {context}

**DocInfos:** {DocInfos}
'''

QUERY_CONTEXT_PROMPT_INPUT = '''#### Begin!!!
**Origin Query:** {query}

**Context:** {context}
'''

EXECUTOR_PROMPT_INPUT = '''#### Begin!!!
{query}
'''

BEGIN_PROMPT_INPUT = '''#### Begin!!!
'''

CHECK_PROMPT_INPUT = '''下面是用户的原始问题：{query}'''
