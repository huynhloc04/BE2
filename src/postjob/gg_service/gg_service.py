
import smtplib
from fastapi import BackgroundTasks, HTTPException
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class GoogleService:

    @staticmethod
    def CONTENT_GOOGLE(message: str, input_email: str = "example@gmail.com"):
        port = 587  # For starttls
        smtp_server = "smtp.gmail.com"
        sender_email = "hiep200326@gmail.com"
        receiver_email = input_email
        password = "aghs ypya luzd seut"
    
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = input_email
        msg['Subject'] = "Thông tin được gửi từ website sharecv.VN"
        msg.attach(MIMEText(message, "html"))
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        return None