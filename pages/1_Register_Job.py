import streamlit as st
from auxillaries import *
from email_auxillaries import *
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import random
import pandas as pd
from validate_email_address import validate_email

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

def check_email(email):
    isExists = validate_email(email, verify=True)
    return isExists
    
def validate_inputs(inputs):
    if inputs['Name'] == '' or inputs['Title'] == '' or inputs['Email'] == '' or check_email(inputs['Email']) == None:
        st.error('Please enter valid Name, Title and Email.')
        return False
    else:
        return True

def get_inputs(df):
  inputs = {}
  name = st.text_input("Enter the Firm Name").strip().upper()
  if name:
      display_existing_jobs(df, name)
  inputs["Name"] = name
  inputs["Title"] = st.text_input("Enter the Job Title").strip().capitalize()
  if is_new(df, inputs):
      inputs["Email"] = st.text_input("Enter the Email address").strip()
      inputs["JobDescription"] = st.text_area("Paste the job description").strip()
      inputs["FirmWebsite"] = st.text_input("Paste the link to the hiring firm's website").strip()
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
  with st.container(border = True):
      st.subheader(f"Job's unique password is: {password}")
      st.write("Please save it for future use.")
      st.divider()
      st.subheader(f"Subject Header for this job: {header}")
      st.info("PLEASE REQUEST THE APPLICANTS TO QUOTE THIS AS THE SUBJECT HEADER.")

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
    
  
