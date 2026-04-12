"""HTTP 传输层，支持自动令牌刷新（同步 + 异步）。"""

from __future__ import annotations

import json
from typing import Any

import httpx

from .exceptions import (
    QBAuthError,
    QBConflictError,
    QBError,
    QBForbiddenError,
    QBNotFoundError,
    QBServerError,
    QBValidationError,
    QBVersionError,
)
from .models import VersionResponse

SDK_VERSION = "0.2.2"
EXPECTED_BACKEND_VERSION = "0.2.0"

_STATUS_MAP: dict[int, type[QBError]] = {
    400: QBValidationError,
    401: QBAuthError,
    403: QBForbiddenError,
    404: QBNotFoundError,
    409: QBConflictError,
}


def _raise_for_status(resp: httpx.Response) -> None:
    if resp.is_success:
        return
    try:
        body = resp.json()
        msg = body.get("error", resp.text)
    except Exception:
        msg = resp.text
    exc_cls = _STATUS_MAP.get(resp.status_code, QBServerError)
    raise exc_cls(msg, status_code=resp.status_code)


def _parse_version(version: str) -> tuple[int, int, int]:
    parts = version.split(".")
    if len(parts) != 3:
        raise QBVersionError(f"无法解析后端版本号: {version}")
    try:
        major, minor, patch = (int(part) for part in parts)
    except ValueError as exc:
        raise QBVersionError(f"无法解析后端版本号: {version}") from exc
    return major, minor, patch


def _is_compatible_version(expected: str, actual: str) -> bool:
    expected_major, expected_minor, expected_patch = _parse_version(expected)
    actual_major, actual_minor, actual_patch = _parse_version(actual)
    if expected_major != actual_major:
        return False
    return (actual_minor, actual_patch) >= (expected_minor, expected_patch)


# ── Sync Transport ────────────────────────────────────────────────────────

class SyncTransport:
    """同步 HTTP 传输层，支持自动令牌刷新。"""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        sdk_version: str = SDK_VERSION,
        expected_backend_version: str = EXPECTED_BACKEND_VERSION,
        check_version: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)
        self._sdk_version = sdk_version
        self._expected_backend_version = expected_backend_version
        self._check_version = check_version
        self._version_checked = False

    def close(self) -> None:
        self._client.close()

    # ── token helpers ─────────────────────────────────────────────────────

    def set_tokens(self, access: str, refresh: str) -> None:
        self._access_token = access
        self._refresh_token = refresh

    def clear_tokens(self) -> None:
        self._access_token = None
        self._refresh_token = None

    @property
    def _auth_headers(self) -> dict[str, str]:
        if self._access_token:
            return {"Authorization": f"Bearer {self._access_token}"}
        return {}

    def _do_refresh(self) -> bool:
        if not self._refresh_token:
            return False
        resp = self._client.post(
            "/auth/refresh",
            json={"refresh_token": self._refresh_token},
        )
        if not resp.is_success:
            return False
        data = resp.json()
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        return True

    def get_version(self) -> VersionResponse:
        resp = self._client.get("/version")
        _raise_for_status(resp)
        return VersionResponse.model_validate(resp.json())

    def ensure_version_compatible(self) -> VersionResponse:
        version = self.get_version()
        if not _is_compatible_version(self._expected_backend_version, version.version):
            raise QBVersionError(
                (
                    "后端版本不兼容: "
                    f"SDK {self._sdk_version} 期望兼容后端 {self._expected_backend_version}，"
                    f"实际检测到 {version.version}"
                )
            )
        self._version_checked = True
        return version

    # ── core request ──────────────────────────────────────────────────────

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: Any = None,
        stream: bool = False,
    ) -> httpx.Response:
        if self._check_version and not self._version_checked and path != "/version":
            self.ensure_version_compatible()

        kwargs: dict[str, Any] = {"headers": self._auth_headers}
        if json_body is not None:
            kwargs["json"] = json_body
        if params:
            kwargs["params"] = {k: v for k, v in params.items() if v is not None}
        if data is not None:
            kwargs["data"] = data
        if files is not None:
            kwargs["files"] = files

        if stream:
            resp = self._client.stream(method, path, **kwargs).__enter__()
            if resp.status_code == 401 and self._do_refresh():
                resp.close()
                kwargs["headers"] = self._auth_headers
                resp = self._client.stream(method, path, **kwargs).__enter__()
            _raise_for_status(resp)
            return resp

        resp = self._client.request(method, path, **kwargs)
        if resp.status_code == 401 and self._do_refresh():
            kwargs["headers"] = self._auth_headers
            resp = self._client.request(method, path, **kwargs)
        _raise_for_status(resp)
        return resp

    # ── convenience shortcuts ─────────────────────────────────────────────

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        return self.request("GET", path, params=params)

    def post(self, path: str, *, json_body: Any = None, **kw: Any) -> httpx.Response:
        return self.request("POST", path, json_body=json_body, **kw)

    def patch(self, path: str, *, json_body: Any = None) -> httpx.Response:
        return self.request("PATCH", path, json_body=json_body)

    def put(self, path: str, **kw: Any) -> httpx.Response:
        return self.request("PUT", path, **kw)

    def delete(self, path: str) -> httpx.Response:
        return self.request("DELETE", path)


# ── Async Transport ───────────────────────────────────────────────────────

class AsyncTransport:
    """异步 HTTP 传输层，支持自动令牌刷新。"""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        sdk_version: str = SDK_VERSION,
        expected_backend_version: str = EXPECTED_BACKEND_VERSION,
        check_version: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)
        self._sdk_version = sdk_version
        self._expected_backend_version = expected_backend_version
        self._check_version = check_version
        self._version_checked = False

    async def close(self) -> None:
        await self._client.aclose()

    # ── token helpers ─────────────────────────────────────────────────────

    def set_tokens(self, access: str, refresh: str) -> None:
        self._access_token = access
        self._refresh_token = refresh

    def clear_tokens(self) -> None:
        self._access_token = None
        self._refresh_token = None

    @property
    def _auth_headers(self) -> dict[str, str]:
        if self._access_token:
            return {"Authorization": f"Bearer {self._access_token}"}
        return {}

    async def _do_refresh(self) -> bool:
        if not self._refresh_token:
            return False
        resp = await self._client.post(
            "/auth/refresh",
            json={"refresh_token": self._refresh_token},
        )
        if not resp.is_success:
            return False
        data = resp.json()
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        return True

    async def get_version(self) -> VersionResponse:
        resp = await self._client.get("/version")
        _raise_for_status(resp)
        return VersionResponse.model_validate(resp.json())

    async def ensure_version_compatible(self) -> VersionResponse:
        version = await self.get_version()
        if not _is_compatible_version(self._expected_backend_version, version.version):
            raise QBVersionError(
                (
                    "后端版本不兼容: "
                    f"SDK {self._sdk_version} 期望兼容后端 {self._expected_backend_version}，"
                    f"实际检测到 {version.version}"
                )
            )
        self._version_checked = True
        return version

    # ── core request ──────────────────────────────────────────────────────

    async def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: Any = None,
        stream: bool = False,
    ) -> httpx.Response:
        if self._check_version and not self._version_checked and path != "/version":
            await self.ensure_version_compatible()

        kwargs: dict[str, Any] = {"headers": self._auth_headers}
        if json_body is not None:
            kwargs["json"] = json_body
        if params:
            kwargs["params"] = {k: v for k, v in params.items() if v is not None}
        if data is not None:
            kwargs["data"] = data
        if files is not None:
            kwargs["files"] = files

        if stream:
            resp = await self._client.stream(method, path, **kwargs).__aenter__()
            if resp.status_code == 401 and await self._do_refresh():
                await resp.aclose()
                kwargs["headers"] = self._auth_headers
                resp = await self._client.stream(method, path, **kwargs).__aenter__()
            _raise_for_status(resp)
            return resp

        resp = await self._client.request(method, path, **kwargs)
        if resp.status_code == 401 and await self._do_refresh():
            kwargs["headers"] = self._auth_headers
            resp = await self._client.request(method, path, **kwargs)
        _raise_for_status(resp)
        return resp

    # ── convenience shortcuts ─────────────────────────────────────────────

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, *, json_body: Any = None, **kw: Any) -> httpx.Response:
        return await self.request("POST", path, json_body=json_body, **kw)

    async def patch(self, path: str, *, json_body: Any = None) -> httpx.Response:
        return await self.request("PATCH", path, json_body=json_body)

    async def put(self, path: str, **kw: Any) -> httpx.Response:
        return await self.request("PUT", path, **kw)

    async def delete(self, path: str) -> httpx.Response:
        return await self.request("DELETE", path)
