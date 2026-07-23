# Agent 设计

## PositionMatchAgent

目标：根据用户画像和岗位数据，输出可解释的岗位匹配建议。

输入：用户画像、岗位条件、公告政策、专业目录。

输出：可报岗位、不建议报考岗位、风险项说明、“冲稳保”组合、人工核验清单。

工具：`profile_reader`、`position_filter`、`policy_retriever`、`risk_checker`。

规则：硬性条件不满足时不得推荐；不确定时标记为“需人工核验”；推荐必须说明字段依据和政策依据。

## StudyPracticeAgent

目标：围绕目标岗位和考试时间，提供备考计划、知识问答、练习解析和复盘。

输入：目标岗位或考试类型、当前备考阶段、错题和练习记录、考试大纲、题库、申论材料、面试题。

输出：周计划、日计划、行测解释、申论批改、面试追问、错题归因和下一步建议。

工具：`knowledge_retriever`、`study_plan_builder`、`answer_reviewer`、`practice_recorder`。

规则：学习计划要可执行；批改必须指出优点、问题和可修改版本；面试建议要稳健、真实、合规。
