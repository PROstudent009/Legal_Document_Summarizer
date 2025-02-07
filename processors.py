from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import llm

parser = StrOutputParser()

def generate_summary(text):
    summary_prompt = ChatPromptTemplate.from_template(
        "You are a highly skilled AI model tasked with summarizing text. "
        "Please summarize the following text concisely:\n\n{document}"
    )
    summary_chain = summary_prompt | llm | parser
    return summary_chain.invoke({"document": text})

def detect_risks(text):
    risk_prompt = ChatPromptTemplate.from_template(
        "Analyze the following text for potential risks, hidden obligations, and dependencies: \n\n{document}"
    )
    risk_chain = risk_prompt | llm | parser
    return risk_chain.invoke({"document": text})
