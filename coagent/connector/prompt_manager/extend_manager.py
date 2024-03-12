
from coagent.connector.schema import Message
from .prompt_manager import PromptManager


class Code2DocPM(PromptManager):
    def handle_code_snippet(self, **kwargs) -> str:
        if 'previous_agent_message' not in kwargs:
            return ""
        previous_agent_message: Message = kwargs['previous_agent_message']
        code_snippet = previous_agent_message.customed_kargs.get("Code Snippet", "")
        current_vertex = previous_agent_message.customed_kargs.get("Current_Vertex", "")
        instruction = "A segment of code that contains the function or method to be documented.\n"
        return instruction + "\n" + f"name: {current_vertex}\n{code_snippet}"

    def handle_specific_objective(self, **kwargs) -> str:
        if 'previous_agent_message' not in kwargs:
            return ""
        previous_agent_message: Message = kwargs['previous_agent_message']
        specific_objective = previous_agent_message.parsed_output.get("Code Path")

        instruction = "Provide the code path of the function or method you wish to document.\n"
        s = instruction + f"\n{specific_objective}"
        return s
    

class CodeRetrievalPM(PromptManager):
    def handle_code_snippet(self, **kwargs) -> str:
        if 'previous_agent_message' not in kwargs:
            return ""
        previous_agent_message: Message = kwargs['previous_agent_message']
        code_snippet = previous_agent_message.customed_kargs.get("Code Snippet", "")
        current_vertex = previous_agent_message.customed_kargs.get("Current_Vertex", "")
        instruction = "the initial Code or objective that the user wanted to achieve"
        return instruction + "\n" + f"name: {current_vertex}\n{code_snippet}"

    def handle_retrieval_codes(self, **kwargs) -> str:
        if 'previous_agent_message' not in kwargs:
            return ""
        previous_agent_message: Message = kwargs['previous_agent_message']
        Retrieval_Codes = previous_agent_message.customed_kargs["Retrieval_Codes"]
        Relative_vertex = previous_agent_message.customed_kargs["Relative_vertex"]
        instruction = "the initial Code or objective that the user wanted to achieve"
        s = instruction + "\n" + "\n".join([f"name: {vertext}\n{code}" for vertext, code in zip(Relative_vertex, Retrieval_Codes)])
        return s
