import streamlit as st
from utils import load_document, store_vectors, retrieve_chunks
from processors import generate_summary, detect_risks
from config import load_env, initialize_pinecone

load_env()

st.title("Groq-based Document Summarizer with Risk Detection")
st.markdown("## Upload your document to summarize & analyze risks.")

uploaded_file = st.file_uploader("Upload a file (TXT, PDF, CSV, EML)", type=["txt", "pdf", "csv", "eml"])

index = initialize_pinecone()

if uploaded_file:
    with st.spinner("Processing..."):
        try:
            doc = load_document(uploaded_file)
            chunks = store_vectors(index, doc)
            st.success("File uploaded and indexed successfully!")
        except Exception as e:
            st.error(f"Error processing file: {e}")

if st.button("Summarize and Analyze Risks"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Uploaded Document")
        st.text_area("Document Content", value=doc[0].page_content[:2000], height=900)
    
    with col2:
        st.markdown("### Generated Summary")
        with st.spinner("Generating summary & risk analysis..."):
            retrieved_text = retrieve_chunks(index)
            
            summary = generate_summary(retrieved_text)
            risk_analysis = detect_risks(retrieved_text)
            
            st.write(summary)
            st.markdown("### Risk Analysis")
            st.write(risk_analysis)

            st.download_button("Download Summary", summary, "summary.txt", "text/plain")
            st.download_button("Download Risk Analysis", risk_analysis, "risk_analysis.txt", "text/plain")
