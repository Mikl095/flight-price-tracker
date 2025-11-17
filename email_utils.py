import os
import requests


# --------------------------------------------------------------
#  Envoi d'un email via SendGrid
# --------------------------------------------------------------

def send_email(to: str, subject: str, html: str, reply_to: str = None) -> bool:
    """
    Envoie un email via SendGrid.
    Retourne True si envoyé avec succès, False sinon.
    """

    sg_key = os.getenv("SENDGRID_KEY")

    if not sg_key:
        print("❌ ERREUR : SENDGRID_KEY est absente des secrets Streamlit / GitHub.")
        return False

    # Adresse expéditeur (obligatoirement Single Sender vérifié)
    from_email = "zendugan95@gmail.com"

    if reply_to is None:
        reply_to = from_email

    data = {
        "personalizations": [{
            "to": [{"email": to}],
            "subject": subject,
        }],
        "from": {
            "email": from_email,
            "name": "Flight Price Tracker"
        },
        "reply_to": {"email": reply_to},
        "content": [{
            "type": "text/html",
            "value": html
        }]
    }

    headers = {
        "Authorization": f"Bearer {sg_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        json=data,
        headers=headers
    )

    # Log d'état utile pour debug
    print("SendGrid response:", response.status_code, response.text)

    return response.status_code in [200, 201, 202]
