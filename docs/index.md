# CPHOS Question Bank SDK

面向 CPHOS 题库系统 bot 账号的 Python SDK，提供同步与异步两套客户端。

## 功能

- **完整 API 覆盖** — 题目 CRUD、试卷 CRUD、审阅人管理、Bundle 下载
- **同步 + 异步** — `QBClient`（同步）和 `AsyncQBClient`（异步）
- **自动 Token 刷新** — access token 过期时自动使用 refresh token 换新
- **类型安全** — 所有响应使用 Pydantic v2 模型，完整类型提示
- **统一异常** — HTTP 错误码映射为语义化异常类

## 安装

从 GitHub 安装（推荐指定版本标签）：

```bash
uv add cphos-qdb@git+https://github.com/CPHOS/cphos-qdb-sdk-python.git@v0.1.0
```

安装最新 `main` 分支：

```bash
uv add cphos-qdb@git+https://github.com/CPHOS/cphos-qdb-sdk-python.git
```

也可从 [GitHub Releases](https://github.com/CPHOS/cphos-qdb-sdk-python/releases) 下载 `.whl` 文件后本地安装。

## 开发

### 单元测试

测试使用 [pytest](https://docs.pytest.org/) + [respx](https://lundberg.github.io/respx/) 模拟 HTTP 请求，覆盖全部模块。

```bash
uv sync --group test
uv run pytest tests/ -v
```

## 文档

- [快速开始](quickstart.md)
- [API 参考](api/client.md)
