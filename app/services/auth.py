from __future__ import annotations

from app.core.security import create_access_token, get_password_hash, verify_password
from app.repositories.users import UserRepository
from app.schemas.auth import TokenResponse
from app.services.errors import AuthError


def authenticate(
    *, username: str, password: str, users: UserRepository
) -> TokenResponse:
    user = users.get_by_username(username)
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError("Incorrect username or password")
    token = create_access_token(data={"sub": user.username})
    return TokenResponse(access_token=token)


def ensure_default_dispatcher(
    *, users: UserRepository, username: str, default_password: str
) -> dict[str, str]:
    """One-shot bootstrap for the single dispatcher account."""
    if users.exists_any():
        return {"msg": "User already exists."}
    users.create(username=username, password_hash=get_password_hash(default_password))
    return {
        "msg": (
            f"Dispatcher user created. Username: {username} | "
            f"Password: {default_password}"
        )
    }
