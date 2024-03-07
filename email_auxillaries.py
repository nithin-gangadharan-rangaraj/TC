import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
import fitz
import io

# Function to convert DataFrame to PDF
def df_to_pdf(df):
    doc = fitz.open()
    table = doc.new_table(table=df.values.tolist())
    stream = io.BytesIO()
    doc.insert_table(table)
    doc.save(stream, garbage=4, deflate=True)  # Save PDF to stream
    doc.close()
    stream.seek(0)
    return stream.getvalue()  # Return PDF as bytes

# Function to send email with PDF attachment
def send_email(email, subject, body, attachment_path):
    # Set up email server
    server = smtplib.SMTP('smtp.example.com', 587)
    server.starttls()

    sender_email = st.secrets['email']
    server.login(sender_email, st.secrets['password'])

    # Create email message
    msg = EmailMessage()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject
    msg.set_content(body)

    # Attach PDF file
    with open(attachment_path, 'rb') as f:
        file_data = f.read()
        msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=attachment_path)

    # Send the email
    server.send_message(msg)

    # Close server connection
    server.quit()

# Streamlit app
def send_report(df, recruiter):
  
    # Convert DataFrame to PDF
    pdf_name = f"{recruiter['Header']}.pdf"
    pdf_data = df_to_pdf(df)
  
    # Input email address
    email = recruiter['Email']

    # Button to send email
    if st.button("Send Email"):
        try:
            # Send email with PDF attachment
            send_email(email, f"Candidate.ai - {recruiter['Header']}", "Greetings, \n Please find attached the consolidated report for the job. \n Regards, \n Candidate.ai \n", pdf_name)
            st.success(f"Report sent to {email} successfully!")
        except:
            st.error("Your Email address is invalid.")
