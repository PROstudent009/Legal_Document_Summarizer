import os
from dotenv import load_dotenv
from transformers import pipeline
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.llms import HuggingFaceHub

load_dotenv()

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def create_vector_store(text, embeddings_model="sentence-transformers/all-MiniLM-L6-v2"):
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_text(text)
    embeddings = HuggingFaceEmbeddings(model_name=embeddings_model)
    return FAISS.from_texts(texts, embeddings)

def create_qa_pipeline(vector_store, llm_model="EleutherAI/gpt-neo-2.7B"):
    
    huggingfacehub_api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    
    if huggingfacehub_api_token is None:
        raise ValueError("HuggingFace Hub API token is missing! Please set the 'HUGGINGFACEHUB_API_TOKEN' in your .env file.")
    
    retriever = vector_store.as_retriever()

    llm = HuggingFaceHub(
        repo_id=llm_model,  
        huggingfacehub_api_token=huggingfacehub_api_token, 
        task="text-generation" 
    )
    
    return RetrievalQA.from_chain_type(llm, retriever=retriever)

def process_pdf_and_answer(pdf_path):
    
    text = extract_text_from_pdf(pdf_path)

    vector_store = create_vector_store(text)

    qa_pipeline = create_qa_pipeline(vector_store)

    answer = qa_pipeline.run("Extract key information from the PDF.")  
    return answer

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RAG Pipeline for PDF analysis")
    parser.add_argument("--pdf", type=str, required=True, help="Path to the PDF file")
    args = parser.parse_args()

    pdf_path = args.pdf

    answer = process_pdf_and_answer(pdf_path)
    print(f"Answer: {answer}")
