import os, sys

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(src_dir)

from configs import llm_model_dict, LLM_MODEL
import openai
# os.environ["OPENAI_PROXY"] = "socks5h://127.0.0.1:7890"
# os.environ["OPENAI_PROXY"] = "http://127.0.0.1:7890"
os.environ["OPENAI_API_KEY"] = ""


if __name__ == "__main__":
    # print("dsadsa", os.environ.get("OPENAI_PROXY"), os.environ.get("OPENAI_API_KEY"))
    from langchain import PromptTemplate, LLMChain
    from langchain.prompts.chat import ChatPromptTemplate
    from langchain.chat_models import ChatOpenAI
    from langchain.schema import HumanMessage
    
    # chat = ChatOpenAI(temperature=0.1, model_name="gpt-3.5-turbo")
    # print(chat.predict("hi!"))

    print(LLM_MODEL, llm_model_dict[LLM_MODEL]["api_key"], llm_model_dict[LLM_MODEL]["api_base_url"])
    model = ChatOpenAI(
        streaming=True,
        verbose=True,
        openai_api_key=llm_model_dict[LLM_MODEL]["api_key"],
        openai_api_base=llm_model_dict[LLM_MODEL]["api_base_url"],
        model_name=LLM_MODEL
    )
    chat_prompt = ChatPromptTemplate.from_messages([("human", "{input}")])
    chain = LLMChain(prompt=chat_prompt, llm=model)
    content = chain({"input": "hello"})
    print(content)