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
