"""Email delivery provider interfaces with Mock structured logging and Production SMTP capabilities."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseEmailProvider(ABC):
    """Abstract contract for transactional email dispatch."""

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """Dispatches an email. Returns True if successfully accepted/delivered."""
        pass


class MockEmailProvider(BaseEmailProvider):
    """Structured mock email provider for local development, CI testing, and offline modes.

    CRITICAL: Never silently drops messages; captures full delivery metadata for assertions.
    """

    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        record = {
            "to_email": to_email,
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body or subject,
            "dispatched_at": datetime.now(timezone.utc).isoformat(),
        }
        self.sent_messages.append(record)
        logger.info(
            f"[MOCK EMAIL DISPATCHED] To: {to_email} | Subject: '{subject}' | Total Sent: {len(self.sent_messages)}"
        )
        return True

    def clear(self) -> None:
        """Clears captured messages (used between unit tests)."""
        self.sent_messages.clear()


class SmtpEmailProvider(BaseEmailProvider):
    """Production SMTP email provider with TLS support."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_pass: str,
        sender_email: str,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
        self.sender_email = sender_email

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        import asyncio
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        import smtplib

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = to_email

        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        def _send():
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.sendmail(self.sender_email, [to_email], msg.as_string())

        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _send)
            logger.info(f"Production email successfully sent to {to_email} via SMTP")
            return True
        except Exception as e:
            logger.error(f"SMTP email dispatch failed to {to_email}: {e}")
            return False


# Global default email provider instance (defaults to Mock in non-prod or unless configured)
_email_provider: BaseEmailProvider = MockEmailProvider()


def get_email_provider() -> BaseEmailProvider:
    """Returns the globally configured email provider instance."""
    return _email_provider


def set_email_provider(provider: BaseEmailProvider) -> None:
    """Configures a custom email provider instance (e.g. for testing)."""
    global _email_provider
    _email_provider = provider
