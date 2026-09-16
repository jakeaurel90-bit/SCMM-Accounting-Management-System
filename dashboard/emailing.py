import requests
from django.conf import settings
from django.core.mail import EmailMessage


def send_pastor_email(subject, body, to_email):
    """
    Sends a single email.

    Uses SendGrid's HTTP API when SENDGRID_API_KEY is configured — this
    works on hosts like Render that block outbound SMTP ports, since it's
    just a normal HTTPS request. Falls back to Django's SMTP-based MAILERS
    setup otherwise (fine for local development, or hosts that don't block
    SMTP).

    Raises an exception on failure so callers can catch and count it,
    exactly like the old EmailMessage.send() call did.
    """
    if settings.SENDGRID_API_KEY:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": settings.DEFAULT_FROM_EMAIL},
                "subject": subject,
                "content": [{"type": "text/plain", "value": body}],
            },
            timeout=10,
        )
        if response.status_code >= 300:
            raise RuntimeError(f"SendGrid error {response.status_code}: {response.text}")
    else:
        email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [to_email])
        email.send(using="default")
