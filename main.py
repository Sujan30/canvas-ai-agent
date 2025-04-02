import os
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model='gpt-4-o')

openai_api_key = os.getenv("OPENAI_API_KEY")



def agent_task(prompt: str):
    modified_prompt = f"Do this Task to the best of your abilities.Here are the instructions:Instructions: {prompt}Do this task in a human manner, and don't sound AI"
    
    llm = ChatOpenAI(model_name='gpt-4', temperature=0)
    message = HumanMessage(content=modified_prompt)
    response = llm([message])
    
    return response.content
