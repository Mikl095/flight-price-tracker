import os
import requests

SENDGRID_API_KEY = os.getenv("SENDGRID_KEY")

def send_email(to, subject, html):
    """
    Envoie un email via SendGrid API.
    Retourne True si OK / False si échec.
    """

    if not SENDGRID_API_KEY:
        print("❌ ERREUR : aucune clé SENDGRID_KEY détectée dans les secrets.")
        return False

    url = "https://api.sendgrid.com/v3/mail/send"

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "personalizations": [
            {
                "to": [{"email": to}],
                "subject": subject
            }
        ],
        "from": {"email": "no-reply@flighttracker.app"},  # valid custom sender
        "content": [
            {
                "type": "text/html",
                "value": html
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code in [200, 202]:
        return True
    else:
        print("❌ SendGrid error:", response.status_code, response.text)
        return False
