"""Tests for QBClient and AsyncQBClient top-level behavior."""

from __future__ import annotations

import httpx
import pytest
import respx

from cphos_qdb import AsyncQBClient, QBClient
from cphos_qdb.exceptions import QBVersionError
from cphos_qdb.models import HealthResponse

from .conftest import BASE_URL, version_data


class TestQBClient:
    @respx.mock(base_url=BASE_URL)
    def test_context_manager(self, respx_mock):
        respx_mock.get("/version").mock(
            return_value=httpx.Response(200, json=version_data())
        )
        respx_mock.get("/health").mock(
            return_value=httpx.Response(200, json={"status": "ok", "service": "qb"})
        )
        with QBClient(BASE_URL) as client:
            health = client.health()
            assert health.status == "ok"

    def test_trailing_slash_stripped(self):
        client = QBClient("http://localhost:8080/", check_version=False)
        assert client._t.base_url == "http://localhost:8080"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_health_no_auth_needed(self, respx_mock):
        respx_mock.get("/health").mock(
            return_value=httpx.Response(200, json={"status": "ok", "service": "qb"})
        )
        client = QBClient(BASE_URL, check_version=False)
        health = client.health()
        assert isinstance(health, HealthResponse)
        assert health.service == "qb"
        client.close()

    def test_custom_timeout(self):
        client = QBClient(BASE_URL, timeout=60.0, check_version=False)
        assert client._t._client.timeout.connect == 60.0
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_version(self, respx_mock):
        respx_mock.get("/version").mock(
            return_value=httpx.Response(200, json=version_data("0.1.2"))
        )
        client = QBClient(BASE_URL, check_version=False)
        version = client.version()
        assert version.version == "0.1.2"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_version_check_fails_on_major_mismatch(self, respx_mock):
        respx_mock.get("/version").mock(
            return_value=httpx.Response(200, json=version_data("1.0.0"))
        )
        client = QBClient(BASE_URL)
        with pytest.raises(QBVersionError):
            client.health()
        client.close()


@pytest.mark.asyncio
class TestAsyncQBClient:
    @respx.mock(base_url=BASE_URL)
    async def test_async_context_manager(self, respx_mock):
        respx_mock.get("/version").mock(
            return_value=httpx.Response(200, json=version_data())
        )
        respx_mock.get("/health").mock(
            return_value=httpx.Response(200, json={"status": "ok", "service": "qb"})
        )
        async with AsyncQBClient(BASE_URL) as client:
            health = await client.health()
            assert health.status == "ok"

    @respx.mock(base_url=BASE_URL)
    async def test_health(self, respx_mock):
        respx_mock.get("/health").mock(
            return_value=httpx.Response(200, json={"status": "ok", "service": "qb"})
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        health = await client.health()
        assert isinstance(health, HealthResponse)
        await client.close()

    async def test_trailing_slash_stripped(self):
        client = AsyncQBClient("http://localhost:8080/", check_version=False)
        assert client._t.base_url == "http://localhost:8080"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_async_version(self, respx_mock):
        respx_mock.get("/version").mock(
            return_value=httpx.Response(200, json=version_data("0.1.3"))
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        version = await client.version()
        assert version.version == "0.1.3"
        await client.close()
