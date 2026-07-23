from backend.agents.position_match import PositionMatchAgent
from backend.agents.study_practice import StudyPracticeAgent


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
