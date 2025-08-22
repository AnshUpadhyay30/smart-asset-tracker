import smtplib, ssl, os
from email.message import EmailMessage

def send_temp_password_email(to_email: str, name: str, temp_password: str):
    """
    Minimal SMTP sender using env:
    MAIL_HOST, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM
    """
    host = os.getenv("MAIL_HOST")
    port = int(os.getenv("MAIL_PORT") or 587)
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    mail_from = os.getenv("MAIL_FROM") or username

    if not (host and username and password and to_email):
        # dev mode: silently skip if not configured
        return

    msg = EmailMessage()
    msg["Subject"] = "Your SmartAsset account credentials"
    msg["From"] = mail_from
    msg["To"] = to_email
    msg.set_content(f"""Hi {name},

Your SmartAsset account is ready.

Temporary password: {temp_password}

Login and you will be asked to set a new password on first sign-in.

Regards,
SmartAsset Admin
""")

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port) as server:
        server.starttls(context=context)
        server.login(username, password)
        server.send_message(msg)