import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def sendgrid_send(to_email, subject, content):
    api_key = os.environ.get("SENDGRID_KEY") or os.getenv("SENDGRID_API_KEY")
    from_email = os.environ.get("SENDGRID_FROM", "alerts@flight-tracker.app")
    if not api_key:
        print("SendGrid API key missing. Not sending email.")
        return False

    try:
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=content
        )
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        print("SendGrid status:", response.status_code)
        return response.status_code in (200, 202)
    except Exception as e:
        print("SendGrid error:", e)
        return False
