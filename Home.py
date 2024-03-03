import streamlit as st
import pandas as pd 
from openai import OpenAI
import gspread
from auxillaries import initiate

st.set_page_config(page_title="Candidate.ai")
st.header("Candidate.ai", divider = 'red')

def main():
    client = OpenAI(
                      api_key=st.secrets['OPENAI-API'],
                    )
    completion = client.chat.completions.create(
                      model="gpt-3.5-turbo",
                      messages=[
                        {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
                        {"role": "user", "content": "Compose a 10 word poem that explains the concept of recursion in programming."}
                      ]
                    )
    st.write(completion.choices[0].message.content)
    
# Run the app
if __name__ == "__main__":
    st.write("Welcome!")
    gsheet = initiate()
    if st.button('Create'):
        main()
