"""题库 SDK 异常类。"""

from __future__ import annotations


class QBError(Exception):
    """SDK 基础异常，所有异常均继承自此类。"""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class QBValidationError(QBError):
    """400 — 请求参数校验失败。"""


class QBAuthError(QBError):
    """401 — 认证失败或令牌过期。"""


class QBForbiddenError(QBError):
    """403 — 权限不足。"""


class QBNotFoundError(QBError):
    """404 — 资源不存在或已删除。"""


class QBConflictError(QBError):
    """409 — 操作冲突。"""


class QBVersionError(QBError):
    """SDK 与后端版本不兼容。"""


class QBServerError(QBError):
    """500 / 503 — 服务端错误。"""
