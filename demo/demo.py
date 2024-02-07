from fastapi import FastAPI, BackgroundTasks
from email.mime.text import MIMEText
import uvicorn
import shutil
from fastapi import UploadFile
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import smtplib
import os

app = FastAPI()

def send_email(pdf_file_path, msg: str, recipient_email):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "hiep200326@gmail.com"
    smtp_password = "aghs ypya luzd seut"

    # Create the email message
    message = MIMEMultipart()
    message['From'] = smtp_user
    message['To'] = recipient_email
    message['Subject'] = 'PDF Attachment'
    message.attach(MIMEText(msg, 'plain'))

    # Attach PDF file to the email
    with open(pdf_file_path, 'rb') as attachment:
        pdf_part = MIMEApplication(attachment.read(), _subtype="pdf")
        pdf_part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(pdf_file_path)}')
        message.attach(pdf_part)

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipient_email, message.as_string())

@app.post("/send_email")
async def send_email_background(uploaded_file: UploadFile, recipient_email: str, background_tasks: BackgroundTasks):
    with open(os.path.join("data", uploaded_file.filename), 'w+b') as file:
        shutil.copyfileobj(uploaded_file.file, file)
    # Use background task to send email in the background
    message = """
    ewucfhbvniujfvcheiwnviwenriuvherwvv
    vrionvvroeinbvveribvnre
    rbveiornbvoeirnbvoeirn
    erbveoribvnreobvn
    """
    background_tasks.add_task(send_email, os.path.join("data", uploaded_file.filename), message, recipient_email)
    return {"message": "Email will be sent in the background."}

    
if __name__ == '__main__':
    uvicorn.run("demo:app", host="localhost", port=6060, reload=True)
    
    

# #   Update point of recuiter's account
# current_user.point -=  valuation_result.total_point
# #   Update point of collaborator's account
# resume = General.get_detail_resume_by_id(cv_id, db_session)
# collab = db_session.execute(select(model.User).where(model.User.id == resume.ResumeVersion.user_id)).scalars().first()
# collab.point += valuation_result.total_point
# resume.ResumeVersion.point_recieved_time = datetime.now()