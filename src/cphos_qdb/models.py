"""Pydantic models mirroring the QB API data structures."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Auth ──────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class UserProfile(BaseModel):
    user_id: str
    username: str
    display_name: str
    role: str
    is_active: bool
    leader_expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


# ── Pagination ────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


# ── Questions ─────────────────────────────────────────────────────────────

class DifficultyUpdatedBy(BaseModel):
    user_id: str
    username: str
    display_name: str


class DifficultyValue(BaseModel):
    score: int = Field(ge=1, le=10)
    notes: str | None = None
    updated_by: DifficultyUpdatedBy | None = None


class QuestionSource(BaseModel):
    tex: str


class QuestionSummary(BaseModel):
    question_id: str
    source: QuestionSource
    category: str
    status: str
    description: str
    score: int | None = None
    author: str = ""
    reviewers: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    difficulty: dict[str, DifficultyValue] = Field(default_factory=dict)
    allow_auto_reviewer: bool = False
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime


class QuestionAssetRef(BaseModel):
    path: str
    file_kind: str
    object_id: str
    mime_type: str


class QuestionPaperRef(BaseModel):
    paper_id: str
    description: str
    title: str
    subtitle: str
    sort_order: int


class QuestionDetail(QuestionSummary):
    tex_object_id: str
    assets: list[QuestionAssetRef] = Field(default_factory=list)
    papers: list[QuestionPaperRef] = Field(default_factory=list)


class QuestionCreateResult(BaseModel):
    question_id: str
    file_name: str
    imported_assets: int
    status: str


class QuestionFileReplaceResult(BaseModel):
    question_id: str
    file_name: str
    source_tex_path: str
    imported_assets: int
    status: str


class QuestionDeleteResult(BaseModel):
    question_id: str
    status: str


class QuestionTagsResponse(BaseModel):
    tags: list[str]


class QuestionDifficultyTagsResponse(BaseModel):
    difficulty_tags: list[str]


# ── Reviewers ─────────────────────────────────────────────────────────────

class ReviewerInfo(BaseModel):
    reviewer_id: str
    username: str
    display_name: str
    assigned_by: str
    created_at: datetime


class ReviewersResponse(BaseModel):
    reviewers: list[ReviewerInfo]


# ── Papers ────────────────────────────────────────────────────────────────

class PaperSummary(BaseModel):
    paper_id: str
    description: str
    title: str
    subtitle: str
    question_count: int
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime


class PaperDetail(BaseModel):
    paper_id: str
    description: str
    title: str
    subtitle: str
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
    questions: list[QuestionSummary] = Field(default_factory=list)


class PaperCreateResult(BaseModel):
    paper_id: str
    file_name: str | None = None
    status: str
    question_count: int


class PaperFileReplaceResult(BaseModel):
    paper_id: str
    file_name: str
    status: str


class PaperDeleteResult(BaseModel):
    paper_id: str
    status: str


# ── System ────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    service: str


class MessageResponse(BaseModel):
    message: str
