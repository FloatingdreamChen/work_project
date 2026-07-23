# 考公 AI 助手

考公 AI 助手是一个面向公务员考试备考与岗位报考决策的本地 AI 项目前置方案。项目技术栈、工程拆分和启动方式参考 `/Users/chenshuaiwen/new_eduagent`，但业务领域改为公务员考试，并将 Agent 数量收敛为 1-2 个，便于从 0 构建、调试和迭代。

## 项目目标

- 帮助用户整理个人条件、筛选可报岗位、识别资格风险。
- 根据岗位目标、考试时间和用户基础生成备考计划。
- 支持行测、申论、面试等问答、练习、解析与复盘。
- 使用本地数据库和向量知识库承载岗位表、公告、考试大纲、政策文件、题库与用户学习记录。

## 核心 Agent

1. `PositionMatchAgent`：岗位匹配、资格审查、冲稳保推荐、风险解释。
2. `StudyPracticeAgent`：学习计划、知识问答、题目解析、申论批改、面试模拟。

## 技术栈

- 后端：Python 3.11、FastAPI、LangGraph、LangChain、SQLAlchemy Async、PostgreSQL。
- 知识库：Milvus、BGE-M3、BGE-Reranker。
- 前端：Vue 3、Vite、TypeScript、Pinia、Vue Router、Element Plus。
- 部署：Docker Compose、uv、本地 `.venv`。

## 目录说明

```text
work_project/
  backend/                 # 后端代码预留目录
  frontend/                # 前端代码预留目录
  docs/                    # 项目前置设计文档
  scripts/                 # 数据库与知识库脚本
  AGENTS.md                # AI 编程代理协作约束
  requirements.txt         # Python 依赖
  docker-compose.yml       # 本地基础服务
  .env.example             # 环境变量模板
  .gitignore               # Git 忽略规则
```

## 当前阶段

本目录已从“项目前置文件包”推进为最小可运行工程雏形：

- `backend/`：FastAPI 分层结构，包含认证、用户画像、岗位导入/检索/匹配、AI 聊天入口和练习批改接口。
- `frontend/`：Vue 3 + Vite + TypeScript + Pinia + Element Plus 工作台，首屏直接提供画像、岗位匹配、AI 问答和练习批改。
- `backend/agents/position_match/`：`PositionMatchAgent`，用确定性规则输出匹配度、资格风险和人工核验项。
- `backend/agents/study_practice/`：`StudyPracticeAgent`，提供备考计划和练习批改的首版规则实现。
- `backend/tests/`：Agent 最小单测。

## 本地启动

1. 启动基础服务：

```bash
docker compose up -d postgres etcd minio milvus
```

2. 创建 Python 环境并安装依赖：

```bash
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt
```

3. 启动后端：

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

4. 启动前端：

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：`http://localhost:3000`。首次使用可在登录页输入用户名和密码，先点“注册”，再登录。

## 验证

当前已通过：

```bash
python -m compileall backend
python -m pytest backend/tests
```

如本机已有旧项目同技术栈环境，也可以直接用该 Python 环境运行本项目；但不要修改旧项目目录下的任何文件。
