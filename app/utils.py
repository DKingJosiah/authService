from datetime import datetime, timedelta, timezone
from jose import jwt
import secrets
from .config import settings

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# ── Fix passlib + bcrypt v5 compatibility ─────────────────────────
# bcrypt v5 raises an error for passwords > 72 bytes instead of
# silently truncating like v4 did. Passlib's internal bug-detection
# test triggers this. This patch restores the old behavior.
import bcrypt as _bcrypt

_original_hashpw = _bcrypt.hashpw
_original_checkpw = _bcrypt.checkpw

def _safe_hashpw(password, salt):
    if isinstance(password, str):
        password = password.encode("utf-8")
    if isinstance(salt, str):
        salt = salt.encode("utf-8")
    return _original_hashpw(password[:72], salt)

def _safe_checkpw(password, hashed):
    if isinstance(password, str):
        password = password.encode("utf-8")
    if isinstance(hashed, str):
        hashed = hashed.encode("utf-8")
    return _original_checkpw(password[:72], hashed)

_bcrypt.hashpw = _safe_hashpw
_bcrypt.checkpw = _safe_checkpw
# ──────────────────────────────────────────────────────────────────

from passlib.context import CryptContext

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token():
    """Generate a cryptographically secure random refresh token string."""
    return secrets.token_urlsafe(64)

def create_verification_token(email: str):
    """Generate a JWT token for email verification valid for 24 hours."""
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode = {"sub": email, "exp": expire, "type": "email_verification"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_email_verification_token(token: str) -> str | None:
    """Decode the verification token and return the email if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "email_verification":
            return None
        return payload.get("sub")
    except jwt.JWTError:
        return None
