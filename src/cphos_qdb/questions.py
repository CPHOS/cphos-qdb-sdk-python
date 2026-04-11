"""题目 API mixin（同步 + 异步）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any

from .models import (
    PaginatedResponse,
    QuestionCreateResult,
    QuestionDeleteResult,
    QuestionDetail,
    QuestionDifficultyTagsResponse,
    QuestionFileReplaceResult,
    QuestionSummary,
    QuestionTagsResponse,
    ReviewersResponse,
)

if TYPE_CHECKING:
    from ._transport import AsyncTransport, SyncTransport


def _build_question_params(
    *,
    paper_id: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    reviewer: str | None = None,
    assigned_reviewer_id: str | None = None,
    score_min: int | None = None,
    score_max: int | None = None,
    difficulty_tag: str | None = None,
    difficulty_min: int | None = None,
    difficulty_max: int | None = None,
    q: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    updated_after: str | None = None,
    updated_before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for key, val in {
        "paper_id": paper_id,
        "category": category,
        "tag": tag,
        "reviewer": reviewer,
        "assigned_reviewer_id": assigned_reviewer_id,
        "score_min": score_min,
        "score_max": score_max,
        "difficulty_tag": difficulty_tag,
        "difficulty_min": difficulty_min,
        "difficulty_max": difficulty_max,
        "q": q,
        "created_after": created_after,
        "created_before": created_before,
        "updated_after": updated_after,
        "updated_before": updated_before,
        "limit": limit,
        "offset": offset,
    }.items():
        if val is not None:
            params[key] = val
    return params


def _build_create_fields(
    description: str,
    *,
    category: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, str]:
    fields: dict[str, str] = {
        "description": description,
    }
    if category is not None:
        fields["category"] = category
    if tags is not None:
        fields["tags"] = json.dumps(tags)
    return fields


def _open_zip(file: str | Path | IO[bytes]) -> tuple[str, IO[bytes], str]:
    if isinstance(file, (str, Path)):
        p = Path(file)
        fh = open(p, "rb")  # noqa: SIM115
        return (p.name, fh, "application/zip")
    return ("upload.zip", file, "application/zip")


# ── Sync ──────────────────────────────────────────────────────────────────

class QuestionsMixin:
    """同步题目操作 mixin。"""

    _t: SyncTransport

    def list_questions(
        self,
        *,
        paper_id: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        reviewer: str | None = None,
        assigned_reviewer_id: str | None = None,
        score_min: int | None = None,
        score_max: int | None = None,
        difficulty_tag: str | None = None,
        difficulty_min: int | None = None,
        difficulty_max: int | None = None,
        q: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PaginatedResponse[QuestionSummary]:
        """分页查询题目。

        Args:
            paper_id: 按所属试卷过滤。
            category: 按分类过滤 (`"none"` / `"T"` / `"E"`)。
            tag: 按标签过滤。
            reviewer: 按审核人过滤。
            assigned_reviewer_id: 按分配的审阅人 UUID 过滤。
            score_min: 分值下限。
            score_max: 分值上限。
            difficulty_tag: 难度 tag，如 `"human"`。
            difficulty_min: 难度下限 (1-10)。
            difficulty_max: 难度上限 (1-10)。
            q: 关键词，模糊匹配 description。
            created_after: 创建时间下限 (ISO 8601)。
            created_before: 创建时间上限 (ISO 8601)。
            updated_after: 更新时间下限 (ISO 8601)。
            updated_before: 更新时间上限 (ISO 8601)。
            limit: 每页数量 (1-100)，默认 20。
            offset: 偏移量。
        """
        params = _build_question_params(
            paper_id=paper_id, category=category, tag=tag,
            reviewer=reviewer, assigned_reviewer_id=assigned_reviewer_id,
            score_min=score_min, score_max=score_max,
            difficulty_tag=difficulty_tag, difficulty_min=difficulty_min,
            difficulty_max=difficulty_max, q=q,
            created_after=created_after, created_before=created_before,
            updated_after=updated_after, updated_before=updated_before,
            limit=limit, offset=offset,
        )
        data = self._t.get("/questions", params=params).json()
        data["items"] = [QuestionSummary.model_validate(i) for i in data["items"]]
        return PaginatedResponse[QuestionSummary].model_validate(data)

    def get_question(self, question_id: str) -> QuestionDetail:
        """获取单个题目完整详情。

        Args:
            question_id: 题目 UUID。
        """
        return QuestionDetail.model_validate(
            self._t.get(f"/questions/{question_id}").json()
        )

    def create_question(
        self,
        file: str | Path | IO[bytes],
        *,
        description: str,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> QuestionCreateResult:
        """上传新题目（zip 包）。

        Args:
            file: zip 文件路径或已打开的二进制文件对象。
            description: 题目描述。
            category: 分类 (`"none"` / `"T"` / `"E"`)。
            tags: 标签列表。
        """
        fname, fh, mime = _open_zip(file)
        try:
            fields = _build_create_fields(
                description,
                category=category,
                tags=tags,
            )
            resp = self._t.request(
                "POST", "/questions",
                data=fields,
                files={"file": (fname, fh, mime)},
            )
        finally:
            if isinstance(file, (str, Path)):
                fh.close()
        return QuestionCreateResult.model_validate(resp.json())

    def update_question_description(
        self,
        question_id: str,
        description: str,
    ) -> QuestionDetail:
        """更新题目描述。

        Args:
            question_id: 题目 UUID。
            description: 题目描述。
        """
        return QuestionDetail.model_validate(
            self._t.patch(
                f"/questions/{question_id}/description",
                json_body={"description": description},
            ).json()
        )

    def update_question_category(self, question_id: str, category: str) -> QuestionDetail:
        """更新题目分类。"""
        return QuestionDetail.model_validate(
            self._t.patch(
                f"/questions/{question_id}/category",
                json_body={"category": category},
            ).json()
        )

    def update_question_tags(self, question_id: str, tags: list[str]) -> QuestionDetail:
        """整体替换题目标签。"""
        return QuestionDetail.model_validate(
            self._t.patch(
                f"/questions/{question_id}/tags",
                json_body={"tags": tags},
            ).json()
        )

    def update_question_status(self, question_id: str, status: str) -> QuestionDetail:
        """更新题目状态。"""
        return QuestionDetail.model_validate(
            self._t.patch(
                f"/questions/{question_id}/status",
                json_body={"status": status},
            ).json()
        )

    def create_question_difficulty(
        self,
        question_id: str,
        algorithm_tag: str,
        score: int,
        *,
        notes: str | None = None,
    ) -> QuestionDetail:
        """创建题目难度条目。"""
        body: dict[str, Any] = {
            "algorithm_tag": algorithm_tag,
            "score": score,
        }
        if notes is not None:
            body["notes"] = notes
        return QuestionDetail.model_validate(
            self._t.post(
                f"/questions/{question_id}/difficulties",
                json_body=body,
            ).json()
        )

    def update_question_difficulty(
        self,
        question_id: str,
        algorithm_tag: str,
        score: int,
        *,
        notes: str | None = None,
    ) -> QuestionDetail:
        """更新题目难度条目。"""
        body: dict[str, Any] = {"score": score}
        if notes is not None:
            body["notes"] = notes
        return QuestionDetail.model_validate(
            self._t.patch(
                f"/questions/{question_id}/difficulties/{algorithm_tag}",
                json_body=body,
            ).json()
        )

    def delete_question_difficulty(self, question_id: str, algorithm_tag: str) -> QuestionDetail:
        """删除题目难度条目。"""
        return QuestionDetail.model_validate(
            self._t.delete(
                f"/questions/{question_id}/difficulties/{algorithm_tag}"
            ).json()
        )

    def replace_question_file(
        self,
        question_id: str,
        file: str | Path | IO[bytes],
    ) -> QuestionFileReplaceResult:
        """替换题目的 zip 文件内容，不修改元数据。

        Args:
            question_id: 题目 UUID。
            file: 新的 zip 文件路径或二进制文件对象。
        """
        fname, fh, mime = _open_zip(file)
        try:
            resp = self._t.put(
                f"/questions/{question_id}/file",
                files={"file": (fname, fh, mime)},
            )
        finally:
            if isinstance(file, (str, Path)):
                fh.close()
        return QuestionFileReplaceResult.model_validate(resp.json())

    def delete_question(self, question_id: str) -> QuestionDeleteResult:
        """软删除题目。"""
        return QuestionDeleteResult.model_validate(
            self._t.delete(f"/questions/{question_id}").json()
        )

    def get_question_tags(self) -> list[str]:
        """获取所有未删除题目使用中的标签列表。"""
        return QuestionTagsResponse.model_validate(
            self._t.get("/questions/tags").json()
        ).tags

    def get_difficulty_tags(self) -> list[str]:
        """获取所有未删除题目使用中的难度标签列表。"""
        return QuestionDifficultyTagsResponse.model_validate(
            self._t.get("/questions/difficulty-tags").json()
        ).difficulty_tags

    def download_question_bundle(
        self,
        question_ids: list[str],
        save_to: str | Path,
    ) -> Path:
        """批量打包下载题目原始文件到本地。

        Args:
            question_ids: 题目 UUID 列表。
            save_to: 本地保存路径。

        Returns:
            保存的文件路径。
        """
        resp = self._t.post(
            "/questions/bundles",
            json_body={"question_ids": question_ids},
        )
        dest = Path(save_to)
        dest.write_bytes(resp.content)
        return dest

    # ── reviewers ─────────────────────────────────────────────────────────

    def list_reviewers(self, question_id: str) -> ReviewersResponse:
        """获取题目的审阅人列表。"""
        return ReviewersResponse.model_validate(
            self._t.get(f"/questions/{question_id}/reviewers").json()
        )

    def assign_reviewer(self, question_id: str, reviewer_id: str) -> ReviewersResponse:
        """分配审阅人到题目。

        Args:
            question_id: 题目 UUID。
            reviewer_id: 要分配的用户 UUID（必须为 `user` 角色且已启用）。
        """
        return ReviewersResponse.model_validate(
            self._t.post(
                f"/questions/{question_id}/reviewers",
                json_body={"reviewer_id": reviewer_id},
            ).json()
        )

    def remove_reviewer(self, question_id: str, reviewer_id: str) -> ReviewersResponse:
        """移除题目的审阅人。"""
        return ReviewersResponse.model_validate(
            self._t.delete(
                f"/questions/{question_id}/reviewers/{reviewer_id}"
            ).json()
        )


# ── Async ─────────────────────────────────────────────────────────────────

class AsyncQuestionsMixin:
    """异步题目操作 mixin，接口与 `QuestionsMixin` 相同。"""

    _t: AsyncTransport

    async def list_questions(
        self,
        *,
        paper_id: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        reviewer: str | None = None,
        assigned_reviewer_id: str | None = None,
        score_min: int | None = None,
        score_max: int | None = None,
        difficulty_tag: str | None = None,
        difficulty_min: int | None = None,
        difficulty_max: int | None = None,
        q: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PaginatedResponse[QuestionSummary]:
        """分页查询题目。参见 [`QuestionsMixin.list_questions`][cphos_qdb.questions.QuestionsMixin.list_questions]。"""
        params = _build_question_params(
            paper_id=paper_id, category=category, tag=tag,
            reviewer=reviewer, assigned_reviewer_id=assigned_reviewer_id,
            score_min=score_min, score_max=score_max,
            difficulty_tag=difficulty_tag, difficulty_min=difficulty_min,
            difficulty_max=difficulty_max, q=q,
            created_after=created_after, created_before=created_before,
            updated_after=updated_after, updated_before=updated_before,
            limit=limit, offset=offset,
        )
        data = (await self._t.get("/questions", params=params)).json()
        data["items"] = [QuestionSummary.model_validate(i) for i in data["items"]]
        return PaginatedResponse[QuestionSummary].model_validate(data)

    async def get_question(self, question_id: str) -> QuestionDetail:
        return QuestionDetail.model_validate(
            (await self._t.get(f"/questions/{question_id}")).json()
        )

    async def create_question(
        self,
        file: str | Path | IO[bytes],
        *,
        description: str,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> QuestionCreateResult:
        fname, fh, mime = _open_zip(file)
        try:
            fields = _build_create_fields(
                description,
                category=category,
                tags=tags,
            )
            resp = await self._t.request(
                "POST", "/questions",
                data=fields,
                files={"file": (fname, fh, mime)},
            )
        finally:
            if isinstance(file, (str, Path)):
                fh.close()
        return QuestionCreateResult.model_validate(resp.json())

    async def update_question_description(
        self,
        question_id: str,
        description: str,
    ) -> QuestionDetail:
        return QuestionDetail.model_validate(
            (await self._t.patch(
                f"/questions/{question_id}/description",
                json_body={"description": description},
            )).json()
        )

    async def update_question_category(self, question_id: str, category: str) -> QuestionDetail:
        return QuestionDetail.model_validate(
            (await self._t.patch(
                f"/questions/{question_id}/category",
                json_body={"category": category},
            )).json()
        )

    async def update_question_tags(self, question_id: str, tags: list[str]) -> QuestionDetail:
        return QuestionDetail.model_validate(
            (await self._t.patch(
                f"/questions/{question_id}/tags",
                json_body={"tags": tags},
            )).json()
        )

    async def update_question_status(self, question_id: str, status: str) -> QuestionDetail:
        return QuestionDetail.model_validate(
            (await self._t.patch(
                f"/questions/{question_id}/status",
                json_body={"status": status},
            )).json()
        )

    async def create_question_difficulty(
        self,
        question_id: str,
        algorithm_tag: str,
        score: int,
        *,
        notes: str | None = None,
    ) -> QuestionDetail:
        body: dict[str, Any] = {
            "algorithm_tag": algorithm_tag,
            "score": score,
        }
        if notes is not None:
            body["notes"] = notes
        return QuestionDetail.model_validate(
            (await self._t.post(
                f"/questions/{question_id}/difficulties",
                json_body=body,
            )).json()
        )

    async def update_question_difficulty(
        self,
        question_id: str,
        algorithm_tag: str,
        score: int,
        *,
        notes: str | None = None,
    ) -> QuestionDetail:
        body: dict[str, Any] = {"score": score}
        if notes is not None:
            body["notes"] = notes
        return QuestionDetail.model_validate(
            (await self._t.patch(
                f"/questions/{question_id}/difficulties/{algorithm_tag}",
                json_body=body,
            )).json()
        )

    async def delete_question_difficulty(self, question_id: str, algorithm_tag: str) -> QuestionDetail:
        return QuestionDetail.model_validate(
            (await self._t.delete(
                f"/questions/{question_id}/difficulties/{algorithm_tag}"
            )).json()
        )

    async def replace_question_file(
        self,
        question_id: str,
        file: str | Path | IO[bytes],
    ) -> QuestionFileReplaceResult:
        fname, fh, mime = _open_zip(file)
        try:
            resp = await self._t.put(
                f"/questions/{question_id}/file",
                files={"file": (fname, fh, mime)},
            )
        finally:
            if isinstance(file, (str, Path)):
                fh.close()
        return QuestionFileReplaceResult.model_validate(resp.json())

    async def delete_question(self, question_id: str) -> QuestionDeleteResult:
        return QuestionDeleteResult.model_validate(
            (await self._t.delete(f"/questions/{question_id}")).json()
        )

    async def get_question_tags(self) -> list[str]:
        return QuestionTagsResponse.model_validate(
            (await self._t.get("/questions/tags")).json()
        ).tags

    async def get_difficulty_tags(self) -> list[str]:
        return QuestionDifficultyTagsResponse.model_validate(
            (await self._t.get("/questions/difficulty-tags")).json()
        ).difficulty_tags

    async def download_question_bundle(
        self,
        question_ids: list[str],
        save_to: str | Path,
    ) -> Path:
        resp = await self._t.post(
            "/questions/bundles",
            json_body={"question_ids": question_ids},
        )
        dest = Path(save_to)
        dest.write_bytes(resp.content)
        return dest

    # ── reviewers ─────────────────────────────────────────────────────────

    async def list_reviewers(self, question_id: str) -> ReviewersResponse:
        return ReviewersResponse.model_validate(
            (await self._t.get(f"/questions/{question_id}/reviewers")).json()
        )

    async def assign_reviewer(self, question_id: str, reviewer_id: str) -> ReviewersResponse:
        return ReviewersResponse.model_validate(
            (await self._t.post(
                f"/questions/{question_id}/reviewers",
                json_body={"reviewer_id": reviewer_id},
            )).json()
        )

    async def remove_reviewer(self, question_id: str, reviewer_id: str) -> ReviewersResponse:
        return ReviewersResponse.model_validate(
            (await self._t.delete(
                f"/questions/{question_id}/reviewers/{reviewer_id}"
            )).json()
        )
