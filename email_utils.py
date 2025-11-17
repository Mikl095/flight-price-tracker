import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from utils.storage import append_log
from datetime import datetime

FROM_EMAIL = "zendugan95@gmail.com"  # doit être vérifié en Single Sender dans SendGrid

def send_email(to: str, subject: str, html: str) -> bool:
    """Envoie un email via SendGrid. Retourne True si OK."""
    key = os.getenv("SENDGRID_KEY")
    timestamp = datetime.now().isoformat()
    if not key:
        append_log(f"{timestamp} - SendEmail - NO_KEY")
        print("SENDGRID_KEY manquante")
        return False

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to,
        subject=subject,
        html_content=html
    )

    try:
        sg = SendGridAPIClient(key)
        response = sg.send(message)
        append_log(f"{timestamp} - SendEmail - to={to} status={response.status_code}")
        print("SendGrid response:", response.status_code)
        return response.status_code in (200, 202)
    except Exception as e:
        append_log(f"{timestamp} - SendEmail - to={to} ERROR {e}")
        print("SendGrid error:", e)
        return False
