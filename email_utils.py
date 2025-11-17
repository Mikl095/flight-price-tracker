import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from utils.storage import append_log
from datetime import datetime

DEFAULT_FROM = os.getenv("SENDGRID_FROM", "zendugan95@gmail.com")

def send_email(to: str, subject: str, html: str):
    """
    Envoie un email via SendGrid.
    Retourne (ok: bool, status_code:int|None).
    """
    key = os.getenv("SENDGRID_KEY")
    ts = datetime.now().isoformat()
    if not key:
        append_log(f"{ts} - send_email - NO_KEY to={to}")
        return False, None

    message = Mail(
        from_email=DEFAULT_FROM,
        to_emails=to,
        subject=subject,
        html_content=html
    )
    try:
        sg = SendGridAPIClient(key)
        response = sg.send(message)
        code = getattr(response, "status_code", None)
        append_log(f"{ts} - send_email - to={to} status={code}")
        # response.body/headers may not exist depending on SDK version
        return (code in (200, 202)), code
    except Exception as e:
        append_log(f"{ts} - send_email - to={to} ERROR {e}")
        return False, None
