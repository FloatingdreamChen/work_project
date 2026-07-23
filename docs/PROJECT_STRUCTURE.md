# 项目框架

```text
work_project/
  backend/
    main.py
    api/routes/
    agents/position_match/
    agents/study_practice/
    core/
    models/
    services/
    schemas/
    tests/
  frontend/src/
    api/
    components/
    router/
    stores/
    views/
  docs/
  scripts/
  data/
```

## 设计原则

- 后端保持 API、Service、Agent、Model 分层。
- Agent 不直接操作数据库，优先通过 Service 或 Tool 调用。
- 前端优先构建真实工作台：岗位匹配、学习计划、练习区。
- RAG 知识库和结构化岗位表分开管理。
