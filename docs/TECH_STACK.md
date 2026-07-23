# 技术栈

本项目沿用参考项目 `/Users/chenshuaiwen/new_eduagent` 的主技术栈，减少新项目搭建风险。

## Backend

- Python 3.11
- FastAPI
- Uvicorn
- Pydantic v2
- SQLAlchemy Async
- asyncpg
- python-jose
- passlib + bcrypt

## Agent

- LangGraph：管理 Agent 状态流转。
- LangChain：LLM、工具调用、提示词和检索链。
- OpenAI-compatible API：优先兼容 DeepSeek、OpenAI 等接口格式。

## Knowledge Base

- Milvus：向量存储。
- BGE-M3：文本向量模型。
- BGE-Reranker：召回结果重排。
- PyMuPDF、python-docx：PDF 和 Word 文档解析。

## Frontend

- Vue 3
- Vite
- TypeScript
- Pinia
- Vue Router
- Element Plus

## Infra

- Docker Compose
- PostgreSQL
- Milvus
- etcd
- MinIO
- uv + `.venv`

## 端口约定

- 后端：`8000`
- 前端：`3000`
- PostgreSQL：`5434`
- Milvus：`19532`
- MinIO：`9002`
