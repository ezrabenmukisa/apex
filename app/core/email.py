import smtplib
from email.message import EmailMessage
from app.config import get_settings

def send_invitation_email(to_email: str, project_name: str, invite_token: str) -> None:
    settings = get_settings()

    invite_link = f"{settings.invite_base_url}?token={invite_token}"

    msg = EmailMessage()
    msg["Subject"] = f"Invitation to join project: {project_name}"
    msg["From"] = settings.mail_default_sender
    msg["To"] = to_email
    msg.set_content(
        f"Hello,\n\nYou have been invited to collaborate on the project '{project_name}' on Apex.\n\n"
        f"Use the link below to accept your invitation:\n{invite_link}\n\n"
        f"This invitation link expires in 7 days."
    )

    password = settings.mail_password.get_secret_value()

    if settings.mail_use_ssl:
        with smtplib.SMTP_SSL(settings.mail_server, settings.mail_port) as server:
            server.login(settings.mail_username, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(settings.mail_server, settings.mail_port) as server:
            server.starttls()
            server.login(settings.mail_username, password)
            server.send_message(msg)