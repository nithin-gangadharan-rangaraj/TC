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
from email_auxillaries import *
from urlextract import URLExtract
import requests
from bs4 import BeautifulSoup
import re
import docx2txt

    
st.set_page_config(page_title="Candidate.ai")
st.image('cai.png', width = 400)
st.subheader("Future-Focused Hiring", divider = 'red')




def get_urls(text):
    extractor = URLExtract()
    urls = extractor.find_urls(text)
    return urls
    
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

        email_body = ""

        # Extract relevant information from the email
        email_info = {}
        links = []
        email_info['ID'] = email_message['From']
        email_info['Exchanges'] = num_exchanges
        email_info['EmailText'] = email_body
        email_info['CoverLetter'] = ''
        email_info['Resume'] = ''
        email_info['Portfolio'] = ''
        email_info['Links'] = []
        email_info['Other'] = ''

        references = email_message.get("References")
        if references:
            num_exchanges = len(references.split())
        num_exchanges += 1
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    email_body += part.get_payload(decode=True).decode()
        else:
            email_body = email_message.get_payload(decode=True).decode()
        links.extend(get_urls(email_body))
        
        email_info['EmailText'] = email_body
        email_info['Exchanges'] = num_exchanges

        if attachment_analysis_needed(email_info['ID'], num_exchanges, df):
            for part in email_message.walk():
                text = ''
                if part.get_content_maintype() == 'application' and part.get_content_subtype() == 'pdf':
                    pdf_bytes = part.get_payload(decode=True)
                    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
                    for page_number in range(len(pdf_document)):
                        page_text = pdf_document[page_number].get_text()
                        text += page_text

                # DOCX attachment
                elif part.get_content_subtype() == 'vnd.openxmlformats-officedocument.wordprocessingml.document':
                    docx_bytes = part.get_payload(decode=True)
                    docx_text = docx2txt.process(io.BytesIO(docx_bytes))
                    text += docx_text
                        
                type = check_type(client, text)
                email_info = assign_text(text, type, email_info)
                
                links.extend(get_urls(text))
                email_info['Links'] = links
                
        emails.append(email_info)
 
    mail.close()
    mail.logout()

    return emails

def scrap_links(links):
    scraped_content = []
    failed_links = []
    for link in links:
        try:
            response = requests.get(link)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                page_text = soup.get_text(separator="\n")
                scraped_content.append(page_text)
            else:
                failed_links.append(link)
        except Exception as e:
            failed_links.append(link)

    scraped_content = '\n'.join(scraped_content)
    return scraped_content, failed_links

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
        # st.subheader("### AI API Usage checker", divider = 'red')
        # st.write(text[:700], answer)
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
    text = text.replace("\n\n", "")
    if type == "CoverLetter":
        email_info['CoverLetter'] += ('\n' + text)
    elif type == "Resume":
        email_info['Resume'] += ('\n' + text)
    elif type == "Portfolio":
        email_info['Portfolio'] += ('\n' + text)
    elif type == "Other":
        email_info['Other'] += ('\n' + text)
    return email_info


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
                candidate_df.loc[int(idx), 'Links'] = str(list(set(eval(str(candidate_df.loc[int(idx), 'Links']).strip()) + email_info['Links'])))
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

def display_recruiter(user, recruiter, recruiter_container):
    with recruiter_container.container(border = True):
        st.subheader(f"Recruiter: {recruiter['Name']}")
        st.write(f"Job Title: **{recruiter['Title']}**")
        st.write(f"Email: **{recruiter['Email']}**")

def remove_blank_lines(text):
    return '\n'.join([line for line in text.split('\n') if line.strip()])

def get_info_summary(client, category, info, job):
    '''
     Calls the OpenAI model to summarize the individual candidate information.

    Returns: 
        str: Summarized version of the candidate information
    '''
    prompt = f'{category.upper().strip()} \n {info.strip()} \n RECRUITING JOB DESCRIPTION: \n {job.strip()}'
    completion = client.chat.completions.create(
                          model="gpt-3.5-turbo",
                          messages=[
                            {"role": "user", "content": f"{prompt}"},
                            {"role": "system", "content": f'''Pick out the relevant information from this {category} that would help to check if 
                                                            it would suit the job description in a maximum of 100 words. Consider only the user provided
                                                            candidate information.
                                                        '''}
                          ]
                        )
    info_summary = completion.choices[0].message.content
    return info_summary

#########################################################################################################################

def generate_prompt(client, candidate, recruiter, scraped_candidate_content, scraped_recruiter_content):
    '''
     Generates prompt for each candidate. To bypass the word count limit in the OpenAI model
     each candidate info is summarized separately. Finally, with the limited words (~100 words) per info,
     all the info can be combined together which would essentially be less than 16K token count.

     Email conversations are unchanged. Resume, Cover letter, Portfolio, Other texts are summarized.

    Returns: 
        str: Prompt with Summarized candidate info
    '''
    
    prompt = "CANDIDATE INFORMATION:\n"
    for category, info in candidate.items():
        if category in ['CoverLetter', 'Resume', 'Portfolio', 'Other']:
            if len(info) > 20:
                info_summary = get_info_summary(client, category, info, recruiter['JobDescription'])
                prompt += (f'''\n              
                                {category.upper().strip()}:\n
                                {info_summary.strip()}\n''')
        if category == 'EmailText':
            if len(info) > 5:
                prompt += (f'''\n              
                                APPLICATION EMAIL CONVERSATION:\n
                                {info.strip()}\n''')
    if len(prompt) > 20:
        prompt += (f"RELEVANT CANDIDATE INFORMATION: {scraped_candidate_content}" if len(scraped_candidate_content) > 10 else '')
        # prompt += (f"RECRUITING JOB DESCRIPTION: {recruiter['JobDescription']}")
        # prompt += ("RECRUITING JOB WEBSITE: \n" + scraped_recruiter_content if len(scraped_recruiter_content) > 10 else '')
    prompt = remove_blank_lines(prompt)
    return prompt

#########################################################################################################################

def add_link_info(links, who):
    scraped_content = ''
    comments = ''
    try:
        scraped_content, failed_links = scrap_links(eval(links))
        if len(failed_links) > 0:
            comments = f'We were unable to consider these links on account of technical constraints: \n\n{failed_links}\n'
    except:
        if not links[0] == '':
            comments = f'We were unable to consider these links on account of technical constraints: \n\n{links}\n'
    return scraped_content, comments 

#########################################################################################################################
        

def get_recommendation_ai(client, candidate, recruiter, scraped_candidate_content, scraped_recruiter_content):
    '''
    Calls the OpenAI model for each candidate to write recommendation.

    Returns: 
        str: Recommendation for the particular candidate.
    '''
    prompt = generate_prompt(client, candidate, recruiter, scraped_candidate_content, scraped_recruiter_content)
    st.write(candidate['ID'])
    st.write(prompt)
    recommendation = ""
    if len(prompt) > 20:
        completion = client.chat.completions.create(
                          model="gpt-3.5-turbo",
                          messages=[
                            {"role": "system", "content": f'''You are a recruiter now. Analyse how good the candidate information fits the following recruiting job description.
                                                            {recruiter['JobDescription']}. {("RECRUITING JOB WEBSITE: \n" + scraped_recruiter_content) if len(scraped_recruiter_content) > 10 else ''}
                                                           You have to provide a recommendation for this candidate in less than 50 words. Consider only the user provided CANDIDATE INFORMATION.
                                                           Must answer it in the following format: 
                                                           Recommendation:
                                                          '''},
                            {"role": "user", "content": f"{prompt}"}
                          ]
                        )
        recommendation = completion.choices[0].message.content
    return recommendation

#########################################################################################################################

def write_recommendation(client, candidate_df, recruiter):
    '''
    Main function to write recommendation in about 50 words for each candidate.
    Iterates through each candidate and creates a dataframe with recommendations.
    
    Returns: 
     df: Candidate recommendations
    '''
    recommendations_info = []
    
    for index, candidate in candidate_df.iterrows():
        single = {}
        scraped_candidate_content, comments_candidate = add_link_info(candidate['Links'], 'CANDIDATE')
        scraped_recruiter_content, comments_recruiter = add_link_info([recruiter['FirmWebsite']], 'RECRUITER')
        recommendation = get_recommendation_ai(client, candidate, recruiter, scraped_candidate_content, scraped_recruiter_content)
        
        single['Name'] = recruiter['Name']
        single['Title'] = recruiter['Title']
        single['ID'] = candidate['ID']
        single['Recommendation'] = recommendation
        single['Comments'] = (comments_candidate + '\n' +  comments_recruiter)
        
        recommendations_info.append(single)  
    rec_df = pd.DataFrame(recommendations_info)
    return rec_df

#########################################################################################################################

def get_ai_help(client, all_candidates, recruiter, num_candidates):
    answer = ""
    if len(all_candidates) > 20:
        completion = client.chat.completions.create(
                          model="gpt-3.5-turbo",
                          messages=[
                            {"role": "system", "content": f"{all_candidates}"},
                            {"role": "user", "content": f'''You are a recruiter now. Consider this job description {recruiter['JobDescription']}.
                                                           Arrange ALL the candidates in the order suitable for this job description. Consider the general
                                                           recruiting strategies.
                                                           MUST Include all {num_candidates} candidates.
                                                           Answer it in the following example format,
                                                           ['ID1', 'ID2'] 
                                                           where IDs are found in the candidate information, ID is in the format: Name <Email>.
                                                           In this example, there are 2 candidates.
                                                        '''}
                          ]
                        )
        answer = completion.choices[0].message.content
    return answer

def arrange_df(ranked_candidates, rec_df):
    id_order = eval(ranked_candidates)
    # st.write(id_order)
    try:
        if type(id_order) == list: 
            df_duplicate = rec_df
            df_duplicate['ID_order'] = df_duplicate['ID'].apply(lambda x: id_order.index(x))
            df_sorted = df_duplicate.sort_values(by='ID_order')
            df_sorted = df_sorted.drop(columns='ID_order') 
            rec_df = df_sorted
            st.success('Ranked the candidates.')
    except:
        st.error("Wrote the recommendations, failed to rank them.")
    return rec_df


def rank_using_ai(rec_df, recruiter, client):
    if len(rec_df) > 1:
        all_candidates = f"Total Number of candidates: {len(rec_df)}\n"
        all_candidates += '\n'.join([candidate['ID'] + "\n" + candidate['Recommendation'] for index, candidate in rec_df.iterrows()])
        ranked_candidates = get_ai_help(client, all_candidates, recruiter, len(rec_df))
        rec_df = arrange_df(ranked_candidates, rec_df)
    return rec_df

def update_recruiter(recruiter, recruiter_df, rsheet):
    # st.write(recruiter)
    prior = len(recruiter_df)
    try:
        index_to_update = recruiter_df.index[recruiter_df['Header'] == recruiter['Header']].tolist()[0]
        recruiter_df.loc[index_to_update] = recruiter
        recruiter_df.dropna(inplace=True)
        assert(prior == len(recruiter_df))
        update_worksheet(rsheet, recruiter_df)
        st.success('Updated the job details successfully.')
    except AssertionError:
        st.error('Error in updating the details :(')

def delete_worksheets(gsheet, wsheet, rec_sheet, recruiter):
    try:
        gsheet.del_worksheet(wsheet)
        gsheet.del_worksheet(rec_sheet)
        st.success("Deleted the candidate data.")
    except:
        st.error("Unable to delete worksheets")

def update_recruiter_sheet(rsheet, recruiter_df, recruiter):
    try:
        recruiter_df = recruiter_df.drop(recruiter_df[recruiter_df['Header'] == recruiter['Header']].index)
        update_worksheet(rsheet, recruiter_df)
        st.success("Deleted the job data")
    except:
        st.error("Error in removing the recruiter data")  


def delete_job(gsheet, wsheet, rec_sheet, rsheet, recruiter_df, recruiter):
    delete = False
    st.subheader("Delete job", divider = 'red')
    st.warning("Please read the instructions carefully before deleting.")
    with st.expander("Deletion Warning", expanded = True):
        st.markdown("""
                        **Before deleting a job, please consider the following**
                        - All **candidate emails** associated with this job will be **permanently deleted and cannot be recovered**.
                        - The job itself will be permanently deleted and cannot be recovered.
                        - If you require a final report, you can obtain one by visiting the 'Check for Candidates' section and requesting a report to be sent to your email.
                        - **Deleting a job is irreversible**. You may need to restart the entire recruiting process, so please ensure you are certain before proceeding with deletion.
                        """)
        delete = st.checkbox("I acknowledge that I have read and understood the instructions for deleting a job.", value = False)
    
    if delete:
        st.info("You can delete the job now.")
        if st.button("Click here to delete"):
            with st.status("Deletion in progress...", expanded=True) as status:
                delete_worksheets(gsheet, wsheet, rec_sheet, recruiter)
                update_recruiter_sheet(rsheet, recruiter_df, recruiter)
                delete_emails(recruiter['Header'])
                st.info("Please wait...")
                st.session_state.clear()  # Clear session state to sign out
                time.sleep(3)
                st.toast('Successfully deleted :)')
                st.rerun()   # Trigger re-run to refresh the app

def display_top(rec_df):
    st.metric(label="Total candidates", value=len(rec_df))
    if len(rec_df) > 0:
        st.write("**Wish to check the :blue[top ranking] candidates?**")
        count = st.slider("Pick top candidates", min_value=0, max_value = min(5, len(rec_df)), value=min(3, len(rec_df)), step=1)
        if count > 0:
            with st.container(border = True):
                st.subheader(f"Top {count} candidate{'s' if count > 1 else ''}:")
                for idx in range(count):
                    name = re.sub(r'([^<]+)\s*<(.+?)>', r'\1: \2', rec_df.loc[idx, 'ID']).strip()
                    with st.popover(f"**{idx + 1}**. {name}"):
                        st.write(rec_df.loc[idx, 'Recommendation'])
        st.divider()
            
# Run the app
if __name__ == "__main__":
    
    gsheet = initiate()
    rsheet = open_worksheet(gsheet, "Recruiters")
    recruiter_df = get_df(rsheet)
    user = check_password(recruiter_df)
    if user:
        recruiter_container = st.empty()
        recruiter = get_recruiter(user, recruiter_df)
        display_recruiter(user, recruiter, recruiter_container)
        wsheet = open_worksheet(gsheet, user + '_candidates')
        client = open_ai_client()
        candidate_df = get_df(wsheet)
        rec_sheet = open_worksheet(gsheet, user + '_recommendation')
        rec_df = get_df(rec_sheet)
        
        tab1, tab2, tab3 = st.tabs(["Check for Candidates", "Update Job Details", "Delete Job"])
        with tab1: 
            st.subheader("Excited to check for applicants?", divider = 'blue')
            st.write("This section helps us to extract the candidates' application emails and interprets them.")
            if st.button('Fetch Candidate Info', use_container_width = True): 
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
            st.write("This is the main part, where the extracted candidate emails are ranked based on the desired criteria.")
            if st.button('Start Ranking', use_container_width = True): 
                with st.status("Updating Info...", expanded=True) as status:
                    if len(candidate_df) > 0:
                        rec_df = write_recommendation(client, candidate_df, recruiter)
                        st.success("Analysed candidates' fitness for the role.")
                        rec_df = rank_using_ai(rec_df, recruiter, client)
                        update_worksheet(rec_sheet, rec_df)
                        status.update(label="Wohoo, analysed and ranked everyone.", state="complete", expanded=True)
                        st.dataframe(rec_df)
                        st.info('Next step: Need a report? Go to the next section.')
                    else:
                        st.error("There are no candidates. Please check with the previous section.")
                
            st.subheader("Analysis", divider = 'blue')
            st.warning("Please note that if the earlier sections aren't finished, the report won't show any new applicants, if any.")
            display_top(rec_df)
            st.write("You can check for all existing candidates here - The candidates displayed are ranked based on the desired criteria.")
            with st.expander("Click here to check all existing candidates."):
                st.dataframe(rec_df, use_container_width = True)
            st.divider()
            st.write("**Need a copy of the recommendation as a report?** Don't worry, We can send it to you at your convenience. Please choose your preferred method.")
            st.download_button(
                                label="Download report ⬇️",
                                data = convert_df(rec_df),
                                file_name=f'{recruiter["Header"]}_report.csv',
                                mime='text/csv',
                                use_container_width = True,
                              )
            if st.button('Send Email ✉️', use_container_width = True): 
                send_report(rec_df, recruiter)

        with tab2:
            headers, disabilities = get_recruiter_headers()
            prior = dict(recruiter)
            # prior['RankingParameters'] = list(eval(prior['RankingParameters'])) if not prior['RankingParameters'] == '' else None
            for header, disability in zip(headers, disabilities):
                if not header == 'Password':
                    if header == 'JobDescription':
                        recruiter[header] = st.text_area(f"{header.capitalize()}", value = recruiter[header], disabled = bool(disability)).strip()
                    # elif header == 'RankingParameters':
                    #     recruiter[header] = st.multiselect("Do you have any specific parameters to rank the applicants?",
                    #                             options = get_ranking_params(),
                    #                             default = list(eval(recruiter[header])) if not recruiter[header] == '' else None,
                    #                             help = "Along with the general recruiting consideration, these parameters would be considered first when ranking the applicants.",
                    #                             placeholder = "May choose upto 5 parameters",
                    #                             max_selections = 5)
                    else:
                        recruiter[header] = st.text_input(f"{header.capitalize()}", value = recruiter[header], disabled = bool(disability)).strip()
            if validate_inputs(recruiter) and not (prior == dict(recruiter)):
                if st.button('Update'):
                    update_recruiter(recruiter, recruiter_df, rsheet)
                    display_recruiter(user, recruiter, recruiter_container)
            else:
                st.error('No updates detected.')

        with tab3:
            delete_job(gsheet, wsheet, rec_sheet, rsheet, recruiter_df, recruiter)
            
            
        # st.sidebar.divider()
        if st.sidebar.button('Check another job'):
            with st.spinner('Logging off, please wait...'):
                st.session_state.clear()  # Clear session state to sign out
                st.toast('You can check for another job now :)')
                time.sleep(1)
                st.rerun()   # Trigger re-run to refresh the app
