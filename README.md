# cphos-qdb

Python SDK for CPHOS Question Bank API (bot account).

提供 `QBClient`（同步）和 `AsyncQBClient`（异步）两套客户端，覆盖题目 CRUD、试卷 CRUD、审阅人管理、Bundle 下载等全部 bot 可用接口。

## 安装

从 GitHub 安装（推荐指定版本标签）：

```bash
uv add cphos-qdb --git https://github.com/CPHOS/cphos-qdb-sdk-python.git --tag v0.1.0
```

安装最新 `main` 分支：

```bash
uv add cphos-qdb --git https://github.com/CPHOS/cphos-qdb-sdk-python.git
```

也可通过 pip 安装：

```bash
pip install git+https://github.com/CPHOS/cphos-qdb-sdk-python.git@v0.1.0
```

或从 [GitHub Releases](https://github.com/CPHOS/cphos-qdb-sdk-python/releases) 下载 `.whl` 文件后本地安装：

```bash
uv add ./cphos_qdb-0.1.0-py3-none-any.whl
```

## 快速使用

```python
from cphos_qdb import QBClient

with QBClient("http://localhost:8080") as client:
    client.login("bot_user", "bot_password")
    questions = client.list_questions(category="T", limit=10)
    for q in questions.items:
        print(q.question_id, q.description)
```

## 文档

推送到 `main` 分支后，GitHub Actions 会自动构建并部署文档到 GitHub Pages。

本地预览：

```bash
uv sync --group docs
uv run mkdocs serve
```
