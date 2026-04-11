"""Tests for Pydantic models."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from cphos_qdb.models import (
    DifficultyValue,
    HealthResponse,
    MessageResponse,
    PaginatedResponse,
    PaperCreateResult,
    PaperDetail,
    PaperSummary,
    QuestionCreateResult,
    QuestionDetail,
    QuestionSummary,
    ReviewerInfo,
    ReviewersResponse,
    TokenResponse,
    UserProfile,
    VersionResponse,
)

from .conftest import (
    NOW,
    paper_detail_data,
    paper_summary_data,
    question_detail_data,
    question_summary_data,
    reviewer_data,
    token_data,
    user_profile_data,
    version_data,
)


class TestTokenResponse:
    def test_valid(self):
        t = TokenResponse.model_validate(token_data())
        assert t.access_token == "acc_test_123"
        assert t.token_type == "bearer"
        assert t.expires_in == 3600

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            TokenResponse.model_validate({"access_token": "x"})


class TestUserProfile:
    def test_valid(self):
        u = UserProfile.model_validate(user_profile_data())
        assert u.user_id == "u-001"
        assert u.role == "bot"
        assert u.is_active is True
        assert u.leader_expires_at is None
        assert isinstance(u.created_at, datetime)

    def test_with_leader_expires(self):
        d = user_profile_data()
        d["leader_expires_at"] = NOW
        u = UserProfile.model_validate(d)
        assert isinstance(u.leader_expires_at, datetime)


class TestDifficultyValue:
    def test_valid(self):
        dv = DifficultyValue.model_validate({"score": 5})
        assert dv.score == 5
        assert dv.notes is None

    def test_score_out_of_range(self):
        with pytest.raises(ValidationError):
            DifficultyValue.model_validate({"score": 0})
        with pytest.raises(ValidationError):
            DifficultyValue.model_validate({"score": 11})


class TestQuestionSummary:
    def test_valid(self):
        q = QuestionSummary.model_validate(question_summary_data())
        assert q.question_id == "q-001"
        assert q.category == "T"
        assert q.tags == ["thermodynamics"]

    def test_default_fields(self):
        d = question_summary_data()
        del d["author"]
        del d["reviewers"]
        del d["tags"]
        del d["difficulty"]
        q = QuestionSummary.model_validate(d)
        assert q.author == ""
        assert q.reviewers == []
        assert q.tags == []
        assert q.difficulty == {}


class TestQuestionDetail:
    def test_inherits_summary_fields(self):
        d = question_detail_data()
        detail = QuestionDetail.model_validate(d)
        assert detail.question_id == "q-001"
        assert detail.tex_object_id == "obj-abc"
        assert len(detail.assets) == 1
        assert detail.assets[0].path == "fig1.png"


class TestPaginatedResponse:
    def test_with_question_summaries(self):
        items = [question_summary_data("q-001"), question_summary_data("q-002")]
        parsed_items = [QuestionSummary.model_validate(i) for i in items]
        pr = PaginatedResponse[QuestionSummary].model_validate({
            "items": parsed_items,
            "total": 50,
            "limit": 20,
            "offset": 0,
        })
        assert pr.total == 50
        assert len(pr.items) == 2
        assert pr.items[1].question_id == "q-002"


class TestPaperModels:
    def test_paper_summary(self):
        ps = PaperSummary.model_validate(paper_summary_data())
        assert ps.paper_id == "p-001"
        assert ps.question_count == 5

    def test_paper_detail_with_questions(self):
        pd = PaperDetail.model_validate(paper_detail_data())
        assert pd.paper_id == "p-001"
        assert len(pd.questions) == 1
        assert pd.questions[0].question_id == "q-001"


class TestReviewerModels:
    def test_reviewer_info(self):
        r = ReviewerInfo.model_validate(reviewer_data())
        assert r.reviewer_id == "u-002"
        assert r.username == "reviewer1"

    def test_reviewers_response(self):
        rr = ReviewersResponse.model_validate({"reviewers": [reviewer_data()]})
        assert len(rr.reviewers) == 1


class TestQuestionCreateResult:
    def test_valid(self):
        r = QuestionCreateResult.model_validate({
            "question_id": "q-new",
            "file_name": "upload.zip",
            "imported_assets": 3,
            "status": "none",
        })
        assert r.question_id == "q-new"
        assert r.imported_assets == 3


class TestPaperCreateResult:
    def test_valid(self):
        r = PaperCreateResult.model_validate({
            "paper_id": "p-new",
            "file_name": None,
            "status": "created",
            "question_count": 2,
        })
        assert r.paper_id == "p-new"
        assert r.file_name is None


class TestSystemModels:
    def test_health(self):
        h = HealthResponse.model_validate({"status": "ok", "service": "qb"})
        assert h.status == "ok"

    def test_version(self):
        v = VersionResponse.model_validate(version_data())
        assert v.version == "0.1.1"

    def test_message(self):
        m = MessageResponse.model_validate({"message": "done"})
        assert m.message == "done"
