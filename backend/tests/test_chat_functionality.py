import asyncio

from backend.config import get_settings
from backend.core.orchestrator import AgentOrchestrator


def test_chat_uses_keyword_fast_path_before_local_classifier(monkeypatch) -> None:
    import backend.core.orchestrator as orchestrator_module

    def broken_classifier(_: str):
        raise AssertionError("classifier should not run for obvious practice query")

    monkeypatch.setattr(orchestrator_module, "classify_query", broken_classifier)
    orchestrator = AgentOrchestrator()

    agent = orchestrator.route("请帮我制定申论备考计划")

    assert agent == "StudyPracticeAgent"
    assert orchestrator._last_route_info["source"] == "rule_intent"
    assert orchestrator._last_route_info["category"] == "study_plan"
    assert orchestrator._last_route_info["category_label"] == "备考计划"


def test_chat_returns_answer_without_llm_or_deep_rag() -> None:
    settings = get_settings()
    old_values = {
        "openai_api_key": settings.openai_api_key,
        "llm_max_retries": settings.llm_max_retries,
        "enable_local_models": settings.enable_local_models,
        "enable_milvus_rag": settings.enable_milvus_rag,
        "enable_local_semantic_rag": settings.enable_local_semantic_rag,
        "enable_query_classifier": settings.enable_query_classifier,
    }
    settings.openai_api_key = ""
    settings.llm_max_retries = 0
    settings.enable_local_models = False
    settings.enable_milvus_rag = False
    settings.enable_local_semantic_rag = False
    settings.enable_query_classifier = False

    try:
        result = asyncio.run(AgentOrchestrator().chat("请帮我制定申论备考计划", conversation_id="chat-test"))
    finally:
        for key, value in old_values.items():
            setattr(settings, key, value)

    assert result["agent"] == "StudyPracticeAgent"
    assert result["answer"]
    assert "建议" in result["answer"] or "AI 深度批改暂时不可用" in result["answer"]
    assert result["conversation_id"] == "chat-test"
    assert result["response_mode"] in {"fallback_rule", "local_rule", "system_fallback"}


def test_general_greeting_does_not_enter_review_flow() -> None:
    settings = get_settings()
    old_api_key = settings.openai_api_key
    settings.openai_api_key = ""

    try:
        result = asyncio.run(AgentOrchestrator().chat("你好", conversation_id="hello-test"))
    finally:
        settings.openai_api_key = old_api_key

    assert result["agent"] == "StudyPracticeAgent"
    assert result["route"]["category"] == "daily_chat"
    assert result["response_mode"] == "local_rule"
    assert result["structured"]["task_type"] == "general"
    assert "你好" in result["answer"]
    assert "评分" not in result["answer"]
    assert "优点" not in result["answer"]
    assert "问题" not in result["answer"]


def test_plain_study_question_does_not_enter_review_flow() -> None:
    settings = get_settings()
    old_api_key = settings.openai_api_key
    settings.openai_api_key = ""

    try:
        result = asyncio.run(AgentOrchestrator().chat("申论怎么学", conversation_id="qa-test"))
    finally:
        settings.openai_api_key = old_api_key

    assert result["structured"]["task_type"] == "qa"
    assert result["route"]["category"] == "knowledge_qa"
    assert result["response_mode"] == "fallback_rule"
    assert result["fallback_reason"]
    assert result["structured"].get("review") is None
    assert "评分" not in result["answer"]
    assert "材料阅读" in result["answer"]


def test_question_optimize_uses_optimize_flow() -> None:
    settings = get_settings()
    old_api_key = settings.openai_api_key
    settings.openai_api_key = ""

    try:
        result = asyncio.run(AgentOrchestrator().chat("润色一下我怎么问申论怎么学", conversation_id="optimize-test"))
    finally:
        settings.openai_api_key = old_api_key

    assert result["route"]["category"] == "question_optimize"
    assert result["structured"]["task_type"] == "optimize"
    assert "我先把你的问题整理为" in result["answer"]
    assert "一下我怎么问" not in result["answer"]
    assert "评分" not in result["answer"]


def test_chat_category_hint_overrides_ambiguous_route() -> None:
    settings = get_settings()
    old_api_key = settings.openai_api_key
    settings.openai_api_key = ""

    try:
        result = asyncio.run(
            AgentOrchestrator().chat(
                "帮我看看申论怎么学",
                conversation_id="hint-test",
                category_hint="question_optimize",
            )
        )
    finally:
        settings.openai_api_key = old_api_key

    assert result["route"]["source"] == "user_hint"
    assert result["route"]["category"] == "question_optimize"
    assert result["structured"]["task_type"] == "optimize"
    assert "评分" not in result["answer"]
