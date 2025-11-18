# utils/email_utils.py
import os
import logging
from typing import Union, Tuple, List

# try to import streamlit secrets if app running in Streamlit
try:
    import streamlit as st
    _ST_AVAILABLE = True
except Exception:
    _ST_AVAILABLE = False

# try to import sendgrid library
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    _HAS_SENDGRID = True
except Exception:
    _HAS_SENDGRID = False

# smtp fallback
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("email_utils")


def _get_sendgrid_key() -> Union[str, None]:
    """Look for key in Streamlit secrets first, then environment var."""
    # Streamlit secrets (recommended)
    if _ST_AVAILABLE:
        try:
            secrets = st.secrets
            # common keys
            key = secrets.get("SENDGRID_KEY") or secrets.get("sendgrid_key") or secrets.get("SENDGRID_API_KEY")
            if key:
                return key
        except Exception:
            pass
    # environment variable fallback
    return os.environ.get("SENDGRID_KEY") or os.environ.get("SENDGRID_API_KEY") or os.environ.get("SENDGRID_KEY")


def _get_default_from() -> Union[str, None]:
    """Return default from address from secrets/env if available."""
    if _ST_AVAILABLE:
        try:
            val = st.secrets.get("SENDGRID_FROM") or st.secrets.get("EMAIL_FROM")
            if val:
                return val
        except Exception:
            pass
    return os.environ.get("SENDGRID_FROM") or os.environ.get("EMAIL_FROM")


def _normalize_recipients(to: Union[str, List[str]]) -> List[str]:
    if isinstance(to, str):
        # allow comma separated
        recipients = [x.strip() for x in to.replace(";", ",").split(",") if x.strip()]
        return recipients
    elif isinstance(to, (list, tuple)):
        return [str(x).strip() for x in to if str(x).strip()]
    else:
        return []


def send_email(to: Union[str, List[str]], subject: str, body: str, from_email: str = None) -> Tuple[bool, Union[int, str]]:
    """
    Send an email using SendGrid if available, otherwise attempt SMTP fallback.
    Returns (ok: bool, status_or_error: int|str)
    """
    recipients = _normalize_recipients(to)
    if not recipients:
        msg = "No recipient provided"
        logger.warning(msg)
        return False, msg

    key = _get_sendgrid_key()
    if not from_email:
        from_email = _get_default_from() or "no-reply@example.com"

    # Try SendGrid if available and key exists
    if _HAS_SENDGRID and key:
        try:
            # SendGrid Mail accepts lists for to_emails
            message = Mail(
                from_email=from_email,
                to_emails=recipients,
                subject=subject,
                html_content=body
            )
            client = SendGridAPIClient(key)
            response = client.send(message)
            status = getattr(response, "status_code", None)
            logger.info(f"Email sent via SendGrid to {recipients}, status {status}")
            return True, status
        except Exception as e:
            logger.exception("SendGrid send failed, will attempt SMTP fallback if configured")
            # fall through to SMTP fallback

    # SMTP fallback if configured via env vars
    smtp_host = os.environ.get("SMTP_HOST") or os.environ.get("EMAIL_SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT") or os.environ.get("EMAIL_SMTP_PORT") or 0)
    smtp_user = os.environ.get("SMTP_USER") or os.environ.get("EMAIL_SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS") or os.environ.get("EMAIL_SMTP_PASS")
    use_tls = os.environ.get("SMTP_TLS", "true").lower() in ("1", "true", "yes")

    if smtp_host and smtp_port:
        try:
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))

            if use_tls:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)

            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)

            server.sendmail(from_email, recipients, msg.as_string())
            server.quit()
            logger.info(f"Email sent via SMTP to {recipients} through {smtp_host}:{smtp_port}")
            return True, "smtp:ok"
        except Exception as e:
            logger.exception("SMTP send failed")
            return False, str(e)

    # If we reached here, no method succeeded / configured
    err = "No SendGrid key found and no SMTP configuration available"
    logger.warning(err)
    return False, err
