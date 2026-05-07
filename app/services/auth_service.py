from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from .. import models, schemas, utils

from fastapi import APIRouter, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

# ── Query Helpers ─────────────────────────────────────────────────

def get_user_by_email(db: Session, email: str, application_id: str = None):
    query = db.query(models.User).filter(models.User.email == email)
    if application_id:
        query = query.filter(models.User.application_id == application_id)
    return query.first()


def get_user_by_username(db: Session, username: str, application_id: str = None):
    query = db.query(models.User).filter(models.User.username == username)
    if application_id:
        query = query.filter(models.User.application_id == application_id)
    return query.first()


def get_user_by_id(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.id == user_id).first()

def verify_user_email(db: Session, token: str) -> bool:
    """Verify email via token and update user's verification status."""
    email = utils.verify_email_verification_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.is_verified:
        return True # Already verified
        
    user.is_verified = True
    db.commit()
    return True


# ── Registration ──────────────────────────────────────────────────

def register_user(db: Session, user_data: schemas.UserCreate) -> models.User:
    """Register a new user. Raises HTTPException on duplicates."""
    from .application_service import ApplicationService
    
    app_service = ApplicationService(db)
    app = app_service.get_application_by_client_id(user_data.client_id)
    
    # Check for duplicate email
    if get_user_by_email(db, user_data.email, application_id=app.id):
        raise HTTPException(status_code=400, detail="Email already registered for this application")

    # Check for duplicate username
    if get_user_by_username(db, user_data.username, application_id=app.id):
        raise HTTPException(status_code=400, detail="Username already taken for this application")

    # Check for duplicate phone number
    if user_data.phone_number:
        existing_phone = db.query(models.User).filter(
            models.User.phone_number == user_data.phone_number,
            models.User.application_id == app.id
        ).first()
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone number already registered for this application")

    hashed_password = utils.get_password_hash(user_data.password)
    db_user = models.User(
        application_id=app.id,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        username=user_data.username,
        email=user_data.email,
        phone_number=user_data.phone_number,
        hashed_password=hashed_password,
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        # Better error detection
        error_msg = str(e).lower()
        if "unique constraint" in error_msg or "duplicate" in error_msg:
            detail = "Registration failed: Email, Username, or Phone already exists."
        else:
            detail = f"Registration failed: {str(e)}"
        
        raise HTTPException(status_code=400, detail=detail)

    # Send welcome/verification email (non-blocking, won't crash if it fails)
    try:
        from .email import send_verification_email
        token = utils.create_verification_token(db_user.email)
        send_verification_email(db_user.email, token)
    except Exception as e:
        # Email sending failed — don't block registration
        print(f"Email error: {e}")
        pass

    return db_user


# ── Authentication ────────────────────────────────────────────────

def authenticate_user(db: Session, email: str, password: str, client_id: str) -> models.User:
    """Verify credentials. Returns user or raises HTTPException."""
    from .application_service import ApplicationService
    
    app_service = ApplicationService(db)
    app = app_service.get_application_by_client_id(client_id)
    
    user = get_user_by_email(db, email, application_id=app.id)
    if not user or not utils.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return user


# ── Session Management ───────────────────────────────────────────

def create_session(
    db: Session,
    user: models.User,
    device_info: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict:
    """Create tokens + DB session record. Returns the full token response dict."""
    # Generate tokens
    access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = utils.create_refresh_token()

    # Create session record
    session_expires = datetime.now(timezone.utc) + timedelta(days=utils.REFRESH_TOKEN_EXPIRE_DAYS)
    db_session = models.Session(
        user_id=user.id,
        refresh_token=refresh_token,
        device_info=device_info,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=session_expires,
    )
    db.add(db_session)

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": utils.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def logout_session(db: Session, refresh_token: str):
    """Deactivate the session for the given refresh token."""
    session = (
        db.query(models.Session)
        .filter(
            models.Session.refresh_token == refresh_token,
            models.Session.is_active == True,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=400, detail="Invalid or already expired session")

    session.is_active = False
    db.commit()


def refresh_session(db: Session, refresh_token: str) -> dict:
    """Validate refresh token, rotate it, and return new tokens."""
    session = (
        db.query(models.Session)
        .filter(
            models.Session.refresh_token == refresh_token,
            models.Session.is_active == True,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Check expiry
    if session.expires_at < datetime.now(timezone.utc):
        session.is_active = False
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token has expired, please login again")

    # Get user
    user = db.query(models.User).filter(models.User.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Generate new access token
    access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Rotate refresh token
    new_refresh_token = utils.create_refresh_token()
    session.refresh_token = new_refresh_token
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": utils.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
