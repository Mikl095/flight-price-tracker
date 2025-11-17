import os
import requests

SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]

def send_email(to_email, subject, message):
    url = "https://api.sendgrid.com/v3/mail/send"

    data = {
        "personalizations": [
            {"to": [{"email": to_email}], "subject": subject}
        ],
        "from": {"email": "alert@flight-tracker.com"},
        "content": [
            {"type": "text/plain", "value": message}
        ],
    }

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(url, json=data, headers=headers)
    return r.status_code
