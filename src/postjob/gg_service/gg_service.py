
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

class GoogleService:

    @staticmethod
    def CONTENT_GOOGLE(msg: str, file_path: str = None, input_email: str = "example@gmail.com"):
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = "hiep200326@gmail.com"
        smtp_password = "aghs ypya luzd seut"

        # Create the email message
        message = MIMEMultipart()
        message['From'] = smtp_user
        message['To'] = input_email
        message['Subject'] = 'PDF Attachment'
        message.attach(MIMEText(msg, 'plain'))

        # Attach PDF file to the email
        if file_path:
            with open(file_path, 'rb') as attachment:
                pdf_part = MIMEApplication(attachment.read(), _subtype="pdf")
                pdf_part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
                message.attach(pdf_part)

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, input_email, message.as_string())
        return None