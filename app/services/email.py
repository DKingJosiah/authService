import secrets
import logging

logger = logging.getLogger(__name__)


def generate_verification_token() -> str:
    """Generate a cryptographically secure token for email verification."""
    return secrets.token_urlsafe(32)


def send_verification_email(to_email: str, token: str):
    """
    Send a verification email to the newly registered user.
    
    TODO: Replace this with your actual email provider (SendGrid, AWS SES, Mailgun, etc.)
    For now, this logs the verification link so you can test without a mail provider.
    """
    # In production, uncomment and configure your email provider:
    #
    # from sendgrid import SendGridAPIClient
    # from sendgrid.helpers.mail import Mail
    # from ..config import settings
    #
    # verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    # message = Mail(
    #     from_email="noreply@yourapp.com",
    #     to_emails=to_email,
    #     subject="Verify Your Email",
    #     html_content=f"""
    #     <h2>Welcome!</h2>
    #     <p>Click the link below to verify your email:</p>
    #     <a href="{verification_link}">{verification_link}</a>
    #     <p>Expires in 24 hours.</p>
    #     """
    # )
    # sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    # sg.send(message)

    # For development — log the token so you can verify manually
    verification_link = f"http://localhost:8000/auth/verify-email?token={token}"
    logger.info(f"📧 Verification email for {to_email}: {verification_link}")
    print(f"📧 [DEV] Verification email for {to_email}: {verification_link}")