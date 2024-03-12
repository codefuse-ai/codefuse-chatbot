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
        "do_doc_retrieval": True,
    },
    "searchChatPhase": {
        "phase_name": "searchChatPhase",
        "phase_type": "BasePhase",
        "chains": ["searchChatChain"],
        "do_search": True,
    },
    "codeChatPhase": {
        "phase_name": "codeChatPhase",
        "phase_type": "BasePhase",
        "chains": ["codeChatChain"],
        "do_code_retrieval": True,
    },
    "toolReactPhase": {
        "phase_name": "toolReactPhase",
        "phase_type": "BasePhase",
        "chains": ["toolReactChain"],
        "do_using_tool": True
    },
    "codeReactPhase": {
        "phase_name": "codeReactPhase",
        "phase_type": "BasePhase",
        # "chains": ["codePlannerChain", "codeReactChain"],
        "chains": ["planChain", "codeReactChain"],
    },
    "codeToolReactPhase": {
        "phase_name": "codeToolReactPhase",
        "phase_type": "BasePhase",
        "chains": ["codeToolPlanChain", "codeToolReactChain"],
        "do_using_tool": True
    },
    "baseTaskPhase": {
        "phase_name": "baseTaskPhase",
        "phase_type": "BasePhase",
        "chains": ["planChain", "executorChain"],
    },
    "metagpt_code_devlop": {
        "phase_name": "metagpt_code_devlop",
        "phase_type": "BasePhase",
        "chains": ["metagptChain",],
    },
    "baseGroupPhase": {
        "phase_name": "baseGroupPhase",
        "phase_type": "BasePhase",
        "chains": ["baseGroupChain"],
    },
    "code2DocsGroup": {
        "phase_name": "code2DocsGroup",
        "phase_type": "BasePhase",
        "chains": ["code2DocsGroupChain"],
    },
    "code2Tests": {
        "phase_name": "code2Tests",
        "phase_type": "BasePhase",
        "chains": ["code2TestsChain"],
    }
}
