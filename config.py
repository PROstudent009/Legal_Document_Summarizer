import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

def load_env():
    load_dotenv()

def initialize_pinecone():
    pc_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = "summarizer-app"
    
    if index_name not in [i.name for i in pc_client.list_indexes()]:
        pc_client.create_index(name=index_name, dimension=384, metric="cosine")

    return pc_client.Index(index_name)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
llm = ChatGroq(model="mixtral-8x7b-32768", api_key=os.getenv("GROQ_API_KEY"))
