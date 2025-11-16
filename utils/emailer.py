import smtplib
from email.mime.text import MIMEText
import os

def send_email_alert(route, price):
    gmail_user = os.getenv("GMAIL_USER")
    gmail_pass = os.getenv("GMAIL_PASS")
    recipient = os.getenv("NOTIFY_EMAIL")

    if not (gmail_user and gmail_pass and recipient):
        print("Email not configured, skipping.")
        return

    subject = f"🔥 Prix en baisse : {route['origin']} → {route['destination']}"
    body = f"""
Prix actuel : {price}€ (seuil {route['target_price']}€)
Départ : {route['departure']}
Retour : {route['return']}

Historique mis à jour dans votre application.
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, recipient, msg.as_string())

    print("Email envoyé ✔️")
  
