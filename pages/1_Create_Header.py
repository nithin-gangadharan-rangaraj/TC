import streamlit as st
from auxillaries import *
from gspread_dataframe import get_as_dataframe
import random

def get_recruiter_df(wsheet):
  return get_as_dataframe(wsheet)

def get_random():
  return random.randint(10000, 99999)
  
def is_new(df, inputs):
  existing_recruiters = (df['Name'] == inputs["name"]) & (df['Title'] == inputs["title"])
  return existing_recruiters.any()


def get_inputs():
  inputs = {}
  inputs["Name"] = st.text_input("Enter the Firm Name").strip().capitalize()
  inputs["Title"] = st.text_input("Enter the Job Title").strip().capitalize()
  inputs["Email"] = st.text_input("Enter the Email address").strip()
  inputs["JobDescription"] = st.text_area("Paste the job description").strip()
  inputs["FirmWebsite"] = st.text_input("Paste the link to the hiring firm's website").strip()
  return inputs

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

def update_worksheet(wsheet, recruiter_df):
    wsheet.clear()
    set_with_dataframe(wsheet, recruiter_df)

def display_info(password, header):
  with st.container(border = True):
      st.subheader(f"Your unique password is: {password}")
      st.write("Please save it for future use.")
      st.divider()
      st.subheader(f"Subject Header for this job: {header}")
      st.write("PLEASE REQUEST THE APPLICANTS TO QUOTE THIS AS THE SUBJECT HEADER.")
      
    
if __name__ == "__main__":
  st.header("Register with us and discover the ease of modern recruitment!", divider = 'red')
  gsheet = initiate()
  wsheet = open_worksheet(gsheet, "Recruiters")
  recruiter_df = get_recruiter_df(wsheet)
  inputs = get_inputs()
  if st.button("Add a new job"):
    if is_new(recruiter_df):
      inputs["Password"] = generate_password(inputs)
      inputs["Header"] = generate_subject_header(inputs)
      recruiter_df.loc[len(recruiter_df)] = inputs
      display_info(inputs["Password"], inputs["Header"])
      update_worksheet(wsheet, recruiter_df)
    else:
      st.error(f"{inputs['name']} recruiting for {inputs['title']} exists. Please recheck!}")
  
