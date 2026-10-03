"""Registration and cookie-backed authentication endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth_security import (
    auth_rate_limiter,
    hash_password,
    new_token,
    token_digest,
    verify_password,
    verify_unknown_password,
)
from app.config import get_settings
from app.database import get_db
from app.dependencies import (
    CSRF_COOKIE,
    CSRF_HEADER,
    SESSION_COOKIE,
    get_current_user,
    get_session_record,
    require_csrf,
    require_public_csrf,
)
from app.models import AuthSession, User, utcnow
from app.schemas import AuthResponse, CSRFResponse, LoginRequest, RegisterRequest, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def _check_rate_limit(request: Request, action: str, identifier: str = "") -> None:
    client_ip = request.client.host if request.client else "unknown"
    key = f"{action}:{client_ip}:{identifier}"
    limit = 10 if action == "register" else 8
    if not auth_rate_limiter.check(key, limit=limit, window_seconds=60):
        raise HTTPException(status_code=429, detail="Too many attempts. Please try again later.")


def _set_cookie(response: Response, key: str, value: str, *, http_only: bool, max_age: int) -> None:
    settings = get_settings()
    response.set_cookie(
        key,
        value,
        max_age=max_age,
        httponly=http_only,
        secure=settings.cookie_secure,
        samesite=settings.cookie_same_site,
        path="/api",
    )


def _new_session(db: Session, user: User, request: Request, response: Response) -> str:
    settings = get_settings()
    prior_session = get_session_record(request, db)
    if prior_session is not None:
        db.delete(prior_session)
    token = new_token()
    csrf_token = new_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.session_ttl_hours)
    db.add(
        AuthSession(
            token_hash=token_digest(token),
            csrf_token_hash=token_digest(csrf_token),
            user_id=user.id,
            expires_at=expires_at,
            created_at=utcnow(),
        )
    )
    db.commit()
    max_age = settings.session_ttl_hours * 60 * 60
    _set_cookie(response, SESSION_COOKIE, token, http_only=True, max_age=max_age)
    _set_cookie(response, CSRF_COOKIE, csrf_token, http_only=False, max_age=max_age)
    return csrf_token


def _rotate_anonymous_csrf(response: Response) -> str:
    csrf_token = new_token()
    _set_cookie(response, CSRF_COOKIE, csrf_token, http_only=False, max_age=600)
    return csrf_token


@router.get("/csrf", response_model=CSRFResponse)
def csrf_token(request: Request, response: Response, db: Session = Depends(get_db)) -> CSRFResponse:
    session_record = get_session_record(request, db)
    if session_record is not None:
        csrf_token_value = new_token()
        session_record.csrf_token_hash = token_digest(csrf_token_value)
        db.commit()
        settings = get_settings()
        _set_cookie(
            response,
            CSRF_COOKIE,
            csrf_token_value,
            http_only=False,
            max_age=settings.session_ttl_hours * 60 * 60,
        )
        return CSRFResponse(csrf_token=csrf_token_value)
    return CSRFResponse(csrf_token=_rotate_anonymous_csrf(response))


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    _csrf: None = Depends(require_public_csrf),
    db: Session = Depends(get_db),
) -> AuthResponse:
    _check_rate_limit(request, "register")
    email = str(payload.email).strip().lower()
    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from exc
    db.refresh(user)
    csrf = _new_session(db, user, request, response)
    return AuthResponse(user=UserRead.model_validate(user), csrf_token=csrf)


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    _csrf: None = Depends(require_public_csrf),
    db: Session = Depends(get_db),
) -> AuthResponse:
    email = str(payload.email).strip().lower()
    _check_rate_limit(request, "login", email)
    user = db.query(User).filter(User.email == email).one_or_none()
    if user is None:
        verify_unknown_password(payload.password)
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not verify_password(user.password_hash, payload.password) or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    csrf = _new_session(db, user, request, response)
    return AuthResponse(user=UserRead.model_validate(user), csrf_token=csrf)


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> None:
    session_record = get_session_record(request, db)
    if session_record is not None and session_record.user_id == user.id:
        db.delete(session_record)
        db.commit()
    response.delete_cookie(
        SESSION_COOKIE,
        path="/api",
        secure=get_settings().cookie_secure,
        httponly=True,
        samesite=get_settings().cookie_same_site,
    )
    response.delete_cookie(
        CSRF_COOKIE,
        path="/api",
        secure=get_settings().cookie_secure,
        httponly=False,
        samesite=get_settings().cookie_same_site,
    )
