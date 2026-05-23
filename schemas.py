from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


# ─── User Schemas ────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Token Schemas ────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None


# ─── Workspace Schemas ────────────────────────────────────────────────────────

class WorkspaceCreate(BaseModel):
    project_name: str
    description: Optional[str] = None

    @field_validator("project_name")
    @classmethod
    def project_name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Project name cannot be empty")
        return v.strip()


class WorkspaceResponse(BaseModel):
    workspace_id: int
    user_id: int
    project_name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Generic Response ─────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True
