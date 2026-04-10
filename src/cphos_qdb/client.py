"""客户端主类，组合所有 API mixin。"""

from __future__ import annotations

from .models import HealthResponse
from ._transport import AsyncTransport, SyncTransport
from .auth import AsyncAuthMixin, AuthMixin
from .papers import AsyncPapersMixin, PapersMixin
from .questions import AsyncQuestionsMixin, QuestionsMixin


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

    def __init__(self, base_url: str, *, timeout: float = 30.0) -> None:
        """Args:
            base_url: API 服务地址，如 `http://localhost:8080`。
            timeout: HTTP 请求超时时间（秒）。
        """
        self._t = SyncTransport(base_url, timeout=timeout)

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


class AsyncQBClient(AsyncAuthMixin, AsyncQuestionsMixin, AsyncPapersMixin):
    """异步题库客户端，面向 bot 账号。

    用法::

        async with AsyncQBClient("http://localhost:8080") as c:
            await c.login("bot", "pass")
            questions = await c.list_questions(category="T")
    """

    def __init__(self, base_url: str, *, timeout: float = 30.0) -> None:
        self._t = AsyncTransport(base_url, timeout=timeout)

    async def close(self) -> None:
        await self._t.close()

    async def __aenter__(self) -> AsyncQBClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def health(self) -> HealthResponse:
        """健康检查，无需认证。"""
        return HealthResponse.model_validate((await self._t.get("/health")).json())
