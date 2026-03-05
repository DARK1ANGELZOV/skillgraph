from datetime import timedelta

from fastapi import Response

from app.core.config import get_settings
from app.core.roles import CompanyRole
from app.core.security import TokenType, create_token
from app.db.models import User, UserCompanyRole

settings = get_settings()


class AuthService:
    access_cookie_name = "sg_access_token"
    refresh_cookie_name = "sg_refresh_token"

    def issue_tokens(self, *, user: User, company_role: UserCompanyRole) -> tuple[str, str]:
        access = create_token(
            subject=user.id,
            company_id=company_role.company_id,
            role=company_role.role.value,
            token_type=TokenType.ACCESS,
            expires_delta=timedelta(minutes=settings.jwt_access_expires_minutes),
        )
        refresh = create_token(
            subject=user.id,
            company_id=company_role.company_id,
            role=company_role.role.value,
            token_type=TokenType.REFRESH,
            expires_delta=timedelta(minutes=settings.jwt_refresh_expires_minutes),
        )
        return access, refresh

    def set_auth_cookies(self, response: Response, *, access_token: str, refresh_token: str) -> None:
        common = {
            "httponly": True,
            "secure": settings.cookie_secure,
            "samesite": "lax",
            "domain": settings.cookie_domain,
            "path": "/",
        }
        response.set_cookie(
            key=self.access_cookie_name,
            value=access_token,
            max_age=settings.jwt_access_expires_minutes * 60,
            **common,
        )
        response.set_cookie(
            key=self.refresh_cookie_name,
            value=refresh_token,
            max_age=settings.jwt_refresh_expires_minutes * 60,
            **common,
        )

    def clear_auth_cookies(self, response: Response) -> None:
        response.delete_cookie(self.access_cookie_name, path="/", domain=settings.cookie_domain)
        response.delete_cookie(self.refresh_cookie_name, path="/", domain=settings.cookie_domain)


AUTH_SERVICE = AuthService()


def can_invite(inviter_role: CompanyRole, target_role: CompanyRole) -> bool:
    matrix = {
        CompanyRole.OWNER: {CompanyRole.HR_SENIOR, CompanyRole.HR_JUNIOR, CompanyRole.SUPERVISOR},
        CompanyRole.HR_SENIOR: {CompanyRole.HR_JUNIOR, CompanyRole.SUPERVISOR},
        CompanyRole.HR_JUNIOR: set(),
        CompanyRole.SUPERVISOR: set(),
        CompanyRole.SUPERADMIN: {
            CompanyRole.OWNER,
            CompanyRole.HR_SENIOR,
            CompanyRole.HR_JUNIOR,
            CompanyRole.SUPERVISOR,
            CompanyRole.SUPERADMIN,
        },
    }
    return target_role in matrix[inviter_role]
