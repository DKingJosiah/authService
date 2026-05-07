from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..utils import limiter
from ..services import auth_service, password as password_service
from .. import utils, schemas, models
from . import auth

router = APIRouter()


@router.post("/forgot-password", response_model=schemas.APIResponse)
@limiter.limit("5/minute")
async def request_password_reset(request: Request, body: schemas.ForgotPassword, db: Session = Depends(get_db)):
    """
    Handle forgotten password requests. Checks if user exists,
    generates token, and sends email.
    """
    user = auth_service.get_user_by_email(db, body.email)
    if user:
        token = password_service.generate_password_reset_token(user.email)
        password_service.send_password_reset_email(user.email, token)
    
    # Always return a generic success message to prevent email enumeration
    return schemas.APIResponse(
        success=True,
        message="If the email is registered, a password reset link has been sent.",
        data=None
    )


@router.post("/reset-password", response_model=schemas.APIResponse)
@limiter.limit("5/minute")
async def reset_password(request: Request, body: schemas.ResetPasswordConfirm, db: Session = Depends(get_db)):
    """
    Completes the password reset process if the token is valid.
    """
    email = password_service.verify_password_reset_token(body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
        
    user = auth_service.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    # Update password
    user.hashed_password = utils.get_password_hash(body.new_password)
    db.commit()

    return schemas.APIResponse(
        success=True,
        message="Password successfully updated.",
        data=None
    )


@router.post("/change-password", response_model=schemas.APIResponse)
@limiter.limit("5/minute")
async def change_password(
    request: Request, 
    body: schemas.ChangePassword, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Route to change password while the user is logged in.
    """
    if not utils.verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
        
    current_user.hashed_password = utils.get_password_hash(body.new_password)
    db.commit()

    return schemas.APIResponse(
        success=True,
        message="Password successfully changed.",
        data=None
    )
