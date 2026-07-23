# AGENTS.md

本文件约束后续 AI 编程代理在本项目中的工作方式。

## 项目边界

- 当前新项目根目录：`/Volumes/XD20/py_project/work_project`
- 可参考项目：`/Users/chenshuaiwen/new_eduagent`
- 严禁修改、删除、移动、覆盖 `/Users/chenshuaiwen/new_eduagent` 下的任何文件。
- 允许读取 `/Users/chenshuaiwen/new_eduagent` 的代码、配置和文档，用于理解技术栈、目录结构、启动方式和工程风格。
- 所有新项目产物必须写入 `/Volumes/XD20/py_project/work_project`。

## 项目定位

本项目是“考公 AI 助手”，面向公务员考试用户，核心能力包括岗位匹配、资格风险检查、备考计划、题目解析、申论批改和面试模拟。

## 技术栈要求

尽量沿用参考项目的技术栈：

- Backend：Python 3.11、FastAPI、Uvicorn、Pydantic、SQLAlchemy Async、asyncpg。
- Agent：LangGraph、LangChain、OpenAI-compatible LLM API。
- RAG：Milvus、BGE-M3、BGE-Reranker。
- Frontend：Vue 3、Vite、TypeScript、Pinia、Vue Router、Element Plus。
- Infra：Docker Compose、PostgreSQL、Milvus、etcd、MinIO。
- Python 环境：优先使用 uv 创建和管理本地 `.venv`。

## Agent 数量

只设计 1-2 个 Agent，不复刻原项目的多 Agent 复杂度。

推荐：

1. `PositionMatchAgent`
   - 解析用户画像：学历、专业、应届身份、基层经历、政治面貌、户籍、证书、工作年限等。
   - 过滤岗位硬性条件。
   - 输出岗位匹配度、资格风险、材料准备建议。
   - 给出“冲、稳、保”岗位组合，但必须说明依据。

2. `StudyPracticeAgent`
   - 生成备考计划。
   - 支持行测、申论、面试问答。
   - 支持题目解析、申论批改、面试追问。
   - 根据用户练习记录调整学习建议。

## 安全与合规

- 不得承诺“必上岸”“保证进面”“保证录取”。
- 不得鼓励用户伪造学历、经历、证书、党员身份、基层经历等资格材料。
- 涉及岗位资格判断时必须说明依据来源，数据不足时应提示人工核验。
- 对政策、公告、岗位表等强时效信息，必须保留来源、发布日期和导入时间。
- 用户个人信息要最小化采集，敏感信息不得进入日志。

## 开发优先级

1. 跑通基础服务：FastAPI、PostgreSQL、Milvus、前端 Vite。
2. 跑通登录与用户画像。
3. 跑通岗位表导入、岗位检索、岗位匹配。
4. 跑通知识库导入与 RAG 问答。
5. 接入 `PositionMatchAgent`。
6. 接入 `StudyPracticeAgent`。
7. 增加前端页面、测试、日志和异常处理。

## 质量要求

- 保持接口清晰，后端返回统一响应结构。
- 重要流程写最小可用测试。
- 复杂 Agent 状态建议使用 LangGraph 显式建模。
- 前端页面优先做真实可用工作台，不做营销式落地页。
- 新增依赖前先检查是否已有同类库。
