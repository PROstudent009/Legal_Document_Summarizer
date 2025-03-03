import os
import PyPDF2
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from docx import Document
import matplotlib.pyplot as plt
import io
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
from fpdf import FPDF  
import getpass
import pandas as pd
import seaborn as sns

load_dotenv()

if not os.environ.get("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = getpass.getpass("Enter API key for Groq: ")

model = ChatGroq(model="llama-3.1-8b-instant", api_key=os.environ.get("GROQ_API_KEY"))

st.markdown(
    """
    <style>
    .main {
        background-color: #f0f2f5;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    h1 {
        color: #2C3E50;
    }
    h2 {
        color: #2980B9;
    }
    .stButton button {
        background-color: #2980B9;
        color: white;
        border: None;
        border-radius: 5px;
        padding: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def read_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file):
    doc = Document(file)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text

def preprocess_text(text):
    return " ".join(text.replace("\n", " ").replace("\r", " ").split())

def chunk_text(text, max_tokens=2000):
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in text.split(". "):
        sentence_length = len(sentence.split())
        if current_length + sentence_length <= max_tokens:
            current_chunk.append(sentence)
            current_length += sentence_length
        else:
            chunks.append(". ".join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length

    if current_chunk:
        chunks.append(". ".join(current_chunk))

    return chunks

def generate_summary(text):
    prompt = f"Please summarize the following content:\n\n{text}"
    try:
        response = model.invoke(prompt)
        if hasattr(response, 'content'):
            summary = response.content
        else:
            summary = str(response)
        return summary.strip() if summary else "No summary available."
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        return None

def summarize_large_text(text, chunk_limit=5000):
    chunks = chunk_text(text, max_tokens=chunk_limit)
    summaries = []
    for chunk in chunks:
        summary = generate_summary(chunk)
        if summary:
            summaries.append(summary)
    return " ".join(summaries)

def detect_key_clauses(text):
    key_clauses = [
        {"clause": "confidentiality", "summary": "Confidentiality clauses ensure that sensitive information remains protected."},
        {"clause": "liability", "summary": "Liability clauses outline the responsibility for damages or losses incurred."},
        {"clause": "termination", "summary": "Termination clauses specify the conditions under which a contract may be ended."},
        {"clause": "force majeure", "summary": "Force majeure clauses excuse parties from performance obligations due to unforeseen events."},
        {"clause": "governing law", "summary": "Governing law clauses specify which jurisdiction's laws will govern the contract."},
        {"clause": "dispute resolution", "summary": "Dispute resolution clauses specify how conflicts between parties will be resolved."},
        {"clause": "amendment", "summary": "Amendment clauses outline the process for changing the terms of the contract."},
        {"clause": "warranty", "summary": "Warranty clauses provide assurances regarding the quality or condition of goods or services."},
    ]
    
    detected_clauses = []
    for clause in key_clauses:
        if clause["clause"].lower() in text.lower():
            clause_start = text.lower().find(clause["clause"].lower())
            context = text[clause_start - 50: clause_start + 200]
            explanation = f"The document mentions '{clause['clause']}' clause. Context: {context.strip()}..."
            detected_clauses.append({
                "clause": clause["clause"].capitalize(),
                "summary": clause["summary"],
                "explanation": explanation
            })
    
    return detected_clauses

def detect_hidden_obligations_or_dependencies(text, summary):
    hidden_obligations = [
        {"phrase": "dependent upon", "summary": "This suggests that some action is conditional upon another."},
        {"phrase": "if", "summary": "This indicates that certain conditions must be met to fulfill the obligation."},
        {"phrase": "may be required", "summary": "Implies that the party could be obligated to perform an action under specific conditions."},
        {"phrase": "should", "summary": "Implies a recommendation or requirement, though not explicitly mandatory."},
        {"phrase": "obligated to", "summary": "Indicates a clear, binding duty to perform an action."},
    ]
    
    hidden_dependencies = []
    
    for item in hidden_obligations:
        if item["phrase"].lower() in text.lower() or item["phrase"].lower() in summary.lower():
            phrase_start = text.lower().find(item["phrase"].lower())
            context = text[phrase_start - 50: phrase_start + 200]
            hidden_dependencies.append({
                "phrase": item["phrase"],
                "summary": item["summary"],
                "context": context.strip()
            })
    
    return hidden_dependencies

def answer_question(question, document_text):
    prompt = f"The following is a legal document:\n\n{document_text}\n\nBased on this document, answer the following question: {question}"
    
    try:
        response = model.invoke(prompt)
        if hasattr(response, 'content'):
            answer = response.content
        else:
            answer = str(response)
        
        return answer.strip() if answer else "No answer available."
    except Exception as e:
        st.error(f"Error answering question: {str(e)}")
        return None

def detect_risks(text, summary):
    risk_phrases = [
        {"phrase": "penalty", "summary": "This indicates financial or legal consequences.", "risk_level": "High"},
        {"phrase": "liability", "summary": "This suggests potential financial responsibility.", "risk_level": "Medium"},
        {"phrase": "default", "summary": "This can lead to serious legal consequences.", "risk_level": "High"},
        {"phrase": "breach", "summary": "This may expose the party to significant penalties.", "risk_level": "High"},
        {"phrase": "suspension", "summary": "This indicates risks of halting services.", "risk_level": "Medium"},
        {"phrase": "should", "summary": "This implies a recommendation, which may not be mandatory.", "risk_level": "Low"},
        {"phrase": "may be required", "summary": "This suggests that obligations could exist under certain conditions.", "risk_level": "Low"},
        {"phrase": "indemnify", "summary": "This entails a duty to compensate for harm or loss, indicating potential financial risk.", "risk_level": "High"},
        {"phrase": "termination for cause", "summary": "This indicates a risk of ending the contract due to specific failures.", "risk_level": "High"},
        {"phrase": "compliance", "summary": "Non-compliance with regulations can lead to legal penalties.", "risk_level": "High"},
    ]
    
    detected_risks = []
    
    for item in risk_phrases:
        if item["phrase"].lower() in text.lower() or item["phrase"].lower() in summary.lower():
            phrase_start = text.lower().find(item["phrase"].lower())
            context = text[phrase_start - 50: phrase_start + 200]
            detected_risks.append({
                "phrase": item["phrase"],
                "summary": item["summary"],
                "context": context.strip(),
                "risk_level": item["risk_level"]
            })
    
    return detected_risks

def calculate_overall_risk_score(detected_risks):
    risk_scores = {
        "High": 5,
        "Medium": 3,
        "Low": 1
    }
    total_score = sum(risk_scores.get(risk['risk_level'], 0) for risk in detected_risks)
    
    return min(total_score, 20)

def plot_risk_assessment_matrix(detected_risks):
    if not detected_risks:
        return None

    likelihood = []
    impact = []

    for risk in detected_risks:
        if risk['risk_level'] == 'High':
            likelihood.append(3)
            impact.append(3)
        elif risk['risk_level'] == 'Medium':
            likelihood.append(2)
            impact.append(2)
        elif risk['risk_level'] == 'Low':
            likelihood.append(1)
            impact.append(1)

    fig, ax = plt.subplots(figsize=(6, 6))
    scatter = ax.scatter(likelihood, impact, alpha=0.6)

    ax.set_xticks([1, 2, 3])
    ax.set_yticks([1, 2, 3])
    ax.set_xticklabels(['Low', 'Medium', 'High'])
    ax.set_yticklabels(['Low', 'Medium', 'High'])
    ax.set_xlabel('Likelihood')
    ax.set_ylabel('Impact')
    ax.set_title('Risk Assessment Matrix')

    for i in range(len(detected_risks)):
        ax.annotate(detected_risks[i]['phrase'], (likelihood[i], impact[i]))

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    
    return img_str

def plot_risk_level_distribution(detected_risks):
    if not detected_risks:
        return None

    risk_levels = [risk['risk_level'] for risk in detected_risks]
    level_counts = {level: risk_levels.count(level) for level in set(risk_levels)}

    fig, ax = plt.subplots(figsize=(4, 3))
    ax.pie(level_counts.values(), labels=level_counts.keys(), autopct='%1.1f%%', startangle=90)
    ax.axis('equal')

    plt.title("Risk Level Distribution", fontsize=10)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    
    return img_str

def plot_risks_by_type(detected_risks):
    if not detected_risks:
        return None

    risk_phrases = [risk['phrase'] for risk in detected_risks]
    phrase_counts = {phrase: risk_phrases.count(phrase) for phrase in set(risk_phrases)}

    fig, ax = plt.subplots(figsize=(4, 3))
    ax.bar(phrase_counts.keys(), phrase_counts.values(), color='lightcoral')
    plt.xticks(rotation=45, ha='right')
    ax.set_title("Risks by Type", fontsize=10)
    ax.set_ylabel("Count")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)

    img_str = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    return img_str

def plot_stacked_bar_chart(detected_risks):
    if not detected_risks:
        return None

    risk_levels = ['High', 'Medium', 'Low']
    level_counts = {level: 0 for level in risk_levels}

    for risk in detected_risks:
        level_counts[risk['risk_level']] += 1

    fig, ax = plt.subplots(figsize=(4, 3))
    ax.bar(level_counts.keys(), level_counts.values(), color=['#ff9999', '#66b3ff', '#99ff99'])
    ax.set_title("Stacked Bar Chart of Risks by Level", fontsize=10)
    ax.set_ylabel("Count")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)

    img_str = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    return img_str

def plot_risk_heatmap(detected_risks):
    if not detected_risks:
        return None

    risk_data = {'Risk Level': [], 'Count': []}
    
    for risk in detected_risks:
        risk_data['Risk Level'].append(risk['risk_level'])
        risk_data['Count'].append(1)

    df = pd.DataFrame(risk_data)
    heatmap_data = df.groupby('Risk Level').count().reset_index()

    if heatmap_data.empty:
        return None

    fig, ax = plt.subplots(figsize=(4, 3))
    sns.heatmap(heatmap_data.pivot_table(index='Risk Level', values='Count'), annot=True, cmap='YlGnBu', ax=ax)
    ax.set_title("Risk Heatmap")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)

    img_str = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    return img_str

def generate_pdf_analysis(document_text, summary, detected_clauses, hidden_obligations, detected_risks, risk_assessment_matrix, risk_level_distribution, risks_by_type, stacked_bar_chart, risk_heatmap):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_draw_color(0, 0, 0)
    pdf.rect(5, 5, 200, 287)

    pdf.add_font("Arial", "", "arial.ttf", uni=True)
    pdf.set_font("Arial", size=12)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, 'Legal Document Analysis Report', ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, 'Executive Summary', ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 10, summary)
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, 'Risk Analysis', ln=True)
    pdf.set_font("Arial", '', 12)
    for risk in detected_risks:
        pdf.cell(0, 10, f"{risk['phrase']}: {risk['summary']} (Risk Level: {risk['risk_level']})", ln=True)
    pdf.ln(10)

    def save_base64_image(image_str, filename):
        with open(filename, "wb") as img_file:
            img_file.write(base64.b64decode(image_str))

    image_filenames = [
        "risk_assessment_matrix.png",
        "risk_level_distribution.png",
        "risks_by_type.png",
        "stacked_bar_chart.png",
        "risk_heatmap.png"
    ]

    images = [risk_assessment_matrix, risk_level_distribution, risks_by_type, stacked_bar_chart, risk_heatmap]
    
    for img_str, filename in zip(images, image_filenames):
        if img_str:  
            save_base64_image(img_str, filename)
            pdf.image(filename, x=10, y=pdf.get_y(), w=90)  

    pdf.ln(10)

    temp_pdf_path = "legal_document_analysis.pdf"
    pdf.output(temp_pdf_path, 'F')

    with open(temp_pdf_path, "rb") as f:
        pdf_buffer = io.BytesIO(f.read())

    os.remove(temp_pdf_path)

    return pdf_buffer

def chatbot_query(user_input):
    try:
        response = model({"text": user_input})
        if isinstance(response, dict) and 'text' in response:
            return response['text']
        else:
            return "Error: Unexpected response format."
    except Exception as e:
        return f"Error: {str(e)}"

def generate_suggestions(text):
    suggestions = []
    
    if "shall" in text.lower():
        suggestions.append("Consider replacing 'shall' with 'must' for clarity.")
    if "may" in text.lower():
        suggestions.append("Clarify the conditions under which actions 'may' be taken.")
    if "if" in text.lower() and "then" not in text.lower():
        suggestions.append("Ensure conditional statements are clear and complete.")
    if "not" in text.lower():
        suggestions.append("Review negative clauses to ensure they are not overly restrictive.")
    
    return suggestions

# Function to send feedback via email
def send_feedback(feedback_content):
    sender_email = os.getenv("SENDER_EMAIL")
    receiver_email = os.getenv("FEEDBACK_EMAIL")
    password = os.getenv("EMAIL_PASS")

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "User Feedback on Legal Document Analysis"

    msg.attach(MIMEText(feedback_content, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
        return True
    except Exception as e:
        return False

# Function to send PDF via email
def send_pdf_via_email(pdf_buffer, recipient_email):
    sender_email = os.getenv("SENDER_EMAIL")
    password = os.getenv("EMAIL_PASS")

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "Legal Document Analysis PDF"

    msg.attach(MIMEText("Please find the attached analysis of your legal document.", 'plain'))

    # Attach the PDF
    pdf_attachment = io.BytesIO()
    pdf_buffer.seek(0)
    pdf_attachment.write(pdf_buffer.read())
    pdf_attachment.seek(0)

    part = MIMEApplication(pdf_attachment.read(), Name='legal_document_analysis.pdf')
    part['Content-Disposition'] = 'attachment; filename="legal_document_analysis.pdf"'
    msg.attach(part)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
        return True
    except Exception as e:
        return False

# Function to simulate tracking updates in the document
def track_updates(document_text):
    updates = [
        {"update": "Updated confidentiality clause.", "suggestion": "Consider specifying the duration of confidentiality."},
        {"update": "Revised liability limits.", "suggestion": "Ensure the limits are realistic and compliant with regulations."},
        {"update": "Clarified termination conditions.", "suggestion": "Check if all potential termination scenarios are covered."},
    ]
    return updates

# Function to get suggestion from Groq API based on the update
def get_update_suggestion(update):
    prompt = f"Suggest improvements or updates for this legal clause: {update}"
    suggestion = generate_summary(prompt)
    return suggestion if suggestion else "No suggestion available."

# Function to display feedback form
def display_feedback_form():
    st.subheader("Feedback Form")
    feedback = st.text_area("Please provide your feedback or suggestions:")
    
    question1 = st.radio("How would you rate the analysis?", ("Excellent", "Good", "Fair", "Poor"))
    question2 = st.radio("Would you recommend this tool to others?", ("Yes", "No"))
    
    if st.button("Submit Feedback"):
        feedback_content = f"Feedback: {feedback}\nRating: {question1}\nRecommendation: {question2}"
        if send_feedback(feedback_content):
            st.success("Thank you for your feedback! It has been sent.")
        else:
            st.error("Failed to send feedback. Please try again later.")

def display_legal_analysis_page():
    st.title("📜 Advanced AI-Driven Legal Document Summarization and Risk Assessment")

    uploaded_file = st.file_uploader("Upload your legal document (PDF or DOCX)", type=["pdf", "docx"])
    if uploaded_file:
        document_text = ""
        if uploaded_file.name.endswith(".pdf"):
            document_text = preprocess_text(read_pdf(uploaded_file))
        elif uploaded_file.name.endswith(".docx"):
            document_text = preprocess_text(extract_text_from_docx(uploaded_file))
        else:
            st.error("Unsupported file type!")
            return

        tabs = st.tabs(["📄 Document Text", "🔍 Summary", "🔑 Key Clauses", "🔒 Hidden Obligations", "⚠ Risk Analysis", "💡 Suggestions & Chatbot", "🔄 Document Update"])

        with tabs[0]:
            st.subheader("Document Text")
            st.write(document_text if document_text else "No text was detected.")

        with tabs[1]:
            st.subheader("Summary")
            summary = summarize_large_text(document_text)
            st.write(summary)

        with tabs[2]:
            st.subheader("Key Clauses Identified")
            detected_clauses = detect_key_clauses(document_text)
            if detected_clauses:
                for clause in detected_clauses:
                    with st.expander(clause['clause'], expanded=False):
                        st.write(f"*Summary:* {clause['summary']}")
                        st.write(f"*Context:* {clause['explanation']}")
            else:
                st.write("No key clauses detected.")

        with tabs[3]:
            st.subheader("Hidden Obligations and Dependencies")
            hidden_obligations = detect_hidden_obligations_or_dependencies(document_text, summary)
            if hidden_obligations:
                for obligation in hidden_obligations:
                    st.write(f"{obligation['phrase']}: {obligation['summary']}")
                    st.write(obligation['context'])
            else:
                st.write("No hidden obligations detected.")

        with tabs[4]:
            st.subheader("Risk Analysis")
            detected_risks = detect_risks(document_text, summary)
            overall_risk_score = calculate_overall_risk_score(detected_risks)

            st.write(f"*Overall Risk Score:* {overall_risk_score}/20")

            if detected_risks:
                for risk in detected_risks:
                    with st.expander(risk['phrase'], expanded=False):
                        st.write(f"*Summary:* {risk['summary']} (Risk Level: {risk['risk_level']})")
                        short_context = risk['context'].strip().split('. ')[0] + '.'
                        st.write(f"*Context:* {short_context}")
            else:
                st.write("No risks detected.")

            risk_assessment_matrix = plot_risk_assessment_matrix(detected_risks)
            risk_level_distribution = plot_risk_level_distribution(detected_risks)
            risks_by_type = plot_risks_by_type(detected_risks)
            stacked_bar_chart = plot_stacked_bar_chart(detected_risks)
            risk_heatmap = plot_risk_heatmap(detected_risks)

            if risk_assessment_matrix:
                st.image(f"data:image/png;base64,{risk_assessment_matrix}", caption="Risk Assessment Matrix")
            if risk_level_distribution:
                st.image(f"data:image/png;base64,{risk_level_distribution}", caption="Risk Level Distribution")
            if risks_by_type:
                st.image(f"data:image/png;base64,{risks_by_type}", caption="Risks by Type")
            if stacked_bar_chart:
                st.image(f"data:image/png;base64,{stacked_bar_chart}", caption="Stacked Bar Chart of Risks by Level")
            if risk_heatmap:
                st.image(f"data:image/png;base64,{risk_heatmap}", caption="Risk Heatmap")

        with tabs[5]:
            st.subheader("Suggestions for Improvement")
            suggestions = generate_suggestions(document_text)
            for suggestion in suggestions:
                st.write(f"- {suggestion}")

            st.subheader("🤖 Chatbot")
            question = st.text_input("Ask a question about the document:")
            if question:
                with st.spinner("Getting answer..."):
                    answer = answer_question(question, document_text)
                    if answer:
                        st.write(f"Answer: {answer}")
                    else:
                        st.write("Sorry, I couldn't find an answer to that question.")

            st.subheader("Download Analysis as PDF")
            pdf_buffer = generate_pdf_analysis(document_text, summary, detected_clauses, hidden_obligations, detected_risks, risk_assessment_matrix, risk_level_distribution, risks_by_type, stacked_bar_chart, risk_heatmap)
            pdf_buffer.seek(0)

            st.download_button(
                label="Download PDF Analysis",
                data=pdf_buffer,
                file_name="legal_document_analysis.pdf",
                mime="application/pdf"
            )

            recipient_email = st.text_input("Enter your email address to receive the PDF:")

            if st.button("Send PDF Analysis"):
                if recipient_email:
                    if send_pdf_via_email(pdf_buffer, recipient_email):
                        st.success("PDF has been sent successfully!")
                    else:
                        st.error("Failed to send PDF. Please try again.")
                else:
                    st.warning("Please enter a valid email address.")

            display_feedback_form()

        with tabs[6]:  
            st.subheader("Document Updates")
            updates = track_updates(document_text)
            if st.button("Show Updates"):
                if updates:
                    for update in updates:
                        with st.expander(update['update'], expanded=False):
                            suggestion = get_update_suggestion(update['update'])
                            st.write(f"*Suggestion:* {suggestion}")
                            if st.button(f"Mark '{update['update']}' as addressed"):
                                st.success(f"'{update['update']}' has been marked as addressed.")
                else:
                    st.write("No updates detected.")

if __name__ == "__main__":
    display_legal_analysis_page()