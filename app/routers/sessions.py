from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, models
from ..database import get_db
from ..utils import limiter
from .auth import get_current_active_user
from ..services import sessions as sessions_service

router = APIRouter()


@router.get("/", response_model=schemas.APIResponse)
@limiter.limit("20/minute")
def get_user_sessions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve all active sessions for the currently logged-in user.
    """
    active_sessions = sessions_service.get_active_sessions(db, current_user.id)
    
    # We can validate our SQL models right into the Pydantic schemas 
    # to safely return them to the user.
    serialized_sessions = [schemas.Session.model_validate(s).model_dump() for s in active_sessions]
    
    return schemas.APIResponse(
        success=True,
        message="Active sessions retrieved successfully.",
        data=serialized_sessions
    )


@router.delete("/all", response_model=schemas.APIResponse)
@limiter.limit("5/minute")
def revoke_all_sessions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Revoke ALL active sessions for the user.
    WARNING: This will log the user out on ALL devices, including the one making this request.
    """
    count = sessions_service.revoke_all_sessions_for_user(db, current_user.id)
    
    return schemas.APIResponse(
        success=True,
        message=f"Successfully revoked {count} active sessions.",
        data={"revoked_count": count}
    )


@router.delete("/{session_id}", response_model=schemas.APIResponse)
@limiter.limit("10/minute")
def revoke_specific_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Revoke a specific session by its internal ID to force a logout on a specific device.
    """
    success = sessions_service.revoke_session(db, session_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=404, 
            detail="Session not found, already inactive, or does not belong to you."
        )
        
    return schemas.APIResponse(
        success=True,
        message="Session has been successfully revoked.",
        data=None
    )
