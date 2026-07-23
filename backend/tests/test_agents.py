from backend.agents.position_match import PositionMatchAgent
from backend.agents.position_match.graph import build_position_match_graph
from backend.agents.study_practice import StudyPracticeAgent
from backend.agents.study_practice.graph import build_study_practice_graph
from backend.config import get_settings
from backend.core.orchestrator import AgentOrchestrator


def test_position_match_agent_flags_risks_and_matches() -> None:
    profile = {
        "education": "本科",
        "degree": "学士",
        "major": "计算机科学与技术",
        "political_status": "共青团员",
        "household_region": "广东",
        "grassroots_experience": "无",
        "work_years": 0,
    }
    positions = [
        {
            "position_name": "一级行政执法员",
            "education_requirement": "本科及以上",
            "degree_requirement": "学士及以上",
            "major_requirement": "计算机科学与技术、软件工程",
            "political_requirement": "不限",
            "household_requirement": "不限",
            "grassroots_requirement": "不限",
            "work_years_requirement": "不限",
            "source_name": "样例岗位表",
        },
        {
            "position_name": "监管岗位",
            "education_requirement": "硕士研究生及以上",
            "degree_requirement": "硕士",
            "major_requirement": "法学",
            "political_requirement": "中共党员",
            "grassroots_requirement": "2年基层工作经历",
            "work_years_requirement": "2年以上",
            "source_name": "样例岗位表",
        },
    ]

    result = PositionMatchAgent().match(profile, positions)

    assert result["items"][0]["position"]["position_name"] == "一级行政执法员"
    assert result["items"][0]["score"] > result["items"][1]["score"]
    assert result["items"][1]["risks"]
    assert "不是官方资格审核结论" in result["disclaimer"]


def test_study_practice_agent_reviews_answer() -> None:
    result = StudyPracticeAgent().review_answer(
        "申论",
        "首先要摸清基层治理中的群众需求，其次要推动资源下沉，最后要完善反馈机制。",
        topic="基层治理",
    )

    assert result["agent"] == "StudyPracticeAgent"
    assert result["score"] >= 45
    assert result["strengths"]
    assert "不承诺" in result["disclaimer"]
    assert "dimension_scores" in result


def test_interview_review_generates_follow_up_question() -> None:
    result = StudyPracticeAgent().review_answer("面试", "首先我会了解情况，其次协调资源。", topic="群众投诉")

    assert result["follow_up_question"]
    assert "真实经历" in result["follow_up_question"]


def test_study_plan_is_personalized_and_minimum_three_months() -> None:
    from datetime import date, timedelta

    plan = StudyPracticeAgent().build_plan(
        target="2027国考",
        exam_date=date.today() + timedelta(days=30),
        daily_hours=3,
        weekly_days=5,
        foundation_level="零基础",
        weak_modules=["行测-数量关系", "申论-大作文"],
        current_scores={"行测-数量关系": 45},
        target_position="税务系统",
    )

    assert plan["planned_days"] >= 90
    assert plan["planned_weeks"] >= 13
    assert plan["min_cycle_enforced"] is True
    assert plan["warning"]
    assert plan["module_weights"]["行测-数量关系"] > plan["module_weights"]["行测-常识"]
    assert plan["weekly_plan"]


def test_orchestrator_uses_agent_fallback_without_api_key() -> None:
    import asyncio

    settings = get_settings()
    settings.openai_api_key = ""
    settings.llm_max_retries = 0

    result = asyncio.run(AgentOrchestrator().chat("请帮我制定申论备考计划"))

    assert result["agent"] == "StudyPracticeAgent"
    assert result["fallback_used"] is True
    assert result["fallback_level"] in {"graph_rule", "agent"}


def test_position_match_graph_runs_multi_node_flow_without_api_key() -> None:
    import asyncio

    settings = get_settings()
    settings.openai_api_key = ""
    settings.llm_max_retries = 0

    graph = build_position_match_graph()
    state = asyncio.run(
        graph.ainvoke(
            {
                "user_message": "我是本科计算机专业2027应届，想报广东国考岗位",
                "positions": [
                    {
                        "position_name": "一级行政执法员",
                        "department": "深圳市税务局",
                        "education_requirement": "本科及以上",
                        "degree_requirement": "不限",
                        "major_requirement": "计算机科学与技术、软件工程",
                        "political_requirement": "不限",
                        "household_requirement": "不限",
                        "grassroots_requirement": "不限",
                        "work_years_requirement": "不限",
                        "source_name": "样例岗位表",
                    }
                ],
            }
        )
    )

    assert state["rule_result"]["items"]
    assert state["match_summary"]["total"] == 1
    assert state["structured_output"]["rule_result"]["items"]
    assert "不是官方资格审核结论" in state["answer"]


def test_study_practice_graph_routes_to_plan_flow_without_api_key() -> None:
    import asyncio

    settings = get_settings()
    settings.openai_api_key = ""
    settings.llm_max_retries = 0

    graph = build_study_practice_graph()
    state = asyncio.run(
        graph.ainvoke(
            {
                "user_message": "请帮我制定申论备考计划，我数量关系比较弱",
                "daily_hours": 2.5,
                "weekly_days": 6,
                "foundation_level": "零基础",
                "weak_modules": ["行测-数量关系"],
            }
        )
    )

    assert state["task_type"] == "plan"
    assert state["plan"]["planned_weeks"] >= 13
    assert state["plan"]["weekly_plan"]
    assert state["structured_output"]["plan"]
    assert "不承诺" in state["answer"]
