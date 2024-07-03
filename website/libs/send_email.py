import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

msg = MIMEMultipart()

PASS_NOT_GIVEN = "Password not given"
EMAIL_NOT_GIVEN = "Email is not given"
EMAIL_ERROR = "Email not sent , please check user email and password"


class MailgunException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Mailgun:
    SMTP_PASS = os.getenv("SMTP_PASSWORD")
    EMAIL = os.getenv("SMTP_EMAIL")

    @classmethod
    def send_email(cls, email: str, subject: str, text: str, html: str):
        if cls.SMTP_PASS is None:
            raise MailgunException(PASS_NOT_GIVEN)

        if cls.EMAIL is None:
            raise MailgunException(EMAIL_NOT_GIVEN)

        msg = MIMEMultipart()
        msg['From'] = cls.EMAIL
        msg['Subject'] = subject
        msg['To'] = email
        body = text
        html = html
        msg.attach(MIMEText(html, 'html'))
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                smtp.starttls()
                smtp.login(cls.EMAIL, cls.SMTP_PASS)
                smtp.send_message(msg)
        except Exception as e:
            raise MailgunException(f"{e}:{EMAIL_ERROR}")