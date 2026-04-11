"""试卷 API mixin（同步 + 异步）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any

from .models import (
    PaginatedResponse,
    PaperCreateResult,
    PaperDeleteResult,
    PaperDetail,
    PaperFileReplaceResult,
    PaperSummary,
)

if TYPE_CHECKING:
    from ._transport import AsyncTransport, SyncTransport


def _build_paper_params(
    *,
    question_id: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    updated_after: str | None = None,
    updated_before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> dict[str, Any]:
    return {
        k: v for k, v in {
            "question_id": question_id,
            "category": category,
            "tag": tag,
            "q": q,
            "created_after": created_after,
            "created_before": created_before,
            "updated_after": updated_after,
            "updated_before": updated_before,
            "limit": limit,
            "offset": offset,
        }.items() if v is not None
    }


# ── Sync ──────────────────────────────────────────────────────────────────

class PapersMixin:
    """同步试卷操作 mixin。"""

    _t: SyncTransport

    def list_papers(
        self,
        *,
        question_id: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        q: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PaginatedResponse[PaperSummary]:
        """分页查询试卷。

        Args:
            question_id: 按包含的题目过滤。
            category: 按包含题目的分类过滤。
            tag: 按包含题目的标签过滤。
            q: 关键词，匹配 description、title、subtitle。
            created_after: 创建时间下限 (ISO 8601)。
            created_before: 创建时间上限 (ISO 8601)。
            updated_after: 更新时间下限 (ISO 8601)。
            updated_before: 更新时间上限 (ISO 8601)。
            limit: 每页数量 (1-100)。
            offset: 偏移量。
        """
        params = _build_paper_params(
            question_id=question_id, category=category, tag=tag, q=q,
            created_after=created_after, created_before=created_before,
            updated_after=updated_after, updated_before=updated_before,
            limit=limit, offset=offset,
        )
        data = self._t.get("/papers", params=params).json()
        data["items"] = [PaperSummary.model_validate(i) for i in data["items"]]
        return PaginatedResponse[PaperSummary].model_validate(data)

    def get_paper(self, paper_id: str) -> PaperDetail:
        """获取试卷详情和题目列表。"""
        return PaperDetail.model_validate(
            self._t.get(f"/papers/{paper_id}").json()
        )

    def create_paper(
        self,
        *,
        description: str,
        title: str,
        subtitle: str,
        question_ids: list[str],
        file: str | Path | IO[bytes] | None = None,
    ) -> PaperCreateResult:
        data_fields: dict[str, str] = {
            "description": description,
            "title": title,
            "subtitle": subtitle,
            "question_ids": json.dumps(question_ids),
        }
        files_dict: dict | None = None
        fh = None
        try:
            if file is not None:
                if isinstance(file, (str, Path)):
                    p = Path(file)
                    fh = open(p, "rb")  # noqa: SIM115
                    files_dict = {"file": (p.name, fh, "application/zip")}
                else:
                    files_dict = {"file": ("appendix.zip", file, "application/zip")}

            resp = self._t.request(
                "POST", "/papers",
                data=data_fields,
                files=files_dict,
            )
        finally:
            if fh is not None:
                fh.close()
        return PaperCreateResult.model_validate(resp.json())

    def update_paper(
        self,
        paper_id: str,
        *,
        description: str | None = None,
        title: str | None = None,
        subtitle: str | None = None,
        question_ids: list[str] | None = None,
    ) -> PaperDetail:
        """部分更新试卷元数据。

        Args:
            paper_id: 试卷 UUID。
            description: 试卷描述。
            title: 试卷标题。
            subtitle: 试卷副标题。
            question_ids: 题目列表（更新后按数组顺序重排）。
        """
        body = {k: v for k, v in {
            "description": description,
            "title": title,
            "subtitle": subtitle,
            "question_ids": question_ids,
        }.items() if v is not None}
        return PaperDetail.model_validate(
            self._t.patch(f"/papers/{paper_id}", json_body=body).json()
        )

    def replace_paper_file(
        self,
        paper_id: str,
        file: str | Path | IO[bytes],
    ) -> PaperFileReplaceResult:
        """替换试卷附录 zip 文件。

        Args:
            paper_id: 试卷 UUID。
            file: 新的 zip 文件路径或二进制文件对象。
        """
        if isinstance(file, (str, Path)):
            p = Path(file)
            fh: IO[bytes] = open(p, "rb")  # noqa: SIM115
            fname = p.name
        else:
            fh = file
            fname = "appendix.zip"
        try:
            resp = self._t.put(
                f"/papers/{paper_id}/file",
                files={"file": (fname, fh, "application/zip")},
            )
        finally:
            if isinstance(file, (str, Path)):
                fh.close()
        return PaperFileReplaceResult.model_validate(resp.json())

    def delete_paper(self, paper_id: str) -> PaperDeleteResult:
        """软删除试卷。"""
        return PaperDeleteResult.model_validate(
            self._t.delete(f"/papers/{paper_id}").json()
        )

    def download_paper_bundle(
        self,
        paper_ids: list[str],
        save_to: str | Path,
    ) -> Path:
        """批量打包下载试卷到本地。

        Args:
            paper_ids: 试卷 UUID 列表。
            save_to: 本地保存路径。

        Returns:
            保存的文件路径。
        """
        resp = self._t.post(
            "/papers/bundles",
            json_body={"paper_ids": paper_ids},
        )
        dest = Path(save_to)
        dest.write_bytes(resp.content)
        return dest


# ── Async ─────────────────────────────────────────────────────────────────

class AsyncPapersMixin:
    """异步试卷操作 mixin，接口与 `PapersMixin` 相同。"""

    _t: AsyncTransport

    async def list_papers(
        self,
        *,
        question_id: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        q: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PaginatedResponse[PaperSummary]:
        """分页查询试卷。参见 [`PapersMixin.list_papers`][cphos_qdb.papers.PapersMixin.list_papers]。"""
        params = _build_paper_params(
            question_id=question_id, category=category, tag=tag, q=q,
            created_after=created_after, created_before=created_before,
            updated_after=updated_after, updated_before=updated_before,
            limit=limit, offset=offset,
        )
        data = (await self._t.get("/papers", params=params)).json()
        data["items"] = [PaperSummary.model_validate(i) for i in data["items"]]
        return PaginatedResponse[PaperSummary].model_validate(data)

    async def get_paper(self, paper_id: str) -> PaperDetail:
        return PaperDetail.model_validate(
            (await self._t.get(f"/papers/{paper_id}")).json()
        )

    async def create_paper(
        self,
        *,
        description: str,
        title: str,
        subtitle: str,
        question_ids: list[str],
        file: str | Path | IO[bytes] | None = None,
    ) -> PaperCreateResult:
        data_fields: dict[str, str] = {
            "description": description,
            "title": title,
            "subtitle": subtitle,
            "question_ids": json.dumps(question_ids),
        }
        files_dict: dict | None = None
        fh = None
        try:
            if file is not None:
                if isinstance(file, (str, Path)):
                    p = Path(file)
                    fh = open(p, "rb")  # noqa: SIM115
                    files_dict = {"file": (p.name, fh, "application/zip")}
                else:
                    files_dict = {"file": ("appendix.zip", file, "application/zip")}

            resp = await self._t.request(
                "POST", "/papers",
                data=data_fields,
                files=files_dict,
            )
        finally:
            if fh is not None:
                fh.close()
        return PaperCreateResult.model_validate(resp.json())

    async def update_paper(
        self,
        paper_id: str,
        *,
        description: str | None = None,
        title: str | None = None,
        subtitle: str | None = None,
        question_ids: list[str] | None = None,
    ) -> PaperDetail:
        body = {k: v for k, v in {
            "description": description,
            "title": title,
            "subtitle": subtitle,
            "question_ids": question_ids,
        }.items() if v is not None}
        return PaperDetail.model_validate(
            (await self._t.patch(f"/papers/{paper_id}", json_body=body)).json()
        )

    async def replace_paper_file(
        self,
        paper_id: str,
        file: str | Path | IO[bytes],
    ) -> PaperFileReplaceResult:
        if isinstance(file, (str, Path)):
            p = Path(file)
            fh: IO[bytes] = open(p, "rb")  # noqa: SIM115
            fname = p.name
        else:
            fh = file
            fname = "appendix.zip"
        try:
            resp = await self._t.put(
                f"/papers/{paper_id}/file",
                files={"file": (fname, fh, "application/zip")},
            )
        finally:
            if isinstance(file, (str, Path)):
                fh.close()
        return PaperFileReplaceResult.model_validate(resp.json())

    async def delete_paper(self, paper_id: str) -> PaperDeleteResult:
        return PaperDeleteResult.model_validate(
            (await self._t.delete(f"/papers/{paper_id}")).json()
        )

    async def download_paper_bundle(
        self,
        paper_ids: list[str],
        save_to: str | Path,
    ) -> Path:
        resp = await self._t.post(
            "/papers/bundles",
            json_body={"paper_ids": paper_ids},
        )
        dest = Path(save_to)
        dest.write_bytes(resp.content)
        return dest
