import streamlit as st
from auxillaries import *
import os

def user_pass(header, df):
  crct_password = df.loc[df['Header'] == header, 'Password'].values
  if len(crct_password) > 0:
    return crct_password[0]
  else:
    return None

def check_password(df):
   
    st.write("Enter the job's unique **Subject Header and Password** and you're good to go! 🙂")
  
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if "header" in st.session_state and "password" in st.session_state:
          header = st.session_state["header"].strip()
          password = st.session_state["password"].strip()
          if (
              header in df['Header'].values
              and password
              == user_pass(header, df)
          ):
              st.session_state["password_correct"] = True
              st.session_state['user'] = st.session_state["header"] 
              del st.session_state["password"]  # don't store username + password
              del st.session_state["header"]
          else:
            st.session_state["password_correct"] = False
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.text_input("Enter the Subject Header", on_change=password_entered, key="header")
        st.text_input(
            "Enter the Job's Password", type="password", on_change=password_entered, key="password", help="Unique password for this job would have been issued during Job Registration."
        )
        # st.caption("New? Register your job under **Register Job** to kick start your recruitment.")
        st.markdown("""
                      <a href="/Register_Job" target="_self"> 
                          Register your job under <b>Register Job</b> to kick start your recruitment.
                      </a>
                  """, unsafe_allow_html=True)
      
        return False
        
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Enter the Subject Header", on_change=password_entered, key="header")
        st.text_input(
            "Enter the Job's Password", type="password", on_change=password_entered, key="password", help="Unique password for this job would have been issued during Job Registration."
        )
        # st.caption("New? Register your job under **Register Job** to kick start your recruitment.")
        st.markdown("""
                      <a href="/Register_Job" target="_self"> 
                          Register your job under <b>Register Job</b> to kick start your recruitment.
                      </a>
                  """, unsafe_allow_html=True)
        st.error("😕 Header not known or password incorrect")
        return False
    else:
        # Password correct.
        return st.session_state['user']
