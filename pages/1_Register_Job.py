import streamlit as st
from auxillaries import *
from email_auxillaries import *
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import random
import pandas as pd

st.image('cai.png', width = 400)

def get_recruiter_df(wsheet):
    values = wsheet.get_all_values()
    recruiter_df = pd.DataFrame(values[1:], columns=values[0])
    return recruiter_df

def get_random():
  return random.randint(10000, 99999)
  
def is_new(df, inputs):
  existing_recruiters = (df['Name'] == inputs["Name"]) & (df['Title'] == inputs["Title"])
  return not existing_recruiters.any()

def display_existing_jobs(df, name):
  st.write(f"Existing job titles listed for {name.upper()}:")
  st.dataframe(pd.DataFrame(df.loc[df['Name'] == name, 'Title'].values, columns=['Job Title']))


def get_inputs(df):
  inputs = {}
  name = st.text_input("Enter the **Firm Name**\*").strip().upper()
  if name:
      display_existing_jobs(df, name)
  inputs["Name"] = name
  inputs["Title"] = st.text_input("Enter the **Job Title**\*").strip().capitalize()
  if is_new(df, inputs):
      inputs["Email"] = st.text_input("Enter the **Email address**\*").strip()
      inputs["JobDescription"] = st.text_area("Paste the **job description**").strip()
      inputs["FirmWebsite"] = st.text_input("Paste the link to the hiring firm's website").strip()
      # inputs["RankingParameters"] = st.multiselect("Do you have any specific parameters to rank the applicants?",
      #                                           options = get_ranking_params(),
      #                                           help = "Along with the general recruiting consideration, these parameters would be considered first when ranking the applicants.",
      #                                           placeholder = "May choose upto 5 parameters",
      #                                           max_selections = 5)
  else:
      st.error(f"{inputs['Name']} recruiting for {inputs['Title']} exists. Please recheck!")
      return False
  return inputs if validate_inputs(inputs) else False

def generate_password(df, inputs):
  unique_flag = False
  while not unique_flag:
    password = inputs['Name'][:3] + inputs['Title'][:4] + str(get_random())
    if password not in df["Password"].values:
      unique_flag = True
  return password
  
def generate_subject_header(df, inputs):
  unique_flag = False
  while not unique_flag:
    header = inputs['Name'].split()[0] + "_" + "_".join(inputs['Title'].split())
    if header not in df["Header"].values:
      unique_flag = True
  return header

def update_worksheet(wsheet, df):
    wsheet.clear()
    set_with_dataframe(wsheet, df)

def display_info(password, header):
    col1, col2 = st.columns(2)
    col1.metric("Subject Header", f"{header}", "Subject Header")
    col2.metric("Job's unique password", f"{password}", "For you to access")
    st.info(f'''⚠️**Important:**
            Please request the applicants to quote **{header}** as the subject.''')

def get_header_list(header):
    with open(f'inputs_{header.split("_")[-1]}.txt', 'r') as f:
        headers = [inp.strip() for inp in f.readlines()]
    return headers

def create_worksheet(gsheet, header):
    gsheet.add_worksheet(title = header, rows="1000", cols="26")
    new_sheet = open_worksheet(gsheet, header)
    headers = get_header_list(header)
    new_sheet.update('A1', [headers])
    
    
if __name__ == "__main__":
  st.header("Register with us and discover the ease of modern recruitment!", divider = 'red')
  gsheet = initiate()
  wsheet = open_worksheet(gsheet, "Recruiters")
  recruiter_df = get_recruiter_df(wsheet)
  recruiter_df.dropna()
  # st.dataframe(recruiter_df)
  inputs = get_inputs(recruiter_df)
  if inputs:
    if st.button("Add a new job"):
      inputs["Password"] = generate_password(recruiter_df, inputs)
      inputs["Header"] = generate_subject_header(recruiter_df, inputs)
      create_worksheet(gsheet, f'{inputs["Header"]}_candidates')
      create_worksheet(gsheet, f'{inputs["Header"]}_recommendation')
      # st.dataframe(recruiter_df)
      recruiter_df.loc[len(recruiter_df)] = inputs
      # st.dataframe(recruiter_df)
      display_info(inputs["Password"], inputs["Header"])
      update_worksheet(wsheet, recruiter_df)
      send_credentials(inputs)
      st.success("Successfully registered the job.")
  else:
    st.error("Please try again.")
    
  
