import os
import mailparser
from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.documents import Document
from config import embeddings

def load_document(uploaded_file):
    temp_file_path = uploaded_file.name
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # File parsing
    if uploaded_file.type == "text/plain":
        loader = TextLoader(temp_file_path)
    elif uploaded_file.type == "text/csv":
        loader = CSVLoader(temp_file_path)
    elif uploaded_file.type == "application/pdf":
        loader = PyPDFLoader(temp_file_path)
    elif uploaded_file.type == "message/rfc822" or uploaded_file.name.endswith(".eml"):
        parsed_email = mailparser.parse_from_file(temp_file_path)
        doc_content = f"Subject: {parsed_email.subject}\nFrom: {parsed_email.from_}\nTo: {parsed_email.to}\n\n{parsed_email.body}"
        return [Document(page_content=doc_content)]
    else:
        raise ValueError("Unsupported file type!")

    return loader.load()

def store_vectors(index, doc):
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(doc)
    
    vectors = [
        (str(i), embeddings.embed_documents([chunk.page_content])[0], {"text": chunk.page_content})
        for i, chunk in enumerate(chunks)
    ]
    index.upsert(vectors)
    
    return chunks

def retrieve_chunks(index):
    query_vector = embeddings.embed_query("summarize the document")
    search_results = index.query(vector=query_vector, top_k=5, include_metadata=True)
    return "\n".join(match["metadata"]["text"] for match in search_results["matches"])
