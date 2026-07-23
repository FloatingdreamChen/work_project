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
    if state.get("user_answer"):
        task_type = "review"
    elif "计划" in message or "备考" in message or "安排" in message:
        task_type = "plan"
    elif "面试" in message:
        task_type = "interview"
    elif "申论" in message or "批改" in message:
        task_type = "review"
    else:
        task_type = "qa"

    practice_type = state.get("practice_type")
    if not practice_type:
        practice_type = "面试" if "面试" in message else "申论" if "申论" in message else "行测"

    return {
        "task_type": task_type,
        "practice_type": practice_type,
        "topic": state.get("topic") or _infer_topic(message),
        "user_answer": state.get("user_answer") or message,
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
    prompt = (
        "你是公务员考试备考教练。请基于任务类型、知识库片段和规则结果回答。"
        "要求具体、可执行，不承诺进面、录取或上岸，不提供作弊建议。"
    )
    user_content = (
        f"任务类型：{state.get('task_type')}\n"
        f"练习类型：{state.get('practice_type')}\n"
        f"用户输入：{state.get('user_message')}\n"
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
        return {"answer": answer, "fallback_used": False, "fallback_level": None}
    except Exception as exc:
        logger.warning("study_graph.llm_failed | error=%s", exc)
        return {
            "answer": _rule_answer(state),
            "fallback_used": True,
            "fallback_level": "graph_rule",
        }


async def compliance_check_node(state: StudyPracticeState) -> dict[str, Any]:
    answer = state.get("answer", "")
    answer, warnings = sanitize_advice(answer, disclaimer=STUDY_DISCLAIMER)
    structured = {
        "task_type": state.get("task_type"),
        "practice_type": state.get("practice_type"),
        "plan": state.get("plan"),
        "review": state.get("review"),
        "sources": state.get("sources", []),
        "fallback_used": state.get("fallback_used", False),
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
    return "review"


def _rule_answer(state: StudyPracticeState) -> str:
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
    review = state.get("review", {})
    return (
        f"评分：{review.get('score')}\n"
        f"优点：{'；'.join(review.get('strengths', []))}\n"
        f"问题：{'；'.join(review.get('problems', []))}\n"
        f"优化示例：{review.get('improved_answer', '')}\n"
        f"下一步：{'；'.join(review.get('next_steps', []))}"
    )


def _infer_topic(message: str) -> str:
    if "基层" in message:
        return "基层治理"
    if "数量" in message or "资料分析" in message:
        return "行测专项"
    if "面试" in message:
        return "结构化面试"
    return "公务员考试备考"


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
