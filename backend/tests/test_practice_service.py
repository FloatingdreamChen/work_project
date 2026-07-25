from backend.services.practice_service import PracticeService


def test_wrong_question_rule_uses_accuracy_score_and_problem_count() -> None:
    service = PracticeService()

    assert service._should_create_wrong_question({"score": 80, "problems": []}, 55) is True
    assert service._should_create_wrong_question({"score": 65, "problems": []}, None) is True
    assert service._should_create_wrong_question({"score": 75, "problems": ["a", "b"]}, None) is True
    assert service._should_create_wrong_question({"score": 80, "problems": ["a"]}, 85) is False


def test_report_keyword_and_suggestions() -> None:
    service = PracticeService()

    keywords = service._extract_keywords("结构不清，审题不准，材料提炼不足")
    suggestions = service._build_suggestions({"申论": 1}, 68, keywords)

    assert "结构" in keywords
    assert any("均分低于70" in item for item in suggestions)


def test_interview_follow_up_stage_and_summary_helpers() -> None:
    service = PracticeService()

    assert service._next_interview_stage(1) == "follow_up"
    assert service._next_interview_stage(3) == "pressure"
    assert service._next_interview_stage(4) == "summary"
    assert "协调资源" in service._fallback_follow_up("follow_up", "我会沟通")

    summary = service._summarize_interview(
        "主题：基层治理",
        [
            {
                "role": "user",
                "review": {"problems": ["结构不清", "例子不足"]},
            }
        ],
    )

    assert "已完成1轮" in summary
    assert "结构不清" in summary
