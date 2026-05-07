from pydantic import BaseModel, EmailStr, model_validator, ConfigDict, Field, field_serializer
from datetime import datetime
from typing import Optional, List, Any


# ── Standardized API Response ─────────────────────────────────────

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Any = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    email: str | None = None

class ApplicationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationResponse(ApplicationBase):
    id: str
    client_id: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_serializer('created_at', 'updated_at', when_used='unless-none')
    def serialize_datetime(self, dt: datetime):
        from datetime import timezone, timedelta
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        target_tz = timezone(timedelta(hours=1))
        return dt.astimezone(target_tz).isoformat()
    
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    username: str = Field(..., min_length=3, max_length=30)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)

class UserCreate(UserBase):
    client_id: str = Field(..., description="The ID of the application making the registration request")
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class User(UserBase):
    id: str
    is_active: bool
    is_verified: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login_at: datetime | None = None

    @field_serializer('created_at', 'updated_at', 'last_login_at', when_used='unless-none')
    def serialize_datetime(self, dt: datetime):
        from datetime import timezone, timedelta
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        target_tz = timezone(timedelta(hours=1))
        return dt.astimezone(target_tz).isoformat()
    
    model_config = ConfigDict(from_attributes=True)

class UserInDB(User):
    hashed_password: str

class UserWithRoles(User):
    roles: List[str] = []


class LoginRequest(BaseModel):
    client_id: str = Field(..., description="The ID of the application making the login request")
    email: EmailStr
    password: str
    device_info: str | None = None
  
    
class ForgotPassword(BaseModel):
    email: EmailStr



class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class ChangePassword(BaseModel):
   current_password: str
   new_password: str = Field(..., min_length=8, max_length=128)
   

   


class SessionCreate(BaseModel):
    device_info: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None

class Session(BaseModel):
    id: str
    user_id: str
    device_info: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    is_active: bool
    expires_at: datetime
    last_active_at: datetime
    created_at: datetime | None = None

    @field_serializer('expires_at', 'last_active_at', 'created_at', when_used='unless-none')
    def serialize_datetime(self, dt: datetime):
        from datetime import timezone, timedelta
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        target_tz = timezone(timedelta(hours=1))
        return dt.astimezone(target_tz).isoformat()

    model_config = ConfigDict(from_attributes=True)
