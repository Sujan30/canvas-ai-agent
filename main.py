import os
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model='gpt-4-o')

def get_best_answer(question, options):
    prompt = f"""Answer the following multiple-choice question. 
    Question: {question}
    Options: {', '.join(options)}

    Only return the exact option you think is correct."""

    response = llm([HumanMessage(content=prompt)])
    return response.content.strip()
