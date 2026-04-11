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

    用法::

        client = QBClient("http://localhost:8080")
        client.login("bot_user", "bot_password")
        questions = client.list_questions(category="T")
        client.close()

    或作为上下文管理器::

        with QBClient("http://localhost:8080") as c:
            c.login("bot", "pass")
            ...
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        check_version: bool = True,
    ) -> None:
        """Args:
            base_url: API 服务地址，如 `http://localhost:8080`。
            timeout: HTTP 请求超时时间（秒）。
            check_version: 是否在首次连接时校验后端版本兼容性。
        """
        self._t = SyncTransport(base_url, timeout=timeout, check_version=check_version)

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

        async with AsyncQBClient("http://localhost:8080") as c:
            await c.login("bot", "pass")
            questions = await c.list_questions(category="T")
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        check_version: bool = True,
    ) -> None:
        self._t = AsyncTransport(base_url, timeout=timeout, check_version=check_version)

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
