import streamlit as st
from auxillaries import *
from gspread_dataframe import get_as_dataframe

def get_recruiter_df(wsheet):
  return get_as_dataframe(wsheet)

def get_inputs():
  name = st.text_input("Enter the Firm Name")
  title = st.text_input("Enter the Job Title")
  job_description = st.text_area("Paste the job description")
  

if __name__ == "__main__":
  gsheet = initiate()
  wsheet = open_worksheet(gsheet, "Recruiters")
  recruiter_df = get_recruiter_df(wsheet)
  st.header("Create a new header")
