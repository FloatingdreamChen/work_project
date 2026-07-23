# 实施计划

## Phase 0：项目初始化

- 创建 `backend`、`frontend`、`docs`、`scripts` 目录。
- 使用 uv 创建 `.venv`。
- 使用 Docker Compose 启动 PostgreSQL、Milvus、etcd、MinIO。
- 从 `.env.example` 复制 `.env`。

## Phase 1：后端基础

FastAPI 应用入口、配置读取、数据库连接、用户注册登录、统一响应结构、基础测试。

## Phase 2：用户画像与岗位数据

用户画像模型和接口、岗位表模型、岗位表导入脚本、岗位查询接口。

## Phase 3：知识库

文档解析、文本切分、embedding、Milvus collection 初始化、RAG 检索服务。

## Phase 4：Agent MVP

实现 `PositionMatchAgent`、`StudyPracticeAgent`、简单 orchestrator 和 `/api/chat` 接口。

## Phase 5：前端工作台

登录页、仪表盘、用户画像页、岗位匹配页、学习计划页、练习问答页。

## 建议启动命令

```bash
cd /Volumes/XD20/py_project/work_project
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
docker compose up -d
```
