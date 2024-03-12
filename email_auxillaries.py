import streamlit as st
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from validate_email_address import validate_email

def check_email(email):
    isExists = validate_email(email, verify=True)
    return isExists

def send_report(df, recruiter):
    try:
        multipart = MIMEMultipart()
        multipart["From"] = st.secrets['email']
        multipart["To"] = recruiter['Email']
        multipart["Subject"] = f'Candidate.ai - {recruiter["Header"]} Report'  
    
        message = """\
        <p>Greetings,</p>
        <p>Please find attached the candidate recommendations for your recruitment.</p>
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
        st.success(f"Email sent to {recruiter['Email']} successfully.")
    except:
        st.error("Error. Please try again later.")

def send_credentials(recruiter):
    try:
        multipart = MIMEMultipart()
        multipart["From"] = st.secrets['email']
        multipart["To"] = recruiter['Email']
        multipart["Subject"] = f'Candidate.ai - {recruiter["Header"]} Login Credentials'  
    
        message = f"""\
        <p>Greetings,</p>
        <p>Credentials for the role: {recruiter["Header"]}.</p><br>
        <p><strong>Recruiter's name: {recruiter['Name']}</strong></p>
        <p><strong>Role: {recruiter['Title']}</strong></p>
        <p><strong>Password: {recruiter['Password']}</strong></p>
        <p>Please save these credentials for future use.</p>
        <p><strong>Regards,</strong><br><strong>Candidate.ai&nbsp;    </strong></p>
        """

        multipart.attach(MIMEText(message, "html"))
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(multipart["From"], st.secrets['password'])
        server.sendmail(multipart["From"], multipart["To"], multipart.as_string())
        server.quit()
        st.success(f"Credentials sent to {recruiter['Email']} successfully.")
    except:
        st.error("Unable to send credentials to your email. Please save the displayed credentials for future use.")
