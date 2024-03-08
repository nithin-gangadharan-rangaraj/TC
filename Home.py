import streamlit as st
import pandas as pd 
import numpy as np
from openai import OpenAI
import gspread
from auxillaries import *
import imaplib
import email
import io
from gspread_dataframe import set_with_dataframe
import fitz
from user_auth import check_password
import time
from email_auxillaries import send_report

st.set_page_config(page_title="Candidate.ai")
st.image('cai.png', width = 400)
st.subheader("Future-Focused Hiring", divider = 'red')
# st.caption("Register your job under **Register Job** to kick start your recruitment.")
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
def fetch_emails_with_subject(email_address, password, subject, client, df):
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
        email_info['EmailText'] = email_body
        email_info['CoverLetter'] = ''
        email_info['Resume'] = ''
        email_info['Portfolio'] = ''
        email_info['Other'] = ''

        # Get the value of the "References" header field
        references = email_message.get("References")

        # If the "References" header field exists, count the number of Message-IDs
        
        if references:
            # Split the references by whitespace and count the number of Message-IDs
            num_exchanges = len(references.split())

        # Add one to account for the initial email in the thread
        num_exchanges += 1
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    email_body += part.get_payload(decode=True).decode()
        else:
            email_body = email_message.get_payload(decode=True).decode()
                
        email_info['EmailText'] = email_body
        email_info['Exchanges'] = num_exchanges

        if attachment_analysis_needed(email_info['ID'], num_exchanges, df):
    
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
            
        
        # email_info['CoverLetter'] = cv_text
        # email_info['Resume'] = resume_text
        # email_info['Portfolio'] = portfolio_text
        # Append email data to the list
        emails.append(email_info)

    # Close the connection
    mail.close()
    mail.logout()

    return emails

def attachment_analysis_needed(email_info_id, num_exchanges, df):
    if email_info_id in df['ID'].values:
        idx = np.where(df['ID'].values == email_info_id)[0]
        if int(df.loc[int(idx), 'Exchanges']) < int(num_exchanges):
            return True
        else:
            return False
    else:
        return True

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
        st.subheader("### AI API Usage checker", divider = 'red')
        st.write(text[:700], answer)
        type_answer = map_type(answer)
    else:
        type_answer = 'Other'
    return type_answer

def map_type(answer):
    answer = answer.upper().strip()
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

# def get_worksheet(gsheet):
#     wsheet = gsheet.sheet1 
#     return wsheet

def get_df(wsheet):
    values = wsheet.get_all_values()
    existing_candidate_df = pd.DataFrame(values[1:], columns=values[0])
    return existing_candidate_df

def read_emails(client, df, subject):
    email_address = st.secrets['email']
    password = st.secrets['password']
    subject = subject
    
    emails = fetch_emails_with_subject(email_address, password, subject, client, df)
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
                for info in ['CoverLetter', 'Resume', 'Portfolio', 'Other']:
                    candidate_df.loc[int(idx), info] += ('\n-----\n' + email_info[info])
        else:
            candidate_df = add_row(candidate_df, email_info)
    return candidate_df

def update_worksheet(wsheet, candidate_df):
    # Clear the existing content (optional)
    wsheet.clear()
    set_with_dataframe(wsheet, candidate_df)

def get_recruiter(header, recruiter_df):
    recruiter = recruiter_df.loc[recruiter_df['Header'] == header]
    return recruiter.iloc[0]

def display_recruiter(user, recruiter):
    with st.container(border = True):
        st.subheader(f"Recruiter: {recruiter['Name']}")
        st.write(f"Job Title: **{recruiter['Title']}**")
        st.write(f"Email: **{recruiter['Email']}**")

def generate_prompt(candidate, recruiter):
    prompt = ""
    for column, value in candidate.items():
        if len(value) > 0:
            prompt += (f'''\n
                            {column.upper().strip()}\n
                            {value.strip()}\n''')
    if len(prompt) > 20:
        prompt += (f'''JOB DESCRIPTION:\n
                        {recruiter['JobDescription']}\n
                        JOB WEBSITE:\n
                        {recruiter['FirmWebsite']}\n
                    ''')
    # st.write(prompt)
    return prompt

def get_recommendation_ai(client, candidate, recruiter):
    prompt = generate_prompt(candidate, recruiter)
    answer = ""
    if len(prompt) > 20:
        completion = client.chat.completions.create(
                          model="gpt-3.5-turbo",
                          messages=[
                            {"role": "system", "content": f"{prompt}"},
                            {"role": "user", "content": '''You are a recruiter now. Analyse how good the candidate is for this job.
                                                           You have to provide a recommendation in less than 50 words.
                                                           Answer it in the following format: 
                                                           Recommendation:
                                                        '''}
                          ]
                        )
        answer = completion.choices[0].message.content
    return answer


def write_recommendation(client, candidate_df, recruiter):
    # rec_df = pd.DataFrame(columns = ['Name', 'Title', 'Email',  'ID', 'Recommendation'])
    recommendations_info = []
    for index, candidate in candidate_df.iterrows():
        single = {}
        single['Name'] = recruiter['Name']
        single['Title'] = recruiter['Title']
        single['ID'] = candidate['ID']
        recommendation = get_recommendation_ai(client, candidate, recruiter)
        single['Recommendation'] = recommendation
        recommendations_info.append(single)
        
    rec_df = pd.DataFrame(recommendations_info)
    return rec_df

def get_ai_help(client, all_candidates, recruiter):
    answer = ""
    if len(all_candidates) > 20:
        completion = client.chat.completions.create(
                          model="gpt-3.5-turbo",
                          messages=[
                            {"role": "system", "content": f"{all_candidates}"},
                            {"role": "user", "content": f'''You are a recruiter now. Consider this job description {recruiter['JobDescription']}.
                                                           Arrange the candidates in the order suitable for this job description.
                                                           Answer it in the following format where IDs are found in the candidate information,
                                                           ID is typically in the format Name <Email>: 
                                                           ['ID1', 'ID2']                                                           
                                                        '''}
                          ]
                        )
        answer = completion.choices[0].message.content
    return answer

def arrange_df(ranked_candidates, rec_df):
    id_order = eval(ranked_candidates)
    st.write(id_order)
    if type(id_order) == list: 
        df_duplicate = rec_df
        df_duplicate['ID_order'] = df_duplicate['ID'].apply(lambda x: id_order.index(x))
        df_sorted = df_duplicate.sort_values(by='ID_order')
        df_sorted = df_sorted.drop(columns='ID_order') 
        rec_df = df_sorted
        st.success("Ranked the candidates.")
    else:
        st.error("Wrote the recommendations, failed to rank them.")
    return rec_df


def rank_using_ai(rec_df, recruiter, client):
    if len(rec_df) > 1:
        all_candidates = '\n'.join([candidate['ID'] + "\n" + candidate['Recommendation'] for index, candidate in rec_df.iterrows()])
        ranked_candidates = get_ai_help(client, all_candidates, recruiter)
        rec_df = arrange_df(ranked_candidates, rec_df)
    return rec_df
        
        
# Run the app
if __name__ == "__main__":
    gsheet = initiate()
    rsheet = open_worksheet(gsheet, "Recruiters")
    recruiter_df = get_df(rsheet)
    user = check_password(recruiter_df)
    if user:
        recruiter = get_recruiter(user, recruiter_df)
        display_recruiter(user, recruiter)
        wsheet = open_worksheet(gsheet, user + '_candidates')
        client = open_ai_client()
        candidate_df = get_df(wsheet)
        rec_sheet = open_worksheet(gsheet, user + '_recommendation')
        rec_df = get_df(rec_sheet)
        
        st.subheader("Excited to check for applicants?", divider = 'blue')
        if st.button('Update Candidate Info'): 
            with st.status("Updating Info...", expanded=True) as status:
                emails = read_emails(client, candidate_df, subject = user)
                st.success('Fetched Emails.')
                candidate_df = update_df(candidate_df, emails)
                st.success('Fetched Information.')
                update_worksheet(wsheet, candidate_df)
                st.success('Updated the data.')
                status.update(label="Updated Candidate Info!", state="complete", expanded=False)
            st.subheader("Applicants so far...")
            st.dataframe(candidate_df, use_container_width = True)
            st.info('Next step: Rank the candidates.')
            
        st.subheader("Rank Applicants", divider = 'blue')
        if st.button('Start Ranking'): 
            with st.status("Updating Info...", expanded=True) as status:
                st.success('Writing recommendations for candidates.')
                rec_df = write_recommendation(client, candidate_df, recruiter)
                # st.success('Updating Data.')
                rec_df = rank_using_ai(rec_df, recruiter, client)
                update_worksheet(rec_sheet, rec_df)
                status.update(label="Wohoo, analysed and ranked everyone.", state="complete", expanded=False)
            st.dataframe(rec_df)
            st.info('Next step: Need a report? Go to the next section.')
            
        st.subheader("Get Reports", divider = 'blue')
        st.warning("If the earlier sections aren't finished, the report won't show any new applicants, if any.")
        with st.expander("Click here to check the existing candidates."):
            st.dataframe(rec_df)
        if st.button('Send Email'): 
            send_report(rec_df, recruiter)

            
        # st.sidebar.divider()
        if st.sidebar.button('Check another job'):
            with st.spinner('Logging off, please wait...'):
                st.session_state.clear()  # Clear session state to sign out
                st.toast('You can check for another job now :)')
                time.sleep(1)
                st.experimental_rerun()   # Trigger re-run to refresh the app
