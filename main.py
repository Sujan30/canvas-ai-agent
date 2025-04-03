from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


import os

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

def load_pdf_for_langchain(pdf_path: str):
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    docs = text_splitter.split_documents(pages)
    return docs

def agent_task(instructions: str, pdf_path = None):
    
    # Load and split PDF content
    if pdf_path:
        docs = load_pdf_for_langchain(pdf_path)
        context = "\n\n".join([doc.page_content for doc in docs[:5]])  # Limit to 5 chunks for token efficiency

        full_prompt = (
        f"Instructions: {instructions}\n\n"
        f"Here is the PDF content:\n{context}\n\n"
        f"Follow the instructions above using the context from the PDF. Be detailed and human."
        f"AI detectors shouldn't be able to detect you!"
        )
    else:
        full_prompt = (
        f"Instructions: {instructions}\n\n"
        f"Follow the instructions above using the context from the PDF. Be detailed and human."
        f"AI detectors shouldn't be able to detect you!"
        )


    
    response = llm.invoke(full_prompt)
    print(f'Assignment finished RAHHH: {response.content} Sujan: 1 SJSU: 0')
    return response.content


instructions = (
    f"Please choose ONE of the listed options from Written_1_Systems_Determinants.pdf. You need to show your work for the mathematics problem as well as give full sentence explanations of the application question."
    f"Submissions will be online through this assignment page. PDFs are strongly preferred, but other formats are acceptable as long as the file sizes are reasonable. (Please don't submit 100MB picture files.)"
    )
pdf_path = 'Written_1_Systems_Determinants.pdf'

#print(agent_task_from_pdf(instructions=instructions, pdf_path=pdf_path))