import streamlit as st
from auxillaries import *
import os

def user_pass(header, df):
  crct_password = df[df['Header'] == header, 'Password'].values
  return crct_password

def check_password(df):
   
    """Returns `True` if the user had a correct password."""
    
    def password_entered(df):
        """Checks whether a password entered by the user is correct."""
        st.session_state["header"] = st.session_state["username"].strip().lower()
        st.session_state["password"] = st.session_state["password"].strip()
      
        if (
            st.session_state["header"] in df['Header'].values
            and st.session_state["password"]
            == user_pass([st.session_state["header"]], df)
        ):
            st.session_state["password_correct"] = True
            st.session_state['user'] = st.session_state["username"] 
            del st.session_state["password"]  # don't store username + password
            del st.session_state["header"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.text_input("Enter the Subject Header", on_change=password_entered, key="header")
        st.text_input(
            "Enter your unique Password", type="password", on_change=password_entered, key="password"
        )
        return False
        
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Enter the Subject Header", on_change=password_entered, key="header")
        st.text_input(
            "Enter your unique Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct.
        return st.session_state['user']
