from __future__ import annotations

import re
from typing import Any

from backend.agents.position_match import PositionMatchAgent
from backend.agents.position_match.state import PositionMatchState
from backend.core.compliance import POSITION_DISCLAIMER, sanitize_advice
from backend.core.logger import get_logger
from backend.services.source_audit_service import SourceAuditService
from backend.tools.gov_exam_tools import search_knowledge, search_positions, web_search


logger = get_logger(__name__)

CURRENT_KEYWORDS = ("最新", "今年", "公告", "政策", "岗位表", "报名时间", "考试时间", "2026", "2027")


async def parse_profile_node(state: PositionMatchState) -> dict[str, Any]:
    """Parse basic profile and query filters from the user message."""
    message = state.get("user_message", "")
    profile = dict(state.get("profile", {}) or {})
    extracted: dict[str, Any] = {}

    if "本科" in message:
        extracted["education"] = "本科"
    elif "硕士" in message or "研究生" in message:
        extracted["education"] = "硕士研究生"
    elif "博士" in message:
        extracted["education"] = "博士研究生"
    elif "大专" in message:
        extracted["education"] = "大专"

    major_patterns = (
        r"(?:我是|学|专业是)?([\u4e00-\u9fa5A-Za-zA-Z]{2,20})专业",
        r"学([\u4e00-\u9fa5A-Za-zA-Z]{2,20})的",
    )
    for pattern in major_patterns:
        match = re.search(pattern, message)
        if match:
            major = match.group(1).replace("专业", "").replace("本科", "").replace("硕士", "").strip("，。,. ")
            if major and len(major) <= 30:
                extracted["major"] = major
                break

    if "应届" in message:
        extracted["fresh_graduate_status"] = "应届"
    if "党员" in message:
        extracted["political_status"] = "中共党员"
    elif "团员" in message:
        extracted["political_status"] = "共青团员"
    elif "群众" in message:
        extracted["political_status"] = "群众"

    year_match = re.search(r"(20\d{2})", message)
    exam_year = int(year_match.group(1)) if year_match else state.get("exam_year")
    exam_type = "国考" if "国考" in message else "省考" if "省考" in message else state.get("exam_type")
    province = _extract_region(message) or state.get("province") or profile.get("target_region")

    merged_profile = {**profile, **extracted}
    missing = [
        label
        for field, label in (
            ("education", "学历"),
            ("major", "专业"),
            ("fresh_graduate_status", "应届身份"),
        )
        if not merged_profile.get(field)
    ]

    logger.info("position_graph.parse_profile | missing=%s", missing)
    return {
        "profile": merged_profile,
        "extracted_profile": extracted,
        "missing_fields": missing,
        "needs_clarification": len(missing) >= 2 and not state.get("positions"),
        "exam_year": exam_year,
        "exam_type": exam_type,
        "province": province,
        "keyword": merged_profile.get("major") or message[:40],
        "needs_current_info": any(keyword in message for keyword in CURRENT_KEYWORDS),
    }


async def ask_clarification_node(state: PositionMatchState) -> dict[str, Any]:
    missing = state.get("missing_fields", [])
    question = (
        "为了做岗位匹配，请先补充："
        + "、".join(missing)
        + "。如方便，也请说明目标考试年份、地区、政治面貌、基层经历和工作年限。"
    )
    return {
        "clarification_question": question,
        "answer": question,
        "structured_output": {
            "needs_clarification": True,
            "missing_fields": missing,
        },
        "sources": [],
    }


async def retrieve_positions_node(state: PositionMatchState) -> dict[str, Any]:
    if state.get("positions"):
        return {"positions": state["positions"]}
    try:
        positions = await search_positions(
            keyword=state.get("keyword"),
            exam_year=state.get("exam_year"),
            province=state.get("province"),
            limit=12,
        )
    except Exception as exc:
        logger.warning("position_graph.retrieve_positions_failed | error=%s", exc)
        positions = []
    return {"positions": positions}


async def check_hard_conditions_node(state: PositionMatchState) -> dict[str, Any]:
    agent = PositionMatchAgent()
    result = agent.match(state.get("profile", {}), state.get("positions", []))
    return {"rule_result": result}


async def retrieve_policy_node(state: PositionMatchState) -> dict[str, Any]:
    query = state.get("user_message", "")
    knowledge = await search_knowledge(query or "公务员考试岗位资格", top_k=4)
    web_results: list[dict[str, Any]] = []
    if state.get("needs_current_info"):
        try:
            web_results = await web_search(query, max_results=3)
            try:
                await SourceAuditService().save_web_sources(web_results)
            except Exception as exc:
                logger.warning("position_graph.web_source_audit_failed | error=%s", exc)
        except Exception as exc:
            logger.warning("position_graph.web_search_failed | error=%s", exc)
    return {
        "knowledge": knowledge,
        "web_results": web_results,
        "sources": _build_sources(knowledge, web_results),
    }


async def rank_positions_node(state: PositionMatchState) -> dict[str, Any]:
    items = state.get("rule_result", {}).get("items", [])
    summary = {
        "total": len(items),
        "charge": len([item for item in items if item.get("tier") == "冲"]),
        "stable": len([item for item in items if item.get("tier") == "稳"]),
        "safe": len([item for item in items if item.get("tier") == "保"]),
        "not_recommended": len([item for item in items if item.get("tier") == "不建议"]),
        "top_items": items[:5],
    }
    return {"match_summary": summary}


async def generate_answer_node(state: PositionMatchState) -> dict[str, Any]:
    agent = PositionMatchAgent()
    try:
        answer = await agent.explain_with_ai(
            profile=state.get("profile", {}),
            positions=state.get("positions", []),
            rule_result=state.get("rule_result"),
            knowledge=state.get("knowledge", []),
            web_results=state.get("web_results", []),
        )
        return {"answer": answer, "fallback_used": False, "fallback_level": None}
    except Exception as exc:
        logger.warning("position_graph.llm_failed | error=%s", exc)
        answer = _rule_answer(state)
        return {"answer": answer, "fallback_used": True, "fallback_level": "graph_rule"}


async def compliance_check_node(state: PositionMatchState) -> dict[str, Any]:
    answer = state.get("answer", "")
    answer, warnings = sanitize_advice(answer, disclaimer=POSITION_DISCLAIMER)

    structured = {
        "profile": state.get("profile", {}),
        "match_summary": state.get("match_summary", {}),
        "rule_result": state.get("rule_result", {}),
        "sources": state.get("sources", []),
        "fallback_used": state.get("fallback_used", False),
    }
    return {
        "answer": answer,
        "structured_output": structured,
        "compliance_warnings": warnings,
    }


def route_after_parse(state: PositionMatchState) -> str:
    return "clarify" if state.get("needs_clarification") else "continue"


def _rule_answer(state: PositionMatchState) -> str:
    items = state.get("rule_result", {}).get("items", [])
    if not items:
        return (
            "暂未检索到可用于匹配的岗位。请先导入岗位表，或补充考试年份、地区、专业等条件。"
        )
    lines = ["已基于岗位硬性条件完成规则匹配："]
    for item in items[:5]:
        position = item.get("position", {})
        lines.append(
            f"- {item.get('tier')}｜{position.get('position_name', '未命名岗位')}："
            f"{item.get('score')}分；风险：{'；'.join(item.get('risks') or ['暂无明确风险'])}"
        )
    lines.append("涉及资格边界的项目已放入人工核验项，请以官方审核为准。")
    return "\n".join(lines)


def _extract_region(message: str) -> str | None:
    regions = ("北京", "上海", "广东", "深圳", "广州", "江苏", "浙江", "山东", "四川", "湖北", "湖南", "福建")
    for region in regions:
        if region in message:
            return region
    return None


def _build_sources(knowledge: list[dict[str, Any]], web_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources = [
        {
            "name": item.get("source_name", "知识库"),
            "url": item.get("metadata", {}).get("path", ""),
            "source_type": item.get("source_type", "knowledge_base"),
            "published_at": item.get("metadata", {}).get("published_at"),
            "imported_at": item.get("metadata", {}).get("imported_at"),
        }
        for item in knowledge
    ]
    sources.extend(
        {
            "name": item.get("title", "联网搜索"),
            "url": item.get("url", ""),
            "source_type": "web",
            "provider": item.get("provider", ""),
            "published_at": item.get("published_at"),
            "imported_at": item.get("imported_at"),
            "credibility": item.get("credibility"),
            "credibility_reason": item.get("credibility_reason"),
        }
        for item in web_results
    )
    return sources
