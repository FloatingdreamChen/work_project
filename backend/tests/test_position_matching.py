from backend.agents.position_match import PositionMatchAgent
from backend.core.major_catalog import major_matches, normalize_major


def test_major_catalog_normalizes_related_majors() -> None:
    assert normalize_major("软件工程") == "计算机类"
    assert normalize_major("计算机科学与技术") == "计算机类"

    matched, needs_verify, reason = major_matches("软件工程", "计算机科学与技术、网络工程")

    assert matched is True
    assert needs_verify is True
    assert "计算机类" in reason or "可能匹配" in reason


def test_position_match_uses_competition_region_and_policy_basis() -> None:
    profile = {
        "education": "本科",
        "degree": "学士",
        "major": "软件工程",
        "target_region": "广东",
    }
    positions = [
        {
            "position_name": "低竞争岗位",
            "province": "广东",
            "city": "深圳",
            "recruitment_count": 4,
            "competition_ratio": 20,
            "education_requirement": "本科及以上",
            "degree_requirement": "不限",
            "major_requirement": "计算机科学与技术",
            "political_requirement": "不限",
            "household_requirement": "不限",
            "grassroots_requirement": "不限",
            "work_years_requirement": "不限",
            "source_name": "2027国考岗位表",
            "source_url": "https://example.com/positions",
        },
        {
            "position_name": "高竞争岗位",
            "province": "北京",
            "recruitment_count": 1,
            "competition_ratio": 150,
            "education_requirement": "本科及以上",
            "degree_requirement": "不限",
            "major_requirement": "计算机科学与技术",
            "political_requirement": "不限",
            "household_requirement": "不限",
            "grassroots_requirement": "不限",
            "work_years_requirement": "不限",
            "source_name": "2027国考岗位表",
        },
    ]

    result = PositionMatchAgent().match(profile, positions, preferred_regions=["深圳"], risk_preference="conservative")

    assert result["items"][0]["position"]["position_name"] == "低竞争岗位"
    assert result["items"][0]["policy_basis"]["source_name"] == "2027国考岗位表"
    assert any("地区偏好" in item for item in result["items"][0]["matched"])
    assert any("竞争比" in item for item in result["items"][1]["risks"])


def test_position_match_strategy_and_previous_score_affect_result() -> None:
    profile = {
        "education": "本科",
        "degree": "学士",
        "major": "软件工程",
        "mock_score": 132,
    }
    positions = [
        {
            "position_name": "稳健岗位",
            "recruitment_count": 3,
            "competition_ratio": 25,
            "previous_min_score": 124,
            "education_requirement": "本科及以上",
            "degree_requirement": "不限",
            "major_requirement": "计算机科学与技术",
            "political_requirement": "不限",
            "household_requirement": "不限",
            "grassroots_requirement": "不限",
            "work_years_requirement": "不限",
        },
        {
            "position_name": "分数偏高岗位",
            "recruitment_count": 1,
            "competition_ratio": 120,
            "previous_min_score": 140,
            "education_requirement": "本科及以上",
            "degree_requirement": "不限",
            "major_requirement": "计算机科学与技术",
            "political_requirement": "不限",
            "household_requirement": "不限",
            "grassroots_requirement": "不限",
            "work_years_requirement": "不限",
        },
    ]

    conservative = PositionMatchAgent().match(profile, positions, risk_preference="conservative")
    aggressive = PositionMatchAgent().match(profile, positions, risk_preference="aggressive")

    assert conservative["strategy"]["tier_thresholds"]["冲"] > aggressive["strategy"]["tier_thresholds"]["冲"]
    assert any("往年分数" in item for item in conservative["items"][0]["matched"])
    assert any("往年分数" in item for item in conservative["items"][1]["risks"])
