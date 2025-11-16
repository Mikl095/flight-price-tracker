import os
import requests

SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
SENDGRID_FROM = os.environ["SENDGRID_FROM"]
SENDGRID_TO = os.environ["SENDGRID_TO"]

def send_email(subject, text):
    url = "https://api.sendgrid.com/v3/mail/send"

    data = {
        "personalizations": [
            {
                "to": [{"email": SENDGRID_TO}],
                "subject": subject
            }
        ],
        "from": {"email": SENDGRID_FROM},
        "content": [
            {"type": "text/plain", "value": text}
        ]
    }

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=data, headers=headers)
    return response.status_code, response.text
