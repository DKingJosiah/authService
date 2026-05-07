import logging
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from .. import utils
from .email import logger

def generate_password_reset_token(email: str) -> str:
    """
    Generate a secure, short-lived token for password reset.
    Expires in 15 minutes.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"sub": email, "exp": expire, "type": "password_reset"}
    return jwt.encode(to_encode, utils.SECRET_KEY, algorithm=utils.ALGORITHM)


def send_password_reset_email(to_email: str, token: str):
    """
    Send an email containing the reset link.
    """
    reset_link = f"http://localhost:8000/password/reset-password?token={token}"
    logger.info(f"🔑 Password reset email for {to_email}: {reset_link}")
    print(f"🔑 [DEV] Password reset for {to_email}: {reset_link}")


def verify_password_reset_token(token: str) -> str | None:
    """
    Verify the reset token. Returns the email if valid.
    """
    try:
        payload = jwt.decode(token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None

