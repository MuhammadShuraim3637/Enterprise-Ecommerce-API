from pathlib import Path
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


def send_html_email(
    to_email: str,
    subject: str,
    template_name: str,
    context: dict,
):
    template_path = Path("app/templates/email") / template_name

    if template_path.exists():
        html_content = template_path.read_text(
            encoding="utf-8"
        ).format(**context)
    else:
        html_content = f"""
        <h2>{subject}</h2>

        <p>
            Click below to verify your account.
        </p>

        <a href="{context.get('verification_url')}">
            Verify Email
        </a>
        """

    payload = {
        "from": settings.EMAIL_FROM,
        "to": [to_email],
        "subject": subject,
        "html": html_content,
    }

    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(
            RESEND_API_URL,
            json=payload,
            headers=headers,
            timeout=10.0,
        )

        if response.status_code in (200, 201):
            logger.info(f"Email sent successfully to {to_email}")
            return True

        # Resend returns useful error details in the response body —
        # e.g. sandbox mode rejecting a recipient other than the account owner.
        logger.error(
            f"Resend API error ({response.status_code}) sending to {to_email}: {response.text}"
        )
        return False

    except httpx.TimeoutException:
        logger.error(f"Email request to Resend timed out for {to_email}")
        return False

    except Exception as e:
        logger.error(f"Email Error: {str(e)}", exc_info=True)
        return False
