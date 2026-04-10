"""Auth API mixin (sync + async)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import MessageResponse, TokenResponse, UserProfile

if TYPE_CHECKING:
    from ._transport import AsyncTransport, SyncTransport


class AuthMixin:
    """同步认证操作 mixin。"""

    _t: SyncTransport

    def login(self, username: str, password: str) -> TokenResponse:
        """登录并获取 token 对，自动保存到传输层。

        Args:
            username: 用户名。
            password: 密码。

        Returns:
            包含 access_token 和 refresh_token 的响应。

        Raises:
            QBAuthError: 用户名或密码错误。
        """
        resp = self._t.request(
            "POST", "/auth/login",
            json_body={"username": username, "password": password},
        )
        tok = TokenResponse.model_validate(resp.json())
        self._t.set_tokens(tok.access_token, tok.refresh_token)
        return tok

    def logout(self) -> MessageResponse:
        """登出并撤销当前 refresh token。"""
        resp = self._t.post(
            "/auth/logout",
            json_body={"refresh_token": self._t._refresh_token or ""},
        )
        result = MessageResponse.model_validate(resp.json())
        self._t.clear_tokens()
        return result

    def me(self) -> UserProfile:
        """获取当前登录用户信息。"""
        return UserProfile.model_validate(self._t.get("/auth/me").json())

    def change_password(self, old_password: str, new_password: str) -> MessageResponse:
        """修改当前用户密码。

        Args:
            old_password: 当前密码。
            new_password: 新密码，长度 ≥ 6。
        """
        resp = self._t.patch(
            "/auth/me/password",
            json_body={"old_password": old_password, "new_password": new_password},
        )
        return MessageResponse.model_validate(resp.json())

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

    async def login(self, username: str, password: str) -> TokenResponse:
        """登录并获取 token 对。参见 [`AuthMixin.login`][cphos_qdb.auth.AuthMixin.login]。"""
        resp = await self._t.request(
            "POST", "/auth/login",
            json_body={"username": username, "password": password},
        )
        tok = TokenResponse.model_validate(resp.json())
        self._t.set_tokens(tok.access_token, tok.refresh_token)
        return tok

    async def logout(self) -> MessageResponse:
        resp = await self._t.post(
            "/auth/logout",
            json_body={"refresh_token": self._t._refresh_token or ""},
        )
        result = MessageResponse.model_validate(resp.json())
        self._t.clear_tokens()
        return result

    async def me(self) -> UserProfile:
        return UserProfile.model_validate((await self._t.get("/auth/me")).json())

    async def change_password(self, old_password: str, new_password: str) -> MessageResponse:
        resp = await self._t.patch(
            "/auth/me/password",
            json_body={"old_password": old_password, "new_password": new_password},
        )
        return MessageResponse.model_validate(resp.json())

    async def search_users(
        self,
        q: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict:
        params: dict = {"q": q}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        return (await self._t.get("/users/search", params=params)).json()
