"""CPHOS Question Bank SDK exceptions."""

from __future__ import annotations


class QBError(Exception):
    """Base exception for all QB SDK errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class QBValidationError(QBError):
    """400 — request validation failed."""


class QBAuthError(QBError):
    """401 — authentication failed or token expired."""


class QBForbiddenError(QBError):
    """403 — insufficient permissions."""


class QBNotFoundError(QBError):
    """404 — resource not found or soft-deleted."""


class QBConflictError(QBError):
    """409 — operation conflict."""


class QBServerError(QBError):
    """500 / 503 — server-side error."""
