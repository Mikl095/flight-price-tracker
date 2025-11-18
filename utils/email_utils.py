# utils/email_utils.py
import os
import logging

# attempt to import Streamlit secrets (optional)
try:
    import streamlit as st
    _ST_AVAILABLE = True
except Exception:
    _ST_AVAILABLE = False

# attempt to import sendgrid
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    _HAS_SENDGRID = True
except Exception:
    _HAS_SENDGRID = False

logger = logging.getLogger("email_utils")


def _get_sendgrid_key():
    # prefer streamlit secrets if available
    if _ST_AVAILABLE:
        try:
            s = st.secrets
            key = s.get("SENDGRID_KEY") or s.get("SENDGRID_API_KEY")
            if key:
                return key
        except Exception:
            pass
    # fallback env vars
    return os.environ.get("SENDGRID_KEY") or os.environ.get("SENDGRID_API_KEY")


def _get_default_from():
    # prefer streamlit secret, then env var
    if _ST_AVAILABLE:
        try:
            s = st.secrets
            frm = s.get("SENDGRID_FROM") or s.get("sendgrid_from")
            if frm:
                return frm
        except Exception:
            pass
    return os.environ.get("SENDGRID_FROM") or os.environ.get("EMAIL_FROM")


def send_email(to: str, subject: str, body: str, from_email: str = None):
    """
    Send email via SendGrid.
    Returns (ok: bool, info: dict)
    info contains keys: msg, status_code (if any), response_body (if any), exc (if any)
    """
    info = {"msg": None, "status_code": None, "response_body": None, "exc": None}
    key = _get_sendgrid_key()
    if not key:
        info["msg"] = "No SENDGRID key found (set in Streamlit secrets or env var)"
        logger.warning(info["msg"])
        return False, info

    if not _HAS_SENDGRID:
        info["msg"] = "sendgrid package not installed in environment"
        logger.warning(info["msg"])
        return False, info

    if not from_email:
        from_email = _get_default_from() or "no-reply@example.com"

    try:
        message = Mail(from_email=from_email, to_emails=to, subject=subject, html_content=body)
        client = SendGridAPIClient(key)
        response = client.send(message)
        status = getattr(response, "status_code", None)
        # try to get response body if present
        resp_body = None
        try:
            resp_body = getattr(response, "body", None) or getattr(response, "text", None)
        except Exception:
            resp_body = None

        info["msg"] = "sent" if status and int(status) in (200, 202) else "accepted" if status else "unknown"
        info["status_code"] = status
        info["response_body"] = resp_body
        logger.info(f"SendGrid response: status={status} body={resp_body}")
        # 202 = accepted by SendGrid
        return (True, info) if status and int(status) in (200, 202) else (False, info)
    except Exception as e:
        logger.exception("SendGrid send failed")
        info["exc"] = str(e)
        info["msg"] = "exception"
        return False, info
            
