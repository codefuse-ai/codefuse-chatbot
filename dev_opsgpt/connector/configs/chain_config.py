from enum import Enum
# from .prompts import PLANNER_TEMPLATE_PROMPT



CHAIN_CONFIGS = {
    "chatChain": {
        "chain_name": "chatChain",
        "chain_type": "BaseChain",
        "agents": ["qaer"],
        "chat_turn": 1,
        "do_checker": False,
        "chain_prompt": ""
    },
    "docChatChain": {
        "chain_name": "docChatChain",
        "chain_type": "BaseChain",
        "agents": ["qaer"],
        "chat_turn": 1,
        "do_checker": False,
        "chain_prompt": ""
    },
    "searchChatChain": {
        "chain_name": "searchChatChain",
        "chain_type": "BaseChain",
        "agents": ["searcher"],
        "chat_turn": 1,
        "do_checker": False,
        "chain_prompt": ""
    },
    "codeChatChain": {
        "chain_name": "codehChatChain",
        "chain_type": "BaseChain",
        "agents": ["code_qaer"],
        "chat_turn": 1,
        "do_checker": False,
        "chain_prompt": ""
    },
    "toolReactChain": {
        "chain_name": "toolReactChain",
        "chain_type": "BaseChain",
        "agents": ["tool_planner", "tool_react"],
        "chat_turn": 2,
        "do_checker": True,
        "chain_prompt": ""
    },
    "codePlannerChain": {
        "chain_name": "codePlannerChain",
        "chain_type": "BaseChain",
        "agents": ["planner"],
        "chat_turn": 1,
        "do_checker": True,
        "chain_prompt": ""
    },
    "codeReactChain": {
        "chain_name": "codeReactChain",
        "chain_type": "BaseChain",
        "agents": ["code_react"],
        "chat_turn": 6,
        "do_checker": True,
        "chain_prompt": ""
    },
    "codeToolPlanChain": {
        "chain_name": "codeToolPlanChain",
        "chain_type": "BaseChain",
        "agents": ["tool_and_code_planner"],
        "chat_turn": 1,
        "do_checker": False,
        "chain_prompt": ""
    },
    "codeToolReactChain": {
        "chain_name": "codeToolReactChain",
        "chain_type": "BaseChain",
        "agents": ["tool_and_code_react"],
        "chat_turn": 3,
        "do_checker": True,
        "chain_prompt": ""
    },
    "planChain": {
        "chain_name": "planChain",
        "chain_type": "BaseChain",
        "agents": ["general_planner"],
        "chat_turn": 1,
        "do_checker": False,
        "chain_prompt": ""
    },
    "executorChain": {
        "chain_name": "executorChain",
        "chain_type": "BaseChain",
        "agents": ["executor"],
        "chat_turn": 1,
        "do_checker": True,
        "chain_prompt": ""
    },
    "executorRefineChain": {
        "chain_name": "executorRefineChain",
        "chain_type": "BaseChain",
        "agents": ["executor", "base_refiner"],
        "chat_turn": 3,
        "do_checker": True,
        "chain_prompt": ""
    },
    "metagptChain": {
        "chain_name": "metagptChain",
        "chain_type": "BaseChain",
        "agents": ["metaGPT_PRD", "metaGPT_DESIGN", "metaGPT_TASK", "metaGPT_CODER"],
        "chat_turn": 1,
        "do_checker": False,
        "chain_prompt": ""
    },
}
