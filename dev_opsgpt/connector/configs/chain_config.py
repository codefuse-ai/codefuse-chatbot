

CHAIN_CONFIGS = {
    "chatChain": {
        "chain_name": "chatChain",
        "chain_type": "BaseChain",
        "agents": ["answer"],
        "chat_turn": 1,
        "do_checker": False,
        "clear_structure": "True",
        "brainstorming": "False",
        "gui_design": "True",
        "git_management": "False",
        "self_improve": "False"
    },
    "docChatChain": {
        "chain_name": "docChatChain",
        "chain_type": "BaseChain",
        "agents": ["qaer"],
        "chat_turn": 1,
        "do_checker": False,
        "clear_structure": "True",
        "brainstorming": "False",
        "gui_design": "True",
        "git_management": "False",
        "self_improve": "False"
    },
    "searchChatChain": {
        "chain_name": "searchChatChain",
        "chain_type": "BaseChain",
        "agents": ["searcher"],
        "chat_turn": 1,
        "do_checker": False,
        "clear_structure": "True",
        "brainstorming": "False",
        "gui_design": "True",
        "git_management": "False",
        "self_improve": "False"
    },
    "codeChatChain": {
        "chain_name": "codehChatChain",
        "chain_type": "BaseChain",
        "agents": ["code_qaer"],
        "chat_turn": 1,
        "do_checker": False,
        "clear_structure": "True",
        "brainstorming": "False",
        "gui_design": "True",
        "git_management": "False",
        "self_improve": "False"
    },
    "toolReactChain": {
        "chain_name": "toolReactChain",
        "chain_type": "BaseChain",
        "agents": ["tool_planner", "tool_react"],
        "chat_turn": 2,
        "do_checker": True,
        "clear_structure": "True",
        "brainstorming": "False",
        "gui_design": "True",
        "git_management": "False",
        "self_improve": "False"
    },
    "codeReactChain": {
        "chain_name": "codeReactChain",
        "chain_type": "BaseChain",
        "agents": ["planner", "code_react"],
        "chat_turn": 2,
        "do_checker": True,
        "clear_structure": "True",
        "brainstorming": "False",
        "gui_design": "True",
        "git_management": "False",
        "self_improve": "False"
    },
    "dataAnalystChain": {
        "chain_name": "dataAnalystChain",
        "chain_type": "BaseChain",
        "agents": ["planner", "code_react"],
        "chat_turn": 2,
        "do_checker": True,
        "clear_structure": "True",
        "brainstorming": "False",
        "gui_design": "True",
        "git_management": "False",
        "self_improve": "False"
    },
}
