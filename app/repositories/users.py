from __future__ import annotations

from typing import Optional, Protocol

from sqlalchemy.orm import Session

from app.db.models import User


class UserRepository(Protocol):
    def get_by_username(self, username: str) -> Optional[User]: ...
    def exists_any(self) -> bool: ...
    def create(self, username: str, password_hash: str) -> User: ...


class SqlUserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_username(self, username: str) -> Optional[User]:
        return self._db.query(User).filter(User.username == username).first()

    def exists_any(self) -> bool:
        return self._db.query(User.id).first() is not None

    def create(self, username: str, password_hash: str) -> User:
        user = User(username=username, password_hash=password_hash)
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
