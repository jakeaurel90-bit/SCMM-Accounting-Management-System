import requests
from django.conf import settings
from django.core.mail import EmailMessage


def send_pastor_email(subject, body, to_email):
    """
    Sends a single email.

    Uses Brevo's HTTP API when BREVO_API_KEY is configured — this works on
    hosts like Render that block outbound SMTP ports, since it's just a
    normal HTTPS request. Falls back to Django's SMTP-based MAILERS setup
    otherwise (fine for local development, or hosts that don't block SMTP).

    Raises an exception on failure so callers can catch and count it,
    exactly like the old EmailMessage.send() call did.
    """
    if settings.BREVO_API_KEY:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": settings.BREVO_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "sender": {"email": settings.DEFAULT_FROM_EMAIL},
                "to": [{"email": to_email}],
                "subject": subject,
                "textContent": body,
            },
            timeout=10,
        )
        if response.status_code >= 300:
            raise RuntimeError(f"Brevo error {response.status_code}: {response.text}")
    else:
        email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [to_email])
        email.send(using="default")
