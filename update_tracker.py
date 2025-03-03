import streamlit as st
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import os

load_dotenv()

def fetch_gdpr_recitals():
    url = "https://gdpr-info.eu/recitals/"
    response = requests.get(url)

    if response.status_code != 200:
        st.error("Failed to fetch data from the GDPR website.")
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

def send_email(recitals):
    sender_email = os.getenv("EMAIL_ADDRESS")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    password = os.getenv("EMAIL_PASSWORD")

    subject = "GDPR Recitals Update"
    body = "New GDPR recitals have been fetched:\n\n"

    for number, details in recitals.items():
        body += f"Recital {number}: {details['title']}\n{details['content']}\n\n"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls() 
            server.login(sender_email, password)  
            server.send_message(msg)  
            st.success("Email notification sent!")
    except smtplib.SMTPAuthenticationError:
        st.error("Failed to login: Check your email and password.")
    except smtplib.SMTPConnectError:
        st.error("Failed to connect to the SMTP server. Check your network connection.")
    except smtplib.SMTPException as e:
        st.error(f"SMTP error occurred: {str(e)}")  
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")  

def store_in_google_sheets(recitals):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")

    st.write(f"Google Credentials Path: {creds_path}")  

    if not creds_path or not os.path.exists(creds_path):
        st.error("Google credentials path is invalid or not set.")
        return

    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)

    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        st.error("Google Sheet ID is not set.")
        return

    sheet = client.open_by_key(sheet_id).sheet1

    for number, details in recitals.items():
        sheet.append_row([number, details['title'], details['content']])
    st.success("Data stored in Google Sheets!")

def display_Update_tracker_page():
    st.title("Update Tracker - GDPR Recitals")

    if st.button("Fetch Live Recitals"):
        with st.spinner("Fetching updates..."):
            recitals = fetch_gdpr_recitals()
            if recitals:
                for number, details in recitals.items():
                    st.markdown(f"*Recital {number}: {details['title']}*")
                    st.write(details['content'])

                send_email(recitals)
                store_in_google_sheets(recitals)
            else:
                st.write("No recitals found.")

if __name__ == "__main__":
    display_Update_tracker_page()