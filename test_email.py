import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", SMTP_USERNAME)
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def send_test_email():
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, RECEIVER_EMAIL]):
        raise Exception("Missing SMTP environment variables")

    subject = "✅ GitHub Actions SMTP Test Email"
    body = f"""
    <h2>Email Test Successful</h2>
    <p>This email confirms SMTP is working from GitHub Actions.</p>
    <p><b>Timestamp:</b> {datetime.utcnow()} UTC</p>
    """

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

    print("✅ Email sent successfully")

if __name__ == "__main__":
    send_test_email()
