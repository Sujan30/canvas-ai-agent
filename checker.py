from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, AgentHistoryList
import re

load_dotenv()




text = "Okay, so, Dr. John McWhorter's Talking Back, Talking Black video? It's all about African American English (AAE), and it really opened my eyes. I mean, before this course, I kinda had some of those common misconceptions, you know? McWhorter, who's a linguist, is super passionate about how AAE isn't just some broken version of English. He argues that it's a legitimate dialect with its own set of rules, its own structure.He gets his point across with stories from his own life, some hardcore linguistic stuff, and tons of examples from Black culture – music, history, the whole shebang. It's basically a public lecture, aimed at anyone who's interested, whether you're an academic or just someone off the street. And McWhorter's message is pretty clear: we need to change the way we think about how Black Americans speak. He dives into the richness of AAE's grammar, where it comes from (that mix of African languages and English is fascinating!), and how society's quick to dismiss it as bad English, which, let's be honest, is tied to some deeper issues.Honestly, one of the biggest things I took away was just how *systematic* AAE is. I'll admit, I always just figured it was, like, a casual way of talking, not a full-blown language with grammar rules and all that. But then McWhorter breaks it down – double negatives, the way be is used (He be working), and how it all follows these specific rules. It kind of blew my mind. It reminded me of when I first started learning how programming languages work. You can't just throw code together and expect it to run; it has its own logic, right? That's how AAE is, and that really clicked for me."

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=os.getenv('GEMINI_API_KEY'))


load_dotenv()

async def load_up_scribbr(text: str) -> float:
    # 1. Prompt it to return *only* the percentage number
    prompt = (
        "Go to the Scribbr AI Content Detector ("
        "https://quillbot.scribbr.com/ai-content-detector?...). "
        f"Paste exactly this text:\n\n'''{text}'''\n\n"
        "Run the check, then respond with ONLY the percentage of AI-generated content "
        "as a number (e.g. 32.5). No extra words."
    )

    

    agent = Agent(task=prompt, llm=llm)
    history = AgentHistoryList()
    raw = await agent.run(history)

    final_step = raw[-1]
    done_action = final_step.action_names()
    score = done_action['done']['text']
    return float(score)

# Example usage












def humanize_text(text: str) -> str:
    messages = [
        SystemMessage(
            content=(
                f"You're job is to make the following text more human-like."
                f"You will follow these instructions on the given text"
                f"You are a skilled human writer with natural language fluency. Rewrite the following text to sound as if it were written entirely by a human. Vary sentence lengths, use natural human-like phrasing, occasional idioms, colloquialisms, and rhetorical questions where appropriate. Avoid robotic or overly formal tone. Maintain the original meaning but make the writing style indistinguishable from a human writer. Add subtle imperfections like minor redundancies, slight passive voice, or casual phrasing that humans naturally use. Output only the rewritten content without any AI-style disclaimers."
                f"You will output the rewritten text only, without any commentary or additional text."
            )
        ),
        HumanMessage(
            content=text
        )
    ]
    message = llm.invoke(messages)
    return message.content




async def work_flow(text: str):
    similarity_score = await load_up_scribbr(text)
    while(similarity_score > 50):
        text = humanize_text(text)
        similarity_score = await load_up_scribbr(text)
    return text    


if __name__ == "__main__":
    result = asyncio.run(load_up_scribbr(text))
    print(result)



