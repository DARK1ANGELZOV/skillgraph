from dataclasses import dataclass

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.roles import CompanyRole
from app.core.security import TokenType, decode_token
from app.db.models import User, UserCompanyRole
from app.db.session import get_db


@dataclass(slots=True)
class AuthContext:
    user: User
    company_id: str
    role: CompanyRole


def _extract_token(
    access_cookie: str | None,
    authorization: str | None,
) -> str:
    if access_cookie:
        return access_cookie
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", maxsplit=1)[1]
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")


def get_current_context(
    db: Session = Depends(get_db),
    access_cookie: str | None = Cookie(default=None, alias="sg_access_token"),
    authorization: str | None = Header(default=None),
) -> AuthContext:
    token = _extract_token(access_cookie, authorization)
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from exc

    if payload.get("type") != TokenType.ACCESS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")

    user = db.get(User, payload.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")

    company_id = payload.get("company_id")
    role_value = payload.get("role")
    if not company_id or not role_value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token payload incomplete")

    try:
        role = CompanyRole(role_value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid role in token") from exc

    role_row = db.scalar(
        select(UserCompanyRole).where(
            UserCompanyRole.user_id == user.id,
            UserCompanyRole.company_id == company_id,
            UserCompanyRole.role == role,
        )
    )
    if not role_row:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membership missing")

    return AuthContext(user=user, company_id=company_id, role=role)


def require_roles(*roles: CompanyRole):
    allowed = set(roles)

    def _checker(ctx: AuthContext = Depends(get_current_context)) -> AuthContext:
        if ctx.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return ctx

    return _checker


def get_refresh_token(refresh_cookie: str | None = Cookie(default=None, alias="sg_refresh_token")) -> str:
    if not refresh_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    return refresh_cookie
