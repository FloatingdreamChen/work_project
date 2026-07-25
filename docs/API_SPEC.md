# API 草案

统一响应结构：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

## Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`

注册请求：

```json
{
  "username": "demo",
  "email": "demo@example.com",
  "password": "Demo123456",
  "role": "user"
}
```

说明：

- 密码至少 8 位，必须包含大小写字母和数字。
- 第一个注册用户可成为 `admin`，之后公开注册默认降级为 `user`。
- 登录失败超过 5 次会临时锁定。
- 登录返回 access token 和 refresh token。
- `positions/import`、`knowledge/init-milvus` 需要 admin 权限。

## Profile

- `GET /api/profiles/me`
- `PUT /api/profiles/me`

## Positions

- `POST /api/positions/import`
- `GET /api/positions`
- `POST /api/positions/match`

## Chat

- `POST /api/v1/chat`

请求：

```json
{
  "message": "我计算机专业，2027应届，可以报哪些国考岗位？",
  "conversation_id": "optional"
}
```

响应：

```json
{
  "answer": "string",
  "agent": "PositionMatchAgent",
  "sources": [],
  "conversation_id": "optional",
  "route": {
    "intent": "position_match",
    "confidence": 0.12,
    "source": "local_classifier"
  },
  "structured": {}
}
```

说明：

- 同一 `conversation_id` 会保留 recent turns 和长期画像/学习记忆。
- `GRAPH_MEMORY_BACKEND=memory` 时为进程内记忆。
- `GRAPH_MEMORY_BACKEND=postgres` 时持久化到 `conversation_memories`。
- `GRAPH_MEMORY_BACKEND=redis` 时写入 Redis。
- 路由优先使用本地 `query-classifier-finetuned`，低置信或不可用时回退关键词。

## Knowledge

- `GET /api/v1/knowledge/status`
- `POST /api/v1/knowledge/search`
- `POST /api/v1/knowledge/init-milvus`

状态响应核心字段：

```json
{
  "models": {
    "bge_m3": {"exists": true, "path": "models/embedding/bge-m3"},
    "reranker": {"exists": true, "path": "models/reranker/bge-reranker-large"},
    "classifier": {"exists": true, "path": "models/classifier/all-MiniLM-L6-v2"},
    "finetuned_classifier": {"exists": true, "path": "models/classifier/query-classifier-finetuned"}
  },
  "vector_rag_ready": true,
  "local_semantic_rag_ready": true
}
```

RAG 兜底顺序：

1. Milvus dense + sparse hybrid search。
2. BGE-Reranker 精排。
3. Milvus 不可用时，本地 BGE-M3 dense 检索。
4. 模型不可用时，本地关键词检索。

## Practice

- `POST /api/v1/practice/review`
- `POST /api/v1/practice/plan`
- `POST /api/v1/practice/report`
- `POST /api/v1/practice/interview/start`
- `POST /api/v1/practice/interview/turn`

面试多轮：

```json
{
  "session_id": "uuid",
  "stage": "follow_up",
  "turn_count": 2,
  "current_question": "请结合具体场景继续回答",
  "summary": "已完成2轮..."
}
```

计划请求：

```json
{
  "target_exam": "2027国考",
  "exam_date": "2027-11-28",
  "target_position": "税务系统",
  "province": "广东",
  "daily_hours": 2.5,
  "weekly_days": 6,
  "foundation_level": "零基础",
  "weak_modules": ["行测-数量关系", "申论-大作文"],
  "current_scores": {"行测-数量关系": 45},
  "include_interview": true
}
```

说明：备考计划最短按 90 天 / 13 周起步；距离考试不足三个月时会返回 `warning` 和 `min_cycle_enforced=true`。
