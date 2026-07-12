import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


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

    message = MIMEMultipart()

    message["From"] = settings.SMTP_USERNAME
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(
        MIMEText(html_content, "html")
    )

    try:

        with smtplib.SMTP(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
        ) as server:

            server.starttls()

            server.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD,
            )

            server.sendmail(
                settings.SMTP_USERNAME,
                to_email,
                message.as_string(),
            )

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {str(e)}")
        logger.error("Gmail: Use App Password, not regular password. Enable 2FA first.")
        return False
    
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {str(e)}")
        return False
    
    except Exception as e:
        logger.error(f"Email Error: {str(e)}", exc_info=True)
        return False