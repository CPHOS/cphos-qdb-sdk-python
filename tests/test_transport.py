"""Tests for SyncTransport and AsyncTransport."""

from __future__ import annotations

import httpx
import pytest
import respx

from cphos_qdb._transport import AsyncTransport, SyncTransport
from cphos_qdb.exceptions import QBAuthError, QBNotFoundError, QBVersionError

BASE_URL = "http://test-api.local"


class TestSyncTransport:
    def test_auth_headers_empty_without_token(self):
        t = SyncTransport(BASE_URL, check_version=False)
        assert t._auth_headers == {}
        t.close()

    def test_auth_headers_after_set_tokens(self):
        t = SyncTransport(BASE_URL, check_version=False)
        t.set_tokens("acc123", "ref456")
        assert t._auth_headers == {"Authorization": "Bearer acc123"}
        t.close()

    def test_clear_tokens(self):
        t = SyncTransport(BASE_URL, check_version=False)
        t.set_tokens("acc", "ref")
        t.clear_tokens()
        assert t._access_token is None
        assert t._refresh_token is None
        t.close()

    @respx.mock(base_url=BASE_URL)
    def test_get_success(self, respx_mock):
        respx_mock.get("/health").mock(return_value=httpx.Response(200, json={"status": "ok"}))
        t = SyncTransport(BASE_URL, check_version=False)
        resp = t.get("/health")
        assert resp.json() == {"status": "ok"}
        t.close()

    @respx.mock(base_url=BASE_URL)
    def test_raises_on_404(self, respx_mock):
        respx_mock.get("/missing").mock(return_value=httpx.Response(404, json={"error": "not found"}))
        t = SyncTransport(BASE_URL, check_version=False)
        with pytest.raises(QBNotFoundError):
            t.get("/missing")
        t.close()

    @respx.mock(base_url=BASE_URL)
    def test_auto_token_refresh_on_401(self, respx_mock):
        # First request returns 401
        respx_mock.get("/data").mock(
            side_effect=[
                httpx.Response(401, json={"error": "expired"}),
                httpx.Response(200, json={"result": "ok"}),
            ]
        )
        # Refresh succeeds
        respx_mock.post("/auth/refresh").mock(
            return_value=httpx.Response(200, json={
                "access_token": "new_acc",
                "refresh_token": "new_ref",
            })
        )
        t = SyncTransport(BASE_URL, check_version=False)
        t.set_tokens("old_acc", "old_ref")
        resp = t.get("/data")
        assert resp.json() == {"result": "ok"}
        assert t._access_token == "new_acc"
        assert t._refresh_token == "new_ref"
        t.close()

    @respx.mock(base_url=BASE_URL)
    def test_401_without_refresh_token_raises(self, respx_mock):
        respx_mock.get("/data").mock(return_value=httpx.Response(401, json={"error": "no auth"}))
        t = SyncTransport(BASE_URL, check_version=False)
        with pytest.raises(QBAuthError):
            t.get("/data")
        t.close()

    @respx.mock(base_url=BASE_URL)
    def test_post_with_json_body(self, respx_mock):
        respx_mock.post("/items").mock(return_value=httpx.Response(201, json={"id": "1"}))
        t = SyncTransport(BASE_URL, check_version=False)
        resp = t.post("/items", json_body={"name": "test"})
        assert resp.json() == {"id": "1"}
        t.close()

    @respx.mock(base_url=BASE_URL)
    def test_params_filter_none(self, respx_mock):
        respx_mock.get("/items").mock(return_value=httpx.Response(200, json=[]))
        t = SyncTransport(BASE_URL, check_version=False)
        t.request("GET", "/items", params={"a": "1", "b": None})
        req = respx_mock.calls.last.request
        assert "a=1" in str(req.url)
        assert "b" not in str(req.url)
        t.close()

    @respx.mock(base_url=BASE_URL)
    def test_version_check_before_first_request(self, respx_mock):
        respx_mock.get("/version").mock(return_value=httpx.Response(200, json={"version": "0.1.1"}))
        respx_mock.get("/health").mock(return_value=httpx.Response(200, json={"status": "ok"}))
        t = SyncTransport(BASE_URL)
        resp = t.get("/health")
        assert resp.json() == {"status": "ok"}
        assert t._version_checked is True
        t.close()

    @respx.mock(base_url=BASE_URL)
    def test_version_check_rejects_incompatible_backend(self, respx_mock):
        respx_mock.get("/version").mock(return_value=httpx.Response(200, json={"version": "1.0.0"}))
        t = SyncTransport(BASE_URL)
        with pytest.raises(QBVersionError):
            t.get("/health")
        t.close()


@pytest.mark.asyncio
class TestAsyncTransport:
    async def test_auth_headers(self):
        t = AsyncTransport(BASE_URL, check_version=False)
        assert t._auth_headers == {}
        t.set_tokens("acc", "ref")
        assert t._auth_headers == {"Authorization": "Bearer acc"}
        await t.close()

    @respx.mock(base_url=BASE_URL)
    async def test_get_success(self, respx_mock):
        respx_mock.get("/health").mock(return_value=httpx.Response(200, json={"status": "ok"}))
        t = AsyncTransport(BASE_URL, check_version=False)
        resp = await t.get("/health")
        assert resp.json() == {"status": "ok"}
        await t.close()

    @respx.mock(base_url=BASE_URL)
    async def test_auto_refresh_on_401(self, respx_mock):
        respx_mock.get("/data").mock(
            side_effect=[
                httpx.Response(401, json={"error": "expired"}),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        respx_mock.post("/auth/refresh").mock(
            return_value=httpx.Response(200, json={
                "access_token": "new_acc",
                "refresh_token": "new_ref",
            })
        )
        t = AsyncTransport(BASE_URL, check_version=False)
        t.set_tokens("old", "old_ref")
        resp = await t.get("/data")
        assert resp.json() == {"ok": True}
        assert t._access_token == "new_acc"
        await t.close()

    @respx.mock(base_url=BASE_URL)
    async def test_raises_on_error(self, respx_mock):
        respx_mock.get("/x").mock(return_value=httpx.Response(404, json={"error": "nope"}))
        t = AsyncTransport(BASE_URL, check_version=False)
        with pytest.raises(QBNotFoundError):
            await t.get("/x")
        await t.close()

    @respx.mock(base_url=BASE_URL)
    async def test_async_version_check_before_first_request(self, respx_mock):
        respx_mock.get("/version").mock(return_value=httpx.Response(200, json={"version": "0.1.1"}))
        respx_mock.get("/health").mock(return_value=httpx.Response(200, json={"status": "ok"}))
        t = AsyncTransport(BASE_URL)
        resp = await t.get("/health")
        assert resp.json() == {"status": "ok"}
        assert t._version_checked is True
        await t.close()
