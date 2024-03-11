from google.oauth2 import service_account
import streamlit as st
import gspread

def open_worksheet(gsheet, sheet_name):
    return gsheet.worksheet(sheet_name)
  
def initiate():
  if 'gsheet' in st.session_state:
      gsheet = st.session_state['gsheet']
  else:
      # Load service account credential
      service_acc = st.secrets["gcp_service_account"]
      
          
      credentials = service_account.Credentials.from_service_account_info(
      service_acc,
      scopes=[
          "https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"
      ],
      )
  
      # Authorize gspread client
      gs = gspread.authorize(credentials)
      # st.write(gs.openall())
      gsheet = gs.open(st.secrets['sheet_name'])
      st.session_state['gsheet'] = gsheet
  return gsheet

def get_recruiter_headers():
    with open('inputs_recruiters.txt', 'r') as f:
        lines = f.readlines()
    headers = []
    disabilities = []
    for line in lines:
        h, d = line.split('-')
        headers.append(h)
        disabilities.append(d)
    return headers, disabilities
