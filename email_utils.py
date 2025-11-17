import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_email(to: str, subject: str, html: str) -> bool:
    """Envoie un email via SendGrid et affiche le code de réponse."""

    SENDGRID_KEY = os.getenv("SENDGRID_KEY")

    if not SENDGRID_KEY:
        print("❌ SENDGRID_KEY manquante (variable d’environnement absente).")
        return False

    message = Mail(
        from_email="zendugan95@gmail.com",   # Ton expéditeur validé
        to_emails=to,
        subject=subject,
        html_content=html
    )

    try:
        sg = SendGridAPIClient(SENDGRID_KEY)
        response = sg.send(message)

        print("📨 SendGrid response code:", response.status_code)
        print("📨 SendGrid response body:", response.body)
        print("📨 SendGrid headers:", response.headers)

        return response.status_code in (200, 202)

    except Exception as e:
        print("❌ Erreur SendGrid:", str(e))
        return False
