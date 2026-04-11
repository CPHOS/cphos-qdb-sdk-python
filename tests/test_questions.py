"""Tests for questions mixin methods."""

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
    QuestionCreateResult,
    QuestionDeleteResult,
    QuestionDetail,
    QuestionSummary,
    ReviewersResponse,
)
from cphos_qdb.questions import _build_create_fields, _build_question_params

from .conftest import (
    BASE_URL,
    paginated_response,
    question_detail_data,
    question_summary_data,
    reviewer_data,
)


# ── Helper function tests ────────────────────────────────────────────────

class TestBuildQuestionParams:
    def test_all_none_returns_empty(self):
        assert _build_question_params() == {}

    def test_filters_none_values(self):
        result = _build_question_params(category="T", tag=None, limit=10)
        assert result == {"category": "T", "limit": 10}

    def test_all_params(self):
        result = _build_question_params(
            paper_id="p1", category="E", tag="optics", reviewer="u1",
            assigned_reviewer_id="u2",
            score_min=10, score_max=30,
            difficulty_tag="human", difficulty_min=3, difficulty_max=8,
            q="keyword", created_after="2026-01-01", created_before="2026-12-31",
            updated_after="2026-06-01", updated_before="2026-06-30",
            limit=50, offset=100,
        )
        assert len(result) == 17
        assert result["paper_id"] == "p1"
        assert result["score_min"] == 10


class TestBuildCreateFields:
    def test_required_only(self):
        fields = _build_create_fields("desc")
        assert fields["description"] == "desc"
        assert "category" not in fields

    def test_with_optionals(self):
        fields = _build_create_fields(
            "desc",
            category="T", tags=["a", "b"],
        )
        assert fields["category"] == "T"
        assert json.loads(fields["tags"]) == ["a", "b"]


# ── Sync mixin tests ────────────────────────────────────────────────────

class TestQuestionsMixin:
    @respx.mock(base_url=BASE_URL)
    def test_list_questions(self, respx_mock):
        items = [question_summary_data("q-001"), question_summary_data("q-002")]
        respx_mock.get("/questions").mock(
            return_value=httpx.Response(200, json=paginated_response(items, total=2))
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = client.list_questions(category="T", limit=20)
        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 2
        assert result.items[0].question_id == "q-001"
        req = respx_mock.calls.last.request
        assert "category=T" in str(req.url)
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_get_question(self, respx_mock):
        respx_mock.get("/questions/q-001").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = client.get_question("q-001")
        assert isinstance(detail, QuestionDetail)
        assert detail.tex_object_id == "obj-abc"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_create_question_with_file_object(self, respx_mock):
        respx_mock.post("/questions").mock(
            return_value=httpx.Response(201, json={
                "question_id": "q-new",
                "file_name": "upload.zip",
                "imported_assets": 2,
                "status": "none",
            })
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        fake_zip = io.BytesIO(b"PK\x03\x04fake")
        result = client.create_question(
            fake_zip,
            description="new question",
            category="T",
            tags=["optics"],
        )
        assert isinstance(result, QuestionCreateResult)
        assert result.question_id == "q-new"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_update_question_description(self, respx_mock):
        respx_mock.patch("/questions/q-001/description").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = client.update_question_description("q-001", "updated")
        assert isinstance(detail, QuestionDetail)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)
        assert body == {"description": "updated"}
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_update_question_category(self, respx_mock):
        respx_mock.patch("/questions/q-001/category").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = client.update_question_category("q-001", "E")
        assert detail.question_id == "q-001"
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {"category": "E"}
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_update_question_tags(self, respx_mock):
        respx_mock.patch("/questions/q-001/tags").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = client.update_question_tags("q-001", ["thermo"])
        assert detail.question_id == "q-001"
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {"tags": ["thermo"]}
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_update_question_status(self, respx_mock):
        respx_mock.patch("/questions/q-001/status").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = client.update_question_status("q-001", "reviewed")
        assert detail.question_id == "q-001"
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {"status": "reviewed"}
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_update_question_author(self, respx_mock):
        respx_mock.patch("/questions/q-001/author").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = client.update_question_author("q-001", "张三")
        assert detail.question_id == "q-001"
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {"author": "张三"}
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_update_question_reviewer_names(self, respx_mock):
        respx_mock.patch("/questions/q-001/reviewer-names").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = client.update_question_reviewer_names("q-001", ["李四", "王五"])
        assert detail.question_id == "q-001"
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {"reviewers": ["李四", "王五"]}
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_create_question_difficulty(self, respx_mock):
        respx_mock.post("/questions/q-001/difficulties").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = client.create_question_difficulty("q-001", "human", 7, notes="较难")
        assert detail.question_id == "q-001"
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {"algorithm_tag": "human", "score": 7, "notes": "较难"}
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_update_question_difficulty(self, respx_mock):
        respx_mock.patch("/questions/q-001/difficulties/human").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = client.update_question_difficulty("q-001", "human", 8)
        assert detail.question_id == "q-001"
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {"score": 8}
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_delete_question_difficulty(self, respx_mock):
        respx_mock.delete("/questions/q-001/difficulties/human").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = client.delete_question_difficulty("q-001", "human")
        assert detail.question_id == "q-001"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_replace_question_file(self, respx_mock):
        respx_mock.put("/questions/q-001/file").mock(
            return_value=httpx.Response(200, json={
                "question_id": "q-001",
                "file_name": "upload.zip",
                "source_tex_path": "main.tex",
                "imported_assets": 1,
                "status": "none",
            })
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = client.replace_question_file("q-001", io.BytesIO(b"PK"))
        assert result.question_id == "q-001"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_delete_question(self, respx_mock):
        respx_mock.delete("/questions/q-001").mock(
            return_value=httpx.Response(200, json={"question_id": "q-001", "status": "deleted"})
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = client.delete_question("q-001")
        assert isinstance(result, QuestionDeleteResult)
        assert result.status == "deleted"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_get_question_tags(self, respx_mock):
        respx_mock.get("/questions/tags").mock(
            return_value=httpx.Response(200, json={"tags": ["optics", "thermo"]})
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        tags = client.get_question_tags()
        assert tags == ["optics", "thermo"]
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_get_difficulty_tags(self, respx_mock):
        respx_mock.get("/questions/difficulty-tags").mock(
            return_value=httpx.Response(200, json={"difficulty_tags": ["human", "ai"]})
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        tags = client.get_difficulty_tags()
        assert tags == ["human", "ai"]
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_download_question_bundle(self, respx_mock, tmp_path):
        respx_mock.post("/questions/bundles").mock(
            return_value=httpx.Response(200, content=b"ZIP_CONTENT_HERE")
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        dest = tmp_path / "bundle.zip"
        result = client.download_question_bundle(["q-001"], str(dest))
        assert result == dest
        assert dest.read_bytes() == b"ZIP_CONTENT_HERE"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_list_reviewers(self, respx_mock):
        respx_mock.get("/questions/q-001/reviewers").mock(
            return_value=httpx.Response(200, json={"reviewers": [reviewer_data()]})
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = client.list_reviewers("q-001")
        assert isinstance(result, ReviewersResponse)
        assert len(result.reviewers) == 1
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_assign_reviewer(self, respx_mock):
        respx_mock.post("/questions/q-001/reviewers").mock(
            return_value=httpx.Response(200, json={"reviewers": [reviewer_data()]})
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = client.assign_reviewer("q-001", "u-002")
        assert len(result.reviewers) == 1
        req = respx_mock.calls.last.request
        body = json.loads(req.content)
        assert body["reviewer_id"] == "u-002"
        client.close()

    @respx.mock(base_url=BASE_URL)
    def test_remove_reviewer(self, respx_mock):
        respx_mock.delete("/questions/q-001/reviewers/u-002").mock(
            return_value=httpx.Response(200, json={"reviewers": []})
        )
        client = QBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = client.remove_reviewer("q-001", "u-002")
        assert result.reviewers == []
        client.close()


# ── Async mixin tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
class TestAsyncQuestionsMixin:
    @respx.mock(base_url=BASE_URL)
    async def test_list_questions(self, respx_mock):
        items = [question_summary_data()]
        respx_mock.get("/questions").mock(
            return_value=httpx.Response(200, json=paginated_response(items))
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = await client.list_questions(category="T")
        assert len(result.items) == 1
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_get_question(self, respx_mock):
        respx_mock.get("/questions/q-001").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = await client.get_question("q-001")
        assert detail.question_id == "q-001"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_create_question(self, respx_mock):
        respx_mock.post("/questions").mock(
            return_value=httpx.Response(201, json={
                "question_id": "q-new",
                "file_name": "upload.zip",
                "imported_assets": 0,
                "status": "none",
            })
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = await client.create_question(
            io.BytesIO(b"PK"),
            description="async q",
        )
        assert result.question_id == "q-new"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_update_question_description(self, respx_mock):
        respx_mock.patch("/questions/q-001/description").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = await client.update_question_description("q-001", "updated")
        assert detail.question_id == "q-001"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_update_question_status(self, respx_mock):
        respx_mock.patch("/questions/q-001/status").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = await client.update_question_status("q-001", "reviewed")
        assert detail.question_id == "q-001"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_update_question_author(self, respx_mock):
        respx_mock.patch("/questions/q-001/author").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = await client.update_question_author("q-001", "张三")
        assert detail.question_id == "q-001"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_update_question_reviewer_names(self, respx_mock):
        respx_mock.patch("/questions/q-001/reviewer-names").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = await client.update_question_reviewer_names("q-001", ["李四", "王五"])
        assert detail.question_id == "q-001"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_create_question_difficulty(self, respx_mock):
        respx_mock.post("/questions/q-001/difficulties").mock(
            return_value=httpx.Response(200, json=question_detail_data())
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        detail = await client.create_question_difficulty("q-001", "human", 6)
        assert detail.question_id == "q-001"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_delete_question(self, respx_mock):
        respx_mock.delete("/questions/q-001").mock(
            return_value=httpx.Response(200, json={"question_id": "q-001", "status": "deleted"})
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = await client.delete_question("q-001")
        assert result.status == "deleted"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_get_tags(self, respx_mock):
        respx_mock.get("/questions/tags").mock(
            return_value=httpx.Response(200, json={"tags": ["t1"]})
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        tags = await client.get_question_tags()
        assert tags == ["t1"]
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_download_bundle(self, respx_mock, tmp_path):
        respx_mock.post("/questions/bundles").mock(
            return_value=httpx.Response(200, content=b"ZIPDATA")
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        dest = tmp_path / "out.zip"
        result = await client.download_question_bundle(["q-001"], str(dest))
        assert dest.read_bytes() == b"ZIPDATA"
        await client.close()

    @respx.mock(base_url=BASE_URL)
    async def test_assign_reviewer(self, respx_mock):
        respx_mock.post("/questions/q-001/reviewers").mock(
            return_value=httpx.Response(200, json={"reviewers": [reviewer_data()]})
        )
        client = AsyncQBClient(BASE_URL, check_version=False)
        client._t.set_tokens("acc", "ref")
        result = await client.assign_reviewer("q-001", "u-002")
        assert len(result.reviewers) == 1
        await client.close()
