# 考公 AI 助手项目总览

本文档用于完整理解当前项目的定位、框架、功能、Agent、模型、兜底机制、数据流和后续建设方向。

项目根目录：

```text
/Volumes/XD20/py_project/work_project
```

参考项目：

```text
/Users/chenshuaiwen/new_eduagent
```

参考项目只允许读取和借鉴，严禁修改、删除、移动或覆盖其中任何文件。

## 1. 项目定位

本项目是“考公 AI 助手”，面向公务员考试用户，核心目标是帮助用户完成：

- 岗位匹配
- 资格风险检查
- 报考材料准备建议
- 备考计划生成
- 行测、申论、面试练习辅助
- 题目解析、申论批改、面试模拟和追问

项目不是官方招录系统，不能替代招录机关资格审核，也不能承诺“必上岸”“保证进面”“保证录取”。

## 2. 当前实现状态

当前项目已经从前置文档包推进为一个最小可运行工程雏形。

已经实现：

- FastAPI 后端应用入口
- 统一 API 路由
- 统一响应结构
- 用户注册、登录、JWT 鉴权
- 用户画像读取和保存
- 岗位数据批量导入
- 岗位列表查询
- 岗位匹配接口
- AI 聊天入口
- 练习批改接口
- 个性化备考计划接口
- 阶段练习报告接口
- `PositionMatchAgent` 规则版 + LLM 解释增强
- `StudyPracticeAgent` 规则版 + LLM 批改增强
- OpenAI-compatible LLM 工厂
- 自动重试、Agent 降级、系统兜底三层兜底雏形
- 知识库检索 MCP 工具
- 联网搜索 MCP 工具
- PositionMatchAgent 多节点 LangGraph 基础流
- StudyPracticeAgent 多节点 LangGraph 基础流
- 轻量知识库构建脚本
- CSV/XLSX 岗位导入脚本
- 可选参考模型复制脚本
- Vue 3 前端工作台
- Agent 最小测试

本轮 1-9 步优化后新增/增强：

- 本地模型状态探测：可识别 BGE-M3、BGE-Reranker、classifier、finetuned classifier 是否存在。
- Milvus RAG 链路：已提供 collection 初始化、知识库 chunk 构建、dense+sparse hybrid search、reranker 精排入口。
- 本地语义 RAG 兜底：Milvus 不可用时，可用 BGE-M3 对本地知识库 chunk 做 dense 检索，并缓存 embedding。
- Query classifier：已接入本地 classifier/finetuned classifier，并基于项目内岗位/备考样本完成一次轻量针对训练。
- AI 问答路由：先做细粒度问题分类，覆盖日常问答、岗位匹配、备考计划、练习批改、面试模拟、知识问答、问题优化和模糊查询；明确意图不再进入本地 classifier 慢路径。
- LangGraph Agent：两个 Agent 均为多节点图，支持画像累积、上下文记忆、长期记忆、知识检索、联网检索、规则结果、LLM 解释、合规检查和节点级失败降级。
- 个性化备考计划：不再固定四周模板，按考试日期、每日小时、每周天数、基础水平、薄弱模块、当前分数动态生成；少于 90 天会提示参考价值不足。
- 练习长期分析：保存练习指标、申论维度分、错题记录，并提供阶段报告和错题查询。
- 岗位匹配：增加专业目录标准化、相关专业核验、竞争比、招录人数、往年分数、地区偏好、风险偏好和政策依据。
- 联网搜索：Tavily/DuckDuckGo 降级，搜索结果带 provider、domain、credibility、published_at、imported_at 和来源审计。
- 前端工作台：增加匹配策略、政策依据展示、知识库状态/检索、练习历史/错题、AI 问答问题分类/路由/降级/来源状态展示、统一错误提示。
- 数据库层：增加 ORM model 映射、Alembic 骨架、导入审计表、知识库表、联网来源审计表和关键索引。
- 安全合规：增加禁止承诺/伪造材料清洗、日志敏感信息脱敏和对应测试。
- 测试体系：后端单元测试覆盖 Agent、RAG、图记忆、岗位匹配、导入解析、联网来源质量、数据库 schema、练习服务和合规模块；前端使用 TypeScript + Vite 构建验证。

仍需依赖环境或后续增强：

- 当前项目根目录已放入 BGE-M3、BGE-Reranker、classifier、finetuned classifier。默认路径为 `models/...`。
- Milvus hybrid search 和 reranker 精排需要 Milvus 服务，并设置 `ENABLE_LOCAL_MODELS=true`、`ENABLE_MILVUS_RAG=true`；Milvus 不可用时可继续走本地 BGE-M3 语义检索或关键词兜底。
- LLM 工具调用目前由 LangGraph 节点编排工具调用，不是完整 ReAct AgentExecutor 自主选择工具。
- 图记忆已支持进程内 memory，新增 PostgreSQL/Redis 可选后端；长期摘要策略和 LangGraph 原生 checkpointer 仍可继续增强。
- 前端仍以一个工作台承载功能，后续可以拆成独立路由页面。

## 3. 技术栈

后端：

- Python 3.11
- FastAPI
- Uvicorn
- Pydantic v2
- Pydantic Settings
- SQLAlchemy Async
- asyncpg
- python-jose
- passlib + bcrypt

Agent 和 LLM 规划：

- LangGraph
- LangChain
- OpenAI-compatible API
- DeepSeek / OpenAI / 其他兼容服务

RAG 规划：

- Milvus
- BGE-M3
- BGE-Reranker
- PyMuPDF
- python-docx

前端：

- Vue 3
- Vite
- TypeScript
- Pinia
- Vue Router
- Element Plus
- Axios

基础设施：

- Docker Compose
- PostgreSQL
- Milvus
- etcd
- MinIO
- uv
- 本地 `.venv`

## 4. 目录结构

```text
work_project/
  backend/
    main.py                     # FastAPI 应用入口
    config.py                   # 环境变量和配置
    dependencies.py             # FastAPI 依赖注入，当前主要是鉴权和 DB
    api/
      router.py                 # API 总路由
      v1/
        auth.py                 # 注册、登录、当前用户
        profiles.py             # 用户画像
        positions.py            # 岗位导入、查询、匹配
        chat.py                 # AI 聊天统一入口
        practice.py             # 练习批改
    agents/
      position_match/
        state.py                # 岗位匹配图状态
        nodes.py                # 岗位匹配图节点
        graph.py                # 岗位匹配 LangGraph 编排
        agent.py                # 岗位匹配规则与 LLM 解释能力
      study_practice/
        state.py                # 备考练习图状态
        nodes.py                # 备考练习图节点
        graph.py                # 备考练习 LangGraph 编排
        agent.py                # 备考练习规则与 LLM 批改能力
    core/
      orchestrator.py           # 简单 Agent 路由器
      responses.py              # 统一响应结构
      security.py               # 密码哈希、JWT
      logger.py                 # 日志初始化
    db/
      session.py                # SQLAlchemy async engine/session
      migrations.py             # 启动时执行 init_db.sql
    services/
      profile_service.py        # 用户画像数据库服务
      position_service.py       # 岗位数据库服务
      practice_service.py       # 练习记录数据库服务
    schemas/
      *.py                      # Pydantic 请求/响应模型
    models/
      __init__.py               # ORM 模型预留
    tests/
      test_agents.py            # Agent 最小测试

  frontend/
    package.json
    vite.config.ts
    src/
      main.ts
      App.vue
      router/index.ts
      stores/auth.ts
      api/
        client.ts               # Axios 客户端
        govExam.ts              # 业务 API 封装
      components/layout/
        AppShell.vue            # 主工作台布局
      views/
        LoginView.vue           # 登录/注册页
        WorkbenchView.vue       # 画像、岗位匹配、问答、批改工作台
      styles.css                # 全局样式

  scripts/
    init_db.sql                 # PostgreSQL 初始化 SQL
    import_positions.py         # CSV/XLSX 岗位表导入
    build_knowledge_base.py     # 轻量知识库 chunk 构建
    copy_reference_models.py    # 可选复制参考项目本地模型

  docs/                         # 设计文档
  docker-compose.yml            # PostgreSQL、Milvus、etcd、MinIO
  requirements.txt              # Python 完整依赖
  README.md                     # 启动说明
  AGENTS.md                     # AI 编程代理工作约束
```

## 5. 后端框架

后端入口是：

```text
backend/main.py
```

应用启动时会做三件事：

1. 初始化日志
2. 尝试执行 `scripts/init_db.sql`
3. 挂载 `/api/v1` 业务路由

健康检查接口：

```text
GET /health
```

业务接口统一挂载在：

```text
/api/v1
```

统一响应结构：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

## 6. API 功能

### 6.1 Auth

文件：

```text
backend/api/v1/auth.py
```

接口：

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

当前能力：

- 用户名 + 邮箱注册
- bcrypt 密码哈希
- 密码策略：至少 8 位，必须包含大小写字母和数字
- JWT access token 登录
- refresh token 刷新和过期处理
- Bearer Token 鉴权
- 角色权限：`admin` / `user`
- 登录失败次数限制：连续失败 5 次会临时锁定
- 管理操作可使用 `get_current_admin` 限制权限

### 6.2 用户画像

文件：

```text
backend/api/v1/profiles.py
backend/services/profile_service.py
```

接口：

```text
GET /api/v1/profiles/me
PUT /api/v1/profiles/me
```

画像字段：

- 目标考试
- 目标地区
- 学历
- 学位
- 专业
- 毕业年份
- 应届身份
- 政治面貌
- 户籍
- 基层经历
- 工作年限
- 证书

安全原则：

- 不采集身份证号
- 不采集准考证号
- 不采集手机号等非必要敏感信息
- 日志不应输出完整个人画像

### 6.3 岗位

文件：

```text
backend/api/v1/positions.py
backend/services/position_service.py
```

接口：

```text
GET  /api/v1/positions
POST /api/v1/positions/import
POST /api/v1/positions/match
```

当前能力：

- 通过 JSON 批量导入岗位
- 按年份、考试类型、省份、关键词查询岗位
- 根据用户画像和岗位条件生成匹配结果
- 保存匹配报告

当前限制：

- XLSX 导入依赖运行环境安装 `openpyxl`
- 专业目录已做小型目录标准化和相关专业核验，但还不是完整教育部专业目录库
- Milvus/BGE 生产级 RAG 需要先启动 Milvus，并用 `scripts/build_knowledge_base.py --upsert-milvus` 入库

### 6.4 Chat

文件：

```text
backend/api/v1/chat.py
backend/core/orchestrator.py
```

接口：

```text
POST /api/v1/chat
```

当前能力：

- 岗位、报名、资格、专业、备考、申论、行测、面试等明确关键词先走快速路由，避免前端首次问答加载本地 classifier 导致慢启动。
- 关键词无法明确区分时，再使用本地 finetuned classifier 判断用户问题属于岗位方向还是备考方向。
- classifier 不可用或低置信时回退默认备考 Agent。
- 路由到对应 LangGraph Agent
- 岗位类问题进入 `PositionMatchAgent` 图
- 备考类问题进入 `StudyPracticeAgent` 图
- 有 API Key 时由 LLM 基于图状态、知识库和工具结果生成回答
- LLM 失败时回落到图内规则回答和三层兜底
- 同一 `conversation_id` 下会保存 recent turns、画像、弱项、当前分数等上下文记忆
- `GRAPH_MEMORY_BACKEND=postgres` 时写入 `conversation_memories` 表；`redis` 时写入 Redis；默认使用进程内 memory

### 6.5 Practice

文件：

```text
backend/api/v1/practice.py
backend/agents/study_practice/agent.py
backend/services/practice_service.py
```

接口：

```text
POST /api/v1/practice/review
```

当前能力：

- 支持行测、申论、面试三个练习类型
- 根据答案长度、结构词、公共治理表达做规则批改
- 输出评分、优点、问题、优化示例、下一步建议
- 保存练习 session 和 review
- 支持面试多轮追问状态，保存 `interview_sessions.stage / turns / summary`

当前限制：

- 不是 LLM 深度批改
- 不支持材料级申论批改
- 面试追问状态已持久化，但还可以继续加入更细的面试评分量表

## 7. Agent 设计

本项目只设计 1-2 个 Agent，不复刻参考项目的多 Agent 复杂度。

### 7.1 PositionMatchAgent

文件：

```text
backend/agents/position_match/state.py
backend/agents/position_match/nodes.py
backend/agents/position_match/graph.py
backend/agents/position_match/agent.py
```

目标：

- 解析用户画像
- 匹配岗位硬性条件
- 输出匹配度
- 输出资格风险
- 输出人工核验项
- 给出“冲、稳、保、不建议”分类

当前输入：

- 用户画像 dict
- 岗位列表 dict

当前输出：

```json
{
  "agent": "PositionMatchAgent",
  "disclaimer": "本结果不是官方资格审核结论...",
  "items": [
    {
      "position": {},
      "tier": "冲/稳/保/不建议",
      "score": 85,
      "matched": [],
      "risks": [],
      "verification": [],
      "rationale": "..."
    }
  ],
  "sources": []
}
```

当前规则：

- 学历匹配
- 学位匹配
- 专业匹配
- 政治面貌匹配
- 户籍匹配
- 工作年限匹配
- 基层经历匹配
- 信息缺失时进入人工核验项
- 明确不满足时进入风险项

重要合规约束：

- 不把 AI 判断描述为官方审核结论
- 不建议用户伪造材料
- 数据不足时提示人工核验
- 强时效岗位信息必须保留来源

LangGraph 节点流：

```text
parse_profile
  -> ask_clarification 或 retrieve_positions
  -> check_hard_conditions
  -> retrieve_policy
  -> rank_positions
  -> generate_answer
  -> compliance_check
```

节点职责：

- `parse_profile`：从用户问题提取学历、专业、应届身份、政治面貌、年份、地区等信息。
- `ask_clarification`：画像缺失严重时先追问，不强行匹配。
- `retrieve_positions`：读取已导入岗位，或使用传入岗位列表。
- `check_hard_conditions`：执行岗位硬性条件规则匹配。
- `retrieve_policy`：检索本地知识库，必要时触发联网搜索。
- `rank_positions`：生成冲、稳、保、不建议的结构化摘要。
- `generate_answer`：有 API Key 时调用 LLM 解释匹配结果；失败时使用规则回答。
- `compliance_check`：移除不合规承诺，补充官方审核免责声明。

### 7.2 StudyPracticeAgent

文件：

```text
backend/agents/study_practice/state.py
backend/agents/study_practice/nodes.py
backend/agents/study_practice/graph.py
backend/agents/study_practice/agent.py
```

目标：

- 生成备考计划
- 支持行测解析
- 支持申论批改
- 支持面试建议
- 根据练习记录给出下一步建议

当前能力：

- 规则版练习批改
- 有 API Key 时使用 LLM 深度批改
- 检索本地知识库片段作为上下文
- 根据考试日期、每日学习时间、每周学习天数、基础水平、薄弱模块、目标岗位生成个性化计划
- 备考计划最短按90天/13周起步，少于三个月会提示参考价值不足并压缩执行
- 输出模块权重、阶段目标、周计划、每日模板、里程碑和动态调整规则
- 根据近阶段练习记录生成阶段报告、均分、问题关键词和下一步建议
- 按练习类型给出不同 next steps

当前限制：

- 已有错题记录、练习指标和 conversation memory；还可继续增强长期摘要策略
- StudyPracticeAgent 已支持节点级人工中断；LangGraph 原生 checkpointer 通过 `ENABLE_LANGGRAPH_CHECKPOINTS` 可选启用

LangGraph 节点流：

```text
classify_task
  -> retrieve_material
  -> build_plan 或 review_answer
  -> generate_response
  -> compliance_check
  -> save_learning_record
```

节点职责：

- `classify_task`：判断用户是要计划、批改、面试建议还是普通问答。
- `retrieve_material`：检索本地知识库片段作为上下文。
- `build_plan`：生成个性化备考计划，按考试日期倒排并保证三个月起步。
- `review_answer`：生成规则版练习批改。
- `generate_response`：有 API Key 时调用 LLM 综合输出；失败时使用规则回答。
- `compliance_check`：移除结果承诺和作弊风险表达，补充合规提示。
- `save_learning_record`：预留图内保存节点，当前 API 层仍负责真实练习记录入库。

## 8. 当前兜底机制

当前项目已经实现三层兜底雏形，位置：

```text
backend/core/retry.py
```

已经存在的基础兜底：

1. 自动重试
   - LLM、工具、Milvus 等可重试错误会按配置重试
   - 配置项：`LLM_MAX_RETRIES`、`LLM_TIMEOUT_SECONDS`

2. Agent 级降级
   - `position_match` 失败时返回岗位规则匹配提示
   - `study_practice` 失败时返回结构化备考建议

3. 系统级兜底
   - Agent 降级也失败时返回统一服务不可用提示
   - 不向用户暴露内部异常细节

4. Agent 路由默认兜底
   - `AgentOrchestrator.route()` 根据关键词判断 Agent
   - 无法识别时默认进入 `StudyPracticeAgent`

5. 规则版 Agent 兜底
   - 当前两个 Agent 都不依赖 LLM
   - 即使没有模型 API key，也能返回基础结果

6. 岗位资格不确定兜底
   - 数据不足或规则无法判断时，不强行给结论
   - 输出 `verification` 人工核验项

仍需增强的兜底：

1. LLM 层兜底
   - 已有 LLM 工厂和重试
   - 仍需实现多个 provider/base_url 自动轮换

2. Agent 层兜底
   - 已有 Agent 级降级文本
   - 仍需做 LangGraph 节点级备用节点和状态恢复

3. RAG 层兜底
   - 第一层：Milvus dense + sparse hybrid search
   - 第二层：BGE-Reranker 精排
   - 第三层：Milvus 不可用时走本地 BGE-M3 dense 检索
   - 第四层：模型或向量服务不可用时走本地关键词检索
   - 每条结果返回 `confidence`、`is_high_confidence`、`retriever` 元数据

建议后续新增文件：

```text
backend/core/fallback.py
backend/agents/position_match/tools.py
backend/agents/study_practice/tools.py
```

## 9. 模型设计

### 9.1 当前模型状态

当前项目已经具备真实 LLM 调用入口。

调用位置：

```text
backend/core/llm_factory.py
```

有 `OPENAI_API_KEY` 时：

- `/api/v1/chat` 会优先调用 OpenAI-compatible LLM
- 练习批改会优先调用 LLM 深度批改
- 岗位匹配可使用 LLM 解释规则匹配结果

没有 `OPENAI_API_KEY` 或 LLM 调用失败时：

- 自动进入 retry / Agent fallback / system fallback
- 规则版 Agent 继续提供基础能力

### 9.2 规划中的 LLM

环境变量：

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
```

默认规划：

```text
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

设计目标：

- 兼容 DeepSeek
- 兼容 OpenAI
- 兼容其他 OpenAI-compatible 服务

当前抽象：

```text
LLMFactory
  - ainvoke()
  - _ainvoke_langchain()
  - _ainvoke_http()
```

### 9.3 当前 embedding、rerank 和 classifier

Embedding：

```text
models/embedding/bge-m3
```

Reranker：

```text
models/reranker/bge-reranker-large
```

Classifier：

```text
models/classifier/all-MiniLM-L6-v2
models/classifier/query-classifier-finetuned
```

用途：

- 公告
- 岗位表说明
- 招考政策
- 专业目录
- 考试大纲
- 题库解析
- 申论材料
- 面试题库

当前状态：

- 依赖已写入 `requirements.txt`
- `scripts/build_knowledge_base.py` 支持本地 chunk 构建、写入 PostgreSQL、写入 Milvus
- `backend/core/knowledge_base.py` 支持 Milvus hybrid search、本地 BGE-M3 dense 检索、关键词兜底
- `backend/core/reranker.py` 支持 BGE-Reranker 精排
- `backend/core/query_classifier.py` 支持本地 classifier 语义路由
- `scripts/train_query_classifier.py` 已支持基于 `data/training/query_intents.jsonl` 做岗位/备考意图针对训练
- 本轮已执行一次 1 epoch 轻量训练，输出到 `models/classifier/query-classifier-finetuned`

## 10. 数据库设计

初始化文件：

```text
scripts/init_db.sql
```

并发与连接池：

- `backend/db/session.py` 使用 SQLAlchemy async engine 连接池。
- 配置项：`DB_POOL_SIZE`、`DB_MAX_OVERFLOW`、`DB_POOL_TIMEOUT`。
- `backend/core/concurrency.py` 提供请求并发限制中间件，配置项为 `REQUEST_CONCURRENCY_LIMIT`。
- 启动时会设置事件循环默认 `ThreadPoolExecutor`，配置项为 `WORKER_THREAD_POOL_SIZE`，用于密码哈希等阻塞任务。

核心表：

```text
users
user_profiles
positions
position_match_reports
practice_sessions
practice_reviews
```

### 10.1 users

保存用户基础账号信息。

关键字段：

- id
- username
- hashed_password
- is_active
- created_at
- updated_at

### 10.2 user_profiles

保存用户岗位匹配需要的画像。

关键字段：

- user_id
- target_exam
- target_region
- education
- degree
- major
- graduation_year
- fresh_graduate_status
- political_status
- household_region
- grassroots_experience
- work_years
- certificates

### 10.3 positions

保存结构化岗位表。

关键字段：

- exam_year
- exam_type
- province
- city
- department
- position_name
- position_code
- recruitment_count
- education_requirement
- degree_requirement
- major_requirement
- political_requirement
- grassroots_requirement
- work_years_requirement
- household_requirement
- remarks
- source_name
- source_url
- imported_at

### 10.4 position_match_reports

保存一次岗位匹配报告。

关键字段：

- user_id
- profile_snapshot
- result
- created_at

### 10.5 practice_sessions / practice_reviews

保存练习作答和批改结果。

## 11. 前端设计

前端入口：

```text
frontend/src/main.ts
```

当前页面：

```text
frontend/src/views/LoginView.vue
frontend/src/views/WorkbenchView.vue
```

布局组件：

```text
frontend/src/components/layout/AppShell.vue
```

API 封装：

```text
frontend/src/api/client.ts
frontend/src/api/govExam.ts
```

状态管理：

```text
frontend/src/stores/auth.ts
```

当前前端能力：

- 登录
- 注册
- 保存用户画像
- 导入样例岗位
- 查询岗位
- 发起岗位匹配
- 显示匹配结果、风险、人工核验项
- AI 问答，展示 Agent 路由、LLM/规则/系统降级状态、来源数量和会话 ID
- 练习批改

设计原则：

- 第一屏是工作台，不做营销页
- 面向反复使用的备考和报考流程
- 信息密度适中，方便扫描和比较
- 控件使用 Element Plus

## 12. 启动方式

### 12.1 后端依赖

项目已有 `.venv`，Python 版本是 3.11.3。

如果使用 uv 管理依赖，推荐：

```bash
uv pip install -r requirements.txt --python .venv/bin/python
```

查看当前 `.venv` 包：

```bash
uv pip list --python .venv/bin/python
```

说明：

当前 `.venv` 可能没有传统 pip 模块，因此：

```bash
python -m pip list
```

可能会提示：

```text
No module named pip
```

这不代表 uv 没法管理依赖。使用 `uv pip list --python .venv/bin/python` 更准确。

### 12.2 基础服务

```bash
docker compose up -d postgres etcd minio milvus
```

端口：

- PostgreSQL: `5434`
- Milvus: `19532`
- MinIO: `9002`
- 后端: `8000`
- 前端: `3000`

### 12.3 后端启动

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 12.4 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问：

```text
http://localhost:3000
```

## 13. 环境变量

模板：

```text
.env.example
```

关键配置：

```text
APP_NAME=GovExamAgent
APP_ENV=development
SECRET_KEY=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=postgresql+asyncpg://gov_exam:gov_exam_password@localhost:5434/gov_exam_agent
MILVUS_HOST=localhost
MILVUS_PORT=19532
MILVUS_COLLECTION=gov_exam_knowledge
OPENAI_API_KEY=replace-with-your-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
EMBEDDING_MODEL=BAAI/bge-m3
RERANK_MODEL=BAAI/bge-reranker-v2-m3
```

本地开发时建议复制：

```bash
cp .env.example .env
```

并修改：

```text
SECRET_KEY
OPENAI_API_KEY
DATABASE_URL
```

## 14. 合规和安全边界

项目必须遵守：

- 不承诺必上岸
- 不承诺保证进面
- 不承诺保证录取
- 不鼓励伪造学历
- 不鼓励伪造经历
- 不鼓励伪造党员身份
- 不鼓励伪造基层经历
- 不鼓励伪造证书
- 不将 AI 判断包装为官方审核结论
- 数据不足时必须提示人工核验
- 政策、公告、岗位表等强时效数据必须保留来源、发布日期和导入时间
- 用户个人信息最小化采集
- 敏感信息不得进入日志

当前代码已经体现：

- 岗位匹配结果包含免责声明
- 不确定项进入人工核验
- 练习建议不承诺考试结果
- 用户画像不包含身份证号、手机号等字段

后续仍需加强：

- 日志脱敏
- API 错误统一处理
- 权限角色控制
- Token 刷新和过期处理
- 数据导入来源校验
- RAG 来源引用强制化

## 15. 测试

当前测试文件：

```text
backend/tests/test_agents.py
```

当前覆盖：

- `PositionMatchAgent` 可以区分匹配岗位和风险岗位
- `StudyPracticeAgent` 可以返回批改结构
- 个性化备考计划会强制三个月起步，并按薄弱模块调整权重
- `StudyPracticeAgent` LangGraph 计划流可以产出结构化计划

运行：

```bash
python -m pytest backend/tests
```

当前已验证：

```text
2 passed
```

后续应增加：

- Auth API 测试
- Profile API 测试
- Position import/list/match API 测试
- Practice API 测试
- 数据库集成测试
- 前端构建测试
- LangGraph 原生 checkpointer 集成测试
- Milvus 真实服务集成测试

## 16. 后续建设路线

建议优先级：

1. 确认 `.venv` 依赖安装完成
2. 启动 PostgreSQL，验证注册、登录、画像保存
3. 启动前端，验证工作台操作闭环
4. 完成 CSV/XLSX 岗位表导入
5. 增加岗位匹配规则字段和专业目录核验
6. 增强 `LLMFactory` 的多 provider 自动切换
7. 增强 LangGraph 节点级兜底和状态恢复
8. 启动 Milvus 并批量导入真实政策/岗位/题库知识库
9. 扩充 query classifier 训练样本和评估集
10. 增加 ReAct 工具调用规划
11. 前端拆分真实页面
12. 增加日志、异常处理、测试和权限控制

## 17. 当前项目一句话总结

当前项目已经从“考公 AI 助手 MVP 工程骨架”推进到可运行的 Agent/RAG 工作台：后端、前端、数据库表、两个 LangGraph Agent、OpenAI-compatible LLM、MCP 工具、本地模型识别、Milvus hybrid RAG、本地 BGE-M3 语义兜底、关键词兜底、classifier 语义路由、上下文记忆和 PostgreSQL/Redis 长期记忆后端都已接入。下一步重点是导入真实知识库、跑 Milvus 集成验证、扩充训练集，并继续增强 ReAct 工具规划。
