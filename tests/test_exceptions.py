"""Tests for exception classes and _raise_for_status."""

from __future__ import annotations

import httpx
import pytest

from cphos_qdb.exceptions import (
    QBAuthError,
    QBConflictError,
    QBError,
    QBForbiddenError,
    QBNotFoundError,
    QBServerError,
    QBValidationError,
    QBVersionError,
)
from cphos_qdb._transport import _raise_for_status


class TestExceptionHierarchy:
    def test_all_inherit_from_qb_error(self):
        for cls in (QBValidationError, QBAuthError, QBForbiddenError,
                    QBNotFoundError, QBConflictError, QBServerError, QBVersionError):
            exc = cls("test", status_code=400)
            assert isinstance(exc, QBError)
            assert isinstance(exc, Exception)

    def test_message_and_status_code(self):
        exc = QBError("something wrong", status_code=500)
        assert exc.message == "something wrong"
        assert exc.status_code == 500
        assert str(exc) == "something wrong"

    def test_status_code_defaults_none(self):
        exc = QBError("no code")
        assert exc.status_code is None


class TestRaiseForStatus:
    def _make_resp(self, status: int, body: dict | str = "") -> httpx.Response:
        if isinstance(body, dict):
            content = httpx.Response(status, json=body).content
            return httpx.Response(status, content=content, headers={"content-type": "application/json"})
        return httpx.Response(status, text=body)

    def test_success_no_raise(self):
        resp = self._make_resp(200, {"ok": True})
        _raise_for_status(resp)  # should not raise

    def test_204_no_raise(self):
        _raise_for_status(httpx.Response(204))

    @pytest.mark.parametrize("status,exc_cls", [
        (400, QBValidationError),
        (401, QBAuthError),
        (403, QBForbiddenError),
        (404, QBNotFoundError),
        (409, QBConflictError),
    ])
    def test_mapped_status_codes(self, status: int, exc_cls: type[QBError]):
        resp = self._make_resp(status, {"error": "fail"})
        with pytest.raises(exc_cls) as exc_info:
            _raise_for_status(resp)
        assert exc_info.value.status_code == status
        assert exc_info.value.message == "fail"

    def test_500_server_error(self):
        resp = self._make_resp(500, {"error": "internal"})
        with pytest.raises(QBServerError) as exc_info:
            _raise_for_status(resp)
        assert exc_info.value.status_code == 500

    def test_unknown_status_maps_to_server_error(self):
        resp = self._make_resp(502, "bad gateway")
        with pytest.raises(QBServerError) as exc_info:
            _raise_for_status(resp)
        assert exc_info.value.status_code == 502

    def test_non_json_body(self):
        resp = self._make_resp(400, "plain text error")
        with pytest.raises(QBValidationError) as exc_info:
            _raise_for_status(resp)
        assert "plain text error" in exc_info.value.message
