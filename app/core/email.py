import json
import urllib.error
import urllib.request
from email.utils import parseaddr

from app.config import get_settings

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"


def send_invitation_email(to_email: str, project_name: str, invite_token: str, message: str = "") -> None:
    settings = get_settings()
    invite_link = f"{settings.invite_base_url}?token={invite_token}"

    body = (
        f"Hello,\n\nYou have been invited to collaborate on the project '{project_name}' on Apex.\n\n"
        f"Message from the project owner:\n{message}\n\n"
        f"Use the link below to accept your invitation:\n{invite_link}\n\n"
        f"This invitation link expires in 7 days."
    )

    name, address = parseaddr(settings.mail_default_sender)
    payload = {
        "sender": {"name": name or "Apex", "email": address},
        "to": [{"email": to_email}],
        "subject": f"Invitation to join project: {project_name}",
        "textContent": body,
    }

    request = urllib.request.Request(
        BREVO_SEND_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "api-key": settings.brevo_api_key.get_secret_value(),
            "content-type": "application/json",
            "accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"Brevo rejected the email (HTTP {e.code}): {detail}") from e