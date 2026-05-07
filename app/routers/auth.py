from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from .. import models, schemas, utils
from ..database import get_db
from ..services import auth_service
from ..utils import limiter

router = APIRouter(tags=["Authentication"])
security = HTTPBearer()


# ── Auth Dependencies ─────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Extract and validate the JWT access token from the Authorization header."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = auth_service.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    """Ensure the authenticated user's account is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user





@router.post("/register", response_model=schemas.APIResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    db_user = auth_service.register_user(db, user)
    return schemas.APIResponse(
        success=True,
        message="User registered successfully. Please check your email to verify your account.",
        data=schemas.User.model_validate(db_user).model_dump(),
    )


@router.get("/verify-email", response_model=schemas.APIResponse)
@limiter.limit("10/minute")
def verify_email(request: Request, token: str, db: Session = Depends(get_db)):
    """Verify user's email address."""
    auth_service.verify_user_email(db, token)
    return schemas.APIResponse(
        success=True,
        message="Email successfully verified.",
        data=None
    )


@router.post("/login", response_model=schemas.APIResponse)
@limiter.limit("5/minute")
def login(request: Request, login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user, create a session, and return access + refresh tokens."""
    user = auth_service.authenticate_user(db, login_data.email, login_data.password, login_data.client_id)
    token_data = auth_service.create_session(
        db,
        user,
        device_info=login_data.device_info,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return schemas.APIResponse(
        success=True,
        message="Login successful",
        data=token_data,
    )


@router.post("/logout", response_model=schemas.APIResponse)
def logout(token_data: schemas.TokenRefresh, db: Session = Depends(get_db)):
    """Logout by deactivating the session associated with the refresh token."""
    auth_service.logout_session(db, token_data.refresh_token)
    return schemas.APIResponse(
        success=True,
        message="Successfully logged out",
    )


@router.post("/refresh", response_model=schemas.APIResponse)
def refresh_token(token_data: schemas.TokenRefresh, db: Session = Depends(get_db)):
    """Issue a new access token using a valid refresh token."""
    new_tokens = auth_service.refresh_session(db, token_data.refresh_token)
    return schemas.APIResponse(
        success=True,
        message="Token refreshed successfully",
        data=new_tokens,
    )


@router.get("/me", response_model=schemas.APIResponse)
def get_me(current_user: models.User = Depends(get_current_active_user)):
    """Get the currently authenticated user's profile."""
    return schemas.APIResponse(
        success=True,
        message="User profile retrieved",
        data=schemas.User.model_validate(current_user).model_dump(),
    )
