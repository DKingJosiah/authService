import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from .. import models, schemas

class ApplicationService:
    def __init__(self, db: Session):
        self.db = db

    def generate_client_credentials(self):
        client_id = str(uuid.uuid4().hex)[:16]  # 16-character pseudo-random string
        client_secret = models.generate_client_secret()
        return client_id, client_secret

    def create_application(self, app_data: schemas.ApplicationCreate) -> tuple[models.Application, str]:
        # Check if name exists
        existing_app = self.db.query(models.Application).filter(models.Application.name == app_data.name).first()
        if existing_app:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application with this name already exists")
        
        client_id, client_secret = self.generate_client_credentials()
        
        new_app = models.Application(
            name=app_data.name,
            description=app_data.description,
            client_id=client_id,
            client_secret=client_secret
        )
        
        self.db.add(new_app)
        self.db.commit()
        self.db.refresh(new_app)
        
        return new_app, client_secret

    def get_applications(self, skip: int = 0, limit: int = 100):
        return self.db.query(models.Application).offset(skip).limit(limit).all()

    def get_application(self, application_id: str):
        app = self.db.query(models.Application).filter(models.Application.id == application_id).first()
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        return app
        
    def get_application_by_client_id(self, client_id: str):
        app = self.db.query(models.Application).filter(models.Application.client_id == client_id).first()
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found for the given client_id")
        return app
