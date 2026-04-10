# 快速开始

## 安装

从 GitHub 安装（推荐指定版本标签）：

```bash
uv add cphos-qdb@git+https://github.com/CPHOS/cphos-qdb-sdk-python.git@v0.1.0
```

安装最新 `main` 分支：

```bash
uv add cphos-qdb@git+https://github.com/CPHOS/cphos-qdb-sdk-python.git
```

## 同步用法

```python
from cphos_qdb import QBClient

with QBClient("http://localhost:8080") as client:
    # 登录
    client.login("bot_user", "bot_password")

    # 健康检查
    health = client.health()
    print(health.status)  # "ok"

    # 查询题目
    result = client.list_questions(category="T", limit=10)
    for q in result.items:
        print(q.question_id, q.description)

    # 获取题目详情
    detail = client.get_question(result.items[0].question_id)

    # 上传题目
    created = client.create_question(
        "path/to/question.zip",
        description="热学标定 gamma",
        difficulty={"human": {"score": 7}},
        category="T",
        tags=["thermodynamics"],
    )

    # 更新题目
    client.update_question(
        created.question_id,
        status="reviewed",
        tags=["thermodynamics", "optics"],
    )

    # 创建试卷
    paper = client.create_paper(
        description="综合训练 A",
        title="综合训练 2026 A 卷",
        subtitle="校内选拔",
        question_ids=[created.question_id],
    )

    # 下载试卷 bundle
    client.download_paper_bundle([paper.paper_id], save_to="bundle.zip")
```

## 异步用法

```python
import asyncio
from cphos_qdb import AsyncQBClient

async def main():
    async with AsyncQBClient("http://localhost:8080") as client:
        await client.login("bot_user", "bot_password")

        questions = await client.list_questions(category="T")
        for q in questions.items:
            print(q.description)

        detail = await client.get_question(questions.items[0].question_id)

asyncio.run(main())
```

## 错误处理

```python
from cphos_qdb import QBClient, QBNotFoundError, QBAuthError

with QBClient("http://localhost:8080") as client:
    client.login("bot_user", "bot_password")

    try:
        client.get_question("nonexistent-uuid")
    except QBNotFoundError as e:
        print(f"题目未找到: {e.message}")
    except QBAuthError:
        print("认证失败，请检查凭据")
```

## 异常类型

| 异常类 | HTTP 状态码 | 说明 |
|---|---|---|
| `QBValidationError` | 400 | 请求参数不合法 |
| `QBAuthError` | 401 | 认证失败或 token 过期 |
| `QBForbiddenError` | 403 | 权限不足 |
| `QBNotFoundError` | 404 | 资源不存在 |
| `QBConflictError` | 409 | 操作冲突 |
| `QBServerError` | 500/503 | 服务端错误 |
