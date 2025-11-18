# utils/email_utils.py
import os
import logging

# try to import streamlit secrets if app running in Streamlit
try:
    import streamlit as st
    _ST_AVAILABLE = True
except Exception:
    _ST_AVAILABLE = False

# try to import sendgrid library
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    _HAS_SENDGRID = True
except Exception:
    _HAS_SENDGRID = False

logger = logging.getLogger("email_utils")


def _get_sendgrid_key():
    """Look for key in Streamlit secrets first, then environment var."""
    # Streamlit secrets (recommended)
    if _ST_AVAILABLE:
        try:
            secrets = st.secrets
            key = secrets.get("SENDGRID_KEY") or secrets.get("sendgrid_key")
            if key:
                return key
        except Exception:
            pass
    # environment variable fallback
    key = os.environ.get("SENDGRID_KEY") or os.environ.get("SENDGRID_API_KEY")
    return key


def send_email(to: str, subject: str, body: str, from_email: str = None) -> (bool, str):
    """
    Send an email using SendGrid.
    Returns (ok: bool, status_or_error: str/int)
    - ok True => status code (int)
    - ok False => error message
    """
    key = _get_sendgrid_key()
    if not key:
        msg = "No SENDGRID key found (set in Streamlit secrets or env var SENDGRID_KEY)"
        logger.warning(msg)
        return False, msg

    if not _HAS_SENDGRID:
        msg = "sendgrid package not installed in environment"
        logger.warning(msg)
        return False, msg

    # default from email: optionally from Streamlit secrets or env or a fixed placeholder
    default_from = None
    if _ST_AVAILABLE:
        default_from = st.secrets.get("SENDGRID_FROM") if hasattr(st, "secrets") else None
    if not default_from:
        default_from = os.environ.get("SENDGRID_FROM") or os.environ.get("EMAIL_FROM")

    if not from_email:
        if default_from:
            from_email = default_from
        else:
            # SendGrid often requires validated sender; fallback to a placeholder but may reject
            from_email = "no-reply@example.com"

    try:
        message = Mail(
            from_email=from_email,
            to_emails=to,
            subject=subject,
            html_content=body
        )
        client = SendGridAPIClient(key)
        response = client.send(message)
        status = getattr(response, "status_code", None)
        logger.info(f"Email sent to {to}, status {status}")
        return True, status
    except Exception as e:
        logger.exception("SendGrid send failed")
        return False, str(e)
