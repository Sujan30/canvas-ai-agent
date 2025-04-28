from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent

load_dotenv()




text = "Okay, so, Dr. John McWhorter's Talking Back, Talking Black video? It's all about African American English (AAE), and it really opened my eyes. I mean, before this course, I kinda had some of those common misconceptions, you know? McWhorter, who's a linguist, is super passionate about how AAE isn't just some broken version of English. He argues that it's a legitimate dialect with its own set of rules, its own structure.He gets his point across with stories from his own life, some hardcore linguistic stuff, and tons of examples from Black culture – music, history, the whole shebang. It's basically a public lecture, aimed at anyone who's interested, whether you're an academic or just someone off the street. And McWhorter's message is pretty clear: we need to change the way we think about how Black Americans speak. He dives into the richness of AAE's grammar, where it comes from (that mix of African languages and English is fascinating!), and how society's quick to dismiss it as bad English, which, let's be honest, is tied to some deeper issues.Honestly, one of the biggest things I took away was just how *systematic* AAE is. I'll admit, I always just figured it was, like, a casual way of talking, not a full-blown language with grammar rules and all that. But then McWhorter breaks it down – double negatives, the way be is used (He be working), and how it all follows these specific rules. It kind of blew my mind. It reminded me of when I first started learning how programming languages work. You can't just throw code together and expect it to run; it has its own logic, right? That's how AAE is, and that really clicked for me."

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=os.getenv('GEMINI_API_KEY'))


load_dotenv()

async def load_up_scribbr(text: str):
    agent = Agent(
        task=f"You will go to the https://quillbot.scribbr.com/ai-content-detector?independentTool=true&language=en&partnerCompany=scribbr&enableUpsell=true&fullScreen=true&cookieConsent=true&hideCautionBox=true and check if the {text} is AI-generated. You will then output the result, which should be what % of the text is AI-generated.",
        llm=llm,
    )
    await agent.run()

asyncio.run(load_up_scribbr(text))




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

def check_scribbr(sample_text: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # 1️⃣  Navigate to Scribbr AI Detector
        page.goto(
            "https://quillbot.scribbr.com/ai-content-detector?independentTool=true&language=en&partnerCompany=scribbr&enableUpsell=true&fullScreen=true&cookieConsent=true&hideCautionBox=true",
            wait_until="domcontentloaded",
            timeout=60000
        )
        print("✅  Navigated to Scribbr AI Detector")

        # 2️⃣  Wait for the specific contenteditable div to attach
        EDITOR = 'div#aidr-input-editor[role="textbox"][contenteditable="true"]'
        page.wait_for_selector(EDITOR, state="attached", timeout=20000)

        print("✅  Editor found")

        page.wait_for_timeout(1000)

        # 3️⃣  Scroll into view & focus via JS (bypasses any pseudo-element cover)
        page.evaluate(f"""() => {{
            const el = document.querySelector('{EDITOR}');
            el.scrollIntoView({{ block: 'center' }});
            el.focus();
        }}""")
        page.wait_for_timeout(1000)

        # 4️⃣  Clear placeholder (Cmd+A + Backspace)
        page.keyboard.press("Meta+A")
        page.keyboard.press("Backspace")

        page.wait_for_timeout(2000)
        print("✅  Typing text...")

        # 5️⃣  Inject your ≥80-word sample
        page.keyboard.insert_text(sample_text)
        page.wait_for_timeout(4000)

        print("✅  Text typed")

        page.keyboard.insert_text(" ")
        page.wait_for_timeout(4000)

        # 6️⃣  Click the Detect AI button
        print("🔍  Triggering Detect AI via ⌘+Enter…")
        detect_btn = page.get_by_role("button", name="Detect AI")
        detect_btn.wait_for(state="visible", timeout=20000)
        detect_btn.wait_for(state="enabled", timeout=20000)
        detect_btn.click(force=True)
        page.wait_for_timeout(8000)
        # 7️⃣  Wait for results to show up
        try:
            page.wait_for_selector(
                'div[data-testid="aidr-output-box"]',
                state="visible",
                timeout=60000
            )
            print("✅  Results are visible!")
        except PlaywrightTimeoutError:
            print("❌  Timed out waiting for results.")

        print("press enter to close")
        input()

        browser.close()





