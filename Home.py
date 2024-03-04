import streamlit as st
import pandas as pd 
from openai import OpenAI
import gspread
from auxillaries import initiate
import imaplib
import email
import io
import fitz

st.set_page_config(page_title="Candidate.ai")
st.header("Candidate.ai", divider = 'red')

def main():
    client = OpenAI(
                      api_key=st.secrets['OPENAI-API'],
                    )
    completion = client.chat.completions.create(
                      model="gpt-3.5-turbo",
                      messages=[
                        {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
                        {"role": "user", "content": "Compose a 10 word poem that explains the concept of recursion in programming."}
                      ]
                    )
    st.write(completion.choices[0].message.content)

# Function to fetch emails with a specific subject
def fetch_emails_with_subject(email_address, password, subject):
    # Connect to the email server
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(email_address, password)
    mail.select('inbox')

    # Search for emails with the specified subject
    result, data = mail.search(None, f'(FROM "{email_address}" SUBJECT "{subject}")')

    # List to store email data
    emails = []

    # Iterate over the emails
    for num in data[0].split():
        result, data = mail.fetch(num, '(RFC822)')
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)

        # Extract relevant information from the email
        email_info = {}
        email_info['From'] = email_message['From']
        email_info['Subject'] = email_message['Subject']
        # Add more fields as needed
        email_body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    email_body += part.get_payload(decode=True).decode()
        else:
            email_body = email_message.get_payload(decode=True).decode()

        cv_text = ""
        # Iterate over the parts of the email message
        for part in email_message.walk():
            # Check if the part is an attachment
            if part.get_content_maintype() == 'application' and part.get_content_subtype() == 'pdf':
                # Read the PDF attachment content into memory
                pdf_bytes = part.get_payload(decode=True)
                # Open the PDF attachment using PyMuPDF
                pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
                # Iterate over each page of the PDF
                for page_number in range(len(pdf_document)):
                    # Extract text from the current page
                    page_text = pdf_document[page_number].get_text()
                    # Append the extracted text to the CV text
                    cv_text += page_text

        email_info['Body'] = email_body
        email_info['CV'] = cv_text
        # Append email data to the list
        emails.append(email_info)

    # Close the connection
    mail.close()
    mail.logout()

    return emails

# Run the app
if __name__ == "__main__":
    st.write("Welcome!")
    gsheet = initiate()
    if st.button('Create'):
        #main()
        email_address = st.secrets['email']
        password = st.secrets['password']
        subject = 'NAME_APPLICATION_FOR_DATA_ANALYST'
        
        emails = fetch_emails_with_subject(email_address, password, subject)
        for email_info in emails:
            st.write("From:", email_info['From'])
            st.write("Subject:", email_info['Subject'])
            st.write("Body:", email_info['Body'])
            st.write("CV:", email_info['CV'])
