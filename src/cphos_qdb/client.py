"""客户端主类，组合所有 API mixin。"""

from __future__ import annotations

from .models import HealthResponse, VersionResponse
from ._transport import (
    EXPECTED_BACKEND_VERSION,
    SDK_VERSION,
    AsyncTransport,
    SyncTransport,
)
from .auth import AsyncAuthMixin, AuthMixin
from .papers import AsyncPapersMixin, PapersMixin
from .questions import AsyncQuestionsMixin, QuestionsMixin

__version__ = SDK_VERSION
EXPECTED_API_VERSION = EXPECTED_BACKEND_VERSION


class QBClient(AuthMixin, QuestionsMixin, PapersMixin):
    """同步题库客户端，面向 bot 账号。

    Bot 账号使用管理员签发的 access token 认证，无需用户名密码登录。

    用法::

        client = QBClient("http://localhost:8080", access_token="bot-token-xxx")
        questions = client.list_questions(category="T")
        client.close()

    或作为上下文管理器::

        with QBClient("http://localhost:8080", access_token="bot-token-xxx") as c:
            ...
    """

    def __init__(
        self,
        base_url: str,
        *,
        access_token: str | None = None,
        timeout: float = 30.0,
        check_version: bool = True,
    ) -> None:
        """Args:
            base_url: API 服务地址，如 `http://localhost:8080`。
            access_token: 管理员签发的 bot access token。
            timeout: HTTP 请求超时时间（秒）。
            check_version: 是否在首次连接时校验后端版本兼容性。
        """
        self._t = SyncTransport(
            base_url, access_token=access_token,
            timeout=timeout, check_version=check_version,
        )

    def close(self) -> None:
        """关闭 HTTP 连接。"""
        self._t.close()

    def __enter__(self) -> QBClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def health(self) -> HealthResponse:
        """健康检查，无需认证。"""
        return HealthResponse.model_validate(self._t.get("/health").json())

    def version(self) -> VersionResponse:
        """获取后端版本号。"""
        return self._t.get_version()


class AsyncQBClient(AsyncAuthMixin, AsyncQuestionsMixin, AsyncPapersMixin):
    """异步题库客户端，面向 bot 账号。

    用法::

        async with AsyncQBClient("http://localhost:8080", access_token="bot-token-xxx") as c:
            questions = await c.list_questions(category="T")
    """

    def __init__(
        self,
        base_url: str,
        *,
        access_token: str | None = None,
        timeout: float = 30.0,
        check_version: bool = True,
    ) -> None:
        self._t = AsyncTransport(
            base_url, access_token=access_token,
            timeout=timeout, check_version=check_version,
        )

    async def close(self) -> None:
        await self._t.close()

    async def __aenter__(self) -> AsyncQBClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def health(self) -> HealthResponse:
        """健康检查，无需认证。"""
        return HealthResponse.model_validate((await self._t.get("/health")).json())

    async def version(self) -> VersionResponse:
        """获取后端版本号。"""
        return await self._t.get_version()
