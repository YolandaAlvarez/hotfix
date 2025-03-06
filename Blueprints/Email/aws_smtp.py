import smtplib
import socket
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Load SMTP credentials from environment variables
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
CC_EMAIL = os.getenv('CC_EMAIL')
SENDER = os.getenv('SENDER')

def send_email_smtp(recipient_email, subject, body):
    # Create a message
    message = MIMEText(body)
    message['From'] = SENDER
    if recipient_email is None:
        recipient_email = CC_EMAIL
    message['To'] = recipient_email
    message['Subject'] = subject

    # Debugging: Check if the hostname resolves correctly
    try:
        socket.gethostbyname(SMTP_HOST)
        print(f"Hostname {SMTP_HOST} resolved successfully.")
    except socket.error as e:
        print(f"Error resolving hostname {SMTP_HOST}: {e}")
        return

    # Connect to the SMTP server and send the email
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:  # Use SMTP_SSL for port 465
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER, [recipient_email], message.as_string())
        print('Email sent successfully!')
    except Exception as e:
        print(f"Error sending email: {e}")

