from __future__ import annotations

from typing import Any

from backend.agents.study_practice import StudyPracticeAgent
from backend.agents.study_practice.state import StudyPracticeState
from backend.core.compliance import STUDY_DISCLAIMER, sanitize_advice
from backend.core.llm_factory import LLMFactory
from backend.core.logger import get_logger
from backend.tools.gov_exam_tools import search_knowledge


logger = get_logger(__name__)


async def classify_task_node(state: StudyPracticeState) -> dict[str, Any]:
    message = state.get("user_message", "")
    category = (state.get("route_info") or {}).get("category")
    if category == "daily_chat" or _is_general_message(message):
        task_type = "general"
    elif category == "question_optimize":
        task_type = "optimize"
    elif category == "study_plan":
        task_type = "plan"
    elif category == "practice_review":
        task_type = "review"
    elif category == "interview":
        task_type = "interview"
    elif category in {"knowledge_qa", "fuzzy_query"}:
        task_type = "qa"
    elif state.get("user_answer"):
        task_type = "review"
    elif "计划" in message or "备考" in message or "安排" in message:
        task_type = "plan"
    elif any(keyword in message for keyword in ("批改", "评分", "打分", "作答", "答案", "帮我看看")):
        task_type = "review"
    elif "面试" in message:
        task_type = "interview"
    else:
        task_type = "qa"

    practice_type = state.get("practice_type")
    if not practice_type:
        practice_type = "面试" if "面试" in message else "申论" if "申论" in message else "行测"

    return {
        "task_type": task_type,
        "question_category": category,
        "practice_type": practice_type,
        "topic": state.get("topic") or _infer_topic(message),
        "user_answer": state.get("user_answer") or (message if task_type == "review" else ""),
        "target_exam": state.get("target_exam") or "公务员考试",
        "daily_hours": state.get("daily_hours") or 2.0,
        "weekly_days": state.get("weekly_days") or 6,
        "foundation_level": state.get("foundation_level") or _infer_foundation(message),
        "weak_modules": state.get("weak_modules") or _infer_weak_modules(message),
        "strong_modules": state.get("strong_modules") or [],
        "preferred_modules": state.get("preferred_modules") or [],
        "current_scores": state.get("current_scores") or {},
        "include_interview": state.get("include_interview", True),
        "weeks": state.get("weeks") or 13,
    }


async def retrieve_material_node(state: StudyPracticeState) -> dict[str, Any]:
    if state.get("task_type") == "general":
        return {"knowledge": [], "sources": []}
    query = " ".join(
        part
        for part in [
            state.get("practice_type", ""),
            state.get("topic") or "",
            state.get("question") or "",
            state.get("user_message", ""),
        ]
        if part
    )
    knowledge = await search_knowledge(query or "公务员考试备考", top_k=4)
    return {
        "knowledge": knowledge,
        "sources": [
            {"name": item.get("source_name", "知识库"), "url": item.get("metadata", {}).get("path", "")}
            for item in knowledge
        ],
    }


async def detect_human_interrupt_node(state: StudyPracticeState) -> dict[str, Any]:
    message = state.get("user_message", "")
    explicit = bool(state.get("human_interrupt"))
    keywords = ("转人工", "人工中断", "人工审核", "老师看一下", "暂停自动")
    needs = explicit or any(keyword in message for keyword in keywords)
    if not needs:
        return {"needs_human_interrupt": False, "interrupt_reason": None}
    reason = "用户请求人工介入" if not explicit else "上游状态要求人工介入"
    return {"needs_human_interrupt": True, "interrupt_reason": reason}


async def human_interrupt_node(state: StudyPracticeState) -> dict[str, Any]:
    reason = state.get("interrupt_reason") or "需要人工处理"
    answer = (
        f"已暂停自动生成，当前节点进入人工处理中断：{reason}。"
        "请由老师或管理员查看用户答案、知识库来源和练习记录后继续处理。"
    )
    return {
        "answer": answer,
        "fallback_used": False,
        "fallback_level": "human_interrupt",
        "response_mode": "human_interrupt",
        "structured_output": {
            "task_type": state.get("task_type"),
            "practice_type": state.get("practice_type"),
            "needs_human_interrupt": True,
            "interrupt_reason": reason,
            "sources": state.get("sources", []),
        },
    }


async def build_plan_node(state: StudyPracticeState) -> dict[str, Any]:
    agent = StudyPracticeAgent()
    plan = agent.build_plan(
        target=state.get("target_exam") or state.get("topic") or "公务员考试",
        weeks=state.get("weeks"),
        exam_date=state.get("exam_date"),
        daily_hours=state.get("daily_hours", 2.0),
        weekly_days=state.get("weekly_days", 6),
        foundation_level=state.get("foundation_level", "零基础"),
        weak_modules=state.get("weak_modules", []),
        strong_modules=state.get("strong_modules", []),
        preferred_modules=state.get("preferred_modules", []),
        current_scores=state.get("current_scores", {}),
        target_position=state.get("target_position"),
        include_interview=state.get("include_interview", True),
    )
    return {"plan": plan}


async def review_answer_node(state: StudyPracticeState) -> dict[str, Any]:
    agent = StudyPracticeAgent()
    review = agent.review_answer(
        practice_type=state.get("practice_type", "申论"),
        user_answer=state.get("user_answer", ""),
        topic=state.get("topic"),
        question=state.get("question"),
    )
    return {"review": review}


async def generate_response_node(state: StudyPracticeState) -> dict[str, Any]:
    if state.get("task_type") in {"general", "optimize"}:
        return {
            "answer": _rule_answer(state),
            "fallback_used": False,
            "fallback_level": None,
            "response_mode": "local_rule",
        }

    prompt = (
        "你是公务员考试备考教练。请基于任务类型、知识库片段和规则结果回答。"
        "要求具体、可执行，不承诺进面、录取或上岸，不提供作弊建议。"
    )
    user_content = (
        f"任务类型：{state.get('task_type')}\n"
        f"练习类型：{state.get('practice_type')}\n"
        f"用户输入：{state.get('user_message')}\n"
        f"长期记忆：{state.get('long_term_memory', {})}\n"
        f"最近对话：{state.get('recent_turns', [])}\n"
        f"规则计划：{state.get('plan', {})}\n"
        f"规则批改：{state.get('review', {})}\n"
        f"知识库片段：{state.get('knowledge', [])}\n"
        "请输出最终回答。"
    )
    try:
        answer = await LLMFactory.ainvoke(
            [{"role": "user", "content": user_content}],
            agent_type="study_practice",
            temperature=0.3,
            system_prompt=prompt,
        )
        return {"answer": answer, "fallback_used": False, "fallback_level": None, "response_mode": "llm"}
    except Exception as exc:
        logger.warning("study_graph.llm_failed | error=%s", exc)
        reason = "已使用本地规则和知识库生成回答。"
        return {
            "answer": _fallback_answer(state, reason),
            "fallback_used": True,
            "fallback_level": "graph_rule",
            "response_mode": "fallback_rule",
            "fallback_reason": reason,
        }


async def compliance_check_node(state: StudyPracticeState) -> dict[str, Any]:
    answer = state.get("answer", "")
    if state.get("task_type") == "general":
        warnings = []
    else:
        answer, warnings = sanitize_advice(answer, disclaimer=STUDY_DISCLAIMER)
    structured = {
        **state.get("structured_output", {}),
        "task_type": state.get("task_type"),
        "question_category": state.get("question_category"),
        "route_info": state.get("route_info"),
        "practice_type": state.get("practice_type"),
        "plan": state.get("plan"),
        "review": state.get("review"),
        "sources": state.get("sources", []),
        "fallback_used": state.get("fallback_used", False),
        "fallback_level": state.get("fallback_level"),
        "response_mode": state.get("response_mode"),
        "fallback_reason": state.get("fallback_reason"),
    }
    return {
        "answer": answer,
        "structured_output": structured,
        "compliance_warnings": warnings,
    }


async def save_learning_record_node(state: StudyPracticeState) -> dict[str, Any]:
    # API-specific practice persistence still lives in practice_service.
    return {"structured_output": {**state.get("structured_output", {}), "saved_by_graph": False}}


def route_by_task_type(state: StudyPracticeState) -> str:
    if state.get("task_type") == "plan":
        return "plan"
    if state.get("task_type") == "review":
        return "review"
    if state.get("task_type") == "interview":
        return "interview"
    if state.get("task_type") == "general":
        return "general"
    if state.get("task_type") == "optimize":
        return "optimize"
    if state.get("task_type") == "qa":
        return "qa"
    if state.get("review") or state.get("user_answer"):
        return "review"
    return "review"


def route_by_interrupt(state: StudyPracticeState) -> str:
    return "interrupt" if state.get("needs_human_interrupt") else "continue"


def _rule_answer(state: StudyPracticeState) -> str:
    if state.get("task_type") == "general":
        message = state.get("user_message", "").strip()
        if any(keyword in message for keyword in ("你是谁", "你能做什么", "你能干什么", "你能干嘛", "有什么功能", "功能")):
            return (
                "我是考公 AI 助手，可以帮你做五类事情：\n"
                "1. 整理用户画像，保存学历、专业、应届身份等报考条件。\n"
                "2. 基于岗位表做岗位匹配，提示资格风险和人工核验项。\n"
                "3. 生成三个月以上的个性化备考计划。\n"
                "4. 查询知识库中的政策、报考和备考资料。\n"
                "5. 进行 AI 问答和面试多轮追问。"
            )
        if any(keyword in message for keyword in ("你好吗", "在吗", "你在吗")):
            return "我在，可以继续帮你分析岗位、备考计划、知识库资料或面试问题。"
        return (
            "你好，我是考公 AI 助手。你可以问我岗位报考条件、资格风险、备考计划、"
            "行测/申论题目解析、申论批改或面试模拟。"
        )
    if state.get("task_type") == "optimize":
        optimized = _optimize_question(state.get("user_message", ""))
        return (
            f"我先把你的问题整理为：{optimized}\n\n"
            "基于这个问题，我建议你补充目标考试、省份/城市、当前基础、可投入时间和薄弱模块。"
            "如果你要我直接回答，可以把整理后的问题发出，或继续补充你的个人情况。"
        )
    if state.get("task_type") == "plan":
        plan = state.get("plan", {})
        weeks = plan.get("weekly_plan", plan.get("plan", []))
        lines = [
            f"建议按 {plan.get('planned_weeks', len(weeks) or 13)} 周推进，"
            f"每周约 {plan.get('weekly_hours')} 小时。"
        ]
        if plan.get("warning"):
            lines.append(f"提醒：{plan['warning']}")
        lines.append("模块权重：" + "；".join(f"{k}:{v}" for k, v in plan.get("module_weights", {}).items()))
        for week in weeks[:8]:
            lines.append(f"- 第{week.get('week')}周｜{week.get('phase')}｜重点：{week.get('focus')}；任务：{'；'.join(week.get('tasks', [])[:3])}")
        if len(weeks) > 8:
            lines.append(f"... 后续还有 {len(weeks) - 8} 周计划，按阶段里程碑继续推进。")
        return "\n".join(lines)
    if state.get("task_type") == "interview":
        return (
            "可以。我可以按结构化面试流程陪你练习。你可以先告诉我目标岗位、题目方向，"
            "或直接发送一道面试题和你的作答；如果需要多轮追问，建议使用面试模拟入口。"
        )
    if state.get("task_type") == "qa":
        message = state.get("user_message", "")
        if "申论" in message:
            return (
                "申论建议按“材料阅读-要点提炼-小题作答-大作文表达”四条线推进：\n"
                "1. 每天做 1 组材料阅读，训练找主体、问题、原因、对策和关键词。\n"
                "2. 每周至少完成 2-3 道小题，重点练概括、综合分析、提出对策。\n"
                "3. 大作文先搭结构，再补论证素材，不要一开始只背范文。\n"
                "4. 每次练完要复盘丢分原因，比如漏点、语言不规范、逻辑跳跃或对策空泛。\n"
                "你可以继续发一段申论作答，我可以按维度帮你批改。"
            )
        if "行测" in message:
            return (
                "行测建议先做模块诊断，再按薄弱项专项训练。言语和判断重稳定正确率，"
                "资料分析重公式和速度，数量关系可先抓高频题型，常识重长期积累。"
                "如果你告诉我各模块正确率和每天学习时间，我可以给你排一个三个月以上的计划。"
            )
        high_confidence = [
            item for item in state.get("knowledge", [])
            if item.get("is_high_confidence") or item.get("confidence", 0) >= 0.65
        ]
        if high_confidence:
            snippets = "\n".join(f"- {item.get('content', '')[:160]}" for item in high_confidence[:3])
            return f"我先根据当前知识库给你一个参考：\n{snippets}\n\n你也可以补充目标考试、地区、专业或当前分数，我会进一步细化。"
        return (
            "我可以继续帮你分析。请补充你的具体问题，例如目标考试、地区、专业、薄弱模块、"
            "题目材料或你的作答内容。"
        )
    review = state.get("review", {})
    return (
        f"评分：{review.get('score')}\n"
        f"优点：{'；'.join(review.get('strengths', []))}\n"
        f"问题：{'；'.join(review.get('problems', []))}\n"
        f"优化示例：{review.get('improved_answer', '')}\n"
        f"下一步：{'；'.join(review.get('next_steps', []))}"
    )


def _fallback_answer(state: StudyPracticeState, reason: str) -> str:
    return (
        f"{reason}以下内容不会编造实时政策，只基于当前问题分类、已导入资料和规则生成。\n\n"
        f"{_rule_answer(state)}"
    )


def _optimize_question(message: str) -> str:
    cleaned = message.strip()
    for prefix in ("润色一下", "优化一下", "改写一下", "整理一下", "润色", "优化", "改写", "帮我", "请"):
        cleaned = cleaned.replace(prefix, "", 1).strip(" ：:，,")
    cleaned = cleaned.removeprefix("一下").strip(" ：:，,")
    if cleaned.startswith("我怎么问"):
        cleaned = cleaned.removeprefix("我怎么问").strip(" ：:，,")
    if "申论怎么学" in cleaned:
        return "申论应该如何系统学习，并在三个月以上周期内提升小题和大作文能力？"
    if not cleaned:
        return "请根据我的目标考试、基础水平和可投入时间，生成一份可执行的备考建议。"
    if "?" in cleaned or "？" in cleaned:
        return cleaned
    return f"{cleaned}？"


def _infer_topic(message: str) -> str:
    if "基层" in message:
        return "基层治理"
    if "数量" in message or "资料分析" in message:
        return "行测专项"
    if "面试" in message:
        return "结构化面试"
    return "公务员考试备考"


def _is_general_message(message: str) -> bool:
    normalized = message.strip().lower()
    greetings = {
        "你好",
        "您好",
        "hi",
        "hello",
        "在吗",
        "嗨",
        "哈喽",
        "早上好",
        "下午好",
        "晚上好",
    }
    return normalized in greetings or normalized.rstrip("！？?!。.") in greetings


def _infer_foundation(message: str) -> str:
    if "零基础" in message or "刚开始" in message or "小白" in message:
        return "零基础"
    if "有基础" in message or "学过" in message:
        return "有基础"
    if "较好" in message or "还可以" in message:
        return "较好"
    return "一般"


def _infer_weak_modules(message: str) -> list[str]:
    modules = []
    mapping = {
        "数量": "行测-数量关系",
        "资料": "行测-资料分析",
        "言语": "行测-言语理解",
        "判断": "行测-判断推理",
        "常识": "行测-常识",
        "申论": "申论-小题",
        "作文": "申论-大作文",
        "面试": "面试-表达与素材",
    }
    for keyword, module in mapping.items():
        if keyword in message and any(flag in message for flag in ("弱", "差", "不会", "薄弱", "低")):
            modules.append(module)
    return modules
