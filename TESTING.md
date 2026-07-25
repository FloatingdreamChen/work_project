# 测试与验证说明

本文档记录当前项目可重复执行的验证命令。所有命令均在项目根目录 `/Volumes/XD20/py_project/work_project` 下执行，前端构建命令除外。

## 后端

```bash
python -m compileall backend scripts
python -m pytest backend/tests
```

当前覆盖：

- Agent 基础规则与 LangGraph 多节点流
- 图记忆与节点失败降级
- StudyPracticeAgent 节点级人工中断
- Auth 密码策略、refresh token hash、角色权限基础结构
- 请求并发限制器
- 个性化备考计划、练习报告、错题记录
- 面试多轮追问状态服务
- 岗位专业目录、竞争比、地区偏好、风险偏好、往年分数
- 知识库关键词兜底与本地模型状态探测
- 本地 BGE-M3 语义 RAG 兜底的轻量工具函数
- query classifier 训练数据和领域校准逻辑
- 联网搜索可信度、发布日期抽取、来源元数据
- 岗位导入字段解析与审计
- 数据库初始化 SQL、关键审计表和索引
- 合规清洗与日志敏感信息脱敏
- 上下文记忆、长期记忆字段和敏感信息脱敏

## 本地模型与训练

检查模型状态：

```bash
.venv/bin/python -c "from backend.core.model_registry import LocalModelRegistry; print({k: v.exists for k, v in LocalModelRegistry.status().items()})"
```

训练 query classifier：

```bash
.venv/bin/python scripts/train_query_classifier.py --dry-run
.venv/bin/python scripts/train_query_classifier.py --epochs 1 --batch-size 4
```

当前训练数据：

```text
data/training/query_intents.jsonl
```

## 前端

```bash
cd frontend
npm run build
```

当前覆盖：

- TypeScript 类型检查
- Vue 单文件组件编译
- Vite 生产构建
- Element Plus 组件引用校验

Vite 可能提示 chunk 超过 500 kB，这是构建体积警告，不代表构建失败。

## AI 问答快速检查

不启动外部 LLM/Milvus 时，也可以验证 Agent 编排是否会返回文本：

```bash
.venv/bin/python -c "import asyncio, time; from backend.config import get_settings; from backend.core.orchestrator import AgentOrchestrator; s=get_settings(); old=s.openai_api_key; s.openai_api_key=''; t=time.perf_counter(); r=asyncio.run(AgentOrchestrator().chat('请帮我制定申论备考计划', conversation_id='manual-check')); print({'seconds': round(time.perf_counter()-t, 3), 'agent': r.get('agent'), 'response_mode': r.get('response_mode'), 'fallback_reason': r.get('fallback_reason'), 'route': r.get('route'), 'answer_preview': r.get('answer', '')[:120]}); s.openai_api_key=old"
```

明确的日常、备考计划、批改、面试、问题优化会显示 `route.source=rule_intent`；明确岗位类问题会显示 `route.source=keyword_fast_path`。这些快速路径用于避免首次问答加载本地 classifier 导致慢启动。

## 需要外部服务的验证

以下能力需要先启动依赖服务或配置密钥：

- PostgreSQL：注册、登录、画像、岗位导入、练习记录持久化。
- Milvus/etcd/MinIO：向量知识库 collection 初始化、hybrid search。
- 本地 BGE-M3/BGE-Reranker 模型文件：dense/sparse embedding 和 reranker 精排。
- OpenAI-compatible API key：LLM 解释、润色、对话生成。
- Tavily API key 或可用网络：联网搜索增强。

启动 PostgreSQL 和后端后，可以运行真实 API 冒烟测试：

```bash
.venv/bin/python scripts/smoke_test_api.py --base-url http://localhost:8000
```

它会验证：

- health
- 注册/登录/当前用户
- 用户画像保存
- 知识库状态
- AI 问答是否返回文本
- 申论批改
- 个性化备考计划
- 面试多轮 start/turn
