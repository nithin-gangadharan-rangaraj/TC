import streamlit as st
from auxillaries import initiate

if __name__ == "__main__":
  gsheet = initiate()
  st.header("Create a new header")
