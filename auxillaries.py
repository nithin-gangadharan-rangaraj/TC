from google.oauth2 import service_account
import streamlit as st
import gspread

def initiate():
  if 'gsheet' in st.session_state:
        gsheet = st.session_state['gsheet']
  else:
      # Load service account credential
      try:
          service_acc = st.secrets["gcp_service_account"]
      except KeyError:
          service_acc = dict(eval(os.environ.get("gcp_service_account")))
          
      credentials = service_account.Credentials.from_service_account_info(
      service_acc,
      scopes=[
          "https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"
      ],
      )
  
      # Authorize gspread client
      gs = gspread.authorize(credentials)
      gsheet = gs.open("ABC-SDA-recruitment")
      st.session_state['gsheet'] = gsheet
  return gsheet
