# **Legal Document Summarizer using Groq LLM**

## **Overview**
The goal is to develop a system that can automatically summarize legal documents efficiently, ensuring the summaries are precise, legally accurate, and relevant. 
This system leverages LangChain for orchestration, RAG for knowledge retrieval, and integrates pre-trained language models for generating concise summaries.

## **Key Components**
- Data Ingestion: Input Sources: Scanned documents (PDFs), Word files, or plain text. Preprocessing: Clean the text by removing unnecessary symbols, headers, footers, and ensuring language consistency.
Index Creation: Chunk large documents into manageable sections (e.g., 500 tokens per chunk).
- Document Indexing and Storage: Generate embeddings for each chunk using models like HuggingFace's sentence transformers.
- RAG pipeline: Retriever: Build a retriever to fetch relevant document chunks based on user queries. Use similarity search with the vector database.
- Orchestration (LangChain):Use LangChain's chains and agents to combine the retriever and reader for end-to-end functionality. Define a custom summarization prompt with clear instructions for the model.
- Summarization Workflow: User Input: Users provide a query or specific summarization request (e.g., "Summarize the arguments in this contract."). Chunk Retrieval: The system retrieves relevant chunks from the vector database.
- LLM Processing: Combine retrieved chunks with a summarization prompt and pass them to the language model. Response Generation: Generate structured summaries (e.g., bullet points, sections) using the language model.

******************************************************************* 
## **Solution**

### **Building RAG app using Streamlit**

Using streamlit library designed by Python, it becomes easier to develop an LLM RAG based application in Python. By creating venv (virtual environment), install all the dependencies required listed in the requirements.txt file. 

The app.py file in the Level 1 folder contains the code with streamlit application which runs on the local port of 8501.

Command used: `streamlit run app.py` in the command prompt.

### Snapshots of the application using streamlit:

<img width="1261" height="693" alt="ss3" src="https://github.com/user-attachments/assets/d23dc3f5-0ae2-4b2b-bf3e-0fb17f2b16c9" />

- The above image displays the generated summary of the uploaded legal document in a concise manner to make the user understand the precised content of the document. 
The summary generated depends on the summary prompt template as well as the chunk retrieval.

<img width="1241" height="719" alt="ss4" src="https://github.com/user-attachments/assets/c9d6faac-4fbb-49a5-b620-9e897ec428f0" />

- The above figure contains the information regarding the key clauses existing in the document to know the user about legal terms present in the document.
The key clauses are pre-defined in the code template and cross-checked with the embeddings based on the similarity search.

<img width="1245" height="673" alt="ss6" src="https://github.com/user-attachments/assets/0a09a10c-c98f-40c1-895c-a6fed997250b" />

- The above image demonstrates the suggestions by the system to improve the document as well as the chat system to retrive the useful information from the document.
The generated risk score, graphs and the user feedback can be downloaded and mailed to the user for analysis.
