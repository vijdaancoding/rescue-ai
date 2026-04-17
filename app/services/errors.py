"""Domain errors. Routers map these to HTTP status codes."""
from __future__ import annotations


class DomainError(Exception):
    """Base class for predictable service failures."""


class NotFoundError(DomainError):
    """Requested entity does not exist."""


class ValidationError(DomainError):
    """Client input violated a business rule."""


class AuthError(DomainError):
    """Authentication failed."""
