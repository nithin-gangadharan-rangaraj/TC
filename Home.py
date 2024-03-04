import streamlit as st
import pandas as pd 
import numpy as np
from openai import OpenAI
import gspread
from auxillaries import initiate
import imaplib
import email
import io
from gspread_dataframe import set_with_dataframe
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
def fetch_emails_with_subject(email_address, password, subject, client):
    # Connect to the email server
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(email_address, password)
    mail.select('inbox')

    # Search for emails with the specified subject
    result, data = mail.search(None, f'(SUBJECT "{subject}")')

    # List to store email data
    emails = []

    # Iterate over the emails
    for num in data[0].split():
        result, data = mail.fetch(num, '(RFC822)')
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)
        num_exchanges = 0

        # cv_text = ''
        email_body = ""
        # resume_text = ""
        # portfolio_text = ""
        # other_text = ""

        # #text-type dictionary assignment
        # text_type = {'CoverLetter': cv_text, 'Resume':resume_text, 'Portfolio': portfolio_text, 'Other': other_text}
        
        # Extract relevant information from the email
        email_info = {}
        email_info['ID'] = email_message['From']
        email_info['Exchanges'] = num_exchanges
        # email_info['EmailText'] = email_body
        # email_info['CoverLetter'] = cv_text
        # email_info['Resume'] = resume_text
        # email_info['Portfolio'] = portfolio_text
        
        
        # Add more fields as needed
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    email_body += part.get_payload(decode=True).decode()
        else:
            email_body = email_message.get_payload(decode=True).decode()

        # Iterate over the parts of the email message
        for part in email_message.walk():
            # Check if the part is an attachment
            text = ''
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
                    text += page_text
                    
            type = check_type(client, text)
            email_info = assign_text(text, type, email_info)
            
        
        # Get the value of the "References" header field
        references = email_message.get("References")

        # If the "References" header field exists, count the number of Message-IDs
        
        if references:
            # Split the references by whitespace and count the number of Message-IDs
            num_exchanges = len(references.split())

        # Add one to account for the initial email in the thread
        num_exchanges += 1

        email_info['EmailText'] = email_body
        email_info['Exchanges'] = num_exchanges

        # email_info['CoverLetter'] = cv_text
        # email_info['Resume'] = resume_text
        # email_info['Portfolio'] = portfolio_text
        # Append email data to the list
        emails.append(email_info)

    # Close the connection
    mail.close()
    mail.logout()

    return emails

def open_ai_client():
    client = OpenAI(
                      api_key=st.secrets['OPENAI-API'],
                    )
    return client
    
def check_type(client, text):
    if len(text) > 20:
        completion = client.chat.completions.create(
                          model="gpt-3.5-turbo",
                          messages=[
                            {"role": "system", "content": f"You're a text analyzer. Analyse this \n {text[:700]} \n"},
                            {"role": "user", "content": '''Analyse the text type: 
                                                           A for cover letter, 
                                                           B for resume, 
                                                           C for portfolio, 
                                                           D for other. 
                                                           If confused, choose D. Do not say anything more than the options.'''}
                          ]
                        )
        answer = completion.choices[0].message.content
        st.write(text[:700], answer)
        type_answer = map_type(answer)
    else:
        type_answer = 'Other'
    return type_answer

def map_type(answer):
    answer = answer.upper.strip()
    if 'A' in answer:
        return 'CoverLetter'
    elif 'B' in answer:
        return 'Resume'
    elif 'C' in answer:
        return 'Portfolio'
    else:
        return 'Other'

def assign_text(text, type, email_info):
    if type == "CoverLetter":
        email_info['CoverLetter'] += ('\n' + text)
    elif type == "Resume":
        email_info['Resume'] += ('\n' + text)
    elif type == "Portfolio":
        email_info['Portfolio'] += ('\n' + text)
    elif type == "Other":
        email_info['Other'] += ('\n' + text)
    return email_info

def get_worksheet(gsheet):
    wsheet = gsheet.sheet1 
    return wsheet

def get_df(wsheet):
    values = wsheet.get_all_values()
    existing_candidate_df = pd.DataFrame(values[1:], columns=values[0])
    return existing_candidate_df

def read_emails(client):
    email_address = st.secrets['email']
    password = st.secrets['password']
    subject = 'NAME_APPLICATION_FOR_DATA_ANALYST'
    
    emails = fetch_emails_with_subject(email_address, password, subject, client)
    return emails

# Define a function to apply
# def detect_exchanges(row, email_info):
#     # if int(row['Exchanges']) != int(email_info['Exchanges']):
#     row['Exchanges'] = email_info['Exchanges']  
#     row['EmailText'] = email_info['EmailText']
#     return row

def add_row(candidate_df, email_info):
    candidate_df.loc[len(candidate_df)] = email_info
    return candidate_df

def update_df(candidate_df, emails):
    for email_info in emails:
        # st.dataframe(candidate_df)
        if email_info['ID'] in candidate_df['ID'].values:
            idx = np.where(candidate_df['ID'].values == email_info['ID'])[0]
            if int(candidate_df.loc[int(idx), 'Exchanges']) < int(email_info['Exchanges']):
                candidate_df.loc[int(idx), ['Exchanges', 'EmailText']] = [email_info['Exchanges'], email_info['EmailText']]
                for info in ['CoverLetter', 'Resume', 'Portfolio']:
                    candidate_df.loc[int(idx), info] += ('\n-----\n' + email_info[info])
        else:
            candidate_df = add_row(candidate_df, email_info)
    return candidate_df

def update_worksheet(wsheet, candidate_df):
    # Clear the existing content (optional)
    wsheet.clear()
    set_with_dataframe(wsheet, candidate_df)

# Run the app
if __name__ == "__main__":
    st.write("Welcome!")
    gsheet = initiate()
    if st.button('Update Candidate Info'):
        #main()
        client = open_ai_client()
        wsheet = get_worksheet(gsheet)
        candidate_df = get_df(wsheet)
        emails = read_emails(client)
        candidate_df = update_df(candidate_df, emails)
        st.dataframe(candidate_df)
        update_worksheet(wsheet, candidate_df)
