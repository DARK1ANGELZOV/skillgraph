from datetime import UTC, datetime, timedelta
import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import AuthContext, get_current_context, get_refresh_token, require_roles
from app.core.roles import CompanyRole
from app.core.security import TokenType, decode_token, get_password_hash, verify_password
from app.db.models import Company, Invite, User, UserCompanyRole
from app.db.session import get_db
from app.schemas.auth import (
    AuthSessionResponse,
    InviteAcceptRequest,
    InviteCreateRequest,
    LoginRequest,
    OwnerRegisterRequest,
)
from app.services.audit import log_audit
from app.services.auth import AUTH_SERVICE, can_invite

router = APIRouter()


@router.post("/register-owner", response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
def register_owner(payload: OwnerRegisterRequest, response: Response, db: Session = Depends(get_db)):
    existing_user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    existing_company = db.scalar(select(Company).where(Company.name == payload.company_name))
    if existing_company:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Company already exists")

    user = User(
        email=payload.email.lower(),
        password_hash=get_password_hash(payload.password),
        full_name=payload.full_name,
    )
    company = Company(name=payload.company_name)
    db.add_all([user, company])
    db.flush()

    membership = UserCompanyRole(user_id=user.id, company_id=company.id, role=CompanyRole.OWNER)
    db.add(membership)

    access_token, refresh_token = AUTH_SERVICE.issue_tokens(user=user, company_role=membership)
    AUTH_SERVICE.set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)

    log_audit(
        db,
        action="owner_registered",
        entity_type="company",
        entity_id=company.id,
        company_id=company.id,
        user_id=user.id,
        payload={"email": user.email},
    )

    db.commit()
    return AuthSessionResponse(user_id=user.id, company_id=company.id, role=membership.role, email=user.email)


@router.post("/login", response_model=AuthSessionResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    role_query = select(UserCompanyRole).where(UserCompanyRole.user_id == user.id)
    if payload.company_id:
        role_query = role_query.where(UserCompanyRole.company_id == payload.company_id)
    membership = db.scalar(role_query.order_by(UserCompanyRole.created_at.asc()))
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No company membership")

    access_token, refresh_token = AUTH_SERVICE.issue_tokens(user=user, company_role=membership)
    AUTH_SERVICE.set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)

    log_audit(
        db,
        action="user_logged_in",
        entity_type="user",
        entity_id=user.id,
        company_id=membership.company_id,
        user_id=user.id,
    )
    db.commit()

    return AuthSessionResponse(user_id=user.id, company_id=membership.company_id, role=membership.role, email=user.email)


@router.post("/refresh", response_model=AuthSessionResponse)
def refresh_session(
    response: Response,
    refresh_token: str = Depends(get_refresh_token),
    db: Session = Depends(get_db),
):
    try:
        payload = decode_token(refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    if payload.get("type") != TokenType.REFRESH:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")

    user = db.get(User, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    try:
        token_role = CompanyRole(payload.get("role"))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token role") from exc

    membership = db.scalar(
        select(UserCompanyRole).where(
            UserCompanyRole.user_id == user.id,
            UserCompanyRole.company_id == payload.get("company_id"),
            UserCompanyRole.role == token_role,
        )
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membership invalid")

    access_token, new_refresh = AUTH_SERVICE.issue_tokens(user=user, company_role=membership)
    AUTH_SERVICE.set_auth_cookies(response, access_token=access_token, refresh_token=new_refresh)

    return AuthSessionResponse(user_id=user.id, company_id=membership.company_id, role=membership.role, email=user.email)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    AUTH_SERVICE.clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/invites", status_code=status.HTTP_201_CREATED)
def create_invite(
    payload: InviteCreateRequest,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(
        require_roles(
            CompanyRole.OWNER,
            CompanyRole.HR_SENIOR,
            CompanyRole.SUPERADMIN,
        )
    ),
):
    if not can_invite(ctx.role, payload.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot invite target role")

    existing_member = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing_member:
        existing_role = db.scalar(
            select(UserCompanyRole).where(
                UserCompanyRole.user_id == existing_member.id,
                UserCompanyRole.company_id == ctx.company_id,
            )
        )
        if existing_role:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already in company")

    invite = Invite(
        company_id=ctx.company_id,
        email=payload.email.lower(),
        role=payload.role,
        token=secrets.token_urlsafe(32),
        invited_by=ctx.user.id,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(invite)
    db.flush()
    log_audit(
        db,
        action="invite_created",
        entity_type="invite",
        entity_id=invite.id,
        company_id=ctx.company_id,
        user_id=ctx.user.id,
        payload={"target_role": payload.role.value, "email": payload.email.lower()},
    )
    db.commit()
    return {
        "id": invite.id,
        "email": invite.email,
        "role": invite.role,
        "token": invite.token,
        "expires_at": invite.expires_at.isoformat(),
    }


@router.post("/invites/accept", response_model=AuthSessionResponse)
def accept_invite(payload: InviteAcceptRequest, response: Response, db: Session = Depends(get_db)):
    invite = db.scalar(select(Invite).where(Invite.token == payload.token))
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.accepted_at:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invite already accepted")
    if invite.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite expired")

    user = db.scalar(select(User).where(User.email == invite.email))
    if not user:
        user = User(
            email=invite.email,
            password_hash=get_password_hash(payload.password),
            full_name=payload.full_name,
        )
        db.add(user)
        db.flush()
    else:
        user.password_hash = get_password_hash(payload.password)
        if payload.full_name:
            user.full_name = payload.full_name

    membership = db.scalar(
        select(UserCompanyRole).where(
            UserCompanyRole.user_id == user.id,
            UserCompanyRole.company_id == invite.company_id,
        )
    )
    if membership:
        membership.role = invite.role
    else:
        membership = UserCompanyRole(user_id=user.id, company_id=invite.company_id, role=invite.role)
        db.add(membership)

    invite.accepted_at = datetime.now(UTC)

    access_token, refresh_token = AUTH_SERVICE.issue_tokens(user=user, company_role=membership)
    AUTH_SERVICE.set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)

    log_audit(
        db,
        action="invite_accepted",
        entity_type="invite",
        entity_id=invite.id,
        company_id=invite.company_id,
        user_id=user.id,
        payload={"role": invite.role.value},
    )

    db.commit()
    return AuthSessionResponse(user_id=user.id, company_id=invite.company_id, role=invite.role, email=user.email)


@router.get("/me", response_model=AuthSessionResponse)
def me(ctx: AuthContext = Depends(get_current_context)):
    return AuthSessionResponse(
        user_id=ctx.user.id,
        company_id=ctx.company_id,
        role=ctx.role,
        email=ctx.user.email,
    )
