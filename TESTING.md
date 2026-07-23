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
- 个性化备考计划、练习报告、错题记录
- 岗位专业目录、竞争比、地区偏好、风险偏好、往年分数
- 知识库关键词兜底与本地模型状态探测
- 联网搜索可信度、发布日期抽取、来源元数据
- 岗位导入字段解析与审计
- 数据库初始化 SQL、关键审计表和索引
- 合规清洗与日志敏感信息脱敏

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

## 需要外部服务的验证

以下能力需要先启动依赖服务或配置密钥：

- PostgreSQL：注册、登录、画像、岗位导入、练习记录持久化。
- Milvus/etcd/MinIO：向量知识库 collection 初始化、hybrid search。
- 本地 BGE-M3/BGE-Reranker 模型文件：dense/sparse embedding 和 reranker 精排。
- OpenAI-compatible API key：LLM 解释、润色、对话生成。
- Tavily API key 或可用网络：联网搜索增强。
