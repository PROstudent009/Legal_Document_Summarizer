import streamlit as st

st.set_page_config(page_title="Advanced AI-Driven Legal Document Summarization and Risk Assessment", layout="wide")

import requests
from bs4 import BeautifulSoup
import legal_document_analysis
import update_tracker  

def fetch_gdpr_recitals():
    url = "https://gdpr-info.eu/recitals/"
    response = requests.get(url)

    if response.status_code != 200:
        st.error("Update The GDPR website.")
        return {}

    soup = BeautifulSoup(response.content, 'html.parser')

    recitals = {}
    articles = soup.find_all('div', class_='artikel')
    
    for i, article in enumerate(articles):
        if i >= 3:  
            break
        link = article.find('a')['href']
        number = article.find('span', class_='nummer').text.strip('()')
        title = article.find('span', class_='titel').text.strip()
        
        rec_response = requests.get(link)
        if rec_response.status_code == 200:
            rec_soup = BeautifulSoup(rec_response.content, 'html.parser')
            content = rec_soup.find('div', class_='entry-content').get_text(strip=True)
            recitals[number] = {'title': title, 'content': content}
        else:
            st.error(f"Failed to fetch recital {number} from {link}")

    return recitals

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Choose a page", ["Legal Document Analysis", "Update_tracker"])

    if page == "Legal Document Analysis":
        legal_document_analysis.display_legal_analysis_page()  
    elif page == "Update_tracker":
        update_tracker.display_Update_tracker_page()  

if __name__ == "__main__":
    main()
