import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .. import models

logger = logging.getLogger(__name__)

# Note: Session creation is handled in auth_service.create_session natively,
# but we provide these tools for managing/revoking out-of-bounds sessions.

def get_active_sessions(db: Session, user_id: str):
    """
    Retrieve a list of all active sessions for a user.
    """
    return db.query(models.Session).filter(
        models.Session.user_id == user_id,
        models.Session.is_active == True,
        models.Session.expires_at > datetime.now(timezone.utc)
    ).all()


def revoke_session(db: Session, session_id: str, user_id: str) -> bool:
    """
    Invalidate a specific session (force logout on that device).
    We require user_id to ensure users can only revoke their own sessions.
    """
    session = db.query(models.Session).filter(
        models.Session.id == session_id,
        models.Session.user_id == user_id,
        models.Session.is_active == True
    ).first()
    
    if session:
        session.is_active = False
        db.commit()
        return True
    return False


def revoke_all_sessions_for_user(db: Session, user_id: str, keep_session_id: str | None = None):
    """
    Invalidate ALL sessions for a user (useful if an account is compromised).
    Optional: Pass keep_session_id to avoid logging out the session sending this request.
    """
    query = db.query(models.Session).filter(
        models.Session.user_id == user_id,
        models.Session.is_active == True
    )
    if keep_session_id:
        query = query.filter(models.Session.id != keep_session_id)
        
    sessions_to_revoke = query.all()
    count = 0
    for s in sessions_to_revoke:
        s.is_active = False
        count += 1
        
    if count > 0:
        db.commit()
        
    return count
