from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from urllib.parse import urlparse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.roles import CompanyRole
from app.core.security import get_password_hash
from app.db.models import Company, User, UserCompanyRole
from app.db.session import SessionLocal

settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")


def _normalize_origin(value: str) -> str:
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.hostname:
        return value.rstrip("/")
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{parsed.hostname}{port}"


def _build_allowed_origins() -> list[str]:
    origins = {
        _normalize_origin(str(settings.frontend_admin_url)),
        _normalize_origin(str(settings.frontend_web_url)),
    }
    expanded = set(origins)
    for origin in origins:
        parsed = urlparse(origin)
        host = parsed.hostname or ""
        if host in {"localhost", "127.0.0.1"}:
            port = f":{parsed.port}" if parsed.port else ""
            expanded.add(f"{parsed.scheme}://localhost{port}")
            expanded.add(f"{parsed.scheme}://127.0.0.1{port}")
            expanded.add(f"{parsed.scheme}://[::1]{port}")
    return sorted(expanded)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_allowed_origins(),
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|\[::1\]|0\.0\.0\.0|host\.docker\.internal|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3})(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.on_event("startup")
def bootstrap_superadmin() -> None:
    if settings.app_env == "test":
        return
    db = SessionLocal()
    try:
        email = settings.superadmin_bootstrap_email.lower().strip()
        password = settings.superadmin_bootstrap_password
        company_name = settings.superadmin_bootstrap_company.strip()

        company = db.scalar(select(Company).where(Company.name == company_name))
        if not company:
            company = Company(name=company_name)
            db.add(company)
            db.flush()

        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                email=email,
                password_hash=get_password_hash(password),
                full_name="Platform Superadmin",
                is_active=True,
            )
            db.add(user)
            db.flush()
        else:
            user.password_hash = get_password_hash(password)
            user.is_active = True

        membership = db.scalar(
            select(UserCompanyRole).where(
                UserCompanyRole.user_id == user.id,
                UserCompanyRole.company_id == company.id,
            )
        )
        if not membership:
            db.add(UserCompanyRole(user_id=user.id, company_id=company.id, role=CompanyRole.SUPERADMIN))
        elif membership.role != CompanyRole.SUPERADMIN:
            membership.role = CompanyRole.SUPERADMIN
        db.commit()
    except OperationalError:
        db.rollback()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": "api"}
