# CPHOS Question Bank SDK

[![SDK Version](https://img.shields.io/badge/SDK-0.2.2-blue?logo=github)](https://github.com/CPHOS/cphos-qdb-sdk-python/releases)
[![Backend Compatibility](https://img.shields.io/badge/Backend-Question_DB%20%3E%3D%200.2.0-2ea44f?logo=github)](https://github.com/CPHOS/Question_DB)

面向 CPHOS 题库系统 bot 账号的 Python SDK，提供同步与异步两套客户端。

## 功能

- **完整 API 覆盖** — bot 可用的认证、题目、试卷、审阅人管理、Bundle 下载
- **同步 + 异步** — `QBClient`（同步）和 `AsyncQBClient`（异步）
- **自动 Token 刷新** — access token 过期时自动使用 refresh token 换新
- **自动版本协商** — 首次请求前自动校验后端 `/version` 与 SDK 兼容性
- **类型安全** — 所有响应使用 Pydantic v2 模型，完整类型提示
- **统一异常** — HTTP 错误码映射为语义化异常类

## 安装

从 GitHub 安装（推荐指定版本标签）：

```bash
uv add cphos-qdb@git+https://github.com/CPHOS/cphos-qdb-sdk-python.git@v0.2.2
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

### 版本化文档

文档站点使用 `mike` 管理多版本：

- 推送到 `main` 自动发布 `dev`
- 推送 `v*` tag 自动发布对应版本并更新 `latest`
- 可通过 workflow dispatch 手动发布指定版本

本地查看版本切换效果：

```bash
uv sync --group docs
uv run mike serve
```

### 版本兼容性

- 要求后端主版本与 SDK 兼容要求一致
- 在主版本一致前提下，后端版本需大于等于 SDK 声明的最低兼容后端版本
- 首次请求会自动检查 `/version`，不兼容时抛出 `QBVersionError`

后端项目：[Question_DB](https://github.com/CPHOS/Question_DB)

## 文档

- [快速开始](quickstart.md)
- [API 参考](api/client.md)
