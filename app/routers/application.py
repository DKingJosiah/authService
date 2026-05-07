from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from .. import schemas
from ..database import get_db
from ..services.application_service import ApplicationService

router = APIRouter(
    prefix="/applications",
    tags=["Applications"]
)

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_application(app_in: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    """
    Register a new application.
    Returns the application details along with the client_secret (only returned once!).
    """
    app_service = ApplicationService(db)
    new_app, client_secret = app_service.create_application(app_in)
    
    # We must construct the response to include the secret since the response schema doesn't have it natively
    return {
        "success": True,
        "message": "Application created successfully",
        "data": {
            **schemas.ApplicationResponse.model_validate(new_app).model_dump(),
            "client_secret": client_secret
        }
    }

@router.get("/", response_model=schemas.APIResponse)
def get_applications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    app_service = ApplicationService(db)
    apps = app_service.get_applications(skip=skip, limit=limit)
    return schemas.APIResponse(
        success=True,
        message="Applications retrieved successfully",
        data=[schemas.ApplicationResponse.model_validate(app).model_dump() for app in apps]
    )

@router.get("/{application_id}", response_model=schemas.APIResponse)
def get_application(application_id: str, db: Session = Depends(get_db)):
    app_service = ApplicationService(db)
    app = app_service.get_application(application_id)
    return schemas.APIResponse(
        success=True,
        message="Application retrieved successfully",
        data=schemas.ApplicationResponse.model_validate(app).model_dump()
    )
