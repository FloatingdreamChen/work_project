# 考公 AI 助手

考公 AI 助手是一个面向公务员考试备考与岗位报考决策的本地 AI 项目前置方案。项目技术栈、工程拆分和启动方式参考 `/Users/chenshuaiwen/new_eduagent`，但业务领域改为公务员考试，并将 Agent 数量收敛为 1-2 个，便于从 0 构建、调试和迭代。

## 项目目标

- 记录。帮助用户整理个人条件、筛选可报岗位、识别资格风险。
- 根据岗位目标、考试时间和用户基础生成备考计划。
- 支持行测、申论、面试等问答、练习、解析与复盘。
- 使用本地数据库和向量知识库承载岗位表、公告、考试大纲、政策文件、题库与用户学习

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
  backend/                 # FastAPI、LangGraph Agent、RAG、MCP、服务层和测试
  frontend/                # Vue 3 工作台
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

- `backend/`：FastAPI 分层结构，包含认证、用户画像、岗位导入/检索/匹配、知识库、AI 聊天入口、备考计划、练习批改、练习报告和错题接口。
- `frontend/`：Vue 3 + Vite + TypeScript + Pinia + Element Plus 工作台，提供画像、岗位匹配、AI 问答、练习批改、个性化计划、知识库检索和练习历史。
- `backend/agents/position_match/`：`PositionMatchAgent`，规则匹配保证结构化结果，有 API Key 时使用 LLM 生成解释和建议。
- `backend/agents/study_practice/`：`StudyPracticeAgent`，规则批改兜底，有 API Key 时使用 LLM 做深度批改。
- `backend/agents/*/state.py`、`nodes.py`、`graph.py`：两个 Agent 均已按 LangGraph 的状态、节点、图编排拆分。
- `POST /api/v1/practice/plan`：根据考试日期、学习时间、基础水平和薄弱模块生成个性化备考计划，最短三个月起步。
- `POST /api/v1/practice/report`：基于近阶段练习记录生成学习报告和调整建议。
- `backend/core/retry.py`：三层兜底雏形，包含自动重试、Agent 级降级、系统级兜底。
- `backend/mcp/`：知识库检索和联网搜索 MCP 工具服务，联网结果带可信度、发布日期和导入时间元数据。
- `backend/models/`、`backend/db/alembic/`：ORM model 映射与 Alembic 迁移骨架。
- `models/`：本地 BGE-M3、BGE-Reranker、classifier、finetuned classifier 模型目录。
- `scripts/train_query_classifier.py`：基于项目内岗位/备考样本对 query classifier 做轻量针对训练。
- `backend/tests/`：覆盖 Agent、RAG、图记忆、岗位匹配、导入解析、联网来源质量、数据库 schema、练习服务和合规模块。

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

需要从局域网访问时，推荐使用只绑定真实 LAN 网卡的启动方式：

```bash
cd frontend
npm run dev:lan
```

它会自动选择非 VPN、非 bridge 的 IPv4，并打印唯一推荐地址，例如 `http://192.168.40.183:3000`。

前端默认地址：`http://localhost:3000`。后端和前端需要分别占用一个终端持续运行，不能启动后关闭终端。

如果页面打不开，先检查端口是否真的在监听：

```bash
lsof -nP -iTCP:3000 -sTCP:LISTEN
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

`3000` 没有输出表示前端没有启动；`8000` 没有输出表示后端没有启动。Vite 打印的多个 `Network` 地址只是本机网卡列表，只有与访问设备处于同一局域网的真实 IP 才能从其他设备打开。

也可以运行项目内诊断脚本：

```bash
bash scripts/check_lan_access.sh
```

当前前端配置已启用 `host: true` 和 `allowedHosts: true`。如果 `localhost` 可以打开但 `Network` 地址打不开，优先选择脚本输出的非 VPN、非 bridge 的 `LAN` 地址；`ppp`、`utun`、`bridge` 网卡地址通常不能作为普通局域网访问地址。

首次使用可在登录页输入用户名和密码，先点“注册”，再登录。

## 验证

当前已通过：

```bash
python -m compileall backend scripts
python -m pytest backend/tests
cd frontend
npm run build
```

模型状态检查和 classifier 训练命令见 `TESTING.md`。

更完整的验证说明见 `TESTING.md`。

如本机已有旧项目同技术栈环境，也可以直接用该 Python 环境运行本项目；但不要修改旧项目目录下的任何文件。
