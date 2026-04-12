"""题库 API 数据模型。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Auth ──────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """登录成功后返回的令牌对。"""

    access_token: str
    """访问令牌。"""
    refresh_token: str
    """刷新令牌。"""
    token_type: str
    """令牌类型，通常为 `bearer`。"""
    expires_in: int
    """访问令牌有效期（秒）。"""


class UserProfile(BaseModel):
    """用户信息。"""

    user_id: str
    """用户 UUID。"""
    username: str
    """用户名。"""
    display_name: str
    """显示名称。"""
    role: str
    """角色，如 `admin`、`user`、`bot`。"""
    is_active: bool
    """账号是否启用。"""
    leader_expires_at: datetime | None = None
    """领队权限过期时间，`None` 表示无领队权限。"""
    created_at: datetime
    """账号创建时间。"""
    updated_at: datetime
    """账号最后更新时间。"""


# ── Pagination ────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应。"""

    items: list[T]
    """当前页数据列表。"""
    total: int
    """符合条件的总数。"""
    limit: int
    """每页数量。"""
    offset: int
    """偏移量。"""


# ── Questions ─────────────────────────────────────────────────────────────

class DifficultyUpdatedBy(BaseModel):
    """难度评估的更新者信息。"""

    user_id: str
    """用户 UUID。"""
    username: str
    """用户名。"""
    display_name: str
    """显示名称。"""


class DifficultyValue(BaseModel):
    """难度评估值。"""

    score: int = Field(ge=1, le=10)
    """难度分值 (1-10)。"""
    notes: str | None = None
    """备注。"""
    updated_by: DifficultyUpdatedBy | None = None
    """最后更新者。"""


class QuestionSource(BaseModel):
    """题目源文件信息。"""

    tex: str
    """TeX 主文件路径。"""


class QuestionSummary(BaseModel):
    """题目摘要（列表项）。"""

    question_id: str
    """题目 UUID。"""
    source: QuestionSource
    """源文件信息。"""
    category: str
    """分类：`none`、`T`（理论）、`E`（实验）。"""
    status: str
    """状态：`none`、`reviewed`、`used`。"""
    description: str
    """题目描述。"""
    score: int | None = None
    """分值。"""
    author: str = ""
    """命题人。"""
    reviewers: list[str] = Field(default_factory=list)
    """审题人列表。"""
    tags: list[str] = Field(default_factory=list)
    """标签列表。"""
    difficulty: dict[str, DifficultyValue] = Field(default_factory=dict)
    """难度评估，key 为评估标签（如 `human`）。"""
    allow_auto_reviewer: bool = False
    """是否允许自动添加审阅人。"""
    created_by: str | None = None
    """创建者用户 UUID。"""
    created_at: datetime
    """创建时间。"""
    updated_at: datetime
    """最后更新时间。"""


class QuestionAssetRef(BaseModel):
    """题目附属资源引用。"""

    path: str
    """资源文件路径。"""
    file_kind: str
    """文件类型。"""
    object_id: str
    """对象存储 ID。"""
    mime_type: str | None = None
    """MIME 类型。"""


class QuestionPaperRef(BaseModel):
    """题目所属试卷的引用。"""

    paper_id: str
    """试卷 UUID。"""
    description: str
    """试卷描述。"""
    title: str
    """试卷标题。"""
    subtitle: str
    """试卷副标题。"""
    sort_order: int
    """题目在试卷中的排序。"""


class QuestionDetail(QuestionSummary):
    """题目详情，包含资源和关联试卷。"""

    tex_object_id: str
    """TeX 文件对象存储 ID。"""
    assets: list[QuestionAssetRef] = Field(default_factory=list)
    """附属资源列表。"""
    papers: list[QuestionPaperRef] = Field(default_factory=list)
    """所属试卷列表。"""


class QuestionCreateResult(BaseModel):
    """题目创建结果。"""

    question_id: str
    """新创建的题目 UUID。"""
    file_name: str
    """上传的文件名。"""
    imported_assets: int
    """导入的资源数量。"""
    status: str
    """题目状态。"""


class QuestionFileReplaceResult(BaseModel):
    """题目文件替换结果。"""

    question_id: str
    """题目 UUID。"""
    file_name: str
    """新文件名。"""
    source_tex_path: str
    """TeX 主文件路径。"""
    imported_assets: int
    """导入的资源数量。"""
    status: str
    """题目状态。"""


class QuestionDeleteResult(BaseModel):
    """题目删除结果。"""

    question_id: str
    """题目 UUID。"""
    status: str
    """删除后状态。"""


class QuestionTagsResponse(BaseModel):
    """题目标签列表响应。"""

    tags: list[str]
    """标签列表。"""


class QuestionDifficultyTagsResponse(BaseModel):
    """难度标签列表响应。"""

    difficulty_tags: list[str]
    """难度标签列表。"""


# ── Reviewers ─────────────────────────────────────────────────────────────

class ReviewerInfo(BaseModel):
    """审阅人信息。"""

    reviewer_id: str
    """审阅人用户 UUID。"""
    username: str
    """用户名。"""
    display_name: str
    """显示名称。"""
    assigned_by: str
    """分配者用户 UUID。"""
    created_at: datetime
    """分配时间。"""


class ReviewersResponse(BaseModel):
    """审阅人列表响应。"""

    reviewers: list[ReviewerInfo]
    """审阅人列表。"""


# ── Papers ────────────────────────────────────────────────────────────────

class PaperSummary(BaseModel):
    """试卷摘要（列表项）。"""

    paper_id: str
    """试卷 UUID。"""
    description: str
    """试卷描述。"""
    title: str
    """试卷标题。"""
    subtitle: str
    """试卷副标题。"""
    question_count: int
    """包含题目数量。"""
    created_by: str | None = None
    """创建者用户 UUID。"""
    created_at: datetime
    """创建时间。"""
    updated_at: datetime
    """最后更新时间。"""


class PaperDetail(BaseModel):
    """试卷详情，包含题目列表。"""

    paper_id: str
    """试卷 UUID。"""
    description: str
    """试卷描述。"""
    title: str
    """试卷标题。"""
    subtitle: str
    """试卷副标题。"""
    created_by: str | None = None
    """创建者用户 UUID。"""
    created_at: datetime
    """创建时间。"""
    updated_at: datetime
    """最后更新时间。"""
    questions: list[QuestionSummary] = Field(default_factory=list)
    """包含的题目列表。"""


class PaperCreateResult(BaseModel):
    """试卷创建结果。"""

    paper_id: str
    """新创建的试卷 UUID。"""
    file_name: str | None = None
    """附录文件名（无附录时为 `None`）。"""
    status: str
    """试卷状态。"""
    question_count: int
    """包含题目数量。"""


class PaperFileReplaceResult(BaseModel):
    """试卷附录文件替换结果。"""

    paper_id: str
    """试卷 UUID。"""
    file_name: str
    """新附录文件名。"""
    status: str
    """替换状态。"""


class PaperDeleteResult(BaseModel):
    """试卷删除结果。"""

    paper_id: str
    """试卷 UUID。"""
    status: str
    """删除后状态。"""


# ── System ────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """健康检查响应。"""

    status: str
    """服务状态，正常为 `ok`。"""
    service: str
    """服务名称。"""


class VersionResponse(BaseModel):
    """后端版本响应。"""

    version: str
    """后端语义化版本号。"""


class MessageResponse(BaseModel):
    """通用消息响应。"""

    message: str
    """消息内容。"""
