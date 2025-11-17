import json
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

CONFIG_FILE = "email_config.json"

def load_email_config():
    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"enabled": False, "email": "", "api_key": ""}

def save_email_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def send_notification(subject, message, to_email, api_key):
    try:
        sg = SendGridAPIClient(api_key)
        email = Mail(
            from_email="noreply@flight-tracker.app",
            to_emails=to_email,
            subject=subject,
            html_content=message
        )
        sg.send(email)
        return True
    except Exception as e:
        print("❌ SendGrid error:", e)
        return False
