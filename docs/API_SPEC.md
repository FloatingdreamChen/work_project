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

- `POST /api/auth/register`
- `POST /api/auth/login`

## Profile

- `GET /api/profiles/me`
- `PUT /api/profiles/me`

## Positions

- `POST /api/positions/import`
- `GET /api/positions`
- `POST /api/positions/match`

## Chat

- `POST /api/chat`

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
  "sources": []
}
```

## Practice

- `POST /api/practice/review`
- `POST /api/practice/plan`
- `POST /api/practice/report`

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
