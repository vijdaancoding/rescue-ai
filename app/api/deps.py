"""
FastAPI dependency wiring.

This is the composition root: concrete repositories are injected into
services here, keeping routers and services free of SQLAlchemy imports.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import User
from app.repositories.ai_metadata import AiMetadataRepository, SqlAiMetadataRepository
from app.repositories.analytics import AnalyticsRepository, SqlAnalyticsRepository
from app.repositories.calls import CallRepository, SqlCallRepository
from app.repositories.dispatches import DispatchRepository, SqlDispatchRepository
from app.repositories.geolocation import GeolocationRepository, SqlGeolocationRepository
from app.repositories.users import SqlUserRepository, UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Repository providers ──────────────────────────────────────────────────────

def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return SqlUserRepository(db)


def get_call_repo(db: Session = Depends(get_db)) -> CallRepository:
    return SqlCallRepository(db)


def get_ai_metadata_repo(db: Session = Depends(get_db)) -> AiMetadataRepository:
    return SqlAiMetadataRepository(db)


def get_dispatch_repo(db: Session = Depends(get_db)) -> DispatchRepository:
    return SqlDispatchRepository(db)


def get_geolocation_repo(db: Session = Depends(get_db)) -> GeolocationRepository:
    return SqlGeolocationRepository(db)


def get_analytics_repo(db: Session = Depends(get_db)) -> AnalyticsRepository:
    return SqlAnalyticsRepository(db)


# ── Auth ─────────────────────────────────────────────────────────────────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    users: UserRepository = Depends(get_user_repo),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise credentials_exception from None

    username = payload.get("sub")
    if not username:
        raise credentials_exception

    user = users.get_by_username(username)
    if user is None:
        raise credentials_exception
    return user
