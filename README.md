# cphos-qdb
<div align="center">
    <h1>cphos-qdb SDK</h1>
    <p>Python SDK for CPHOS Question Bank API (bot account)</p>
    <a href="https://github.com/CPHOS/cphos-qdb-sdk-python/releases"><img src="https://img.shields.io/badge/SDK-1.0.0-blue?logo=github" alt="SDK Version"></a>
    <a href="https://github.com/CPHOS/Question_DB"><img src="https://img.shields.io/badge/Backend-Question_DB%20%3E%3D%201.0.0-2ea44f?logo=github" alt="Backend Compatibility"></a>
</div>

提供 `QBClient`（同步）和 `AsyncQBClient`（异步）两套客户端，覆盖 bot 账号可用的认证、题目、试卷、审阅人管理和 Bundle 下载接口，并在首次请求时自动检查后端版本兼容性。

权限说明：SDK 不在客户端硬编码 bot 权限策略，具体可调用能力由后端鉴权规则最终判定。

## 安装

从 GitHub 安装（推荐指定版本标签）：

```bash
uv add cphos-qdb@git+https://github.com/CPHOS/cphos-qdb-sdk-python.git@v1.0.0
```

安装最新 `main` 分支：

```bash
uv add cphos-qdb@git+https://github.com/CPHOS/cphos-qdb-sdk-python.git
```

也可通过 pip 安装：

```bash
pip install git+https://github.com/CPHOS/cphos-qdb-sdk-python.git@v1.0.0
```

或从 [GitHub Releases](https://github.com/CPHOS/cphos-qdb-sdk-python/releases) 下载 `.whl` 文件后本地安装：

```bash
uv add ./cphos_qdb-1.0.0-py3-none-any.whl
```

## 快速使用

```python
from cphos_qdb import QBClient

with QBClient("http://localhost:8080", access_token="bot-token-xxx") as client:
    print(client.version().version)
    questions = client.list_questions(category="T", limit=10)
    for q in questions.items:
        print(q.question_id, q.description)

    created = client.create_question(
        "path/to/question.zip",
        description="热学标定 gamma",
        category="T",
        tags=["thermodynamics"],
    )

    client.update_question_status(created.question_id, "reviewed")
    client.update_question_tags(created.question_id, ["thermodynamics", "optics"])
    client.update_question_author(created.question_id, "张三")
    client.update_question_reviewer_names(created.question_id, ["李四", "王五"])
    client.create_question_difficulty(created.question_id, "human", 7, notes="较难")
```

## 开发

### 文档

文档使用 `mike` 进行版本化发布，支持在站点中切换不同版本。

- 推送到 `main`：自动发布 `dev`（并更新 `latest` 别名）
- 推送 `v*` tag（如 `v1.0.0`）：自动发布对应版本并更新 `latest`
- `workflow_dispatch`：可手动输入版本号发布

首次启用时，请将仓库 GitHub Pages 来源设置为：`gh-pages` 分支 / 根目录。

本地预览：

```bash
uv sync --group docs
uv run mkdocs serve
```

本地版本化预览：

```bash
uv run mike serve
```

### 单元测试

测试使用 [pytest](https://docs.pytest.org/) + [respx](https://lundberg.github.io/respx/) 模拟 HTTP 请求，覆盖异常、模型、传输层、认证、题目、试卷及客户端全部模块。

```bash
uv sync --group test
uv run pytest tests/ -v
```

### 版本兼容性

- 主版本号必须一致
- 在主版本一致前提下，后端版本必须大于等于 SDK 声明的最低兼容后端版本
- 首次请求前会自动调用 `/version` 检查，不兼容时抛出 `QBVersionError`

后端项目：[Question_DB](https://github.com/CPHOS/Question_DB)
