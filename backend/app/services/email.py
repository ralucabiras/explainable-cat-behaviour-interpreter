import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    async def send_confirmation(self, recipient: str, display_name: str, token: str) -> str:
        settings = get_settings()
        confirmation_url = f"{settings.frontend_url}/confirm-email?token={token}"
        if settings.email_delivery_mode == "console":
            logger.warning("Development confirmation URL for %s: %s", recipient, confirmation_url)
            return confirmation_url
        if settings.email_delivery_mode != "gmail":
            raise RuntimeError("EMAIL_DELIVERY_MODE must be 'console' or 'gmail'")
        if not settings.gmail_address or not settings.gmail_app_password:
            raise RuntimeError("Gmail SMTP credentials are not configured")
        await asyncio.to_thread(
            self._send_gmail,
            recipient,
            display_name,
            confirmation_url,
            settings.gmail_address,
            settings.gmail_app_password,
            settings.email_from_name,
        )
        return confirmation_url

    @staticmethod
    def _send_gmail(
        recipient: str,
        display_name: str,
        confirmation_url: str,
        gmail_address: str,
        app_password: str,
        from_name: str,
    ) -> None:
        message = EmailMessage()
        message["Subject"] = "Confirm your Whiskerwise email"
        message["From"] = f"{from_name} <{gmail_address}>"
        message["To"] = recipient
        message.set_content(
            f"Hello {display_name},\n\n"
            "Confirm your email address to activate your account:\n"
            f"{confirmation_url}\n\n"
            "This link expires in 24 hours. If you did not create this account, ignore this email."
        )
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(gmail_address, app_password)
            server.send_message(message)
