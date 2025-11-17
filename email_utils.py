import os
import requests

API_KEY = os.environ.get("SENDGRID_API_KEY")

def send_email(to_email, subject, message):
    if not API_KEY:
        print("❌ ERREUR : SENDGRID_API_KEY manquant dans GitHub Secrets")
        return

    url = "https://api.sendgrid.com/v3/mail/send"

    data = {
        "personalizations": [
            {"to": [{"email": to_email}], "subject": subject}
        ],
        "from": {"email": "alerts@flight-tracker.com"},
        "content": [
            {"type": "text/plain", "value": message}
        ],
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(url, json=data, headers=headers)
    print("Email status:", r.status_code)
    return r.status_code
