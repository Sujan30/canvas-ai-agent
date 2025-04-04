import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import re

load_dotenv()


llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=os.getenv('GEMINI_API_KEY'))

def check_work(instructions: str, answers: str, supplemental_info: str = "None"):
    messages = [
        SystemMessage(
            content=(
                "You are a teacher grading a student's assignment.\n\n"
                "Instructions:\n"
                f"{instructions}\n\n"
                "The student's answer will be shown next. Your job is to:\n"
                "1. Check if the student's answer follows the instructions.\n"
                "2. Check if the answer sounds human-written (not AI-generated).\n"
                "3. Use the PDF content (if provided) to verify accuracy.\n\n"
                "Return your evaluation in strict JSON format like this:\n"
                "{\n"
                '  "passed": true,\n'
                '  "human_written": true,\n'
                '  "score": 9.5,\n'
                '  "feedback": "Good job. Try adding more explanation in part b."\n'
                "}\n"
                "Only return valid JSON, no commentary."
            )
        ),
        HumanMessage(
            content=f"Student's answer:\n{answers}\n\nPDF content (if available): {supplemental_info}"
        )
    ]

    response = llm.invoke(messages)

    
    try:
        raw_content = response.content.strip()
        if raw_content.startswith("```json"):
            raw_content = re.sub(r"```json|```", "", raw_content).strip()
        if raw_content.endswith("```"):
            raw_content = raw_content[-3:].strip()

        evaluation = json.loads(raw_content)
    except json.JSONDecodeError as e:
        print("⚠️ Failed to parse Gemini output as JSON. Raw response:")
        print(response.content)
        evaluation = {
            "passed": False,
            "human_written": False,
            "score": 0,
            "feedback": f"Failed to parse model output. Error: {str(e)}"
        }

    return evaluation


