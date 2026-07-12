from app.core.config import settings
from app.utils.email import send_html_email


class EmailService:

    @staticmethod
    def send_verification_email(
        email: str,
        token: str,
    ):

        verification_url = (
            f"{settings.FRONTEND_URL}/verify-email?token={token}"
        )

        return send_html_email(
            to_email=email,
            subject="Verify Your Account",
            template_name="verify_email.html",
            context={
                "verification_url": verification_url
            },
        )

    @staticmethod
    def send_password_reset_email(
        email: str,
        token: str,
    ):

        reset_url = (
            f"{settings.FRONTEND_URL}/reset-password?token={token}"
        )

        return send_html_email(
            to_email=email,
            subject="Reset Your Password",
            template_name="reset_password.html",
            context={
                "verification_url": reset_url
            },
        )