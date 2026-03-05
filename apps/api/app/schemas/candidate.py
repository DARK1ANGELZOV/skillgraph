from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class VacancyCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    department: str = Field(min_length=2, max_length=255)
    seniority: str = Field(default="middle", max_length=64)
    requirements: str = Field(min_length=10)


class VacancyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    department: str
    seniority: str
    requirements: str
    is_active: bool
    created_at: datetime


class CandidateInviteRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    vacancy_id: str | None = None
    experience_years: int | None = Field(default=None, ge=0, le=60)
    skills: list[str] = Field(default_factory=list)
    education: str | None = Field(default=None, max_length=3000)


class CandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: EmailStr
    status: str
    vacancy_id: str | None
    experience_years: int | None
    skills: list[str]
    education: str | None
    magic_link_token: str
    interview_id: str | None = None
    interview_link: str | None = None
    tests_link: str | None = None
    created_at: datetime
