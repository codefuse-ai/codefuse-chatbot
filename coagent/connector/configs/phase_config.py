PHASE_CONFIGS = {
    "chatPhase": {
        "phase_name": "chatPhase",
        "phase_type": "BasePhase",
        "chains": ["chatChain"],
        "do_summary": False,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_code_retrieval": False,
        "do_tool_retrieval": False,
        "do_using_tool": False
    },
    "docChatPhase": {
        "phase_name": "docChatPhase",
        "phase_type": "BasePhase",
        "chains": ["docChatChain"],
        "do_summary": False,
        "do_search": False,
        "do_doc_retrieval": True,
        "do_code_retrieval": False,
        "do_tool_retrieval": False,
        "do_using_tool": False
    },
    "searchChatPhase": {
        "phase_name": "searchChatPhase",
        "phase_type": "BasePhase",
        "chains": ["searchChatChain"],
        "do_summary": False,
        "do_search": True,
        "do_doc_retrieval": False,
        "do_code_retrieval": False,
        "do_tool_retrieval": False,
        "do_using_tool": False
    },
    "codeChatPhase": {
        "phase_name": "codeChatPhase",
        "phase_type": "BasePhase",
        "chains": ["codeChatChain"],
        "do_summary": False,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_code_retrieval": True,
        "do_tool_retrieval": False,
        "do_using_tool": False
    },
    "toolReactPhase": {
        "phase_name": "toolReactPhase",
        "phase_type": "BasePhase",
        "chains": ["toolReactChain"],
        "do_summary": False,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_code_retrieval": False,
        "do_tool_retrieval": False,
        "do_using_tool": True
    },
    "codeReactPhase": {
        "phase_name": "codeReactPhase",
        "phase_type": "BasePhase",
        # "chains": ["codePlannerChain", "codeReactChain"],
        "chains": ["planChain", "codeReactChain"],
        "do_summary": False,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_code_retrieval": False,
        "do_tool_retrieval": False,
        "do_using_tool": False
    },
    "codeToolReactPhase": {
        "phase_name": "codeToolReactPhase",
        "phase_type": "BasePhase",
        "chains": ["codeToolPlanChain", "codeToolReactChain"],
        "do_summary": False,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_code_retrieval": False,
        "do_tool_retrieval": False,
        "do_using_tool": True
    },
    "baseTaskPhase": {
        "phase_name": "baseTaskPhase",
        "phase_type": "BasePhase",
        "chains": ["planChain", "executorChain"],
        "do_summary": False,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_code_retrieval": False,
        "do_tool_retrieval": False,
        "do_using_tool": False
    },
    "metagpt_code_devlop": {
        "phase_name": "metagpt_code_devlop",
        "phase_type": "BasePhase",
        "chains": ["metagptChain",],
        "do_summary": False,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_code_retrieval": False,
        "do_tool_retrieval": False,
        "do_using_tool": False
    },
    "baseGroupPhase": {
        "phase_name": "baseGroupPhase",
        "phase_type": "BasePhase",
        "chains": ["baseGroupChain"],
        "do_summary": False,
        "do_search": False,
        "do_doc_retrieval": False,
        "do_code_retrieval": False,
        "do_tool_retrieval": False,
        "do_using_tool": False
    },
}
