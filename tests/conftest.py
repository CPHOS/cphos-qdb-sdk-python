"""Shared fixtures and mock data for tests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import httpx
import pytest
import respx

from cphos_qdb import QBClient, AsyncQBClient

BASE_URL = "http://test-api.local"

NOW = "2026-04-10T08:00:00Z"


# ── Mock data factories ──────────────────────────────────────────────────

def token_data() -> dict[str, Any]:
    return {
        "access_token": "acc_test_123",
        "refresh_token": "ref_test_456",
        "token_type": "bearer",
        "expires_in": 3600,
    }


def version_data(version: str = "0.2.0") -> dict[str, Any]:
    return {"version": version}


def user_profile_data() -> dict[str, Any]:
    return {
        "user_id": "u-001",
        "username": "bot_user",
        "display_name": "Bot User",
        "role": "bot",
        "is_active": True,
        "leader_expires_at": None,
        "created_at": NOW,
        "updated_at": NOW,
    }


def question_summary_data(qid: str = "q-001") -> dict[str, Any]:
    return {
        "question_id": qid,
        "source": {"tex": "main.tex"},
        "category": "T",
        "status": "none",
        "description": "热学题目",
        "score": 20,
        "author": "author1",
        "reviewers": [],
        "tags": ["thermodynamics"],
        "difficulty": {"human": {"score": 7, "notes": None, "updated_by": None}},
        "allow_auto_reviewer": False,
        "created_by": "u-001",
        "created_at": NOW,
        "updated_at": NOW,
    }


def question_detail_data(qid: str = "q-001") -> dict[str, Any]:
    d = question_summary_data(qid)
    d.update({
        "tex_object_id": "obj-abc",
        "assets": [
            {"path": "fig1.png", "file_kind": "asset", "object_id": "obj-fig1", "mime_type": "image/png"},
        ],
        "papers": [],
    })
    return d


def paper_summary_data(pid: str = "p-001") -> dict[str, Any]:
    return {
        "paper_id": pid,
        "description": "综合训练",
        "title": "综合训练 2026",
        "subtitle": "A 卷",
        "question_count": 5,
        "created_by": "u-001",
        "created_at": NOW,
        "updated_at": NOW,
    }


def paper_detail_data(pid: str = "p-001") -> dict[str, Any]:
    return {
        "paper_id": pid,
        "description": "综合训练",
        "title": "综合训练 2026",
        "subtitle": "A 卷",
        "created_by": "u-001",
        "created_at": NOW,
        "updated_at": NOW,
        "questions": [question_summary_data()],
    }


def paginated_response(items: list[dict], total: int | None = None) -> dict[str, Any]:
    return {
        "items": items,
        "total": total or len(items),
        "limit": 20,
        "offset": 0,
    }


def reviewer_data() -> dict[str, Any]:
    return {
        "reviewer_id": "u-002",
        "username": "reviewer1",
        "display_name": "Reviewer One",
        "assigned_by": "u-001",
        "created_at": NOW,
    }


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture()
def mock_api():
    """Context-managed respx mock router."""
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


@pytest.fixture()
def sync_client():
    """Pre-configured sync client (not logged in)."""
    client = QBClient(BASE_URL, check_version=False)
    yield client
    client.close()


@pytest.fixture()
def async_client():
    """Pre-configured async client (not logged in)."""
    client = AsyncQBClient(BASE_URL, check_version=False)
    yield client


@pytest.fixture()
def authed_sync_client(mock_api, sync_client):
    """Sync client with tokens already set (skips login HTTP call)."""
    sync_client._t.set_tokens("acc_test_123", "ref_test_456")
    return sync_client


@pytest.fixture()
def authed_async_client(mock_api, async_client):
    """Async client with tokens already set."""
    async_client._t.set_tokens("acc_test_123", "ref_test_456")
    return async_client
