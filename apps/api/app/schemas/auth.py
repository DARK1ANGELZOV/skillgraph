from pydantic import BaseModel, EmailStr, Field

from app.core.roles import CompanyRole


class OwnerRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company_name: str = Field(min_length=2, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company_id: str | None = None


class AuthSessionResponse(BaseModel):
    user_id: str
    company_id: str
    role: CompanyRole
    email: EmailStr


class InviteCreateRequest(BaseModel):
    email: EmailStr
    role: CompanyRole


class InviteAcceptRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class InviteResponse(BaseModel):
    id: str
    email: EmailStr
    role: CompanyRole
    token: str
    expires_at: str
