"""Tests for auth mixin methods."""

from __future__ import annotations

import httpx
import pytest
import respx

from cphos_qdb import AsyncQBClient, QBClient
from cphos_qdb.exceptions import QBAuthError
from cphos_qdb.models import MessageResponse, TokenResponse, UserProfile

from .conftest import BASE_URL, token_data, user_profile_data


class TestAuthMixin:
    @respx.mock(base_url=BASE_URL)
    def test_login_success(self, respx_mock):
        respx_mock.post("/auth/login").mock(
            return_value=httpx.Response(200, json=token_data())
        )
        client = QBClient(BASE_URL)
        tok = client.login("bot", "pass")
        assert isinstance(tok, TokenResponse)
        assert tok.access_token == "acc_test_123"
        assert client._t._access_token == "acc_test_123"
        assert client._t._refresh_token == "ref_test_456"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_login_sends_credentials(self, respx_mock):
        respx_mock.post("/auth/login").mock(
            return_value=httpx.Response(200, json=token_data())
        )
        client = QBClient(BASE_URL)
        client.login("myuser", "mypass")
        req = respx_mock.calls.last.request
        import json
        body = json.loads(req.content)
        assert body == {"username": "myuser", "password": "mypass"}
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_login_wrong_password(self, respx_mock):
        respx_mock.post("/auth/login").mock(
            return_value=httpx.Response(401, json={"error": "invalid credentials"})
        )
        client = QBClient(BASE_URL)
        with pytest.raises(QBAuthError):
            client.login("bot", "wrong")
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_logout(self, respx_mock):
        respx_mock.post("/auth/logout").mock(
            return_value=httpx.Response(200, json={"message": "logged out"})
        )
        client = QBClient(BASE_URL)
        client._t.set_tokens("acc", "ref")
        result = client.logout()
        assert isinstance(result, MessageResponse)
        assert result.message == "logged out"
        assert client._t._access_token is None
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_me(self, respx_mock):
        respx_mock.get("/auth/me").mock(
            return_value=httpx.Response(200, json=user_profile_data())
        )
        client = QBClient(BASE_URL)
        client._t.set_tokens("acc", "ref")
        profile = client.me()
        assert isinstance(profile, UserProfile)
        assert profile.username == "bot_user"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_change_password(self, respx_mock):
        respx_mock.patch("/auth/me/password").mock(
            return_value=httpx.Response(200, json={"message": "password updated"})
        )
        client = QBClient(BASE_URL)
        client._t.set_tokens("acc", "ref")
        result = client.change_password("old", "newpass")
        assert result.message == "password updated"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_search_users(self, respx_mock):
        user_list = {"users": [{"user_id": "u-002", "username": "alice"}], "total": 1}
        respx_mock.get("/users/search").mock(
            return_value=httpx.Response(200, json=user_list)
        )
        client = QBClient(BASE_URL)
        client._t.set_tokens("acc", "ref")
        result = client.search_users("alice", limit=10, offset=0)
        assert result["total"] == 1
        req = respx_mock.calls.last.request
        assert "q=alice" in str(req.url)
        assert "limit=10" in str(req.url)
        client.close()


@pytest.mark.asyncio
class TestAsyncAuthMixin:
    @respx.mock(base_url=BASE_URL)
    async def test_login_success(self, respx_mock):
        respx_mock.post("/auth/login").mock(
            return_value=httpx.Response(200, json=token_data())
        )
        client = AsyncQBClient(BASE_URL)
        tok = await client.login("bot", "pass")
        assert isinstance(tok, TokenResponse)
        assert client._t._access_token == "acc_test_123"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_logout(self, respx_mock):
        respx_mock.post("/auth/logout").mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )
        client = AsyncQBClient(BASE_URL)
        client._t.set_tokens("acc", "ref")
        result = await client.logout()
        assert result.message == "ok"
        assert client._t._access_token is None
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_me(self, respx_mock):
        respx_mock.get("/auth/me").mock(
            return_value=httpx.Response(200, json=user_profile_data())
        )
        client = AsyncQBClient(BASE_URL)
        client._t.set_tokens("acc", "ref")
        profile = await client.me()
        assert profile.role == "bot"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_change_password(self, respx_mock):
        respx_mock.patch("/auth/me/password").mock(
            return_value=httpx.Response(200, json={"message": "updated"})
        )
        client = AsyncQBClient(BASE_URL)
        client._t.set_tokens("acc", "ref")
        result = await client.change_password("old", "new123")
        assert result.message == "updated"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_search_users(self, respx_mock):
        respx_mock.get("/users/search").mock(
            return_value=httpx.Response(200, json={"users": [], "total": 0})
        )
        client = AsyncQBClient(BASE_URL)
        client._t.set_tokens("acc", "ref")
        result = await client.search_users("nobody")
        assert result["total"] == 0
        await client.close()
