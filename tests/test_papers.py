"""Tests for papers mixin methods."""

from __future__ import annotations

import io
import json
from pathlib import Path

import httpx
import pytest
import respx

from cphos_qdb import AsyncQBClient, QBClient
from cphos_qdb.models import (
    PaginatedResponse,
    PaperCreateResult,
    PaperDeleteResult,
    PaperDetail,
    PaperFileReplaceResult,
    PaperSummary,
)
from cphos_qdb.papers import _build_paper_params

from .conftest import (
    BASE_URL,
    paginated_response,
    paper_detail_data,
    paper_summary_data,
)


# ── Helper tests ─────────────────────────────────────────────────────────

class TestBuildPaperParams:
    def test_all_none_returns_empty(self):
        assert _build_paper_params() == {}

    def test_filters_none(self):
        result = _build_paper_params(category="T", q="test", limit=10, offset=None)
        assert result == {"category": "T", "q": "test", "limit": 10}

    def test_all_params(self):
        result = _build_paper_params(
            question_id="q1", category="E", tag="optics", q="keyword",
            created_after="2026-01-01", created_before="2026-12-31",
            updated_after="2026-06-01", updated_before="2026-06-30",
            limit=20, offset=40,
        )
        assert len(result) == 10


# ── Sync mixin tests ────────────────────────────────────────────────────

class TestPapersMixin:
    @respx.mock(base_url=BASE_URL)
    def test_list_papers(self, respx_mock):
        items = [paper_summary_data("p-001"), paper_summary_data("p-002")]
        respx_mock.get("/papers").mock(
            return_value=httpx.Response(200, json=paginated_response(items, total=2))
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = client.list_papers(category="T", limit=20)
        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 2
        assert result.items[0].paper_id == "p-001"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_get_paper(self, respx_mock):
        respx_mock.get("/papers/p-001").mock(
            return_value=httpx.Response(200, json=paper_detail_data())
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = client.get_paper("p-001")
        assert isinstance(detail, PaperDetail)
        assert detail.title == "综合训练 2026"
        assert len(detail.questions) == 1
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_create_paper_without_file(self, respx_mock):
        respx_mock.post("/papers").mock(
            return_value=httpx.Response(201, json={
                "paper_id": "p-new",
                "file_name": None,
                "status": "created",
                "question_count": 2,
            })
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = client.create_paper(
            description="test paper",
            title="Title",
            subtitle="Sub",
            question_ids=["q-001", "q-002"],
        )
        assert isinstance(result, PaperCreateResult)
        assert result.paper_id == "p-new"
        assert result.question_count == 2
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_create_paper_with_file_object(self, respx_mock):
        respx_mock.post("/papers").mock(
            return_value=httpx.Response(201, json={
                "paper_id": "p-new",
                "file_name": "appendix.zip",
                "status": "created",
                "question_count": 1,
            })
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        fake_zip = io.BytesIO(b"PK\x03\x04fake")
        result = client.create_paper(
            description="with file",
            title="T",
            subtitle="S",
            question_ids=["q-001"],
            file=fake_zip,
        )
        assert result.file_name == "appendix.zip"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_update_paper(self, respx_mock):
        respx_mock.patch("/papers/p-001").mock(
            return_value=httpx.Response(200, json=paper_detail_data())
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = client.update_paper("p-001", title="New Title")
        assert isinstance(detail, PaperDetail)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)
        assert body == {"title": "New Title"}
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_update_paper_question_ids(self, respx_mock):
        respx_mock.patch("/papers/p-001").mock(
            return_value=httpx.Response(200, json=paper_detail_data())
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        client.update_paper("p-001", question_ids=["q-001", "q-002"])
        req = respx_mock.calls.last.request
        body = json.loads(req.content)
        assert body["question_ids"] == ["q-001", "q-002"]
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_replace_paper_file(self, respx_mock):
        respx_mock.put("/papers/p-001/file").mock(
            return_value=httpx.Response(200, json={
                "paper_id": "p-001",
                "file_name": "appendix.zip",
                "status": "replaced",
            })
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = client.replace_paper_file("p-001", io.BytesIO(b"PK"))
        assert isinstance(result, PaperFileReplaceResult)
        assert result.status == "replaced"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_delete_paper(self, respx_mock):
        respx_mock.delete("/papers/p-001").mock(
            return_value=httpx.Response(200, json={"paper_id": "p-001", "status": "deleted"})
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = client.delete_paper("p-001")
        assert isinstance(result, PaperDeleteResult)
        assert result.status == "deleted"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_download_paper_bundle(self, respx_mock, tmp_path):
        respx_mock.post("/papers/bundles").mock(
            return_value=httpx.Response(200, content=b"PAPER_ZIP")
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        dest = tmp_path / "papers.zip"
        result = client.download_paper_bundle(["p-001"], str(dest))
        assert result == dest
        assert dest.read_bytes() == b"PAPER_ZIP"
        client.close()


# ── Async mixin tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
class TestAsyncPapersMixin:
    @respx.mock(base_url=BASE_URL)
    async def test_list_papers(self, respx_mock):
        items = [paper_summary_data()]
        respx_mock.get("/papers").mock(
            return_value=httpx.Response(200, json=paginated_response(items))
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = await client.list_papers(q="综合")
        assert len(result.items) == 1
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_get_paper(self, respx_mock):
        respx_mock.get("/papers/p-001").mock(
            return_value=httpx.Response(200, json=paper_detail_data())
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = await client.get_paper("p-001")
        assert detail.paper_id == "p-001"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_create_paper(self, respx_mock):
        respx_mock.post("/papers").mock(
            return_value=httpx.Response(201, json={
                "paper_id": "p-new",
                "file_name": None,
                "status": "created",
                "question_count": 1,
            })
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = await client.create_paper(
            description="async paper",
            title="T",
            subtitle="S",
            question_ids=["q-001"],
        )
        assert result.paper_id == "p-new"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_update_paper(self, respx_mock):
        respx_mock.patch("/papers/p-001").mock(
            return_value=httpx.Response(200, json=paper_detail_data())
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = await client.update_paper("p-001", subtitle="B 卷")
        assert detail.paper_id == "p-001"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_delete_paper(self, respx_mock):
        respx_mock.delete("/papers/p-001").mock(
            return_value=httpx.Response(200, json={"paper_id": "p-001", "status": "deleted"})
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = await client.delete_paper("p-001")
        assert result.status == "deleted"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_download_bundle(self, respx_mock, tmp_path):
        respx_mock.post("/papers/bundles").mock(
            return_value=httpx.Response(200, content=b"DATA")
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        dest = tmp_path / "out.zip"
        await client.download_paper_bundle(["p-001"], str(dest))
        assert dest.read_bytes() == b"DATA"
        await client.close()
