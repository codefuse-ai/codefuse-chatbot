BASE_PROMPT_CONFIGS = [
    {"field_name": 'agent_profile', "function_name": 'handle_agent_profile', "is_context": False},
    {"field_name": 'tool_information',"function_name": 'handle_tool_data', "is_context": False},
    {"field_name": 'context_placeholder', "function_name": '', "is_context": True},
    {"field_name": 'reference_documents', "function_name": 'handle_doc_info'},
    {"field_name": 'session_records', "function_name": 'handle_session_records'},
    {"field_name": 'task_records', "function_name": 'handle_task_records'},
    {"field_name": 'output_format', "function_name": 'handle_output_format', 'title': 'Response Output Format', "is_context": False},
    {"field_name": 'begin!!!', "function_name": 'handle_response', "is_context": False, "omit_if_empty": False}
    ]

BASE_NOTOOLPROMPT_CONFIGS = [
    {"field_name": 'agent_profile', "function_name": 'handle_agent_profile', "is_context": False},
    {"field_name": 'context_placeholder', "function_name": '', "is_context": True},
    {"field_name": 'reference_documents', "function_name": 'handle_doc_info'},
    {"field_name": 'session_records', "function_name": 'handle_session_records'},
    {"field_name": 'output_format', "function_name": 'handle_output_format', 'title': 'Response Output Format', "is_context": False},
    {"field_name": 'begin!!!', "function_name": 'handle_response', "is_context": False, "omit_if_empty": False}
    ]

EXECUTOR_PROMPT_CONFIGS = [
    {"field_name": 'agent_profile', "function_name": 'handle_agent_profile', "is_context": False},
    {"field_name": 'tool_information',"function_name": 'handle_tool_data', "is_context": False},
    {"field_name": 'context_placeholder', "function_name": '', "is_context": True},
    {"field_name": 'reference_documents', "function_name": 'handle_doc_info'},
    {"field_name": 'session_records', "function_name": 'handle_session_records'},
    {"field_name": 'task_records', "function_name": 'handle_task_records'},
    {"field_name": 'current_plan', "function_name": 'handle_current_plan'},
    {"field_name": 'output_format', "function_name": 'handle_output_format', 'title': 'Response Output Format', "is_context": False},
    {"field_name": 'begin!!!', "function_name": 'handle_response', "is_context": False, "omit_if_empty": False}
    ]

SELECTOR_PROMPT_CONFIGS = [
    {"field_name": 'agent_profile', "function_name": 'handle_agent_profile', "is_context": False},
    {"field_name": 'tool_information',"function_name": 'handle_tool_data', "is_context": False},
    {"field_name": 'agent_infomation', "function_name": 'handle_agent_data', "is_context": False, "omit_if_empty": False},
    {"field_name": 'context_placeholder', "function_name": '', "is_context": True},
    {"field_name": 'reference_documents', "function_name": 'handle_doc_info'},
    {"field_name": 'session_records', "function_name": 'handle_session_records'},
    {"field_name": 'current_plan', "function_name": 'handle_current_plan'},
    {"field_name": 'output_format', "function_name": 'handle_output_format', 'title': 'Response Output Format', "is_context": False},
    {"field_name": 'begin!!!', "function_name": 'handle_response', "is_context": False, "omit_if_empty": False}
    ]