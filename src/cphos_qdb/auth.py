"""认证 API mixin（同步 + 异步）。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import UserProfile

if TYPE_CHECKING:
    from ._transport import AsyncTransport, SyncTransport


class AuthMixin:
    """同步认证操作 mixin。"""

    _t: SyncTransport

    def me(self) -> UserProfile:
        """获取当前登录用户信息。"""
        return UserProfile.model_validate(self._t.get("/auth/me").json())

    def search_users(
        self,
        q: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict:
        """按关键词搜索用户（用于审阅人分配）。

        Args:
            q: 搜索关键词，匹配 username / display_name。
            limit: 每页数量 (1-100)。
            offset: 偏移量。
        """
        params: dict = {"q": q}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        return self._t.get("/users/search", params=params).json()


class AsyncAuthMixin:
    """异步认证操作 mixin，接口与 `AuthMixin` 相同。"""

    _t: AsyncTransport

    async def me(self) -> UserProfile:
        """获取当前登录用户信息。"""
        return UserProfile.model_validate((await self._t.get("/auth/me")).json())

    async def search_users(
        self,
        q: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict:
        """按关键词搜索用户。参见 [`AuthMixin.search_users`][cphos_qdb.auth.AuthMixin.search_users]。"""
        params: dict = {"q": q}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        return (await self._t.get("/users/search", params=params)).json()
