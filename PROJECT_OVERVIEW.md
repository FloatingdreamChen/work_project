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
- `PositionMatchAgent` 规则版
- `StudyPracticeAgent` 规则版
- Vue 3 前端工作台
- Agent 最小测试

尚未完整实现：

- LangGraph 显式状态图
- OpenAI-compatible LLM 调用
- LLM 工厂
- 三层兜底机制
- Milvus RAG 检索服务
- BGE-M3 embedding 接入
- BGE-Reranker 接入
- 岗位表 CSV/XLSX 文件解析导入
- 前端多页面拆分和复杂交互
- 完整日志、审计、异常追踪
- 数据库 ORM model 层

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
        agent.py                # 岗位匹配 Agent
      study_practice/
        agent.py                # 备考练习 Agent
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
    import_positions.py         # 岗位表导入脚本占位
    build_knowledge_base.py     # 知识库构建脚本占位

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
GET  /api/v1/auth/me
```

当前能力：

- 用户名注册
- bcrypt 密码哈希
- JWT 登录
- Bearer Token 鉴权

当前限制：

- 没有角色权限
- 没有邮箱、手机号
- 没有刷新 token
- 没有登录失败次数限制

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

- `scripts/import_positions.py` 还只是占位
- 暂不支持直接解析 CSV/XLSX 岗位表
- 专业目录只做字符串规则判断
- 没有接公告政策 RAG

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

- 根据关键词判断用户问题属于岗位方向还是备考方向
- 路由到对应 Agent 名称
- 返回规则模板回答

当前限制：

- 未接入真实 LLM
- 未接入 LangGraph
- 未接入上下文记忆
- 未接入 RAG 来源引用

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

当前限制：

- 不是 LLM 深度批改
- 不支持材料级申论批改
- 不支持面试多轮追问状态

## 7. Agent 设计

本项目只设计 1-2 个 Agent，不复刻参考项目的多 Agent 复杂度。

### 7.1 PositionMatchAgent

文件：

```text
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

### 7.2 StudyPracticeAgent

文件：

```text
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
- 规则版四周备考计划
- 按练习类型给出不同 next steps

当前限制：

- 没有真实 LLM
- 没有知识库检索
- 没有错题长期记忆
- 没有 LangGraph 状态流

## 8. 当前兜底机制

当前项目没有完整的“三层兜底机制”。

已经存在的基础兜底：

1. Agent 路由默认兜底
   - `AgentOrchestrator.route()` 根据关键词判断 Agent
   - 无法识别时默认进入 `StudyPracticeAgent`

2. 规则版 Agent 兜底
   - 当前两个 Agent 都不依赖 LLM
   - 即使没有模型 API key，也能返回基础结果

3. 岗位资格不确定兜底
   - 数据不足或规则无法判断时，不强行给结论
   - 输出 `verification` 人工核验项

尚未实现的三层兜底：

1. LLM 层兜底
   - 主模型失败后切备用模型
   - 主 base_url 失败后切备用 base_url
   - LLM 超时后降级短回答

2. Agent 层兜底
   - LangGraph 节点失败后走备用节点
   - 工具调用失败后返回结构化错误
   - 多轮状态损坏后恢复到安全状态

3. RAG 层兜底
   - Milvus 不可用时走无检索回答
   - embedding 失败时走关键词检索
   - reranker 失败时直接使用召回结果
   - 无来源时提示“资料不足，需人工核验”

建议后续新增文件：

```text
backend/core/retry.py
backend/core/llm_factory.py
backend/core/fallback.py
backend/core/knowledge_base.py
backend/core/reranker.py
backend/agents/position_match/graph.py
backend/agents/study_practice/graph.py
```

## 9. 模型设计

### 9.1 当前模型状态

当前项目尚未接入真实 LLM。

当前回答来自：

- Python 规则判断
- 固定模板
- 简单关键词路由

因此当前不需要 `OPENAI_API_KEY` 也能跑基础功能。

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

后续建议抽象：

```text
LLMFactory
  - get_chat_model()
  - get_coder_model()
  - get_fallback_model()
  - clear_cache()
```

### 9.3 规划中的 embedding 和 rerank

Embedding：

```text
BGE-M3
```

Reranker：

```text
BGE-Reranker
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
- 脚本 `scripts/build_knowledge_base.py` 仍是占位
- 后端尚未实现 Milvus collection 初始化和检索服务

## 10. 数据库设计

初始化文件：

```text
scripts/init_db.sql
```

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
- AI 问答
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
- Agent 兜底测试
- RAG 检索失败测试

## 16. 后续建设路线

建议优先级：

1. 确认 `.venv` 依赖安装完成
2. 启动 PostgreSQL，验证注册、登录、画像保存
3. 启动前端，验证工作台操作闭环
4. 完成 CSV/XLSX 岗位表导入
5. 增加岗位匹配规则字段和专业目录核验
6. 引入 `LLMFactory`
7. 引入 `retry` 和三层兜底
8. 接入 LangGraph 状态图
9. 接入 Milvus RAG
10. 接入 BGE-M3 和 BGE-Reranker
11. 前端拆分真实页面
12. 增加日志、异常处理、测试和权限控制

## 17. 当前项目一句话总结

当前项目是一个“考公 AI 助手 MVP 工程骨架”：后端、前端、数据库表、基础 Agent 和主要业务接口已经搭好；现阶段以规则版 Agent 保证基本可用，尚未接入真实 LLM、RAG、LangGraph 和完整三层兜底机制。
