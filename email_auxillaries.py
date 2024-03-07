import streamlit as st
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def send_report(df, recruiter):
    multipart = MIMEMultipart()
    multipart["From"] = st.secrets['email']
    multipart["To"] = recruiter['Email']
    multipart["Subject"] = f'Candidate.ai - {recruiter['Header'] Report}'  

    message = """\
    <p><strong>Candidate Report:</strong></p>
    <p>Greetings,</p>
    <p>Please find attached the candidate file for the job</p>
    <p><strong>Regards,</strong><br><strong>Candidate.ai&nbsp;    </strong></p>
    """
    
    attachment = MIMEApplication(df.to_csv())
    attachment["Content-Disposition"] = 'attachment; filename=" {}"'.format(f"{recruiter['Header']}.csv")
    multipart.attach(attachment)
    multipart.attach(MIMEText(message, "html"))
    
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(multipart["From"], st.secrets['password'])
    server.sendmail(multipart["From"], multipart["To"], multipart.as_string())
    server.quit()
