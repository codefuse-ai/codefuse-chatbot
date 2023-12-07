from enum import Enum
from .prompts import (
    REACT_PROMPT_INPUT, CHECK_PROMPT_INPUT, EXECUTOR_PROMPT_INPUT, CONTEXT_PROMPT_INPUT, QUERY_CONTEXT_PROMPT_INPUT,PLAN_PROMPT_INPUT,
    RECOGNIZE_INTENTION_PROMPT,
    CHECKER_TEMPLATE_PROMPT,
    CONV_SUMMARY_PROMPT,
    QA_PROMPT, CODE_QA_PROMPT, QA_TEMPLATE_PROMPT,
    EXECUTOR_TEMPLATE_PROMPT,
    REFINE_TEMPLATE_PROMPT,
    PLANNER_TEMPLATE_PROMPT, GENERAL_PLANNER_PROMPT, DATA_PLANNER_PROMPT, TOOL_PLANNER_PROMPT,
    PRD_WRITER_METAGPT_PROMPT, DESIGN_WRITER_METAGPT_PROMPT, TASK_WRITER_METAGPT_PROMPT, CODE_WRITER_METAGPT_PROMPT,
    REACT_TEMPLATE_PROMPT,
    REACT_TOOL_PROMPT, REACT_CODE_PROMPT, REACT_TOOL_AND_CODE_PLANNER_PROMPT, REACT_TOOL_AND_CODE_PROMPT
)



class AgentType:
    REACT = "ReactAgent"
    EXECUTOR = "ExecutorAgent"
    ONE_STEP = "BaseAgent"
    DEFAULT = "BaseAgent"



AGETN_CONFIGS = {
    "checker": {
        "role": {
            "role_prompt": CHECKER_TEMPLATE_PROMPT,
            "role_type": "assistant",
            "role_name": "checker",
            "role_desc": "",
            "agent_type": "BaseAgent"
        },
        "chat_turn": 1,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False
    },
    "conv_summary": {
        "role": {
            "role_prompt": CONV_SUMMARY_PROMPT,
            "role_type": "assistant",
            "role_name": "conv_summary",
            "role_desc": "",
            "agent_type": "BaseAgent"
        },
        "chat_turn": 1,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False
    },
    "general_planner": {
        "role": {
            "role_prompt": PLANNER_TEMPLATE_PROMPT,
            "role_type": "assistant",
            "role_name": "general_planner",
            "role_desc": "",
            "agent_type": "BaseAgent"
        },
        "chat_turn": 1,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False
    },
    "executor": {
        "role": {
            "role_prompt": EXECUTOR_TEMPLATE_PROMPT,
            "role_type": "assistant",
            "role_name": "executor",
            "role_desc": "",
            "agent_type": "ExecutorAgent",
        },
        "stop": "\n**Observation:**",
        "chat_turn": 1,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False
    },
    "base_refiner": {
        "role": {
            "role_prompt": REFINE_TEMPLATE_PROMPT,
            "role_type": "assistant",
            "role_name": "base_refiner",
            "role_desc": "",
            "agent_type": "BaseAgent"
        },
        "chat_turn": 1,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False
    },
    "planner": {
        "role": {
            "role_prompt": DATA_PLANNER_PROMPT,
            "role_type": "assistant",
            "role_name": "planner",
            "role_desc": "",
            "agent_type": "BaseAgent"
        },
        "chat_turn": 1,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False
    },
    "intention_recognizer": {
        "role": {
            "role_prompt": RECOGNIZE_INTENTION_PROMPT,
            "role_type": "assistant",
            "role_name": "intention_recognizer",
            "role_desc": "",
            "agent_type": "BaseAgent"
        },
        "chat_turn": 1,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False
    },
    "tool_planner": {
        "role": {
            "role_prompt": TOOL_PLANNER_PROMPT,
            "role_type": "assistant",
            "role_name": "tool_planner",
            "role_desc": "",
            "agent_type": "BaseAgent"
        },
        "chat_turn": 1,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False
    },
    "tool_and_code_react": {
        "role": {
            "role_prompt": REACT_TOOL_AND_CODE_PROMPT,
            "role_type": "assistant",
            "role_name": "tool_and_code_react",
            "role_desc": "",
            "agent_type": "ReactAgent",
        },
        "stop": "\n**Observation:**",
        "chat_turn": 7,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False
    },
    "tool_and_code_planner": {
        "role": {
            "role_prompt": REACT_TOOL_AND_CODE_PLANNER_PROMPT,
            "role_type": "assistant",
            "role_name": "tool_and_code_planner",
            "role_desc": "",
            "agent_type": "BaseAgent"
        },
        "chat_turn": 1,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False
    },
    "tool_react": {
        "role": {
            "role_prompt": REACT_TOOL_PROMPT,
            "role_type": "assistant",
            "role_name": "tool_react",
            "role_desc": "",
            "agent_type": "ReactAgent"
        },
        "chat_turn": 5,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False,
        "stop": "\n**Observation:**"
    },
    "code_react": {
        "role": {
            "role_prompt": REACT_CODE_PROMPT,
            "role_type": "assistant",
            "role_name": "code_react",
            "role_desc": "",
            "agent_type": "ReactAgent"
        },
        "chat_turn": 5,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False,
        "stop": "\n**Observation:**"
    },
    "qaer": {
        "role": {
            "role_prompt": QA_TEMPLATE_PROMPT,
            "role_type": "assistant",
            "role_name": "qaer",
            "role_desc": "",
            "agent_type": "BaseAgent"
        },
        "chat_turn": 1,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False
    },
    "code_qaer": {
        "role": {
            "role_prompt": CODE_QA_PROMPT ,
            "role_type": "assistant",
            "role_name": "code_qaer",
            "role_desc": "",
            "agent_type": "BaseAgent"
        },
        "chat_turn": 1,
        "do_search": False,
        "do_doc_retrieval": True,
        "do_tool_retrieval": False
    },
    "searcher": {
        "role": {
            "role_prompt": QA_TEMPLATE_PROMPT,
            "role_type": "assistant",
            "role_name": "searcher",
            "role_desc": "",
            "agent_type": "BaseAgent"
        },
        "chat_turn": 1,
        "do_search": True,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False
    },
    "metaGPT_PRD": {
        "role": {
            "role_prompt": PRD_WRITER_METAGPT_PROMPT,
            "role_type": "assistant",
            "role_name": "metaGPT_PRD",
            "role_desc": "",
            "agent_type": "BaseAgent"
        },
        "chat_turn": 1,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False,
        "focus_agents": [],
        "focus_message_keys": [],
    },

    "metaGPT_DESIGN": {
        "role": {
            "role_prompt": DESIGN_WRITER_METAGPT_PROMPT,
            "role_type": "assistant",
            "role_name": "metaGPT_DESIGN",
            "role_desc": "",
            "agent_type": "BaseAgent"
        },
        "chat_turn": 1,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False,
        "focus_agents": ["metaGPT_PRD"],
        "focus_message_keys": [],
    },
    "metaGPT_TASK": {
        "role": {
            "role_prompt": TASK_WRITER_METAGPT_PROMPT,
            "role_type": "assistant",
            "role_name": "metaGPT_TASK",
            "role_desc": "",
            "agent_type": "BaseAgent"
        },
        "chat_turn": 1,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False,
        "focus_agents": ["metaGPT_DESIGN"],
        "focus_message_keys": [],
    },
    "metaGPT_CODER": {
        "role": {
            "role_prompt": CODE_WRITER_METAGPT_PROMPT,
            "role_type": "assistant",
            "role_name": "metaGPT_CODER",
            "role_desc": "",
            "agent_type": "ExecutorAgent"
        },
        "chat_turn": 1,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_tool_retrieval": False,
        "focus_agents": ["metaGPT_DESIGN", "metaGPT_TASK"],
        "focus_message_keys": [],
    },
}