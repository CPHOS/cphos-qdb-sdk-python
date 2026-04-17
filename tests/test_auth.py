"""Tests for auth mixin methods."""

from __future__ import annotations

import httpx
import pytest
import respx

from cphos_qdb import AsyncQBClient, QBClient
from cphos_qdb.models import UserProfile

from .conftest import BASE_URL, user_profile_data


class TestAuthMixin:
    @respx.mock(base_url=BASE_URL)
    def test_me(self, respx_mock):
        respx_mock.get("/auth/me").mock(
            return_value=httpx.Response(200, json=user_profile_data())
        )
        client = QBClient(BASE_URL, access_token="bot-token", check_version=False)
        profile = client.me()
        assert isinstance(profile, UserProfile)
        assert profile.username == "bot_user"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_search_users(self, respx_mock):
        user_list = {"users": [{"user_id": "u-002", "username": "alice"}], "total": 1}
        respx_mock.get("/users/search").mock(
            return_value=httpx.Response(200, json=user_list)
        )
        client = QBClient(BASE_URL, access_token="bot-token", check_version=False)
        result = client.search_users("alice", limit=10, offset=0)
        assert result["total"] == 1
        req = respx_mock.calls.last.request
        assert "q=alice" in str(req.url)
        assert "limit=10" in str(req.url)
        client.close()

    def test_access_token_via_constructor(self):
        client = QBClient(BASE_URL, access_token="my-bot-token", check_version=False)
        assert client._t._access_token == "my-bot-token"
        client.close()


@pytest.mark.asyncio
class TestAsyncAuthMixin:
    @respx.mock(base_url=BASE_URL)
    async def test_me(self, respx_mock):
        respx_mock.get("/auth/me").mock(
            return_value=httpx.Response(200, json=user_profile_data())
        )
        client = AsyncQBClient(BASE_URL, access_token="bot-token", check_version=False)
        profile = await client.me()
        assert profile.role == "bot"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_search_users(self, respx_mock):
        respx_mock.get("/users/search").mock(
            return_value=httpx.Response(200, json={"users": [], "total": 0})
        )
        client = AsyncQBClient(BASE_URL, access_token="bot-token", check_version=False)
        result = await client.search_users("nobody")
        assert result["total"] == 0
        await client.close()

    async def test_access_token_via_constructor(self):
        client = AsyncQBClient(BASE_URL, access_token="my-bot-token", check_version=False)
        assert client._t._access_token == "my-bot-token"
        await client.close()
