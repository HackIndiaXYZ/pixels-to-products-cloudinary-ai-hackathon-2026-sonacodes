"""Reusable authentication and CSRF dependencies for protected APIs."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth_security import constant_time_equal, token_digest
from app.database import get_db
from app.models import AuthSession, User

SESSION_COOKIE = "wardrobeai_session"
CSRF_COOKIE = "wardrobeai_csrf"
CSRF_HEADER = "X-CSRF-Token"


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail="Authentication required.")


def get_session_record(request: Request, db: Session) -> AuthSession | None:
    raw_token = request.cookies.get(SESSION_COOKIE)
    if not raw_token:
        return None
    return db.get(AuthSession, token_digest(raw_token))


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    session_record = get_session_record(request, db)
    if session_record is None:
        raise _unauthorized()
    expires_at = session_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        db.delete(session_record)
        db.commit()
        raise _unauthorized()
    user = db.get(User, session_record.user_id)
    if user is None or not user.is_active:
        raise _unauthorized()
    return user


def require_csrf(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    csrf_cookie = request.cookies.get(CSRF_COOKIE, "")
    csrf_header = request.headers.get(CSRF_HEADER, "")
    raw_session = request.cookies.get(SESSION_COOKIE, "")
    if not csrf_cookie or not csrf_header or not constant_time_equal(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="CSRF validation failed.")
    session_record = db.get(AuthSession, token_digest(raw_session)) if raw_session else None
    if (
        session_record is None
        or session_record.user_id != user.id
        or not constant_time_equal(session_record.csrf_token_hash, token_digest(csrf_header))
    ):
        raise HTTPException(status_code=403, detail="CSRF validation failed.")


def require_public_csrf(request: Request) -> None:
    csrf_cookie = request.cookies.get(CSRF_COOKIE, "")
    csrf_header = request.headers.get(CSRF_HEADER, "")
    if not csrf_cookie or not csrf_header or not constant_time_equal(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="CSRF validation failed.")
